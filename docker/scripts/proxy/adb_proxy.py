import asyncio
import logging
import binascii
import os
from datetime import datetime
import re

# 定义配置变量
PROXY_LISTEN_HOST = '0.0.0.0'
PROXY_LISTEN_PORT = 5037
ADB_SERVER_HOST = '127.0.0.1'
ADB_SERVER_PORT = 5038
USER_ID_FILE_PATH = '/tmp/adb_proxy_user_id.txt'

# 从环境变量获取日志级别，默认为INFO
LOG_LEVEL = os.getenv('ADB_PROXY_LOG_LEVEL', 'INFO').upper()

# 日志级别映射
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
    'NONE': logging.CRITICAL + 1  # 自定义级别，用于关闭所有日志
}

# 获取日志级别
if LOG_LEVEL == 'NONE':
    # 完全关闭日志
    logging.basicConfig(
        level=logging.CRITICAL + 1,
        handlers=[]
    )
else:
    # 设置日志级别
    level = LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger("adb_proxy")

def get_user_id_from_file():
    """
    从文件读取 userId，如果文件不存在或读取失败则返回默认值
    """
    try:
        if os.path.exists(USER_ID_FILE_PATH):
            with open(USER_ID_FILE_PATH, 'r', encoding='utf-8') as f:
                user_id = f.read().strip()
                if user_id:
                    logger.info(f"📁 从文件读取到 userId: {user_id}")
                    return user_id
                else:
                    logger.warning("📁 userId 文件存在但为空")
        else:
            logger.debug("📁 userId 文件不存在")
    except Exception as e:
        logger.error(f"❌ 读取 userId 文件失败: {e}")
    
    # 返回默认值
    default_user_id = "u10_"
    logger.info(f"🔄 使用默认 userId: {default_user_id}")
    return default_user_id

# 添加启动日志
logger.info("ADB 代理脚本开始启动")
logger.info(f"代理监听地址: {PROXY_LISTEN_HOST}:{PROXY_LISTEN_PORT}")
logger.info(f"目标ADB服务地址: {ADB_SERVER_HOST}:{ADB_SERVER_PORT}")
logger.info(f"日志级别: {LOG_LEVEL}")
logger.info(f"userId 文件路径: {USER_ID_FILE_PATH}")

# Hook函数：修改ps命令
def hook_ps_command(data: bytes) -> bytes:
    """
    修改ps命令，在ps && ps -A后面添加| grep 'u10_'过滤条件
    同时处理ADB协议的长度字段
    """
    try:
        str_data = data.decode('utf-8', errors='replace')
        
        # 匹配ps && ps -A命令
        if 'ps && ps -A' in str_data:
            logger.info(f"🔍 检测到ps命令: {str_data.strip()}")
            
            # 解析ADB协议格式：长度+命令
            # 例如：0011shell:ps && ps -A
            # 0011是长度，shell:ps && ps -A是命令
            if len(str_data) >= 4:
                try:
                    # 提取长度字段（前4个字符）
                    length_str = str_data[:4]
                    original_length = int(length_str, 16)
                    
                    # 提取命令部分（从第5个字符开始）
                    command_part = str_data[4:]
                    
                    # 动态获取 userId
                    user_id = get_user_id_from_file()
                    
                    # 只有当 userId 不为空且不是默认值时才进行替换
                    if user_id:
                        # 修改命令，使用动态的 userId
                        modified_command = command_part.replace('ps && ps -A', f'ps && ps -A | grep \'{user_id}\'')
                        logger.info(f"🔧 使用 userId '{user_id}' 修改 ps 命令")
                    else:
                        # userId 为空或默认值，保持原始命令不变
                        modified_command = command_part
                        logger.info("🔄 userId 为空或默认值，保持原始 ps 命令不变")
                    
                    # 计算新的长度
                    new_length = len(modified_command)
                    new_length_hex = f"{new_length:04x}"
                    
                    # 构建新的ADB协议数据
                    new_str_data = new_length_hex + modified_command
                    
                    logger.info(f"📏 原始长度: {original_length} (0x{length_str})")
                    logger.info(f"📏 新长度: {new_length} (0x{new_length_hex})")
                    logger.info(f"✅ 修改后的命令: {new_str_data.strip()}")
                    
                    return new_str_data.encode('utf-8')
                    
                except ValueError as e:
                    logger.error(f"❌ 长度字段解析失败: {e}")
                    return data
            else:
                logger.error(f"❌ 数据格式错误，长度不足4字符: {str_data}")
                return data
        else:
            # 如果不是目标命令，记录原始数据（仅在DEBUG级别）
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"📝 原始请求: {str_data.strip()}")
            
    except Exception as e:
        logger.error(f"❌ hook_ps_command 异常: {e}")
    
    return data

async def request_hook(data: bytes, peername=None) -> bytes:
    # 应用ps命令hook
    modified_data = hook_ps_command(data)
    
    # TODO: 可在此处添加其他请求修改逻辑
    # logger.info(f"request_hook: {data} , peername: {peername}")
    
    return modified_data

async def response_hook(data: bytes, peername=None) -> bytes:
    # TODO: 可在此处修改响应内容
    logger.info(f"response_hook: {data} , peername: {peername}")
    return data

def log_data(prefix, data, peername=None):
    try:
        str_data = data.decode('utf-8', errors='replace')
    except Exception as e:
        str_data = str(data)
    logger.info(f"{prefix} [{peername}]\nSTR: {str_data}")

class ProxyConnection:
    def __init__(self, client_reader, client_writer, peername):
        self.client_reader = client_reader
        self.client_writer = client_writer
        self.peername = peername
        self.server_reader = None
        self.server_writer = None
        self.client_closed = False
        self.server_closed = False

    async def start(self):
        try:
            logger.info(f"新连接: {self.peername}")
            self.server_reader, self.server_writer = await asyncio.open_connection(
                ADB_SERVER_HOST, ADB_SERVER_PORT)
            logger.info(f"已连接到真实 adb 服务: {ADB_SERVER_HOST}:{ADB_SERVER_PORT}")
            await asyncio.gather(
                self.pipe(self.client_reader, self.server_writer, 'C->S', request_hook, 'client'),
                self.pipe(self.server_reader, self.client_writer, 'S->C', response_hook, 'server')
            )
        except Exception as e:
            logger.error(f"连接处理异常: {e}")
        finally:
            await self.close()

    async def pipe(self, reader, writer, direction, hook, which):
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    logger.info(f"{direction} 连接关闭 [{self.peername}]")
                    try:
                        writer.write_eof()
                        await writer.drain()
                    except Exception as e:
                        logger.debug(f"{direction} 写入 EOF 异常: {e}")
                    if which == 'client':
                        self.client_closed = True
                    else:
                        self.server_closed = True
                    break
                log_data(direction, data, self.peername)
                data = await hook(data, self.peername)
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logger.error(f"{direction} 管道异常: {e}")

    async def close(self):
        if self.client_writer and not self.client_writer.is_closing():
            self.client_writer.close()
            await self.client_writer.wait_closed()
        if self.server_writer and not self.server_writer.is_closing():
            self.server_writer.close()
            await self.server_writer.wait_closed()
        logger.info(f"连接关闭: {self.peername}")

async def handle_client(client_reader, client_writer):
    peername = client_writer.get_extra_info('peername')
    conn = ProxyConnection(client_reader, client_writer, peername)
    await conn.start()

async def main():
    server = await asyncio.start_server(
        handle_client, PROXY_LISTEN_HOST, PROXY_LISTEN_PORT)
    addr = server.sockets[0].getsockname()
    logger.info(f"ADB 代理启动，监听 {addr}")
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("ADB 代理已退出") 
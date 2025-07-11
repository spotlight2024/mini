import asyncio
import logging
import binascii
import os
from datetime import datetime
import re

# 日志配置
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, 'proxy.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("adb_proxy")

PROXY_LISTEN_HOST = '0.0.0.0'
PROXY_LISTEN_PORT = 5037
ADB_SERVER_HOST = '127.0.0.1'
ADB_SERVER_PORT = 5038

# 预留的 hook
def replace_webview_devtools_pid(data: bytes, new_pid: str) -> bytes:
    """
    替换 grep -a '@webview_devtools_remote_.*' /proc/net/unix 命令中的 pid 为 new_pid。
    如果不是该命令，原样返回。
    """
    try:
        str_data = data.decode('utf-8', errors='replace')
        pattern = r"grep -a '@webview_devtools_remote_.*?(\\d+)' /proc/net/unix"
        match = re.search(pattern, str_data)
        if match:
            new_str_data = re.sub(r"(@webview_devtools_remote_)\\d+", r"\\1" + new_pid, str_data)
            return new_str_data.encode('utf-8')
    except Exception as e:
        logger.error(f"replace_webview_devtools_pid 异常: {e}")
    return data

async def request_hook(data: bytes, peername=None) -> bytes:
    # TODO: 可在此处修改请求内容
    # logger.info(f"request_hook: {data} , peername: {peername}")
    # 这里不直接写替换逻辑，只调用方法
    # new_pid = "YOUR_PID"  # 由外部调用时传入
    # return replace_webview_devtools_pid(data, new_pid)
    return data

async def response_hook(data: bytes, peername=None) -> bytes:
    # TODO: 可在此处修改响应内容
    logger.info(f"response_hook: {data} , peername: {peername}")
    return data

def log_data(prefix, data, peername=None):
    try:
        hex_data = binascii.hexlify(data).decode('ascii')
        str_data = data.decode('utf-8', errors='replace')
    except Exception as e:
        hex_data = str(data)
        str_data = str(data)
    logger.info(f"{prefix} [{peername}]\nHEX: {hex_data}\nSTR: {str_data}")

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
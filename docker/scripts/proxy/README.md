# ADB Proxy 代理服务

## 📋 概述

ADB Proxy 是一个基于 `asyncio` 的异步代理服务，用于拦截和修改 ADB 协议通信。主要功能包括：

- 🔄 **协议代理**: 监听本地端口，转发 ADB 请求到真实服务
- 🎯 **命令拦截**: 动态修改 ps 命令，实现进程过滤
- 👥 **多用户支持**: 支持多用户容器环境下的用户隔离
- 🔧 **灵活配置**: 支持动态 userId 传递和命令修改

## 🏗️ 系统架构

### 整体架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ADB Client    │    │   ADB Proxy     │    │   Real ADB      │
│                 │    │                 │    │   Server        │
│  (5037端口)     │───▶│  (5037→5038)    │───▶│  (5038端口)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   UserId File   │
                       │  /tmp/adb_*.txt │
                       └─────────────────┘
```

### 核心组件

#### 1. **代理服务层**
- **监听器**: `asyncio.start_server()` 监听 5037 端口
- **连接管理**: `ProxyConnection` 类管理每个客户端连接
- **数据转发**: 双向数据流处理 (Client ↔ Proxy ↔ Server)

#### 2. **Hook 处理层**
- **请求 Hook**: `request_hook()` 处理客户端请求
- **响应 Hook**: `response_hook()` 处理服务器响应
- **命令修改**: `hook_ps_command()` 动态修改 ps 命令

#### 3. **用户隔离层**
- **文件管理**: `/tmp/adb_proxy_user_id.txt` 存储当前用户 ID
- **动态读取**: 实时从文件读取 userId
- **智能过滤**: 根据 userId 动态生成 grep 过滤条件

## 🔄 工作原理

### 1. **连接建立流程**
```
1. ADB Client 连接到 Proxy (5037端口)
2. Proxy 建立到 Real ADB Server 的连接 (5038端口)
3. 创建 ProxyConnection 实例管理双向数据流
4. 启动异步管道处理数据转发
```

### 2. **数据转发流程**
```
Client Request → Proxy → Hook处理 → Real Server
Real Server Response → Proxy → Hook处理 → Client
```

### 3. **命令修改流程**
```
1. 检测 ps && ps -A 命令
2. 从文件读取当前 userId
3. 判断 userId 有效性
4. 动态生成 grep 过滤条件
5. 修改 ADB 协议长度字段
6. 返回修改后的命令
```

### 4. **用户隔离机制**
```
1. Selenium 获取 userId 并写入文件
2. ADB Proxy 实时读取文件
3. 根据 userId 动态过滤进程
4. 新用户连接时自动覆盖旧文件
```

## 📁 文件结构

```
mini/docker/scripts/proxy/
├── adb_proxy.py                    # 主代理服务
├── test_simple_user_id_flow.py     # 测试脚本
├── README_USER_ID_FLOW.md          # 详细使用说明
└── README.md                       # 本文档
```

## ⚙️ 配置参数

### 环境变量
```bash
# 日志级别配置
export ADB_PROXY_LOG_LEVEL=INFO    # DEBUG, INFO, WARNING, ERROR, NONE

# 代理配置
PROXY_LISTEN_HOST = '0.0.0.0'      # 监听地址
PROXY_LISTEN_PORT = 5037           # 监听端口
ADB_SERVER_HOST = '127.0.0.1'      # 目标服务器地址
ADB_SERVER_PORT = 5038             # 目标服务器端口
```

### 文件路径
```bash
# userId 文件路径
USER_ID_FILE_PATH = '/tmp/adb_proxy_user_id.txt'
```

## 🚀 使用方式

### 1. **启动代理服务**
```bash
# 进入代理目录
cd mini/docker/scripts/proxy

# 启动代理
python3 adb_proxy.py
```

### 2. **配置 Selenium**
```java
// 在 capabilities 中设置 userId
capabilities.setCapability("se:userId", "u10_123");
```

### 3. **运行测试**
```bash
# 运行基本测试
python3 test_simple_user_id_flow.py

# 查看日志
tail -f proxy.log
```

## 🔧 核心功能

### 1. **智能命令修改**
```python
def hook_ps_command(data: bytes) -> bytes:
    """
    智能修改 ps 命令
    - 检测 ps && ps -A 命令
    - 动态读取 userId
    - 根据 userId 有效性决定是否修改
    """
    # 检测目标命令
    if 'ps && ps -A' in str_data:
        # 获取 userId
        user_id = get_user_id_from_file()
        
        # 智能判断
        if user_id and user_id != "u10_":
            # 有效 userId：添加过滤条件
            modified_command = command_part.replace(
                'ps && ps -A', 
                f'ps && ps -A | grep \'{user_id}\''
            )
        else:
            # 无效 userId：保持原命令
            modified_command = command_part
```

### 2. **动态用户隔离**
```python
def get_user_id_from_file():
    """
    从文件读取 userId
    - 支持文件不存在的情况
    - 支持空文件的情况
    - 提供默认值降级
    """
    try:
        if os.path.exists(USER_ID_FILE_PATH):
            with open(USER_ID_FILE_PATH, 'r', encoding='utf-8') as f:
                user_id = f.read().strip()
                if user_id:
                    return user_id
    except Exception as e:
        logger.error(f"读取 userId 文件失败: {e}")
    
    # 返回默认值
    return "u10_"
```

### 3. **异步连接管理**
```python
class ProxyConnection:
    """
    代理连接管理
    - 维护客户端和服务器连接
    - 处理双向数据流
    - 管理连接生命周期
    """
    async def pipe(self, reader, writer, direction, hook, which):
        """
        异步数据管道
        - 持续读取数据
        - 应用 hook 处理
        - 转发到目标
        """
```

## 📊 监控和日志

### 日志级别
```bash
# 设置详细日志
export ADB_PROXY_LOG_LEVEL=DEBUG

# 设置简洁日志
export ADB_PROXY_LOG_LEVEL=INFO

# 关闭日志
export ADB_PROXY_LOG_LEVEL=NONE
```

### 关键日志示例
```
2025-07-30 10:30:15 [INFO] ADB 代理脚本开始启动
2025-07-30 10:30:15 [INFO] 代理监听地址: 0.0.0.0:5037
2025-07-30 10:30:15 [INFO] 目标ADB服务地址: 127.0.0.1:5038
2025-07-30 10:30:16 [INFO] 新连接: ('192.168.1.100', 54321)
2025-07-30 10:30:16 [INFO] 已连接到真实 adb 服务: 127.0.0.1:5038
2025-07-30 10:30:17 [INFO] 🔍 检测到ps命令: 0011shell:ps && ps -A
2025-07-30 10:30:17 [INFO] 📁 从文件读取到 userId: u10_123
2025-07-30 10:30:17 [INFO] 🔧 使用 userId 'u10_123' 修改 ps 命令
2025-07-30 10:30:17 [INFO] ✅ 修改后的命令: 0011shell:ps && ps -A | grep 'u10_123'
```

## 🧪 测试验证

### 测试覆盖
- ✅ **基本功能测试**: 文件读写、命令修改
- ✅ **边界条件测试**: 空文件、文件不存在
- ✅ **并发测试**: 多用户同时连接
- ✅ **错误处理测试**: 异常情况处理

### 运行测试
```bash
# 运行所有测试
python3 test_simple_user_id_flow.py

# 预期输出
🚀 开始测试简化的 userId 传递流程
==================================================
🧪 测试简化的 userId 传递流程...
📝 写入测试 userId: test_user_123
✅ userId 读取成功
✅ ps 命令修改成功
✅ 空 userId 时保持原始命令不变
✅ 默认值正确
✅ 默认值时保持原始命令不变
🎉 所有测试通过！
==================================================
🎉 简化测试通过！userId 传递流程正常工作
```

## 🔍 故障排除

### 常见问题

#### 1. **连接失败**
```bash
# 检查端口占用
netstat -tlnp | grep 5037

# 检查防火墙
sudo ufw status

# 重启代理
python3 adb_proxy.py
```

#### 2. **文件权限问题**
```bash
# 检查文件权限
ls -la /tmp/adb_proxy_user_id.txt

# 修复权限
chmod 666 /tmp/adb_proxy_user_id.txt
```

#### 3. **日志调试**
```bash
# 设置详细日志
export ADB_PROXY_LOG_LEVEL=DEBUG

# 查看实时日志
tail -f proxy.log
```

### 监控命令
```bash
# 查看连接状态
netstat -an | grep 5037

# 查看文件内容
cat /tmp/adb_proxy_user_id.txt

# 查看进程
ps aux | grep adb_proxy
```

## 🔒 安全考虑

### 1. **文件安全**
- 临时文件权限控制
- 定期清理机制
- 内容验证

### 2. **用户隔离**
- userId 唯一性保证
- 会话隔离
- 资源清理

### 3. **网络安全**
- 端口访问控制
- 连接数限制
- 异常连接检测

## 📈 性能优化

### 1. **异步处理**
- 使用 `asyncio` 提高并发性能
- 非阻塞 I/O 操作
- 连接池管理

### 2. **内存优化**
- 流式数据处理
- 及时释放资源
- 避免内存泄漏

### 3. **日志优化**
- 异步日志写入
- 日志级别控制
- 日志轮转

## 🔄 扩展功能

### 1. **插件化 Hook**
```python
# 自定义 Hook 示例
async def custom_request_hook(data: bytes, peername=None) -> bytes:
    # 自定义处理逻辑
    return modified_data
```

### 2. **配置化管理**
```python
# 配置文件支持
config = {
    'listen_host': '0.0.0.0',
    'listen_port': 5037,
    'target_host': '127.0.0.1',
    'target_port': 5038,
    'log_level': 'INFO'
}
```

### 3. **监控集成**
```python
# 监控指标
metrics = {
    'connections': 0,
    'requests': 0,
    'errors': 0,
    'response_time': []
}
```

## 📝 更新日志

### v1.0.0 (2025-07-30)
- ✅ 基础代理功能
- ✅ 异步连接管理
- ✅ 基本命令拦截

### v1.1.0 (2025-07-30)
- ✅ 动态 userId 支持
- ✅ 智能命令修改
- ✅ 多用户隔离
- ✅ 完善错误处理

## 🤝 贡献指南

### 代码规范
- 遵循 PEP 8 (Python)
- 添加适当的注释和文档
- 保持代码简洁可读

### 测试要求
- 新功能必须包含测试
- 保持测试覆盖率 > 80%
- 运行所有测试确保通过

---

*最后更新时间: 2025-07-30* 
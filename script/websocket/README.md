# WebSocket 服务

这是一个基于 FastAPI 的高性能 WebSocket 服务实现，支持多客户端连接、消息广播、分组通信等功能。

## 特性

- 支持多客户端并发连接
- 支持消息广播和分组通信
- 支持自定义消息处理器
- 完整的类型提示
- 内置日志记录
- 单元测试覆盖

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 基本使用

```python
from fastapi import FastAPI
from websocket.server import WebSocketServer

app = FastAPI()
websocket_server = WebSocketServer(app)
```

### 2. 自定义消息处理

```python
from websocket.message_handler import MessageType, Message

async def custom_handler(message: Message) -> None:
    # 处理消息
    print(f"Received message: {message.content}")

# 注册处理器
websocket_server.register_message_handler(MessageType.TEXT, custom_handler)
```

### 3. 发送消息

```python
# 发送个人消息
await websocket_server.send_personal_message(
    {"type": "message", "content": "Hello!"},
    "client_id"
)

# 广播消息
await websocket_server.broadcast_message(
    {"type": "broadcast", "content": "Hello everyone!"}
)

# 向组广播消息
await websocket_server.broadcast_to_group(
    {"type": "group", "content": "Hello group!"},
    "group_id"
)
```

### 4. 分组管理

```python
# 添加客户端到组
websocket_server.add_client_to_group("client_id", "group_id")

# 从组中移除客户端
websocket_server.remove_client_from_group("client_id", "group_id")
```

## 消息类型

支持以下消息类型：

- TEXT: 文本消息
- JSON: JSON 格式消息
- BINARY: 二进制消息
- PING: 心跳消息
- PONG: 心跳响应

## 日志配置

服务使用 Python 标准库的 logging 模块进行日志记录。默认配置如下：

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 运行测试

```bash
pytest tests/test_websocket.py -v
```

## 示例应用

查看 `example.py` 文件获取完整的使用示例。

## 性能优化

1. 使用异步 IO 处理并发连接
2. 使用字典和集合进行快速查找
3. 支持消息广播和分组通信
4. 内置连接管理和错误处理

## 注意事项

1. 确保正确处理 WebSocket 连接的断开
2. 注意内存使用，及时清理断开的连接
3. 考虑添加心跳机制保持连接活跃
4. 在生产环境中配置适当的日志级别

## 贡献

欢迎提交 Issue 和 Pull Request。

## 许可证

MIT License 
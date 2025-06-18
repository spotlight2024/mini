from fastapi import FastAPI
import logging
import asyncio
from typing import Dict, Any

from websocket import WebSocketServer, Message, MessageType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="WebSocket Example")

# 创建 WebSocket 服务器
websocket_server = WebSocketServer(app)

# 自定义消息处理器
async def handle_chat_message(message: Message) -> None:
    """处理聊天消息"""
    logger.info(f"Received chat message: {message.content}")
    
    # 广播消息给所有客户端
    await websocket_server.broadcast_message({
        "type": "chat",
        "content": message.content,
        "sender": message.metadata.get("sender", "anonymous")
    })

async def handle_system_message(message: Message) -> None:
    """处理系统消息"""
    logger.info(f"Received system message: {message.content}")
    
    # 发送系统消息给指定客户端
    target_client = message.metadata.get("target_client")
    if target_client:
        await websocket_server.send_personal_message({
            "type": "system",
            "content": message.content
        }, target_client)

# 注册自定义消息处理器
websocket_server.register_message_handler(MessageType.TEXT, handle_chat_message)
websocket_server.register_message_handler(MessageType.JSON, handle_system_message)

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional, Set, MutableMapping
import logging
import uuid
import json
from .manager import WebSocketManager
from .message_handler import MessageHandler, Message, MessageType

logger = logging.getLogger(__name__)

class WebSocketServer:
    """WebSocket 服务器"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.manager = WebSocketManager()
        self.message_handler = MessageHandler()
        self._setup_routes()
        self._setup_default_handlers()
    
    def _setup_routes(self) -> None:
        """设置路由"""
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await self._handle_websocket_connection(websocket, client_id)
    
    def _setup_default_handlers(self) -> None:
        """设置默认消息处理器"""
        async def handle_text_message(message: Message) -> None:
            """处理文本消息"""
            logger.info(f"Received text message: {message.content}")
            client_id = message.metadata.get("client_id")
            if client_id:
                # 如果是 PING 消息，返回 PONG
                if message.content == "ping":
                    await self.manager.send_personal_message("pong", client_id)
                else:
                    # 回显消息
                    await self.manager.send_personal_message(message.content, client_id)
        
        async def handle_json_message(message: Message) -> None:
            """处理 JSON 消息"""
            logger.info(f"Received JSON message: {message.content}")
            client_id = message.metadata.get("client_id")
            if client_id:
                # 回显消息
                await self.manager.send_personal_message(
                    json.dumps(message.content),
                    client_id
                )
        
        async def handle_binary_message(message: Message) -> None:
            """处理二进制消息"""
            logger.info(f"Received binary message of length: {len(message.content)}")
            client_id = message.metadata.get("client_id")
            if client_id:
                # 回显消息
                await self.manager.send_personal_message(
                    message.content,
                    client_id,
                    is_binary=True
                )
        
        async def handle_ping_message(message: Message) -> None:
            """处理 PING 消息"""
            logger.debug("Received PING message")
            client_id = message.metadata.get("client_id")
            if client_id:
                # 发送 PONG 响应
                await self.manager.send_personal_message("pong", client_id)
        
        # 注册消息处理器
        self.message_handler.register_handler(MessageType.TEXT, handle_text_message)
        self.message_handler.register_handler(MessageType.JSON, handle_json_message)
        self.message_handler.register_handler(MessageType.BINARY, handle_binary_message)
        self.message_handler.register_handler(MessageType.PING, handle_ping_message)
    
    async def _handle_websocket_connection(self, websocket: WebSocket, client_id: str) -> None:
        """处理 WebSocket 连接"""
        try:
            logger.info(f"Client ID: {client_id}")
            # 生成唯一的客户端 ID
            if not client_id:
                client_id = str(uuid.uuid4())
            
            # 建立连接
            await self.manager.connect(websocket, client_id)
            
            try:
                while True:
                    # 接收消息
                    data = await websocket.receive()

                    logger.info(f"Received data: {data}")
                    # 处理断开连接消息
                    if data.get("type") == "websocket.disconnect":
                        logger.info(f"Client {client_id} disconnected")
                        self.manager.disconnect(client_id)
                        break
                    
                    # 根据消息类型创建 Message 对象
                    message = self._create_message_from_data(dict(data))
                    if message:
                        # 添加客户端 ID 到消息元数据
                        message.metadata["client_id"] = client_id
                        # 处理消息
                        await self.message_handler.handle_message(message)
                    
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                self.manager.disconnect(client_id)
                
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {str(e)}")
            self.manager.disconnect(client_id)
    
    def _create_message_from_data(self, data: Dict[str, Any]) -> Optional[Message]:
        """根据接收到的数据创建 Message 对象"""
        if "text" in data:
            try:
                # 尝试解析 JSON
                content = json.loads(data["text"])
                return Message(
                    type=MessageType.JSON,
                    content=content,
                    metadata={}
                )
            except json.JSONDecodeError:
                # 如果不是 JSON，则作为文本消息处理
                return Message(
                    type=MessageType.TEXT,
                    content=data["text"],
                    metadata={}
                )
        elif "bytes" in data:
            return Message(
                type=MessageType.BINARY,
                content=data["bytes"],
                metadata={}
            )
        elif "json" in data:
            return Message(
                type=MessageType.JSON,
                content=data["json"],
                metadata={}
            )
        else:
            logger.warning(f"Unknown message type: {data}")
            return None
    
    def register_message_handler(self, message_type: MessageType, handler: Any) -> None:
        """注册自定义消息处理器"""
        self.message_handler.register_handler(message_type, handler)
    
    async def broadcast_message(self, message: Any, exclude: Optional[Set[str]] = None) -> None:
        """广播消息给所有客户端"""
        if isinstance(message, dict):
            message = json.dumps(message)
        await self.manager.broadcast(message, exclude or set())
    
    async def send_personal_message(self, message: Any, client_id: str, is_binary: bool = False) -> None:
        """发送个人消息"""
        if isinstance(message, dict) and not is_binary:
            message = json.dumps(message)
        await self.manager.send_personal_message(message, client_id, is_binary)
    
    def add_client_to_group(self, client_id: str, group_id: str) -> None:
        """将客户端添加到组"""
        self.manager.add_to_group(client_id, group_id)
    
    def remove_client_from_group(self, client_id: str, group_id: str) -> None:
        """将客户端从组中移除"""
        self.manager.remove_from_group(client_id, group_id)
    
    async def broadcast_to_group(self, message: Any, group_id: str, exclude: Optional[Set[str]] = None) -> None:
        """向组广播消息"""
        if isinstance(message, dict):
            message = json.dumps(message)
        await self.manager.broadcast_to_group(message, group_id, exclude or set()) 
from typing import Dict, Any, Callable, Awaitable
import json
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"

@dataclass
class Message:
    """消息数据类"""
    type: MessageType
    content: Any
    metadata: Dict[str, Any] = None

class MessageHandler:
    """消息处理器"""
    
    def __init__(self):
        self.handlers: Dict[MessageType, Callable[[Message], Awaitable[None]]] = {}
        self.default_handler: Callable[[Message], Awaitable[None]] = None
    
    def register_handler(self, message_type: MessageType, handler: Callable[[Message], Awaitable[None]]) -> None:
        """注册消息处理器"""
        self.handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def register_default_handler(self, handler: Callable[[Message], Awaitable[None]]) -> None:
        """注册默认消息处理器"""
        self.default_handler = handler
        logger.info("Registered default message handler")
    
    async def handle_message(self, message: Message) -> None:
        """处理消息"""
        try:
            handler = self.handlers.get(message.type, self.default_handler)
            if handler:
                await handler(message)
            else:
                logger.warning(f"No handler registered for message type: {message.type}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            raise
    
    @staticmethod
    def create_text_message(content: str, metadata: Dict[str, Any] = None) -> Message:
        """创建文本消息"""
        return Message(
            type=MessageType.TEXT,
            content=content,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_json_message(content: Dict[str, Any], metadata: Dict[str, Any] = None) -> Message:
        """创建 JSON 消息"""
        return Message(
            type=MessageType.JSON,
            content=content,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_binary_message(content: bytes, metadata: Dict[str, Any] = None) -> Message:
        """创建二进制消息"""
        return Message(
            type=MessageType.BINARY,
            content=content,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_ping_message(metadata: Dict[str, Any] = None) -> Message:
        """创建 PING 消息"""
        return Message(
            type=MessageType.PING,
            content=None,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_pong_message(metadata: Dict[str, Any] = None) -> Message:
        """创建 PONG 消息"""
        return Message(
            type=MessageType.PONG,
            content=None,
            metadata=metadata or {}
        ) 
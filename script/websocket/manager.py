from typing import Dict, Set, Any, Optional
from fastapi import WebSocket
import json
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ClientInfo:
    """客户端信息类"""
    websocket: WebSocket
    client_id: str
    connected_at: datetime
    metadata: Dict[str, Any] = None

class WebSocketManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.groups: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """建立 WebSocket 连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str) -> None:
        """断开 WebSocket 连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            # 从所有组中移除客户端
            for group in self.groups.values():
                group.discard(client_id)
            logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: Any, client_id: str, is_binary: bool = False) -> None:
        """发送个人消息"""
        if client_id in self.active_connections:
            try:
                if is_binary:
                    await self.active_connections[client_id].send_bytes(message)
                else:
                    await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: Any, exclude: Optional[Set[str]] = None) -> None:
        """广播消息给所有客户端"""
        exclude_set = exclude or set()
        for client_id, connection in self.active_connections.items():
            if client_id not in exclude_set:
                try:
                    if isinstance(message, bytes):
                        await connection.send_bytes(message)
                    else:
                        await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message to client {client_id}: {str(e)}")
                    self.disconnect(client_id)
    
    def add_to_group(self, client_id: str, group_id: str) -> None:
        """将客户端添加到组"""
        if group_id not in self.groups:
            self.groups[group_id] = set()
        self.groups[group_id].add(client_id)
    
    def remove_from_group(self, client_id: str, group_id: str) -> None:
        """将客户端从组中移除"""
        if group_id in self.groups:
            self.groups[group_id].discard(client_id)
    
    async def broadcast_to_group(self, message: Any, group_id: str, exclude: Optional[Set[str]] = None) -> None:
        """向组广播消息"""
        if group_id in self.groups:
            exclude_set = exclude or set()
            for client_id in self.groups[group_id]:
                if client_id not in exclude_set:
                    try:
                        if isinstance(message, bytes):
                            await self.active_connections[client_id].send_bytes(message)
                        else:
                            await self.active_connections[client_id].send_text(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting message to group {group_id} client {client_id}: {str(e)}")
                        self.disconnect(client_id)
    
    def get_active_clients(self) -> Dict[str, WebSocket]:
        """获取所有活跃的客户端信息"""
        return self.active_connections.copy()
    
    def get_group_clients(self, group_id: str) -> Set[str]:
        """获取指定组的所有客户端ID"""
        return self.groups.get(group_id, set()).copy() 
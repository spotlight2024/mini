import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from websocket.server import WebSocketServer
from websocket.message_handler import MessageType, Message

# 统一的 app 和 WebSocketServer fixture
@pytest.fixture(scope="session")
def app_and_server():
    app = FastAPI()
    ws_server = WebSocketServer(app)
    return app, ws_server

@pytest.fixture
def client(app_and_server):
    app, _ = app_and_server
    return TestClient(app)

@pytest.fixture
def websocket_server(app_and_server):
    _, ws_server = app_and_server
    return ws_server

def test_websocket_connection(client, websocket_server):
    """测试 WebSocket 连接"""
    with client.websocket_connect("/ws/test_client") as websocket:
        # 验证客户端是否在活跃连接列表中
        assert "test_client" in websocket_server.manager.get_active_clients()
        # 发送一个简单的消息来验证连接是否正常工作
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"

def test_text_message_handling(client, websocket_server):
    """测试文本消息处理"""
    with client.websocket_connect("/ws/test_client") as websocket:
        websocket.send_text("Hello, WebSocket!")
        response = websocket.receive_text()
        assert response == "Hello, WebSocket!"

def test_json_message_handling(client, websocket_server):
    """测试 JSON 消息处理"""
    with client.websocket_connect("/ws/test_client") as websocket:
        message = {"type": "json", "content": {"key": "value"}}
        websocket.send_json(message)
        response = websocket.receive_json()
        assert response["type"] == "json"
        assert response["content"]["key"] == "value"

def test_binary_message_handling(client, websocket_server):
    """测试二进制消息处理"""
    with client.websocket_connect("/ws/test_client") as websocket:
        binary_data = b"Hello, Binary!"
        websocket.send_bytes(binary_data)
        response = websocket.receive_bytes()
        assert response == binary_data

def test_group_broadcasting(client, websocket_server):
    """测试组广播功能"""
    with client.websocket_connect("/ws/client1") as ws1, \
         client.websocket_connect("/ws/client2") as ws2:
        websocket_server.add_client_to_group("client1", "test_group")
        websocket_server.add_client_to_group("client2", "test_group")
        
        # 广播消息
        asyncio.run(websocket_server.broadcast_to_group(
            {"type": "broadcast", "content": "Group message"},
            "test_group"
        ))
        
        # 验证两个客户端都收到了消息
        response1 = ws1.receive_json()
        response2 = ws2.receive_json()
        assert response1["type"] == "broadcast"
        assert response1["content"] == "Group message"
        assert response2["type"] == "broadcast"
        assert response2["content"] == "Group message"

def test_personal_message(client, websocket_server):
    """测试个人消息发送"""
    with client.websocket_connect("/ws/test_client") as websocket:
        asyncio.run(websocket_server.send_personal_message(
            {"type": "personal", "content": "Personal message"},
            "test_client"
        ))
        response = websocket.receive_json()
        assert response["type"] == "personal"
        assert response["content"] == "Personal message"

def test_client_disconnection(client, websocket_server):
    """测试客户端断开连接"""
    with client.websocket_connect("/ws/test_client") as websocket:
        # 验证连接已建立
        assert "test_client" in websocket_server.manager.get_active_clients()
        # 关闭连接
        websocket.close()
    # 验证连接已断开
    assert "test_client" not in websocket_server.manager.get_active_clients()

def test_custom_message_handler(client, websocket_server):
    """测试自定义消息处理器"""
    # 注册自定义 handler
    result = {}
    async def custom_handler(message: Message) -> None:
        result["type"] = message.type
        result["content"] = message.content
        # 发送响应
        await websocket_server.send_personal_message(
            {"type": "response", "content": message.content},
            "test_client"
        )
    
    websocket_server.register_message_handler(MessageType.TEXT, custom_handler)
    
    with client.websocket_connect("/ws/test_client") as websocket:
        websocket.send_text("Custom message")
        # 等待响应
        response = websocket.receive_json()
        assert response["type"] == "response"
        assert response["content"] == "Custom message"
        # 验证 handler 被调用
        assert result["type"] == MessageType.TEXT
        assert result["content"] == "Custom message" 
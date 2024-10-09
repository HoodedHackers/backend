import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket
from .connection_manager import ManagerTypes, Managers

test_app = FastAPI()

@test_app.websocket("/ws/{lobby_id}")
async def websocket_endpoint(websocket: WebSocket, lobby_id: int):
    manager = Managers.get_manager(ManagerTypes.JOIN_LEAVE)
    await manager.connect(websocket, lobby_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"message": data}, lobby_id)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        manager.disconnect(websocket, lobby_id)



@pytest.mark.asyncio
async def test_websocket():
    client = TestClient(test_app)
    with client.websocket_connect("/ws/1") as websocket:
        websocket.send_text("Hello")
        data = websocket.receive_json()
        assert data == {"message": "Hello"}

@pytest.mark.asyncio
async def test_multiple_clients():
    client = TestClient(test_app)
    with client.websocket_connect("/ws/1") as websocket1, client.websocket_connect("/ws/1") as websocket2:
        websocket1.send_text("Hello from client 1")
        data1 = websocket1.receive_json()
        data2 = websocket2.receive_json()
        assert data1 == {"message": "Hello from client 1"}
        assert data2 == {"message": "Hello from client 1"}

from enum import Enum
from typing import Any, Dict, List

from fastapi import WebSocket


class ManagerTypes(Enum):
    JOIN_LEAVE = 1
    TURNS = 2


class ConnectionManager:
    lobbies: Dict[int, List[WebSocket]]

    def __init__(self):
        self.lobbies = {}

    async def connect(self, websocket: WebSocket, lobby_id: int):
        await websocket.accept()
        if lobby_id not in self.lobbies:
            self.lobbies[lobby_id] = []
        self.lobbies[lobby_id].append(websocket)

    def disconnect(self, websocket: WebSocket, lobby_id: int):
        if lobby_id not in self.lobbies:
            return
        self.lobbies[lobby_id].remove(websocket)
        if len(self.lobbies[lobby_id]) == 0:
            del self.lobbies[lobby_id]

    async def broadcast(self, message: Any, lobby_id: int):
        if lobby_id not in self.lobbies:
            return
        for connection in self.lobbies[lobby_id]:
            await connection.send_json(message)


class Managers:
    managers = {
        ManagerTypes.JOIN_LEAVE: ConnectionManager(),
        ManagerTypes.TURNS: ConnectionManager(),
    }

    @classmethod
    def get_manager(cls, type) -> ConnectionManager:
        manager = Managers.managers.get(type)
        if manager is None:
            raise Exception("Bad manager type")
        return manager

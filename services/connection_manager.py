from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from fastapi import WebSocket


class ManagerTypes(Enum):
    JOIN_LEAVE = 1
    TURNS = 2


@dataclass
class PlayerWs:
    id_player: int
    websockets: WebSocket


class ConnectionManager:
    lobbies: Dict[int, List[PlayerWs]]

    def __init__(self):
        self.lobbies = {}

    async def connect(self, websocket: WebSocket, lobby_id: int, player_id: int):
        await websocket.accept()
        if lobby_id not in self.lobbies:
            self.lobbies[lobby_id] = []

        self.lobbies[lobby_id].append(PlayerWs(player_id, websocket))

    def disconnect(self, lobby_id: int, player_id: int):
        if lobby_id not in self.lobbies:
            return
        for player in self.lobbies[lobby_id]:
            if player.id_player == player_id:
                self.lobbies[lobby_id].remove(player)
        if len(self.lobbies[lobby_id]) == 0:
            del self.lobbies[lobby_id]

    async def broadcast(self, message: Any, lobby_id: int):
        if lobby_id not in self.lobbies:
            return
        for connection in self.lobbies[lobby_id]:
            await connection.websockets.send_json(message)

    def remove_lobby(self, lobby_id: int):
        if lobby_id in self.lobbies:
            del self.lobbies[lobby_id]


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

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from fastapi import WebSocket


class ManagerTypes(Enum):
    JOIN_LEAVE = 1
    TURNS = 2
    GAME_STATUS = 3
    BOARD_STATUS = 4
    CARDS_FIGURE = 5
    CARDS_MOV = 6


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

    async def disconnect_all(self, lobby_id: int):
        if lobby_id not in self.lobbies:
            return
        conns = self.lobbies[lobby_id]
        for con in conns:
            await con.websockets.close()
        del self.lobbies[lobby_id]

    async def broadcast(self, message: Any, lobby_id: int):
        if lobby_id not in self.lobbies:
            return
        for connection in self.lobbies[lobby_id]:
            await connection.websockets.send_json(message)

    async def send(self, message: Any, lobby_id: int, player_id: int):
        for lobby in self.lobbies[lobby_id]:
            if lobby.id_player == player_id:
                await lobby.websockets.send_json(message)

    def remove_lobby(self, lobby_id: int):
        if lobby_id in self.lobbies:
            del self.lobbies[lobby_id]


class Managers:
    managers = {
        ManagerTypes.JOIN_LEAVE: ConnectionManager(),
        ManagerTypes.TURNS: ConnectionManager(),
        ManagerTypes.CARDS_MOV: ConnectionManager(),
        ManagerTypes.GAME_STATUS: ConnectionManager(),
        ManagerTypes.BOARD_STATUS: ConnectionManager(),
        ManagerTypes.CARDS_FIGURE: ConnectionManager(),
    }

    @classmethod
    def get_manager(cls, type) -> ConnectionManager:
        manager = Managers.managers.get(type)
        if manager is None:
            raise Exception("Bad manager type")
        return manager

    @classmethod
    async def disconnect_all(cls, game_id: int):
        for manager in Managers.managers.values():
            await manager.disconnect_all(game_id)

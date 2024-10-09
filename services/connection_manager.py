from typing import Dict, List
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from repositories.game import GameRepository
from repositories.player import PlayerRepository


class LobbyConnectionHandler:
    def __init__(self):
        # Diccionario que tendrá una lista de conexiones por cada lobby
        self.lobbies: Dict[int, List[WebSocket]] = {}

    async def listen(
        self,
        websocket: WebSocket,
        lobby_id: int,
        game_repo: GameRepository,
        player_repo: PlayerRepository,
    ):
        await self.connect(websocket, lobby_id)
        try:
            while True:
                data = await websocket.receive_json()
                user_id = data.get("user_identifier")
                if user_id is None:
                    await websocket.send_json({"error": "User id is missing"})
                    continue

                player = player_repo.get_by_identifier(user_id)
                if player is None:
                    await websocket.send_json({"error": "Player not found"})
                    continue

                action = data.get("action")
                game = game_repo.get(lobby_id)
                if game is None:
                    await websocket.send_json({"error": "Game not found"})
                    continue

                players_raw = game.players
                players = [{"id": p.id, "name": p.name} for p in players_raw]

                if action == "connect":
                    await self.broadcast({"players": players}, lobby_id)

                elif action == "disconnect":
                    await self.broadcast({"players": players}, lobby_id)
                    await self.disconnect(websocket, lobby_id)
                else:
                    await websocket.send_json({"error": "Invalid action"})

        except WebSocketDisconnect:
            await self.disconnect(websocket, lobby_id)

    async def connect(self, websocket: WebSocket, lobby_id: int):
        await websocket.accept()

        if lobby_id not in self.lobbies:
            self.lobbies[lobby_id] = []
        self.lobbies[lobby_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, lobby_id: int):
        if lobby_id in self.lobbies:
            self.lobbies[lobby_id].remove(websocket)

            if len(self.lobbies[lobby_id]) == 0:
                del self.lobbies[lobby_id]

    async def broadcast(self, message: dict, lobby_id: int):
        if lobby_id in self.lobbies:
            for connection in self.lobbies[lobby_id]:
                await connection.send_json(message)

    async def list_connections(self, lobby_id: int):
        if lobby_id in self.lobbies:
            return self.lobbies[lobby_id]
        return []

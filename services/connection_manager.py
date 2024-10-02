from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect

from repositories.player import PlayerRepository


class LobbyConnectionHandler:
    def __init__(self):
        # Diccionario que tendrá una lista de conexiones por cada lobby
        self.lobbies: Dict[int, List[WebSocket]] = {}

    async def listen(
        self, websocket: WebSocket, lobby_id: int, player_repo: PlayerRepository
    ):
        await self.connect(websocket, lobby_id)
        try:
            while True:
                data = await websocket.receive_json()
                user_id = data.get("user_identifier")
                player = player_repo.get_by_identifier(user_id)

                if player is not None:
                    user_name = player.name

                    if data.get("action") == "connect":
                        await self.broadcast(
                            {"user_name": user_name, "action": "connect"}, lobby_id
                        )

                    elif data.get("action") == "disconnect":
                        await self.broadcast(
                            {"user_name": user_name, "action": "disconnect"}, lobby_id
                        )
                        await self.disconnect(websocket, lobby_id)

                    else:
                        await websocket.send_json({"error": "Invalid action"})
                else:
                    await websocket.send_json({"error": "User not found"})

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

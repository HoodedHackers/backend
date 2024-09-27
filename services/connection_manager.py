from typing import Dict, List
from fastapi import WebSocket

class ManejadorConexionesLobby:
    def __init__(self):
        # Diccionario que tendrá una lista de conexiones por cada lobby
        self.lobbies: Dict[int, List[WebSocket]] = {}

    async def conectar(self, websocket: WebSocket, lobby_id: int):
        # Añadimos la conexión del jugador a la lista lobby especificado
        await websocket.accept()
        
        if lobby_id not in self.lobbies:
            self.lobbies[lobby_id] = []
        self.lobbies[lobby_id].append(websocket)

    def desconectar(self, websocket: WebSocket, lobby_id: int):
        if lobby_id in self.lobbies:
            self.lobbies[lobby_id].remove(websocket)
            
            if len(self.lobbies[lobby_id]) == 0:
                del self.lobbies[lobby_id]

    async def broadcast(self, message: str, lobby_id: int):
        if lobby_id in self.lobbies:
            for connection in self.lobbies[lobby_id]:
                await connection.send_text(message)
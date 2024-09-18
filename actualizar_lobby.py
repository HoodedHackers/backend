from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient
from typing import List, Dict

app = FastAPI()


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

manejador = ManejadorConexionesLobby()

@app.websocket("/ws/lobby/{lobby_id}")
async def websocket_endpoint(websocket: WebSocket, lobby_id: int):
    # Conectar al nuevo jugador a la lista de conexiones del lobby
    await manejador.conectar(websocket, lobby_id)

    await manejador.broadcast(f"Un nuevo jugador ha ingresado al lobby {lobby_id}.", lobby_id)
    
    try:
        while True:
            # Esto solo lo ponemos para mantener la conexión abierta
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Desconectar al jugador y notificamos a los demás jugadores
        manejador.desconectar(websocket, lobby_id)

        await manejador.broadcast(f"Un jugador ha abandonado el lobby {lobby_id}.", lobby_id)

# ------ TEST ------ #

# Los jugadores reciben notificaciones cuando alguien se conecta o se
# desconecta.
def test_conectar_y_desconectar():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/lobby/1") as clientws1:
            with client.websocket_connect("/ws/lobby/1") as clientws2:
                # El jugador 1 se conecta
                data1 = clientws1.receive_text()
                assert data1 == "Un nuevo jugador ha ingresado al lobby 1."
                
                # El jugador 2 se conecta
                data2 = clientws2.receive_text()
                assert data2 == "Un nuevo jugador ha ingresado al lobby 1."
                
                # El jugador 1 se desconecta
                clientws1.close()
                data3 = clientws2.receive_text()
                assert data3 == "Un jugador ha abandonado el lobby 1."
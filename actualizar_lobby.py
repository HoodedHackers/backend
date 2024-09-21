from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from services.connection_manager import ManejadorConexionesLobby

app = FastAPI()

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

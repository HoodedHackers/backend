from os import getenv
from fastapi import FastAPI, Response, Request, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import Database
from repositories import GameRepository
from services.connection_manager import ManejadorConexionesLobby

manejador = ManejadorConexionesLobby()

db_uri = getenv("DB_URI")
if db_uri is not None:
    db = Database(db_uri=db_uri)
else:
    db = Database()
db.create_tables()
app = FastAPI()
game_repo = GameRepository(db.session())


@app.middleware("http")
async def add_game_repo_to_request(request: Request, call_next):
    request.state.game_repo = game_repo
    response = await call_next(request)
    return response


def get_games_repo(request: Request) -> GameRepository:
    return request.state.game_repo


@app.get("/api/lobby")
def get_games_available(repo: GameRepository = Depends(get_games_repo)):
    lobbies = repo.get_available(10)
    return lobbies

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
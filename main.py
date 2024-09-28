from os import getenv
from fastapi import FastAPI, Response, Request, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import BaseModel

from database import Database
from repositories import GameRepository
from services.connection_manager import LobbyConnectionHandler

connection_manager = LobbyConnectionHandler()

db_uri = getenv("DB_URI")
if db_uri is not None:
    db = Database(db_uri=db_uri)
else:
    db = Database()
db.create_tables()
app = FastAPI()
game_repo = GameRepository(db.session())


class GameStateOutput(BaseModel):
    name: str
    current_players: int
    max_players: int
    min_players: int
    is_started: bool
    turn: int


@app.middleware("http")
async def add_game_repo_to_request(request: Request, call_next):
    request.state.game_repo = game_repo
    response = await call_next(request)
    return response


def get_games_repo(request: Request) -> GameRepository:
    return request.state.game_repo


@app.get("/api/lobby")
def get_games_available(repo: GameRepository = Depends(get_games_repo)):
    lobbies_queries = repo.get_available(10)
    lobbies = []
    for lobby_query in lobbies_queries:
        lobby = GameStateOutput(
            name=lobby_query.name,
            current_players=len(lobby_query.players),
            max_players=lobby_query.max_players,
            min_players=lobby_query.min_players,
            is_started=lobby_query.started,
            turn=lobby_query.current_player_turn,
        )
        lobbies.append(lobby)
    return lobbies

@app.websocket("/ws/lobby/{lobby_id}")
async def lobby_websocket_handler(websocket: WebSocket, lobby_id: int):
    # Conectar al nuevo jugador a la lista de conexiones del lobby
    await connection_manager.connect(websocket, lobby_id)

    # Si se conecto un nuevo jugador al lobby notificamos a los demás jugadores
    await connection_manager.broadcast(f"Un nuevo jugador se ha unido al lobby {lobby_id}.", lobby_id)
    
    try:
        while True:
            await websocket.receive_text() # DUMP

    except WebSocketDisconnect:
        # Desconectar al jugador y notificamos a los demás jugadores
        connection_manager.disconnect(websocket, lobby_id)

        await connection_manager.broadcast(f"Un jugador ha abandonado el lobby {lobby_id}.", lobby_id)

@app.get("/api/lobby/{id}")
def get_game(id: int, repo: GameRepository = Depends(get_games_repo)):
    lobby_query = repo.get(id)
    if lobby_query is None:
        raise HTTPException(status_code=404, detail="Lobby not found")
    lobby = GameStateOutput(
        name=lobby_query.name,
        current_players=len(lobby_query.players),
        max_players=lobby_query.max_players,
        min_players=lobby_query.min_players,
        is_started=lobby_query.started,
        turn=lobby_query.current_player_turn,
    )
    return lobby

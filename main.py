from os import getenv
from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy.orm import Session
from fastapi.websockets import WebSocket
import asyncio

from database import Database
from repositories import GameRepository

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


@app.websocket("ws/api/lobby")
async def notify_new_games(websocket: WebSocket, repo: GameRepository = Depends(get_games_repo)):
    await websocket.accept()
    previous_lobbies = repo.get_available(10)
    while True:
        await asyncio.sleep(5)
        current_lobbies = repo.get_available(10)
        if previous_lobbies != current_lobbies:
            await websocket.send_json(current_lobbies)
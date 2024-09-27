from os import getenv
from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy.orm import Session
from fastapi.websockets import WebSocket, WebSocketDisconnect

import asyncio
from database import Database
from repositories import GameRepository
import services.counter

timer = services.counter.Counter()

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


@app.post("/api/lobby/timer")
async def start_timer():
    await asyncio.sleep(120)
    return Response(status_code=200, content="Timer finished")

@app.websocket("/ws/timer")
async def timer_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()

            if message.get("action") == "start":
                if not timer.running:
                    await timer.start(websocket)

            elif message.get("action") == "stop":
                await timer.stop()

    except WebSocketDisconnect:
        await timer.stop()

from os import getenv
from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy.orm import Session

from database import Database
from repositories import GameRepository
from pydantic import BaseModel
from fastapi import HTTPException
from typing import List
import random

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


# endpoing juguete, borralo cuando haya uno de verdad
@app.get("/api/borrame")
async def borrame(games_repo: GameRepository = Depends(get_games_repo)):
    games = games_repo.get_many(10)
    return {"games": games}


class PlayerOutRandom(BaseModel):
    id: int
    name: str


class GamePlayerResponse(BaseModel):
    game_id: int
    players: List[PlayerOutRandom]


@app.post("/api/start_game", response_model=GamePlayerResponse)
async def sortear_jugadores(
    game_id: int, game_repo: GameRepository = Depends(get_games_repo)
):

    game = game_repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    elif len(game.players) < game.min_players:
        raise HTTPException(
            status_code=412,
            detail="No se puede sortear jugadores si no hay suficientes jugadores",
        )
    elif game.started == True:
        random.shuffle(game.players)
        game_repo.save(game)

        players_out = [
            PlayerOutRandom(id=player.id, name=player.name) for player in game.players
        ]
    else:
        raise HTTPException(
            status_code=412,
            detail="No se puede sortear jugadores si la partida no ha comenzado",
        )

    return GamePlayerResponse(game_id=game_id, players=players_out)



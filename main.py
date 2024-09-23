from os import getenv
from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy.orm import Session

from database import Database
from repositories import GameRepository
from pydantic import BaseModel
from typing import List
from fastapi import HTTPException, Depends


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


class PlayerExit(BaseModel):
    id: int
    name: str
    activate: bool

class ExitRequest(BaseModel): #le llega esto al endpoint
    identifier : str


class GamePlayerResponse(BaseModel):
    game_id: int
    players: List[PlayerOutRandom]


@app.delete(
    "/api/lobby/{game_id}}", response_model=GamePlayerResponse
)
async def exitGame(
    game_id: int, exit_request: ExitRequest, games_repo: GameRepository = Depends(get_games_repo)
):
    game = games_repo.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    # ve si el jugador esta en la partida, por las dudas ah

    if not player:
        raise HTTPException(status_code=400, detail="El jugadorno esta en la partida")

    elif not game.started == False:
        raise HTTPException(status_code=400, detail="El jugador ya abandono la partida")


# tomar en cuenta que se si un jugador esta en la partida si en game esta en la lista de players
# puedo sacar de la lista al jugador y ahi ya no esta en la partida :D en players no hay que hacer nada porque
# en players esta el id y el nombre del jugador, en Game esta la relacion players y host
#definir en el modelo el remove de un jugador, con su identifier
from os import getenv
from uuid import uuid4, UUID
from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import Database
from repositories import GameRepository, PlayerRepository
from model import Player


db_uri = getenv("DB_URI")
if db_uri is not None:
    db = Database(db_uri=db_uri)
else:
    db = Database()
db.create_tables()

# creamos la App
app = FastAPI()

player_repo = PlayerRepository(db.session())
game_repo = GameRepository(db.session())


@app.middleware("http")
async def add_repos_to_request(request: Request, call_next):
    request.state.game_repo = game_repo
    request.state.player_repo = player_repo
    response = await call_next(request)
    return response


def get_games_repo(request: Request) -> GameRepository:
    return request.state.game_repo


def get_player_repo(request: Request) -> PlayerRepository:
    return request.state.player_repo


class SetNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class SetNameResponse(BaseModel):
    name: str = Field()
    identifier: UUID = Field()


@app.post("/api/name")
async def set_player_name(
    setNameRequest: SetNameRequest,
    player_repo: PlayerRepository = Depends(get_player_repo),
) -> SetNameResponse:
    identifier = uuid4()
    player_repo.save(Player(name=setNameRequest.name, identifier=identifier))
    return SetNameResponse(name=setNameRequest.name, identifier=identifier)

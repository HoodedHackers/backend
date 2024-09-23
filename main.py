from os import getenv
from uuid import uuid4, UUID
from fastapi import FastAPI, Response, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
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

session = db.get_session()
player_repo = PlayerRepository(session)
game_repo = GameRepository(session)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    id_uuid = uuid4()
    player_repo.save(Player(name=setNameRequest.name, identifier=id_uuid))
    return SetNameResponse(name=setNameRequest.name, identifier=id_uuid)

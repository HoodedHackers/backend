from os import getenv
from uuid import UUID, uuid4
from fastapi import FastAPI, Response, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi import HTTPException
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
session = db.session()
app = FastAPI()

session = db.get_session()
player_repo = PlayerRepository(session)
game_repo = GameRepository(session)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GameStateOutput(BaseModel):
    name: str
    current_players: int
    max_players: int
    min_players: int
    is_started: bool
    turn: int


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


class req_in(BaseModel):
    id_game: int = Field()
    identifier_player: str = Field()


@app.put("/api/lobby/{id_game}")
async def endpoint_unirse_a_partida(
    req: req_in,
    games_repo: GameRepository = Depends(get_games_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
):
    new_identifier = UUID(req.identifier_player)
    print(new_identifier)
    selec_player = player_repo.get_by_identifier(new_identifier)
    selec_game = games_repo.get(req.id_game)
    if selec_player is None:
        raise HTTPException(status_code=404, detail="Player dont found!")
    if selec_game is None:
        raise HTTPException(status_code=404, detail="Game dont found!")
    selec_game.add_player(selec_player)
    games_repo.save(selec_game)
    return {"status": "success!"}


class SetNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class SetNameResponse(BaseModel):
    name: str
    identifier: UUID


@app.post("/api/name")
async def set_player_name(
    setNameRequest: SetNameRequest,
    player_repo: PlayerRepository = Depends(get_player_repo),
) -> SetNameResponse:
    id_uuid = uuid4()
    player_repo.save(Player(name=setNameRequest.name, identifier=id_uuid))
    return SetNameResponse(name=setNameRequest.name, identifier=id_uuid)

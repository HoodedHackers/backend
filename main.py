from os import getenv

from fastapi import FastAPI, Response, Request, Depends, HTTPException

from uuid import UUID, uuid4
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import BaseModel, Field

from database import Database

from repositories import GameRepository
from pydantic import BaseModel
from typing import List

from repositories import GameRepository, PlayerRepository
from model import Player


db_uri = getenv("DB_URI")
if db_uri is not None:
    db = Database(db_uri=db_uri)
else:
    db = Database()
db.create_tables()
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



# endpoing juguete, borralo cuando haya uno de verdad
@app.get("/api/borrame")
async def borrame(games_repo: GameRepository = Depends(get_games_repo)):
    games = games_repo.get_many(10)
    return {"games": games}


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

'''''
class SetNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class SetNameResponse(BaseModel):
    name: str
    identifier: UUID

class PlayerOutRandom(BaseModel):  
    id: int

"""
class PlayerExit(BaseModel):
    id: int
    name: str
    activate: bool
"""


class ExitRequest(BaseModel):  # le llega esto al endpoint
    identifier: UUID


class GamePlayerResponse(BaseModel):  # Lo que envia
    game_id: int
    players: List[PlayerOutRandom]


# api/lobby/{game_id}
@app.delete("/api/lobby/{game_id}", response_model=GamePlayerResponse)
async def exitGame(
    game_id: int,
    exit_request: ExitRequest,
    games_repo: GameRepository = Depends(get_games_repo),
):
    game = games_repo.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    # ve si el jugador esta en la partida, por las dudas ah
    elif not game.started == False:
        raise HTTPException(status_code=400, detail="El juego no empezo'")

    player_exit = (
        next(
            player
            for player in game.players
            if player.identifier == exit_request.identifier
        ),
        None,
    )

    if player_exit is None:
        raise HTTPException(status_code=404, detail="El jugador no existe")

    game.delete_player(player_exit)
    games_repo.save(game)

    """''
    if game.host.id == player_exit.id
        game.host = None
    """ ""
    return GamePlayerResponse(
        game_id=game.id,
        players=[
            PlayerOutRandom(
                id=player.id, name=player.name, identifier=player.identifier
            )
            for player in game.players
        ],
    )


# tomar en cuenta que se si un jugador esta en la partida si en game esta en la lista de players
# puedo sacar de la lista al jugador y ahi ya no esta en la partida :D en players no hay que hacer nada porque
# en players esta el id y el nombre del jugador, en Game esta la relacion players y host
# definir en el modelo el remove de un jugador, con su identifier, es igual que add pero al reves

@app.post("/api/name")
async def set_player_name(
    setNameRequest: SetNameRequest,
    player_repo: PlayerRepository = Depends(get_player_repo),
) -> SetNameResponse:
    id_uuid = uuid4()
    player_repo.save(Player(name=setNameRequest.name, identifier=id_uuid))
    return SetNameResponse(name=setNameRequest.name, identifier=id_uuid)

'''''
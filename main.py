from os import getenv
from uuid import UUID, uuid4
from typing import List
import random

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import Database
from model import Player, Game
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
    started: bool
    turn: int
    players: List[str]


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


class GameIn(BaseModel):
    identifier: UUID
    name: str = Field(min_length=1, max_length=64)
    max_players: int = Field(ge=2, le=4)
    min_players: int = Field(ge=2, le=4)


class PlayerOut(BaseModel):
    name: str


class GameOut(BaseModel):
    id: int
    name: str
    max_players: int
    min_players: int
    started: bool
    players: List[PlayerOut]


@app.post("/api/lobby", response_model=GameOut)
async def create_game(
    game_create: GameIn,
    game_repo: GameRepository = Depends(get_games_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
) -> GameOut:

    if game_create.min_players > game_create.max_players:
        raise HTTPException(
            status_code=412,
            detail="El número mínimo de jugadores no puede ser mayor al máximo",
        )
    player = player_repo.get_by_identifier(game_create.identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    new_game = Game(
        name=game_create.name,
        host=player,
        host_id=player.id,
        max_players=game_create.max_players,
        min_players=game_create.min_players,
        started=False,
    )

    game_repo.save(new_game)

    players_out = [PlayerOut(name=player.name) for player in new_game.players]

    return GameOut(
        id=new_game.id,
        name=new_game.name,
        max_players=new_game.max_players,
        min_players=new_game.min_players,
        started=new_game.started,
        players=players_out,
    )


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
            started=lobby_query.started,
            turn=lobby_query.current_player_turn,
            players=[player.name for player in lobby_query.players],
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
        started=lobby_query.started,
        turn=lobby_query.current_player_turn,
        players=[player.name for player in lobby_query.players],
    )
    return lobby


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


"""
class PlayerExit(BaseModel):
    id: int
    name: str
    activate: bool
"""

class PlayerOutRandom(BaseModel):
    name: str
    identifier: UUID


class ExitRequest(BaseModel):  # le llega esto al endpoint
    identifier: UUID


class GamePlayerResponse(BaseModel):  # Lo que envia
    game_id: int
    players: List[PlayerOutRandom]
    ident : ExitRequest

# api/lobby/{game_id}
@app.patch("/api/lobby/salir/{game_id}", response_model=GamePlayerResponse)
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
        )
    )
    print(player_exit.identifier)

    if player_exit is None:
        raise HTTPException(status_code=404, detail="El jugador no existe")

    if game.host.identifier == player_exit.identifier:
        game.host = None
    
    game.delete_player(player_exit)
    games_repo.save(game)

    
    return GamePlayerResponse(
        game_id=game.id,
        players=[
            PlayerOutRandom(name=player.name, identifier=UUID(str(player.identifier)))
            for player in game.players
        ],
        out=ExitRequest(
            ident=exit_request.identifier,
        ),
    )

# tomar en cuenta que se si un jugador esta en la partida si en game esta en la lista de players
# puedo sacar de la lista al jugador y ahi ya no esta en la partida :D en players no hay que hacer nada porque
# en players esta el id y el nombre del jugador, en Game esta la relacion players y host
# definir en el modelo el remove de un jugador, con su identifier, es igual que add pero al reves


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
    selec_player = player_repo.get_by_identifier(new_identifier)
    selec_game = games_repo.get(req.id_game)
    if selec_player is None:
        raise HTTPException(status_code=404, detail="Player dont found!")
    if selec_game is None:
        raise HTTPException(status_code=404, detail="Game dont found!")
    selec_game.add_player(selec_player)
    games_repo.save(selec_game)
    return {"status": "success!"}

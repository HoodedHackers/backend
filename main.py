from os import getenv
from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.websockets import WebSocket, WebSocketDisconnect
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import List, Dict

import asyncio
from database import Database
from repositories import GameRepository, PlayerRepository
import services.counter
from model import Player, Game
from repositories import (
    GameRepository,
    PlayerRepository,
    FigRepository,
    create_all_figs,
)

from services.connection_manager import LobbyConnectionHandler


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
card_repo = FigRepository(session)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
create_all_figs(card_repo)


@app.middleware("http")
async def add_repos_to_request(request: Request, call_next):
    request.state.game_repo = game_repo
    request.state.player_repo = player_repo
    request.state.card_repo = card_repo
    response = await call_next(request)
    return response


def get_games_repo(request: Request) -> GameRepository:
    return request.state.game_repo


def get_card_repo(request: Request) -> FigRepository:
    return request.state.card_repo


def get_player_repo(request: Request) -> PlayerRepository:
    return request.state.player_repo


class GameStateOutput(BaseModel):
    name: str
    current_players: int
    max_players: int
    min_players: int
    started: bool
    turn: int
    players: List[str]


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
    new_game.add_player(player)

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


@app.websocket("/ws/lobby/{lobby_id}")
async def lobby_websocket_handler(websocket: WebSocket, lobby_id: int):
    connection_manager = LobbyConnectionHandler()
    await connection_manager.listen(websocket, lobby_id, player_repo)


@app.post("/api/lobby/timer")
async def start_timer():
    await asyncio.sleep(120)
    return Response(status_code=200, content="Timer finished")


@app.websocket("/ws/timer")
async def timer_websocket(websocket: WebSocket):
    timer = services.counter.Counter()
    await timer.listen(websocket)


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


@app.put("/api/lobby/{id_game}/start")
async def start_game(
    id_game: int, games_repo: GameRepository = Depends(get_games_repo)
):
    selec_game = games_repo.get(id_game)
    if selec_game is None:
        raise HTTPException(status_code=404, detail="Game dont found")
    if len(selec_game.players) < selec_game.min_players:
        raise HTTPException(
            status_code=412, detail="Doesnt meet the minimum number of players"
        )
    selec_game.started = True
    games_repo.save(selec_game)
    return {"status": "success!"}


class GameIn2(BaseModel):
    game_id: int
    players: List[str]


class CardsFigOut(BaseModel):
    card_id: int
    card_name: str


class PlayerOut2(BaseModel):
    player: str
    cards_out: List[CardsFigOut]


class SetCardsResponse(BaseModel):
    all_cards: List[PlayerOut2]


@app.post("/api/partida/en_curso", response_model=SetCardsResponse)
async def repartir_cartas_figura(
    req: GameIn2,
    card_repo: FigRepository = Depends(get_card_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
    game_repo: GameRepository = Depends(get_games_repo),
):
    all_cards = []
    for player in req.players:
        identifier_player = UUID(player)
        in_game_player = player_repo.get_by_identifier(identifier_player)
        in_game = game_repo.get(req.game_id)
        if in_game_player is None:
            raise HTTPException(status_code=404, detail="Player dont found!")
        if in_game is None:
            raise HTTPException(status_code=404, detail="Game dont found!")
        if not in_game_player in in_game.players:
            continue
        cards = card_repo.get_many(3)
        new_cards = []
        for card in cards:
            new_card = CardsFigOut(card_id=card.id, card_name=card.name)
            new_cards.append(new_card)
        new_dic = PlayerOut2(player=player, cards_out=new_cards)
        all_cards.append(new_dic)
    return SetCardsResponse(all_cards=all_cards)


class IdentityIn(BaseModel):
    identifier: UUID


class PlayersOfGame(BaseModel):
    identifier: UUID
    name: str


class ResponseOut(BaseModel):
    id: int
    started: bool
    players: List[PlayersOfGame]


@app.patch("/api/lobby/{id}", response_model=ResponseOut)
def unlock_game_not_started(
    id: int, ident: IdentityIn, repo: GameRepository = Depends(get_games_repo)
):
    lobby_query = repo.get(id)
    if lobby_query is None:
        raise HTTPException(status_code=404, detail="Lobby not found")
    elif lobby_query.started == True:
        raise HTTPException(status_code=412, detail="Game already started")

    if len(lobby_query.players) == lobby_query.max_players:
        player_exit = (  # obtiene el jugador de la lista de jugadores que se quiere ir
            next(
                (
                    player
                    for player in lobby_query.players
                    if player.identifier == ident.identifier
                )
            )
        )
        if player_exit == lobby_query.host:  # si el jugador que se quiere ir es el host
            repo.delete(lobby_query)  # borro la partida
            return ResponseOut(id=0, started=False, players=[])  # devuelvo vacio

        lobby_query.delete_player(player_exit)  # borro al jugador de la lista
        lobby_query.started = False  # seteo en falso
        repo.save(lobby_query)  # guardo los cambios de la partida
        list_players = [  # guarda la lista de jugadores
            PlayersOfGame(identifier=UUID(str(player.identifier)), name=player.name)
            for player in lobby_query.players
        ]
        return ResponseOut(
            id=lobby_query.id, started=lobby_query.started, players=list_players
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="No hay suficientes jugadores para desbloquear la partida",
        )

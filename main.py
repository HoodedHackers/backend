import asyncio
from os import getenv
from typing import Dict, List
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import services.connection_manager
import services.counter
from database import Database
from model import Game, Player
from model.exceptions import GameStarted, PreconditionsNotMet
from repositories import (FigRepository, GameRepository, PlayerRepository,
                          create_all_figs)

from services import Managers, ManagerTypes

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


class GameIn(BaseModel):
    identifier: UUID 
    name: str = Field(min_length=1, max_length=64)
    max_players: int = Field(ge=2, le=4)
    min_players: int = Field(ge=2, le=4)


class PlayerOut(BaseModel):
    id_player: UUID #NO LE ENVIO ESTO id int 


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
    players_out = [
        PlayerOut(id_player=UUID(str(player.identifier))) for player in new_game.players
    ]
    return GameOut(
        id=new_game.id,
        name=new_game.name,
        max_players=new_game.max_players,
        min_players=new_game.min_players,
        started=new_game.started,
        players=players_out,
    )


class GameStateOutput(BaseModel):
    id: int
    name: str
    current_players: int
    max_players: int
    min_players: int
    started: bool
    turn: int
    players: List[str]


@app.get("/api/lobby")
def get_games_available(
    repo: GameRepository = Depends(get_games_repo),
) -> List[GameStateOutput]:
    lobbies_queries = repo.get_available(10)
    lobbies = []
    for lobby_query in lobbies_queries:
        lobby = GameStateOutput(
            id=lobby_query.id,
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


@app.post("/api/lobby/timer")
async def start_timer():
    await asyncio.sleep(120)
    return Response(status_code=200, content="Timer finished")


@app.websocket("/ws/timer")
async def timer_websocket(websocket: WebSocket):
    timer = services.counter.Counter()
    await timer.listen(websocket)


@app.websocket("/ws/api/lobby")
async def notify_new_games(websocket: WebSocket):

    await websocket.accept()

    previous_lobbies = game_repo.get_available(10)

    while True:
        await asyncio.sleep(1)
        current_lobbies = game_repo.get_available(10)
        if previous_lobbies != current_lobbies:
            await websocket.send_json({"message": "update"})


@app.get("/api/lobby/{id}")
def get_game(id: int, repo: GameRepository = Depends(get_games_repo)):
    lobby_query = repo.get(id)
    if lobby_query is None:
        raise HTTPException(status_code=404, detail="Lobby not found")
    lobby = GameStateOutput(
        id=lobby_query.id,
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
    id: int
    name: str
    identifier: str


@app.post("/api/name")
async def set_player_name(
    setNameRequest: SetNameRequest,
    player_repo: PlayerRepository = Depends(get_player_repo),
) -> SetNameResponse:
    player = Player(name=setNameRequest.name)
    player_repo.save(player)
    return SetNameResponse(
        id=player.id, name=player.name, identifier=str(player.identifier)
    )


class JoinGameRequest(BaseModel):
    id_game: int = Field()
    identifier_player: str = Field()


@app.put("/api/lobby/{id_game}")
async def join_game(
    req: JoinGameRequest,
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
    join_leave_manager = Managers.get_manager(ManagerTypes.JOIN_LEAVE)
    await join_leave_manager.broadcast(
        {
            "player_id": selec_player.id,
            "action": "join",
            "player_name": selec_player.name,
        },
        selec_game.id,
    )
    return {"status": "success!"}


class StartGameRequest(BaseModel):
    identifier: UUID = Field(UUID)


@app.put("/api/lobby/{id_game}/start")
async def start_game(
    id_game: int,
    start_game_request: StartGameRequest,
    games_repo: GameRepository = Depends(get_games_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
):
    selec_game = games_repo.get(id_game)
    if selec_game is None:
        raise HTTPException(status_code=404, detail="Game dont found")
    player = player_repo.get_by_identifier(start_game_request.identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Requesting player not found")
    if player != selec_game.host:
        raise HTTPException(status_code=402, detail="Non host player request")
    try:
        selec_game.start()
    except PreconditionsNotMet:
        raise HTTPException(
            status_code=400, detail="Doesnt meet the minimum number of players"
        )
    except GameStarted:
        raise HTTPException(status_code=400, detail="Game has already started")
    selec_game.started = True
    selec_game.shuffle_players()
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
    id_play: int


class PlayersOfGame(BaseModel):
    id_player: int
    name: str


class ResponseOut(BaseModel):
    players: List[PlayersOfGame]


@app.patch("/api/lobby/{id}", response_model=ResponseOut)
def exit_game(
    id: int,
    ident: IdentityIn,
    repo: GameRepository = Depends(get_games_repo),
    repo_player: PlayerRepository = Depends(get_player_repo),
):
    lobby_query = repo.get(id)
    if lobby_query is None:
        raise HTTPException(status_code=404, detail="Lobby not found")
    player_exit = repo_player.get(ident.id_play) #ver
    if player_exit is None:
        raise HTTPException(status_code=404, detail="Player not found")
    elif player_exit not in lobby_query.players:
        raise HTTPException(status_code=404, detail="Player not in lobby")
    # si el host se quiere ir y el juego no empezo, se borra el lobby
    elif player_exit == lobby_query.host and lobby_query.started is False:
        repo.delete(lobby_query)
        #MANDO UN MENSAJE DE OK
        #return ResponseOut(players=[])
    elif (
        len(lobby_query.players) == 2 and lobby_query.started is True
    ):  # falta test para este caso
        repo.delete(lobby_query)
        # debo hablar con front sobre que retornar en estos casos
        return ResponseOut(players = [])  #ver esto con front #mandar la lista de jugadore que quedar

    # en cualquier otro caso, es decir, si el juego ya empezo o si un jugador comun se quiere
    # ir o el host se quiere y empezo el juego entonces se borra al jugador del lobby o partida :D
    lobby_query.delete_player(player_exit)
    repo.save(lobby_query)
    #list_player va, no va id ni started
    list_players = [
        PlayersOfGame(
            identifier=player.id_player, name=player.name 
        )  # cambiar esto, no se debe devolver el uuid
        for player in lobby_query.players
    ]
    return ResponseOut(   #aca va solo el nombre, solo va el nombre con la lista de jugadores
        players=list_players
    )


class AdvanceTurnRequest(BaseModel):
    identifier: UUID = Field(UUID)


@app.post("/api/lobby/{game_id}/advance")
async def advance_game_turn(
    game_id: int,
    advance_request: AdvanceTurnRequest,
    player_repo: PlayerRepository = Depends(get_player_repo),
    game_repo: GameRepository = Depends(get_games_repo),
):
    player = player_repo.get_by_identifier(advance_request.identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    game = game_repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if player not in game.players:
        raise HTTPException(status_code=404, detail="Player is not in game")
    if player != game.current_player():
        raise HTTPException(status_code=401, detail="It's not your turn")
    try:
        game.advance_turn()
    except PreconditionsNotMet:
        raise HTTPException(status_code=401, detail="Game hasn't started yet")
    current_player = game.current_player()
    assert current_player is not None
    turn_manager = Managers.get_manager(ManagerTypes.TURNS)
    await turn_manager.broadcast(
        {
            "current_turn": game.current_player_turn,
            "game_id": game.id,
            "player_id": current_player.id,
        },
        game_id,
    )
    return {"status": "success"}


@app.websocket("/api/lobby/{game_id}/turns")
async def turn_change_notifier(websocket: WebSocket, game_id: int):
    manager = Managers.get_manager(ManagerTypes.TURNS)
    await manager.connect(websocket, game_id)
    try:
        while True:
            await websocket.receive_bytes()
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)

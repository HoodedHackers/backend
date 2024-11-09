import asyncio
import random
from os import getenv
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import services.counter
from database import Database
from model import (BOARD_MAX_SIDE, BOARD_MIN_SIDE, TOTAL_FIG_CARDS,
                   TOTAL_HAND_FIG, TOTAL_HAND_MOV, Game, History, MoveCards,
                   Player)
from model.exceptions import GameStarted, PreconditionsNotMet
from repositories import GameRepository, HistoryRepository, PlayerRepository
from services import Managers, ManagerTypes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
history_repo = HistoryRepository(session)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_repos_to_request(request: Request, call_next):
    request.state.game_repo = game_repo
    request.state.player_repo = player_repo
    request.state.history_repo = history_repo
    response = await call_next(request)
    return response


def get_history_repo(request: Request) -> HistoryRepository:
    return request.state.history_repo


def get_games_repo(request: Request) -> GameRepository:
    return request.state.game_repo


def get_player_repo(request: Request) -> PlayerRepository:
    return request.state.player_repo


class GameIn(BaseModel):
    identifier: UUID
    name: str = Field(min_length=1, max_length=64)
    max_players: int = Field(ge=2, le=4)
    min_players: int = Field(ge=2, le=4)
    is_private: bool
    password: Optional[str] = None


class PlayerOut(BaseModel):
    id_player: UUID


class GameOut(BaseModel):
    id: int
    name: str
    max_players: int
    min_players: int
    started: bool
    is_private: bool
    players: List[PlayerOut]


@app.post("/api/lobby", response_model=GameOut)
async def create_game(
    game_create: GameIn,
    game_repo: GameRepository = Depends(get_games_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
) -> GameOut:
    """
    Crea un nuevo juego en el lobby
    """

    if game_create.min_players > game_create.max_players:
        raise HTTPException(
            status_code=412,
            detail="El número mínimo de jugadores no puede ser mayor al máximo",
        )
    if game_create.is_private and game_create.password is None:
        raise HTTPException(
            status_code=412,
            detail="Se necesita una contraseña para un juego privado",
        )
    player = player_repo.get_by_identifier(game_create.identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    password_hash = None
    if game_create.password:
        password_hash = pwd_context.hash(game_create.password)

    new_game = Game(
        name=game_create.name,
        host=player,
        host_id=player.id,
        max_players=game_create.max_players,
        min_players=game_create.min_players,
        started=False,
        is_private=game_create.is_private,
        password=password_hash,
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
        is_private=new_game.is_private,
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
    is_private: bool = False
    players: List[str]


@app.get("/api/lobby")
def get_games_available(
    repo: GameRepository = Depends(get_games_repo),
    max_players: Optional[int] = None,
    name: Optional[str] = None,
) -> List[GameStateOutput]:
    """
    Retorna una lista de juegos disponibles
    """
    params: Dict[str, Any] = {
        "count": 10,
    }
    if max_players is not None:
        params["max_players"] = max_players
    if name is not None:
        params["name"] = name
    lobbies_queries = repo.get_available(**params)
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
            is_private=lobby_query.is_private,
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
        is_private=lobby_query.is_private,
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
    password: Optional[str] = None


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

    if selec_game.is_private and req.password is not None:
        if not pwd_context.verify(req.password, selec_game.password):
            raise HTTPException(status_code=401, detail="Invalid password")

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


def get_players_and_cards(game: Game):
    # print(game.get_player_hand_figures(1))
    return [
        {"player_id": p.id, "cards": game.get_player_hand_figures(p.id)}
        for p in game.players
    ]


async def broadcast_players_and_cards(manager, game_id, game):
    players_cards = get_players_and_cards(game)
    await manager.broadcast(
        {"players": players_cards},
        game_id,
    )


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
    handMov = []
    selec_game.distribute_deck()
    for player in selec_game.players:
        selec_game.add_random_card(player.id)
        selec_game.deal_card_mov(player.id)
        game_repo.save(selec_game)
        handMov = selec_game.get_player_hand_movs(player.id)
        manager0 = Managers.get_manager(ManagerTypes.CARDS_MOV)
        await manager0.single_send(
            {"action": "deal", "card_mov": handMov},
            id_game,
            player.id,
        )
    games_repo.save(selec_game)
    manager = Managers.get_manager(ManagerTypes.CARDS_FIGURE)
    await broadcast_players_and_cards(manager, id_game, selec_game)
    await Managers.get_manager(ManagerTypes.GAME_STATUS).broadcast(
        {
            "game_id": id_game,
            "status": "started",
        },
        id_game,
    )
    return {"status": "success!"}


class GameIn2(BaseModel):
    game_id: int
    player: str


class SetCardsResponse(BaseModel):
    player_id: int
    all_cards: List[int]


@app.websocket("/ws/lobby/{game_id}/figs")
async def deal_cards_figure(websocket: WebSocket, game_id: int, player_id: int):
    """
    Este WS se encarga de repartir las cartas de figura a los jugadores conectados
    y de mostrar a los demas jugadores las cartas figura del jugador en turno.
    en espera: {receive: 'cards'} en el mensaje y ademas de el player id en la url

    """
    game = game_repo.get(game_id)
    player = player_repo.get(player_id)
    if game is None:
        await websocket.accept()
        await websocket.send_json({"error": "Game not found"})
        await websocket.close()
        return

    if player is None:
        await websocket.accept()
        await websocket.send_json({"error": "Player not found"})
        await websocket.close()
        return
    if player not in game.players:
        await websocket.accept()
        await websocket.send_json({"error": "Player not in game"})
        await websocket.close()
        return

    manager = Managers.get_manager(ManagerTypes.CARDS_FIGURE)
    await manager.connect(websocket, game_id, player_id)
    try:
        while True:
            data = await websocket.receive_json()
            request = data.get("receive")
            if request is None:
                await websocket.send_json({"error": "invalid request"})
                continue

            await broadcast_players_and_cards(manager, game_id, game)

    except WebSocketDisconnect:
        manager.disconnect(game_id, player_id)


class ExitRequest(BaseModel):
    identifier: UUID


def check_victory(game: Game):
    return game.started and len(game.players) == 1


async def nuke_game(game: Game, games_repo: GameRepository):
    games_repo.delete(game)
    await Managers.disconnect_all(game.id)


@app.post("/api/lobby/{game_id}/exit")
async def exit_game(
    game_id: int,
    exit_request: ExitRequest,
    games_repo: GameRepository = Depends(get_games_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
):
    game = games_repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    player = player_repo.get_by_identifier(exit_request.identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Jugador no encontrade")
    if player not in game.players:
        raise HTTPException(status_code=404, detail="Jugador no presente en la partida")
    leave_manager = Managers.get_manager(ManagerTypes.JOIN_LEAVE)
    if player == game.host and not game.started:
        games_repo.delete(game)
        await leave_manager.broadcast("el host ha abandonado la partida", game.id)
        await Managers.disconnect_all(game.id)
        return {"status": "success"}

    game.delete_player(player)
    games_repo.save(game)

    if check_victory(game):
        winner = game.get_player_in_game(0)
        await leave_manager.broadcast({"response": winner.id}, game.id)
        await Managers.disconnect_all(game.id)
        games_repo.delete(game)
        return {"status": "success"}

    return {"status": "success"}


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
    for player in game.players:
        game.deal_card_mov(player.id)
        game_repo.save(game)
        handMov = game.get_player_hand_movs(player.id)
        await Managers.get_manager(ManagerTypes.CARDS_MOV).single_send(
            {"action": "deal", "card_mov": handMov},
            game.id,
            player.id,
        )
    cards = game.add_random_card(player.id)
    game_repo.save(game)
    manager = Managers.get_manager(ManagerTypes.CARDS_FIGURE)
    await broadcast_players_and_cards(manager, game_id, game)
    turn_manager = Managers.get_manager(ManagerTypes.TURNS)

    await turn_manager.broadcast(
        {
            "current_turn": game.current_player_turn,
            "game_id": game.id,
            "player_id": current_player.id,
            "player_name": current_player.name,
        },
        game_id,
    )

    return {"status": "success"}


@app.websocket("/ws/lobby/{game_id}/movement_cards")
async def notify_movement_card(
    websocket: WebSocket,
    game_id: int,
    player_UUID: UUID,
):
    """
    Este WS se encarga de notificar la mano de cartas de movimiento de cada jugador.
    Retorna mensajes con alguno o todos los parametros segun disponga el front:
        {
            "action": "select"|"use_card"|"use_card_single"|"recover_card"|"deal"|,
            "card_mov":[card.id],
            "player_id": int,
            "card_id": int,
            "index": int,
            "len": len(hand) | len(mov_parcial),
        },
    """
    game = game_repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    player = player_repo.get_by_identifier(player_UUID)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    id = player.id
    manager = Managers.get_manager(ManagerTypes.CARDS_MOV)
    await manager.connect(websocket, game_id, id)
    try:
        while True:
            data = await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(game_id, id)


class SelectMovRequest(BaseModel):
    identifier: UUID = Field(UUID)
    card_id: int
    card_index: int
    game_id: int


@app.post("/api/lobby/{game_id}/use_movement_card")
async def select_movement_card(
    req: SelectMovRequest,
    player_repo: PlayerRepository = Depends(get_player_repo),
    game_repo: GameRepository = Depends(get_games_repo),
):
    """
    Este endpoint se encarga de recibir la selección de cartas de un jugador y notificar a los demás jugadores de la partida.

    """
    game = game_repo.get(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    player = player_repo.get_by_identifier(req.identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    if player not in game.players:
        raise HTTPException(status_code=404, detail="Player dont found in game!")

    if player != game.current_player():
        raise HTTPException(status_code=401, detail="It's not your turn")

    index = req.card_index
    current_card = req.card_id
    hand = game.get_player_hand_movs(player.id)
    if current_card not in hand:
        raise HTTPException(status_code=404, detail="Card not in hand")
    manager = Managers.get_manager(ManagerTypes.CARDS_MOV)
    await manager.broadcast(
        {
            "action": "select",
            "player_id": player.id,
            "card_id": current_card,
            "index": index,
        },
        game.id,
    )
    return "success!"


def board_status_message(game: Game):
    board = [tile.value for tile in game.board]
    possible_figures = [
        {
            "player_id": player.id,
            "moves": [
                {
                    "tiles": move.true_positions_canonical(),
                    "fig_id": move.figure_id(),
                }
                for move in game.get_possible_figures(player.id)
            ],
        }
        for player in game.players
    ]
    return {
        "game_id": game.id,
        "board": board,
        "possible_figures": possible_figures,
    }


@app.websocket("/ws/lobby/{game_id}/board")
async def lobby_notify_board(websocket: WebSocket, game_id: int, player_id: int):
    """
    Este WS se encarga de notificar el estado del tablero a los jugadores conectados.
    Retorna mensajes de la siguiente forma:
        {
            "game_id": int,
            "board": [int],
            "possible_moves": [
                {
                    "player_id": int,
                    "moves": [
                        {
                            "tiles": [int],
                            "fig_id": int
                        }
                    ]
                }
            ]
        }
    Tambien se puede recibir pedidos del estado del tablero usando el siguiente mensaje:
        {
            "request": "status"
        }
    """
    manager = Managers.get_manager(ManagerTypes.BOARD_STATUS)
    await manager.connect(websocket, game_id, player_id)
    try:
        while True:
            data = await websocket.receive_json()
            request = data.get("request")
            if request is None or request != "status":
                await websocket.send_json({"error": "invalid request"})
                continue
            game = game_repo.get(game_id)
            if game is None:
                await websocket.send_json({"error": "invalid game id"})
                continue
            await websocket.send_json(board_status_message(game))
    except WebSocketDisconnect:
        manager.disconnect(game_id, player_id)


class InHandFigure(BaseModel):
    player_identifier: UUID = Field(UUID)
    card_id: int


@app.post("/api/lobby/in-course/{game_id}/discard_figs")
async def discard_hand_figure(
    game_id: int,
    player_ident: InHandFigure,
    game_repo: GameRepository = Depends(get_games_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
):
    game = game_repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    player = player_repo.get_by_identifier(player_ident.player_identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Jugador no encontrade")
    if player not in game.players:
        raise HTTPException(status_code=404, detail="Jugador no presente en la partida")

    hand_figures = game.get_player_hand_figures(player.id)
    if player_ident.card_id not in hand_figures:
        raise HTTPException(
            status_code=404, detail="Carta no encontrada en la mano del jugador"
        )

    figures = game.ids_get_possible_figures(player.id)
    manager = Managers.get_manager(ManagerTypes.CARDS_FIGURE)
    if player_ident.card_id not in figures:
        await manager.broadcast({"error": "Invalid figure"}, game_id)
    else:
        hand_fig = game.discard_card_hand_figures(player.id, player_ident.card_id)
        game.discard_card_movement(player.id)
        players = [
            {"player_id": p.id, "cards": game.get_player_hand_figures(p.id)}
            for p in game.players
        ]
        await manager.broadcast({"players": players}, game_id)
        game_repo.save(game)
        return {"status": "success"}


@app.websocket("/ws/lobby/{game_id}/turns")
async def turn_change_notifier(websocket: WebSocket, game_id: int, player_id: int):
    """
    {
        "current_turn": int,
        "game_id": int,
        "player_id": int,
        "player_name": str
    }
    """
    manager = Managers.get_manager(ManagerTypes.TURNS)
    await manager.connect(websocket, game_id, player_id)
    try:
        while True:
            req = await websocket.receive_json()
            if req.get("request") == "status":
                game = game_repo.get(game_id)
                if game is None:
                    await websocket.send_json(
                        {
                            "error": "invalid game",
                        }
                    )
                    continue
                current_player = game.current_player()
                if current_player is None:
                    await websocket.send_json(
                        {
                            "error": "game has no players",
                        }
                    )
                    continue
                await websocket.send_json(
                    {
                        "current_turn": game.current_player_turn,
                        "game_id": game.id,
                        "player_id": current_player.id,
                        "player_name": current_player.name,
                    }
                )
    except WebSocketDisconnect:
        manager.disconnect(game_id, player_id)


@app.websocket("/ws/lobby/{game_id}")
async def lobby_notify_inout(websocket: WebSocket, game_id: int, player_id: int):
    """
    Este ws se encarga de notificar a los usuarios conectados dentro de un juego cuando otro usuario se conecta o desconecta, enviando la lista
    actualizada de jugadores actuales, tambien los agrega a la DB.

    Se espera: {user_identifier: 'str'}

    Se retorna: {players: [{player_id: 'int', player_name: 'str'}]}
    """
    game = game_repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    player = player_repo.get(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    manager = Managers.get_manager(ManagerTypes.JOIN_LEAVE)
    await manager.connect(websocket, game_id, player_id)
    try:
        while True:
            data = await websocket.receive_json()
            user_id = data.get("user_identifier")
            if user_id is None:
                await websocket.send_json({"error": "User id is missing"})
                continue

            player = player_repo.get_by_identifier(UUID(user_id))
            if player is None:
                await websocket.send_json({"error": "Player not found"})
                continue

            seed_password = data.get("password")
            if seed_password is not None:
                if not pwd_context.verify(seed_password, game.password):
                    await websocket.send_json({"error": "Invalid password"})
                    continue

            game.add_player(player)
            game_repo.save(game)

            players_raw = game.players
            players = [{"player_id": p.id, "player_name": p.name} for p in players_raw]
            await manager.broadcast({"players": players}, game_id)

    except WebSocketDisconnect:
        manager.disconnect(game_id, player_id)
        players_raw = game.players
        players = [{"player_id": p.id, "player_name": p.name} for p in players_raw]
        await manager.broadcast({"players": players}, game_id)


@app.websocket("/ws/lobby/{game_id}/status")
async def lobby_notify_status(websocket: WebSocket, game_id: int, player_id: int):
    """
    Este WS se encarga de notificar el estado de la partida a los jugadores conectados.
    Retorna mensajes de la siguiente forma:
        {
            "game_id": int,
            "status": "started"|"finished"|"canceled"
        }
    """
    manager = Managers.get_manager(ManagerTypes.GAME_STATUS)
    await manager.connect(websocket, game_id, player_id)
    try:
        while True:
            data = await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(game_id, player_id)


class MovePlayer(BaseModel):
    identifier: UUID
    origin_tile: int
    dest_tile: int
    card_mov_id: int
    index_hand: int


class PlayResponseSingle(BaseModel):
    card_mov: List[int]  # hand_mov - mov_parcial


@app.post("/api/game/{game_id}/play_card")
async def play_card_mov(
    req: MovePlayer,
    game_id: int,
    player_repo: PlayerRepository = Depends(get_player_repo),
    games_repo: GameRepository = Depends(get_games_repo),
    history_repo: HistoryRepository = Depends(get_history_repo),
):
    """
    Este endpoint se encarga de realizar un movimiento en el tablero de un jugador

    Se retorna al ws de tablero: (ver /ws/lobby/{game_id}/board)
    Se retorna al ws de cartas:
        {
            "action": "use_card"|"use_card_single"
            "card_mov":         |[card.id]
            "player_id": int,
            "len": int
        }
    """
    game = games_repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    player = player_repo.get_by_identifier(req.identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    if player not in game.players:
        raise HTTPException(status_code=404, detail="Player not in game")
    if player != game.current_player():
        raise HTTPException(status_code=401, detail="It's not your turn")

    if req.card_mov_id not in game.get_player_hand_movs(player.id):
        raise HTTPException(status_code=404, detail="Card not in hand")

    card = MoveCards(id=req.card_mov_id, dist=[])
    card.create_card(req.card_mov_id)

    origin_x = req.origin_tile % 6
    origin_y = req.origin_tile // 6
    destination_x = req.dest_tile % 6
    destination_y = req.dest_tile // 6

    tuple_origin = (origin_x, origin_y)
    tuple_destination = (destination_x, destination_y)

    tuples_valid = card.sum_dist(tuple_origin)

    if tuple_destination not in tuples_valid:
        print("Invalid move")
        raise HTTPException(status_code=404, detail="Invalid move")

    game.swap_tiles(origin_x, origin_y, destination_x, destination_y)

    history = History(
        game_id=game_id,
        player_id=player.id,
        fig_mov_id=req.card_mov_id,
        origin_x=origin_x,
        origin_y=origin_y,
        dest_x=destination_x,
        dest_y=destination_y,
    )
    history_repo.save(history)

    cards_left = game.add_single_mov(player.id, req.card_mov_id)
    mov_parcial = game.get_player_mov_parcial(player.id)
    game_repo.save(game)
    manager_board = Managers.get_manager(ManagerTypes.BOARD_STATUS)
    manager_card_mov = Managers.get_manager(ManagerTypes.CARDS_MOV)

    await manager_board.broadcast(
        board_status_message(game),
        game_id,
    )

    await manager_card_mov.broadcast(
        {
            "action": "use_card",
            "player_id": player.id,
            "len": TOTAL_HAND_MOV
            - len(mov_parcial),  # LEN DE LA DIFERENCIA (3-mov_parcial)
        },
        game.id,
    )

    return PlayResponseSingle(card_mov=cards_left)


class UndoMoveRequest(BaseModel):
    identifier: UUID = Field(UUID)


@app.post("/api/game/{game_id}/undo")
async def undo_move(
    request: UndoMoveRequest,
    game_id: int,
    player_repo: PlayerRepository = Depends(get_player_repo),
    games_repo: GameRepository = Depends(get_games_repo),
    history_repo: HistoryRepository = Depends(get_history_repo),
):
    """
    Este endpoint se encarga de deshacer el último movimiento realizado por un jugador

    Se envia por el ws ws de tablero: (ver /ws/lobby/{game_id}/board)
    Se envia por el ws de cartas:
        {
            "action": "recover_card"|"recover_card_single"
            "card_mov":             |[card.id]
            "player_id": int,
            "len": int
        }
    """
    player = player_repo.get_by_identifier(request.identifier)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    game = games_repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if player not in game.players:
        raise HTTPException(status_code=404, detail="Player not in game")
    if player != game.current_player():
        raise HTTPException(status_code=401, detail="It's not your turn")

    last_play = history_repo.get_last(game_id)
    if not last_play:
        raise HTTPException(status_code=404, detail="No history found")
    if last_play.player_id != player.id:
        raise HTTPException(status_code=404, detail="Nothing to undo")

    game.swap_tiles(
        last_play.dest_x, last_play.dest_y, last_play.origin_x, last_play.origin_y
    )
    # recordar que aplica sobre la mano de movimientos parciales del jugador
    cards_left = game.remove_single_mov(player.id, last_play.fig_mov_id)
    game_repo.save(game)

    history_repo.delete(last_play)

    manager_board = Managers.get_manager(ManagerTypes.BOARD_STATUS)
    manager_card_mov = Managers.get_manager(ManagerTypes.CARDS_MOV)

    await manager_board.broadcast(
        board_status_message(game),
        game_id,
    )

    await manager_card_mov.broadcast(
        {
            "action": "recover_card",
            "player_id": player.id,
            "len": len(cards_left),
        },
        game.id,
    )

    await manager_card_mov.single_send(
        {
            "action": "recover_card_single",
            "card_mov": cards_left,  # hand_mov - mov_parcial
            "player_id": player.id,
        },
        game.id,
        player.id,
    )
    return {"status": "success!"}


@app.get("/api/history/{game_id}")
async def get_history(
    game_id: int, history_repo: HistoryRepository = Depends(get_history_repo)
):
    history = history_repo.get_all(game_id)
    return history

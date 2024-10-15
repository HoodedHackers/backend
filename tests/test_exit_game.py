import asyncio
import unittest
from os import getenv
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

import asserts
import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket, WebSocketDisconnect

from database import Database
from main import app, game_repo, get_games_repo, player_repo
from model import Game, Player
from repositories import GameRepository, PlayerRepository
from repositories.player import PlayerRepository
from services import Managers, ManagerTypes

client = TestClient(app)


def set_player_name(name: str):
    response = client.post("/api/name", json={"name": name})
    assert response.status_code == 200
    return response.json()


def create_game(identifier: UUID, name: str, min_players: int, max_players: int):
    response = client.post(
        "/api/lobby",
        json={
            "identifier": identifier,
            "name": name,
            "min_players": min_players,
            "max_players": max_players,
        },
    )
    assert response.status_code == 200
    return response.json()


def endpoint_unirse_a_partida(game_id: int, player_identifier: str):
    response = client.put(
        f"/api/lobby/{game_id}",
        json={"id_game": game_id, "identifier_player": player_identifier},
    )
    assert response.status_code == 200
    return response.json()


def game_and_players():
    player1 = set_player_name("Player 1")
    player2 = set_player_name("Player 2")
    player3 = set_player_name("Player 3")
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    endpoint_unirse_a_partida(game["id"], player3["identifier"])
    return game, player1, player2, player3


@app.websocket("/ws/{lobby_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, lobby_id: int, player_id: int):
    manager = Managers.get_manager(ManagerTypes.JOIN_LEAVE)
    await manager.connect(websocket, lobby_id, player_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"message": data}, lobby_id)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        manager.disconnect(lobby_id, player_id)


# caso en donde el jugador no host sale y aun no empezo la partida
@pytest.mark.asyncio
async def test_exit_game_success():
    game, player1, player2, player3 = game_and_players()
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"id_play": player2["identifier"]}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    res = game_repo.get(game["id"])
    # print(res.players)
    assert len(res.players) == 2
    # assert len(game_repo.get(game["id"]).players) == 2


# caso en donde el jugador host sale y aun no empezo la partida
def test_exit_game_not_started_host():
    game, player1, player2, player3 = game_and_players()
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"id_play": player1["identifier"]}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert game_repo.get(game["id"]) is None

    manager = Managers.get_manager(ManagerTypes.JOIN_LEAVE)
    assert id not in manager.lobbies


# test en donde no se encontro el lobby, no exite el juego
def test_exit_game_not_found():
    response = client.patch("/api/lobby/9999", json={"id_play": str(uuid4())})
    assert response.status_code == 404
    assert response.json()["detail"] == "Lobby not found"


# test en donde se empezo el juego y sale un jugador
def test_exit_game_already_started():
    game, player1, player2, player3 = game_and_players()

    game_instance = game_repo.get(game["id"])
    assert game_instance is not None
    game_instance.started = True
    game_repo.save(game_instance)
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"id_play": player1["identifier"]}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert len(game_repo.get(game["id"]).players) == 2


# caso en donde salen el host y luego quiere salir otro jugador (caso extremo)
def test_exit_game_after_lobby_deleted():
    player1 = set_player_name("Test Player")
    player2 = set_player_name("Test player 2")

    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"id_play": player1["identifier"]}
    )
    assert response.status_code == 200
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"id_play": player2["identifier"]}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Lobby not found"


# caso en que un jugador no exista en la partida/sala de espera y quiera salir
def test_game_player_not_found():
    player1 = set_player_name("Test Player")
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    non_existent_player = str(uuid4())
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"id_play": non_existent_player}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Player not found"


# caso en donde el jugador no esta en la sala de espera
def test_exit_game_not_in_lobby():
    player1 = set_player_name("Test Player")
    player2 = set_player_name("Test Player 2")
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"id_play": player2["identifier"]}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Player not in lobby"


# caso en el que hay 2 jugadores y uno gana porque el otro abandono la partida
def test_exit_game_two_players_started():
    player1 = set_player_name("Player 1")
    player2 = set_player_name("Player 2")

    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=2
    )
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    game_instance = game_repo.get(game["id"])
    assert game_instance is not None
    game_instance.started = True
    game_repo.save(game_instance)
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"id_play": player1["identifier"]}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert game_repo.get(game["id"]) is None


"""

class TestExitGame(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.dbs = Database().session()
        self.games_repo = GameRepository(self.dbs)
        self.player_repo = PlayerRepository(self.dbs)
        identifier1 = str(uuid4())
        identifier2 = str(uuid4())
        identifier3 = str(uuid4())
        identifier4 = str(uuid4())

        self.host = Player(name="Ely")
        self.player_repo.save(self.host)

        self.players = [
            Player(name="Lou"),
            Player(name="Lou^2"),
            Player(name="Andy"),
        ]
        for p in self.players:
            self.player_repo.save(p)

        self.game = Game(
            id=1,
            name="Game of Falls",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[],
            host=self.host,
            host_id=self.host.id,
        )

        self.games_repo.save(self.game)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        # self.dbs.query(FigCards).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_connect_from_lobby(self):

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):  # patch("main.card_repo", self.fig_cards_repo):

            player_id0 = self.players[0].id
            player_id1 = self.players[1].id
            # card_id0 = self.fig_cards[0].id
            #player_id0_ident = self.game.players[0].identifier

            # Debe haber al menos dos jugadores en el juego
            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])
           # self.game.started = True
#ver que onda aca
            player_id0_ident = self.players[0].identifier
#            self.games_repo.save(self.game)
            print("pase por el save")
            # Conectamos ambos jugadores
            with self.client.websocket_connect(
                f"/ws/lobby/1?player_id={player_id0}"
            ) as websocket0:
                with self.client.websocket_connect(
                    f"/ws/lobby/1?player_id={player_id1}"
                ) as websocket1:
                    print("pase por los websocket")

                    # El jugador uno usa la URL @app.patch("/api/lobby/{lobby_id}")  id_play: str
                    response = self.client.patch(
                        f"/api/lobby/1", json = {"id_play":str(player_id0_ident)},
                    )
                    print("ya pase por el response")
                    print(response)
                    assert response.status_code == 200
                    data = response.json()
                    assert data == {"status": "success"}

                    # Comprobamos que se haya efectuado el broadcast
                    data1 = websocket0.receive_json()
                    print(data1)
                    assert data1 == {"action": "el host salio"}
                    data2 = websocket1.receive_json()
                    assert data2 == {"action": "el host salio"}

"""

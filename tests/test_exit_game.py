from os import getenv
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

import asserts
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from database import Database
from main import app, game_repo, get_games_repo, player_repo
from model import Game, Player
from repositories import GameRepository, PlayerRepository
from repositories.player import PlayerRepository

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


# caso en donde el jugador no host sale y aun no empezo la partida
def test_exit_game_success():
    game, player1, player2, player3 = game_and_players()
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player2["identifier"]}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["started"] == False
    assert len(result["players"]) == 2


# caso en donde el jugador host sale y aun no empezo la partida
def test_exit_game_not_started_host():
    game, player1, player2, player3 = game_and_players()
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player1["identifier"]}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["started"] == False
    assert len(result["players"]) == 0


# test en donde no se encontro el lobby, no exite el juego
def test_exit_game_not_found():
    response = client.patch("/api/lobby/9999", json={"identifier": str(uuid4())})
    assert response.status_code == 404


# test en donde se empezo el juego y sale un jugador
def test_exit_game_already_started():
    game, player1, player2, player3 = game_and_players()

    game_instance = game_repo.get(game["id"])
    assert game_instance is not None
    game_instance.started = True
    game_repo.save(game_instance)
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player1["identifier"]}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["started"] == True
    assert len(result["players"]) == 2


# caso en donde salen el host y luego quiere salir otro jugador (caso extremo)
def test_exit_game_after_lobby_deleted():
    player1 = set_player_name("Test Player")
    player2 = set_player_name("Test player 2")
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player1["identifier"]}
    )
    assert response.status_code == 200
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player2["identifier"]}
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
        f"/api/lobby/{game['id']}", json={"identifier": non_existent_player}
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
        f"/api/lobby/{game['id']}", json={"identifier": player2["identifier"]}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Player not in lobby"

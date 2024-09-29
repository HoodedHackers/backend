from fastapi.testclient import TestClient
import asserts
from main import app
import asserts
from unittest.mock import MagicMock

from main import get_games_repo

from model import Game, Player
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI, HTTPException, Depends
from repositories import GameRepository
from uuid import uuid4

client = TestClient(app)


# todo, corregir el test

@patch("main.GameRepository")
@patch("main.PlayerRepository")
def test_crear_partida(mock_game_repo, mock_player_repo):

    test_identifier = uuid4()  
    mock_player = Player(id=99, name="host", identifier=test_identifier)

    mock_game_repo.return_value.save = AsyncMock()
    mock_game_repo.return_value.save.return_value = Game(
        id=1,
        name="partida1",
        max_players=4,
        min_players=2,
        started=False,
        host=Player(name="host", id=99, identifier = uuid4()),
        host_id=99,
        players=[],
    )
    mock_player_repo.return_value.get_by_identifier.return_value = AsyncMock(return_value=mock_player)
    response = client.post(
        "/api/lobby", json={"identifier": str(test_identifier), "name": "partida1", "max_players": 4, "min_players": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "partida1"
    assert data["max_players"] == 4
    assert data["min_players"] == 2
    assert data["started"] is False
    assert isinstance(data["id"], int)
    assert data["players"] != []


@patch("main.GameRepository")
def test_crear_partida_error_min_mayor_max(mock_game_repo):
    response = client.post(
        "/api/lobby", json={"identifier": "123e4567-e89b-12d3-a456-426614174000", "name": "partida1", "max_players": 3, "min_players": 4}
    )
    assert response.status_code == 412
    assert response.json() == {
        "detail": "El número mínimo de jugadores no puede ser mayor al máximo"
    }


@patch("main.GameRepository")
def test_crear_partida_error_min_jugadores_invalido(mock_game_repo):
    response = client.post(
        "/api/lobby", json={"identifier": "123e4567-e89b-12d3-a456-426614174000", "name": "partida1", "max_players": 4, "min_players": 1}
    )
    assert response.status_code == 422


@patch("main.GameRepository")
def test_crear_partida_nombre_vacio(mock_game_repo):
    response = client.post(
        "/api/lobby", json={"identifier": "123e4567-e89b-12d3-a456-426614174000", "name": "", "max_players": 4, "min_players": 2}
    )
    assert response.status_code == 422


def test_crear_partida_campos_invalidos():
    response = client.post(
        "/api/lobby", json={"identifier": "123e4567-e89b-12d3-a456-426614174000", "name": "", "max_players": None, "min_players": None}
    )
    assert response.status_code == 422


@patch("main.GameRepository")
def test_crear_partida_error_brutal(mock_game_repo):
    response = client.post(
        "/api/lobby", json={"identifier": "123e4567-e89b-12d3-a456-426614174000","name": "partida1", "max_players": 5, "min_players": 1}
    )
    assert response.status_code == 422

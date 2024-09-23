from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List
import asserts

from main import app

from fastapi.testclient import TestClient

import asserts
from unittest.mock import MagicMock

from main import get_games_repo

from model import Game, Player
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI, HTTPException, Depends
from repositories import GameRepository

client = TestClient(app)

"""""
def test_borrame():
    response = client.get("/api/borrame")
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(response.json(), {"games": []})
"""


@patch("main.GameRepository")
def test_crear_partida(mock_game_repo):

    mock_game_repo.return_value.save = AsyncMock()
    mock_game_repo.return_value.save.return_value = Game(
        id=1,
        name="partida1",
        max_players=4,
        min_players=2,
        started=False,
        players=[],
    )

    response = client.post(
        "/api/lobby", json={"name": "partida1", "max_players": 4, "min_players": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "partida1"
    assert data["max_players"] == 4
    assert data["min_players"] == 2
    assert data["started"] is False
    assert isinstance(data["id"], int)
    assert data["players"] == []  # no se si esta bien


@patch("main.GameRepository")
def test_crear_partida_error_min_mayor_max(mock_game_repo):
    response = client.post(
        "/api/lobby", json={"name": "partida1", "max_players": 4, "min_players": 5}
    )
    assert response.status_code == 412
    assert response.json() == {
        "detail": "El número mínimo de jugadores no puede ser mayor al máximo"
    }


@patch("main.GameRepository")
def test_crear_partida_error_min_igual_max(mock_game_repo):
    response = client.post(
        "/api/lobby", json={"name": "partida1", "max_players": 4, "min_players": 4}
    )
    assert response.status_code == 412
    assert response.json() == {
        "detail": "El número mínimo de jugadores no puede ser igual al máximo"
    }


@patch("main.GameRepository")
def test_crear_partida_error_min_jugadores_invalido(mock_game_repo):
    response = client.post(
        "/api/lobby", json={"name": "partida1", "max_players": 4, "min_players": 1}
    )
    assert response.status_code == 412
    assert response.json() == {"detail": "El número de jugadores debe ser entre 2 y 4"}


@patch("main.GameRepository")
def test_crear_partida_nombre_vacio(mock_game_repo):
    response = client.post(
        "/api/lobby", json={"name": "", "max_players": 4, "min_players": 2}
    )
    assert response.status_code == 412
    assert response.json() == {"detail": "El nombre de la partida no puede estar vacío"}


def test_crear_partida_campos_invalidos():
    response = client.post(
        "/api/lobby", json={"name": "", "max_players": None, "min_players": None}
    )
    assert response.status_code == 422

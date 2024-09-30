from fastapi.testclient import TestClient
from main import app
import asserts
from unittest.mock import MagicMock
from fastapi import Request, Depends, HTTPException

from main import get_games_repo

from model import Game, Player
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI, HTTPException, Depends
from repositories import GameRepository, PlayerRepository
from uuid import uuid4
from repositories.player import PlayerRepository
from os import getenv
from database import Database
from main import game_repo, player_repo

client = TestClient(app)


def test_create_game():
    # Crea un jugador host
    test_identifier = uuid4()
    host = Player(name="host", identifier=test_identifier)
    player_repo.save(host)

    # Guarda al jugador usando el endpoint
    response = client.post(
        "/api/lobby",
        json={
            "identifier": str(test_identifier),
            "name": "partida1",
            "max_players": 4,
            "min_players": 2,
        },
    )

    # Verifica el estado de la respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "partida1"
    assert data["max_players"] == 4
    assert data["min_players"] == 2
    assert data["started"] is False
    assert isinstance(data["id"], int)
    assert data["players"] == [{"name": "host"}]

    game = game_repo.get(data["id"])
    assert game is not None
    assert game.name == "partida1"
    assert game.host == host


@patch("main.GameRepository")
def test_crear_partida_error_min_mayor_max(mock_game_repo):
    response = client.post(
        "/api/lobby",
        json={
            "identifier": "123e4567-e89b-12d3-a456-426614174000",
            "name": "partida1",
            "max_players": 3,
            "min_players": 4,
        },
    )
    assert response.status_code == 412
    assert response.json() == {
        "detail": "El número mínimo de jugadores no puede ser mayor al máximo"
    }


@patch("main.GameRepository")
def test_crear_partida_error_min_jugadores_invalido(mock_game_repo):
    response = client.post(
        "/api/lobby",
        json={
            "identifier": "123e4567-e89b-12d3-a456-426614174000",
            "name": "partida1",
            "max_players": 4,
            "min_players": 1,
        },
    )
    assert response.status_code == 422


@patch("main.GameRepository")
def test_crear_partida_nombre_vacio(mock_game_repo):
    response = client.post(
        "/api/lobby",
        json={
            "identifier": "123e4567-e89b-12d3-a456-426614174000",
            "name": "",
            "max_players": 4,
            "min_players": 2,
        },
    )
    assert response.status_code == 422


def test_crear_partida_campos_invalidos():
    response = client.post(
        "/api/lobby",
        json={
            "identifier": "123e4567-e89b-12d3-a456-426614174000",
            "name": "",
            "max_players": None,
            "min_players": None,
        },
    )
    assert response.status_code == 422


@patch("main.GameRepository")
def test_crear_partida_error_brutal(mock_game_repo):
    response = client.post(
        "/api/lobby",
        json={
            "identifier": "123e4567-e89b-12d3-a456-426614174000",
            "name": "partida1",
            "max_players": 5,
            "min_players": 1,
        },
    )
    assert response.status_code == 422

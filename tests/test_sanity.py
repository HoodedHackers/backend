from fastapi.testclient import TestClient

import asserts

from main import app

from fastapi.testclient import TestClient

import asserts
from unittest.mock import MagicMock

from main import get_games_repo
from model import Game, Player
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI, HTTPException, Depends


client = TestClient(app)


def test_borrame():
    response = client.get("/api/borrame")
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(response.json(), {"games": []})


client = TestClient(app)


def test_crear_partida():
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
    assert data["players"] != []  # no se si esta bien


def test_crear_partida_error_min_mayor_max():
    response = client.post(
        "/api/lobby", json={"name": "partida1", "max_players": 4, "min_players": 5}
    )
    assert response.status_code == 412
    assert response.json() == {
        "detail": "El número mínimo de jugadores no puede ser mayor al máximo"
    }


def test_crear_partida_error_min_igual_max():
    response = client.post(
        "/api/lobby", json={"name": "partida1", "max_players": 4, "min_players": 4}
    )
    assert response.status_code == 412
    assert response.json() == {
        "detail": "El número mínimo de jugadores no puede ser igual al máximo"
    }


def test_crear_partida_error_min_jugadores_invalido():
    response = client.post(
        "/api/lobby", json={"name": "partida1", "max_players": 4, "min_players": 1}
    )
    assert response.status_code == 412
    assert response.json() == {"detail": "El número de jugadores debe ser entre 2 y 4"}


def test_crear_partida_nombre_vacio():
    response = client.post(
        "/api/lobby", json={"name": "", "max_players": 4, "min_players": 2}
    )
    assert response.status_code == 412
    assert response.json() == {"detail": "El nombre de la partida no puede estar vacío"}



"""""

def test_crear_partida_campos_invalidos():
    response = client.post(
        "/api/lobby", json={"name": "", "max_players": None, "min_players": None}
    )
    assert response.status_code == 422
""" ""

"""""
algo sacado de chatgpt porque estaba muy trabada, 
no funca pero sirve la idea, queria ver como se hacian los 
mock con random

def mock_game_repo():
    # Crear un mock para GameRepository
    with patch("repositories.general.GameRepository") as mock:
        yield mock


def test_sortear_jugadores(mock_game_repo, client):
    # Configura el juego de prueba
    game_id = 1
    player1 = Player(name="Player 1")
    player2 = Player(name="Player 2")
    game = Game(
        id=game_id,
        name="Test Game",
        players=[player1, player2],
        min_players=2,
        max_players=4,
    )

    # Configurar el comportamiento del mock
    mock_game_repo.return_value.get.return_value = game
    mock_game_repo.return_value.save = AsyncMock()

    # Llamar al endpoint
    response = client.post("/api/start_game", json={"game_id": game_id})

    # Verificar que la respuesta sea correcta
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["game_id"] == game_id
    assert "players" in response_data
    assert len(response_data["players"]) == len(game.players)

    # Verifica que los jugadores han sido sorteados
    assert sorted([p.name for p in game.players]) == sorted(
        [p["name"] for p in response_data["players"]]
    )
    assert response_data["players"] != game.players  # Verifica que el orden ha cambiado


def test_sortear_jugadores_no_sufficient_players(mock_game_repo, client):
    # Ajustar el juego para que tenga menos de min_players
    game_id = 1
    player1 = Player(name="Player 1")
    game = Game(
        id=game_id, name="Test Game", players=[player1], min_players=2, max_players=4
    )

    # Configurar el comportamiento del mock
    mock_game_repo.return_value.get.return_value = game

    response = client.post("/api/start_game", json={"game_id": game_id})

    assert response.status_code == 412
    assert response.json() == {
        "detail": "No se puede sortear jugadores si no hay suficientes jugadores"
    }


def test_sortear_jugadores_game_not_found(mock_game_repo, client):
    # Configurar el comportamiento del mock para devolver None
    mock_game_repo.return_value.get.return_value = None

    response = client.post("/api/start_game", json={"game_id": 9999})

    assert response.status_code == 404
    assert response.json() == {"detail": "Partida no encontrada"}
""" ""

from fastapi.testclient import TestClient
import asserts
from main import app
import asserts
from unittest.mock import MagicMock
from fastapi import Request, Depends, HTTPException

from main import get_games_repo

from model import Game, Player
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI, HTTPException, Depends
from repositories import GameRepository, PlayerRepository
from uuid import uuid4, UUID
from repositories.player import PlayerRepository
from os import getenv
from database import Database
from main import game_repo, player_repo
from unittest.mock import Mock
import pytest
from main import PlayerOutRandom
client = TestClient(app)


# crear un jugador
def set_player_name(name: str):
    response = client.post("/api/name", json={"name": name})
    assert response.status_code == 200
    return response.json()


# crear un juego
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


# unirse a un juego
def endpoint_unirse_a_partida(game_id: int, player_identifier: str):
    response = client.put(
        f"/api/lobby/{game_id}",
        json={"id_game": game_id, "identifier_player": player_identifier},
    )
    assert response.status_code == 200
    return response.json()



def test_exit_game_success():
    player1 = set_player_name("Player 1")
    player2 = set_player_name("Player 2")
    player3 = set_player_name("Player 3")

    # Crear el juego
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    
    # Unirse al juego
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    ################### aca va start partida
    


    # El jugador sale de la partida
    response = client.patch(
        f"/api/lobby/salir/{game['id']}",
        json={"identifier": player2["identifier"]}
    )
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["game_id"] == game["id"]
    assert len(result["players"]) == 2  # Solo debería quedar un jugador
 #   assert result["players"][0]["identifier"] == str(player1["identifier"])


''''
# salir de un juego
def exit_game(game_id: int, player_identifier: UUID):
    response = client.delete(
        f"/api/lobby/{game_id}", json = {"identifier": str(player_identifier)}
    )
    assert response.status_code == 200
    return response.json()
'''

"""
# simulo el game repository
@pytest.fixture
def mock_game_repo():
    mock = Mock()
    app.dependency_overrides[get_games_repo] = lambda: mock
    return mock


# test para cuando el jugador no esta en la partida
@pytest.fixture
def test_exit_game_player_in_game(mock_game_repo):
    player1_uuid = uuid4()
    player2_uuid = uuid4()
    player3_uuid = uuid4()
    mock_game = Mock()
    mock_game.players = [
        {"id": 1, "name": "player1", "identifier": player1_uuid},
        {"id": 2, "name": "Player2", "identifier": player2_uuid},
        {"id": 3, "name": "Player3", "identifier": player3_uuid},
    ]
    mock_game_repo.get.return_value = mock_game
    response = client.delete(
        f"/api/lobby/1", json={"identifier": str(player2_uuid)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == 1
    assert len(data["players"]) == 2  # como se va uno quedan solo 2 jugadores
    remaining_players = [player["identifier"] for player in data["players"]]
    assert str(player1_uuid) in remaining_players  # Player1 sigue en la partida
    assert str(player3_uuid) in remaining_players  # Player3 sigue en la partida
    assert str(player2_uuid) not in remaining_players  # Player2 ha salido


def test_exit_game_not_in_game(mock_game_repo):
    player1_uuid = uuid4()
    player2_uuid = uuid4()
    player3_uuid = uuid4()
    mock_game = Mock()
    mock_game.players = [
        {"id": 1, "name": "player1", "identifier": player1_uuid},
        {"id": 2, "name": "Player2", "identifier": player2_uuid},
        {"id": 3, "name": "Player3", "identifier": player3_uuid},
    ]
    mock_game_repo.get.return_value = mock_game
    non_exist_player_uuid = uuid4()
    id = 1
    response = client.delete(
        f"/api/lobby/{id}", json={"identifier": non_exist_player_uuid}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "El jugador no existe"}


# Test cuando la partida no existe
def test_exit_game_no_game(mock_game_repo):
    mock_game_repo.get.return_value = None  # La partida no existe

    player_uuid = uuid4()
    response = client.delete(f"/api/lobby/1", json={"identifier": str(player_uuid)})

    # Aserciones
    assert response.status_code == 404
    assert response.json() == {"detail": "Partida no encontrada"}

"""

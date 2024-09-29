from fastapi.testclient import TestClient
import pytest
from uuid import UUID, uuid4
from unittest.mock import Mock

import asserts

from main import app, get_games_repo

client = TestClient(app)


def test_borrame():
    response = client.get("/api/borrame")
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(response.json(), {"games": []})


"""
# crear un jugador
def create_player(name: str):
    response = client.post("/api/player", json={"name": name})
    assert response.status_code == 200
    return response.json()

# crear un juego
def create_game(name: str, min_players: int, max_players: int):
    response = client.post("/api/lobby", json={"name": name, "min_players": min_players, "max_players": max_players})
    assert response.status_code == 200
    return response.json()

# unirse a un juego
def join_game(game_id: int, player_identifier: str): #ver que onda con esto
    response = client.put(f"/api/lobby/{game_id}", json={"id_game": game_id, "identifier_player": player_identifier})
    assert response.status_code == 200
    return response.json()

# salir de un juego
def exit_game(game_id: int, player_identifier: str):
    response = client.delete(f"/api/lobby/{game_id}", json={"id_game": game_id, "identifier_player": player_identifier})
    assert response.status_code == 200
    return response.json()

"""


# simulo el game repository
def mock_game_repo():
    mock = Mock()
    app.dependency_overrides[get_games_repo] = lambda: mock
    return mock


# test para cuando el jugador no esta en la partida
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
        "/api/lobby/1", json={"game_id": 1, "identifier": str(player2_uuid)}
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
    response = client.delete(
        "/api/lobby/1", json={"game_id": 1, "identifier": non_exist_player_uuid}
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

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import asserts
from main import app

client = TestClient(app)


@pytest.fixture
def player_a():
    return {"id": 1, "name": "Alice"}


@pytest.fixture
def game_pos():
    return {
        "id": 1,
        "name": "partida",
        "max_players": 2,
        "min_players": 2,
        "started": False,
        "players": [{"id": 0, "name": "Owner"}, {"id": 1, "name": "Alice"}],
    }


@pytest.fixture
def game_pre():
    return {
        "id": 1,
        "name": "partida",
        "max_players": 2,
        "min_players": 2,
        "started": False,
        "players": [{"id": 0, "name": "Owner"}],
    }


@patch("main.GameRepository")
@patch("main.PlayerRepository")
def test_post_new_player(
    mock_GameRepository, mock_PlayerRepository, game_pre, game_pos, player_a
):
    mock_GameRepository.get.return_value = game_pre
    mock_PlayerRepository.get.return_value = player_a

    response = client.post("/api/lobby/1", json={"id_game": 1, "id_player": 1})

    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(response.json, game_pos)

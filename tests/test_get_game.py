from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

from main import app
from model import Game, Player

client = TestClient(app)


data_out = Game(
    id=1,
    name="Game of Thrones",
    current_player_turn=0,
    max_players=4,
    min_players=2,
    started=False,
    players=[Player(id=1, name="Player 1"), Player(id=2, name="Player 2")]
)

def test_get_game():
    with patch("repositories.game.GameRepository.get") as mock_get:
        mock_get.return_value = data_out
        response = client.get("/api/lobby/1")
        assert response.status_code == 200
        assert response.json() == {
            "name": "Game of Thrones",
            "current_players": 2,
            "max_players": 4,
            "min_players": 2,
            "is_started": False,
            "turn": 0
        }

def test_get_game_not_found():
    with patch("repositories.game.GameRepository.get") as mock_get:
        mock_get.return_value = None
        response = client.get("/api/lobby/1")
        assert response.status_code == 404
        assert response.json() == {"detail": "Lobby not found"}
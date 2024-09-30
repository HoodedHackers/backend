from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from model import Game, Player

client = TestClient(app)

data_out1 = Game(
    id=1000,
    name="Game of Falls",
    current_player_turn=0,
    max_players=4,
    min_players=2,
    started=False,
    players=[Player(id=10000, name="Lou")],

    host_id=1,
)

data_out2 = Game(
    id=2000,
    name="Game of Thrones",
    current_player_turn=0,
    max_players=4,
    min_players=2,
    started=False,
    players=[Player(id=20000, name="Lou^2"),
            Player(id=30000, name="Andy")],
    host_id=2,
)

def test_start_game_error_404():
    with patch("repositories.game.GameRepository.get") as mock_get:
        mock_get.return_value = None

        response = client.put("/api/lobby/0/start")
        assert response.status_code == 404
        assert response.json() == {"detail": "Game dont found"}

def test_start_game_error_412():
    with patch("repositories.game.GameRepository.get") as mock_get:
        mock_get.return_value = data_out1

        response = client.put("/api/lobby/1/start")
        assert response.status_code == 412
        assert response.json() == {"detail": "Doesnt meet the minimum number of players"}

def test_start_game_success():
    with patch("repositories.game.GameRepository.get") as mock_get:
        mock_get.return_value = data_out2

        response = client.put("/api/lobby/2/start")
        assert response.status_code == 200
        assert response.json() == {"status": "success!"}
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest
from uuid import uuid4
from main import app, GameIn
from model import Game, Player

client = TestClient(app)


data_out = []
data_out.append(Game(
    id=1,
    name="Game of Thrones",
    current_player_turn=0,
    max_players=4,
    min_players=2,
    started=False,
    players=[Player(id=1, name="Matias"), Player(id=2, name="Camilo")],
    )
)


def test_update_list():
    
    with patch("repositories.game.GameRepository.get_available") as mock_get:
        mock_get.return_value = data_out

        previous_lobbies = client.get("/api/lobby")
        assert previous_lobbies.status_code == 200
        assert previous_lobbies.json() == [
            {
                "name": "Game of Thrones",
                "current_players": 2,
                "max_players": 4,
                "min_players": 2,
                "started": False,
                "turn": 0,
                "players": ["Matias", "Camilo"],
            }
        ]
            
        with client.websocket_connect("/ws/api/lobby") as websocket:
            
            client.post("/api/lobby", json={
                "identifier": uuid4(),
                "name": "Super Mario",
                "max_players": 4,
                "min_players": 2
            })

            result = websocket.receive_json()
            assert result == {"message": "update"}
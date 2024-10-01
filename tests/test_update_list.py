from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest
from main import app
from model import Game, Player
import asyncio

client = TestClient(app)


mock_game_side_effect = [
    [
        Game(
            id=1,
            name="Game of Thrones",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[Player(id=1, name="Matias"), Player(id=2, name="Camilo")],
        )
    ],
    [
        Game(
            id=2,
            name="Super Mario",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[],
        )
    ],
    [
        Game(
            id=3,
            name="Super Mario 2.0",
            current_player_turn=1,
            max_players=4,
            min_players=2,
            started=False,
            players=[Player(id=3, name="Javier")],
        )
    ],
]


@pytest.mark.asyncio
async def test_update_list():

    with patch("repositories.game.GameRepository.get_available") as mock_get:
        mock_get.side_effect = mock_game_side_effect

        with client.websocket_connect("/ws/api/lobby") as websocket:

            await asyncio.sleep(1)

            assert websocket.receive_json() == {"message": "update"}

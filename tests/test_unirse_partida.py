import pytest
from fastapi.testclient import TestClient
import asserts
from main import app

client = TestClient(app)

@pytest.fixture
def game_pos():
    return {
        "id": 1,
        "name": "Game of Thrones",
        "max_players": 2,
        "min_players": 2,
        "started": False,
        "players": [{"id": 1, "name": "Alice",  "identifier": "sdsda"}],
    }


def test_post_new_player(game_pos):
    
    response = client.put("/api/lobby/1", json={"id_game": 1, "identifier_player": "sdsda"})
    
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(response.json, game_pos)

from uuid import UUID

import asserts
from fastapi.testclient import TestClient

from main import app, game_repo, player_repo
from model import Game, Player

client = TestClient(app)

def test_deal_mov():
    value1 = UUID("0123456789abcdef0123456789abcdef")
    p1 = Player(name="Alice", identifier=value1)
    player_repo.save(p1)
    g = Game(name="test deal")
    g.set_defaults()
    game_repo.save(g)
    g.add_player(p1)
    
    response = client.post(
        "/api/partida/en_curso/movimiento",
        json={
            "game_id": 1,
            "players": "0123456789abcdef0123456789abcdef",
        },
    )
    count = len(response.json())
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(count, 3)
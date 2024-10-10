from uuid import UUID

import asserts
from fastapi.testclient import TestClient

from main import app, card_repo, create_all_figs, game_repo, player_repo
from model import Game, Player

client = TestClient(app)


def test_deal():
    create_all_figs(card_repo)
    value1 = UUID("0123456789abcdef0123456789abcdef")
    p1 = Player(name="Alice", identifier=value1)
    player_repo.save(p1)
    g = Game(name="test game")
    g.set_defaults()
    game_repo.save(g)
    g.add_player(p1)
    response = client.post(
        "/api/partida/en_curso",
        json={
            "game_id": 1,
            "players": "0123456789abcdef0123456789abcdef"
        },
    )
    asserts.assert_equal(response.status_code, 200)

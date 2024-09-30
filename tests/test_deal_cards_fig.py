from fastapi.testclient import TestClient
import asserts
from model import Game, Player
from uuid import UUID
from main import app, player_repo, game_repo, card_repo, create_all_figs

client = TestClient(app)


def test_deal():
    create_all_figs(card_repo)
    value1 = UUID("0123456789abcdef0123456789abcdef")
    value2 = UUID("1167dc19fb854db8b0e02c03986caa3b")
    p1 = Player(name="Alice", identifier=value1)
    p2 = Player(name="Alice", identifier=value2)
    player_repo.save(p1)
    player_repo.save(p2)
    g = Game(name="test game")
    g.set_defaults()
    game_repo.save(g)
    g.add_player(p1)
    g.add_player(p2)
    response = client.post(
        "/api/partida/en_curso",
        json={
            "game_id": 1,
            "players": [
                "0123456789abcdef0123456789abcdef",
                "1167dc19fb854db8b0e02c03986caa3b",
            ],
        },
    )
    asserts.assert_equal(response.status_code, 200)

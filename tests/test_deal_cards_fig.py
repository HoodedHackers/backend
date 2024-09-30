from fastapi.testclient import TestClient
import asserts
from model import Game, Player
from uuid import UUID
from main import app, player_repo, game_repo, card_repo
from create_cards import create_all_figs

client = TestClient(app)


def test_deal():
    create_all_figs(card_repo)
    response = client.post(
        "/api/partida/en_curso",
        json={"game_id": 2, "players": ["algo", "algo1", "algo2"]},
    )
    asserts.assert_equal(response.status_code, 200)

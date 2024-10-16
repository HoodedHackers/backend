from uuid import UUID

import asserts
from fastapi.testclient import TestClient

from main import app, card_repo, create_all_figs, game_repo, player_repo
from model import Game, Player

client = TestClient(app)


<<<<<<< HEAD
# def test_deal():
#     create_all_figs(card_repo)
#     value1 = UUID("0123456789abcdef0123456789abcdef")
#     value2 = UUID("1167dc19fb854db8b0e02c03986caa3b")
#     p1 = Player(name="Alice", identifier=value1)
#     p2 = Player(name="Alice", identifier=value2)
#     player_repo.save(p1)
#     player_repo.save(p2)
#     g = Game(name="test game")
#     g.set_defaults()
#     game_repo.save(g)
#     g.add_player(p1)
#     g.add_player(p2)
#     response = client.post(
#         "/api/partida/en_curso",
#         json={
#             "game_id": 1,
#             "players": [
#                 "0123456789abcdef0123456789abcdef",
#                 "1167dc19fb854db8b0e02c03986caa3b",
#             ],
#         },
#     )
#     asserts.assert_equal(response.status_code, 200)
=======
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
        json={"game_id": 1, "players": "0123456789abcdef0123456789abcdef"},
    )
    asserts.assert_equal(response.status_code, 200)
>>>>>>> origin/SWC-40_Crear_carta_figura

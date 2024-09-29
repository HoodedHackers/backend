import unittest
from fastapi.testclient import TestClient
import asserts
from model import Game, Player
from uuid import UUID
from main import app, player_repo, game_repo

client = TestClient(app)


def test_add_game_seccess():
    value = UUID("0123456789abcdef0123456789abcdef")
    p = Player(name="Alice", identifier=value)
    player_repo.save(p)
    g = Game(name="test game")
    g.set_defaults()
    game_repo.save(g)
    response = client.put(
        "/api/lobby/1",
        json={"id_game": 1, "identifier_player": "0123456789abcdef0123456789abcdef"},
    )
    asserts.assert_equal(response.status_code, 200)


def test_add_game_none_player():
    response = client.put(
        "/api/lobby/1",
        json={"id_game": 1, "identifier_player": "0123456789abcdef0123456789abcde5"},
    )
    asserts.assert_equal(response.status_code, 404)


def test_add_game_none_game():
    response = client.put(
        "/api/lobby/1",
        json={"id_game": 15, "identifier_player": "0123456789abcdef0123456789abcdef"},
    )
    asserts.assert_equal(response.status_code, 404)

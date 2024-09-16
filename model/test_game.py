from game import Game, GameFull
from player import Player

from asserts import assert_raises, assert_equal


def test_add_player():
    g = Game(id=0, name="test game")
    g.add_player(Player(name="pepe"))


def test_game_full():
    g = Game(id=0, name="test game", max_players=2)
    with assert_raises(GameFull):
        g.add_player(Player(name="0"))
        g.add_player(Player(name="1"))
        g.add_player(Player(name="2"))


def test_advance_turm():
    g = Game(id=0, name="test game")
    g.add_player(Player(name="0"))
    g.add_player(Player(name="1"))
    assert_equal(g.current_player, 0)
    g.advance_player()
    assert_equal(g.current_player, 1)
    g.advance_player()
    assert_equal(g.current_player, 0)

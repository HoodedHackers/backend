from .game import Game
from .exceptions import GameFull, PreconditionNotMet
from .player import Player

from asserts import assert_raises, assert_equal


def test_add_player():
    g = Game(id=0, name="test game")
    g.add_player(Player(name="pepe"))


def test_game_full():
    g = Game(name="test game", max_players=2)
    g.set_defaults()
    with assert_raises(GameFull):
        g.add_player(Player(name="0"))
        g.add_player(Player(name="1"))
        g.add_player(Player(name="2"))


def test_advance_turm():
    g = Game(name="test game")
    g.set_defaults()
    g.add_player(Player(name="0"))
    g.add_player(Player(name="1"))
    print(g)
    assert_equal(g.current_player_turn, 0)
    g.advance_player()
    assert_equal(g.current_player_turn, 1)
    g.advance_player()
    assert_equal(g.current_player_turn, 0)


def test_game_has_tiles():
    g = Game(name="test game")
    g.set_defaults()
    assert len(g.board) == 36


def test_advance_turn():
    g = Game(name="test game")
    g.set_defaults()
    p0, p1 = Player(name="0"), Player(name="1")
    g.add_player(p0)
    g.add_player(p1)
    g.started = True
    current_player = g.current_player()
    assert p0 == current_player
    g.advance_turn()
    current_player = g.current_player()
    assert p1 == current_player
    g.advance_turn()
    current_player = g.current_player()
    assert p0 == current_player


def test_current_player_without_players():
    g = Game(name="test game")
    g.set_defaults()
    current_player = g.current_player()
    assert current_player is None


def test_advance_not_started():
    g = Game(name="test game")
    g.set_defaults()
    with assert_raises(PreconditionNotMet):
        g.advance_turn()

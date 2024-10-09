import random
from unittest.mock import patch

from asserts import assert_equal, assert_raises

from .exceptions import PreconditionsNotMet
from .game import Game, GameFull
from .player import Player


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


def test_delete_player():
    g = Game(name="test game")
    g.set_defaults()
    p = Player(name="0")
    g.add_player(p)
    assert p in g.players
    g.delete_player(p)
    assert p not in g.players

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
    with assert_raises(PreconditionsNotMet):
        g.advance_turn()


def test_game_player_info():
    g = Game(name="test game")
    g.set_defaults()
    assert len(g.player_info) == 0
    g.add_player(Player(name="player 1"))
    assert len(g.player_info) == 1


def test_shuffle_players():
    players = [Player(name=f"player {n}", id=n) for n in range(4)]
    g = Game(name="test game", players=players)

    with patch("random.shuffle", side_effect=lambda x: random.Random(42).shuffle(x)):
        g.shuffle_players()

    ordered_players = g.ordered_players()
    assert len(ordered_players) == len(players)
    assert set(ordered_players) == set(players)
    assert ordered_players[0] != players[0]


def test_removing_player_changes_turn_order():
    players = [Player(name=f"player {n}", id=n) for n in range(4)]
    g = Game(name="test game", players=players)
    g.delete_player(players[0])
    assert max(player.turn_position for player in g.player_info.values()) == 2

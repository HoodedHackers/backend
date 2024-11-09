import random
from unittest.mock import patch

from asserts import assert_equal, assert_raises

from .exceptions import PreconditionsNotMet
from .game import Game, GameFull
from .mov_cards import TOTAL_MOV
from .player import Player
from .board import Color
from .figure_search import Figure, CandidateShape
from unittest.mock import MagicMock, patch

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


def test_hand_mov():
    players = [Player(name=f"player {n}", id=n) for n in range(4)]
    list = [1, 2, 3]
    g = Game(name="test game", players=players)
    g.set_defaults()
    total = len(g.all_movs)
    assert total == TOTAL_MOV
    g.add_hand_mov(list, list, g.players[0].id)
    hand = g.player_info[0].hand_mov
    assert len(g.all_movs) == TOTAL_MOV - 3
    assert len(hand) == 3


def test_get_player_figures():
    g = Game(name="test game")
    g.set_defaults()
    p0, p1 = Player(name="0", id=1), Player(name="1", id=2)
    g.add_player(p0)
    g.add_player(p1)

    g.distribute_deck()
    figure = g.get_player_figures(p0.id)
    assert len(figure) == 25
    assert g.get_player_figures(p1.id) != []


def test_get_player_hand_figure():
    g = Game(name="test game")
    p0, p1 = Player(name="0", id=1), Player(name="1", id=2)
    g.add_player(p0)
    g.add_player(p1)
    g.distribute_deck()
    g.player_info[p0.id].hand_fig = [1, 2, 3]

    hand_figure = g.get_player_hand_figures(p0.id)
    assert len(hand_figure) == 3
    assert g.get_player_figures(p0.id) != []
    assert g.get_player_hand_figures(p0.id) == [1, 2, 3]


def test_add_random_card():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    p1 = Player(name="Player 1", id=2)
    p2 = Player(name="Player 2", id=3)
    g.add_player(p0)
    g.add_player(p1)
    g.add_player(p2)
    g.distribute_deck()

    g.player_info[p0.id].hand_fig = [1]

    hand_fig = g.add_random_card(p0.id)
    assert len(hand_fig) == 3
    print(hand_fig)
    print(g.player_info[p0.id].fig)
    assert len(g.player_info[p0.id].fig) == 14


def test_add_random_card2():
    g = Game(name="test game")
    g.set_defaults()
    p0 = Player(name="Player 0", id=1)
    g.add_player(p0)

    g.player_info[p0.id].fig = [1, 2, 3, 4, 5, 6]
    g.player_info[p0.id].hand_fig = [1]

    hand_fig = g.add_random_card(p0.id)
    assert len(hand_fig) == 3
    assert len(g.player_info[p0.id].fig) == 4


def test_add_random_card_with_non_figs():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    g.add_player(p0)

    g.player_info[p0.id].fig = []
    g.player_info[p0.id].hand_fig = [1]

    hand_fig = g.add_random_card(p0.id)
    print(hand_fig)
    assert len(hand_fig) == 1
    assert len(g.player_info[p0.id].fig) == 0


def test_add_random_card_with_non_figs2():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    g.add_player(p0)

    g.player_info[p0.id].fig = [5, 4, 6, 7, 8, 9]
    g.player_info[p0.id].hand_fig = [1, 2, 3]

    hand_fig = g.add_random_card(p0.id)
    print(hand_fig)
    assert len(hand_fig) == 3
    assert len(g.player_info[p0.id].fig) == 6


def test_get_player_hand_movs():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    g.add_player(p0)
    g.player_info[p0.id].hand_mov = [1, 2, 3]
    hand_mov = g.get_player_hand_movs(p0.id)
    assert len(hand_mov) == 3
    assert hand_mov == [1, 2, 3]


def test_discard_card_hand_figures():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    g.add_player(p0)
    g.player_info[p0.id].hand_fig = [1, 2, 3]
    g.discard_card_hand_figures(p0.id, 2)
    assert len(g.player_info[p0.id].hand_fig) == 2
    assert g.player_info[p0.id].hand_fig == [1, 3]


def test_discard_card_hand_figures_empty():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    g.add_player(p0)
    g.player_info[p0.id].hand_fig = []
    g.discard_card_hand_figures(p0.id, 2)
    assert len(g.player_info[p0.id].hand_fig) == 0


def test_discard_card_hand_figures2():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    g.add_player(p0)
    g.player_info[p0.id].hand_fig = [1, 2, 3]
    g.discard_card_hand_figures(p0.id, 4)
    assert len(g.player_info[p0.id].hand_fig) == 3
    assert g.player_info[p0.id].hand_fig == [1, 2, 3]


def test_get_player_in_game():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    p1 = Player(name="Player 1", id=2)
    g.add_player(p0)
    g.add_player(p1)
    assert g.get_player_in_game(0) == p0


def test_distribute_deck():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    p1 = Player(name="Player 1", id=2)
    g.add_player(p0)
    g.add_player(p1)
    g.add_player(Player(name="Player 2", id=3))
    g.distribute_deck()
    assert len(g.player_info[p0.id].fig) == 16
    assert len(g.player_info[p1.id].fig) == 16
    assert len(g.player_info[3].fig) == 16

def test_ids_get_possible_figures():
    g = Game(name="test game")
    p0 = Player(name="Player 0", id=1)
    g.add_player(p0)

    f = Figure(1, [(0, 0), (0, 1), (0, 2), (0, 3)])
    r = Color.RED
    fa = Figure(2, [(3, 1), (0, 1), (0, 2), (0, 3)])
    fav = Color.GREEN
    fb = Figure(3, [(0, 4), (0, 1), (0, 2), (0, 3)])
    fcb = Color.BLUE
    a = CandidateShape(f, (0, 0), r)
    b = CandidateShape(fa, (0, 1), fav)
    c = CandidateShape(fb, (0, 2), fcb)
    g.get_possible_figures = MagicMock(return_value=[a, b, c])

    g.player_info[1].hand_fig = [1, 2, 3]

    result = g.ids_get_possible_figures(1)
    assert result == [1, 2, 3]
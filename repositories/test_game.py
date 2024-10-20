import unittest

import asserts
from apscheduler.triggers.base import random

from database import Database
from model import Game, Player
from repositories import GameRepository, PlayerRepository


def make_game(
    player_repo, name=None, max_players=None, min_players=None, started=None, players=[]
):
    host = Player(name="host")
    for player in players:
        player_repo.save(player)
    player_repo.save(host)
    game = Game(
        name=name,
        max_players=max_players,
        min_players=min_players,
        host=host,
        host_id=host.id,
        started=started,
        players=players,
    )
    return game


class TestGameRepo(unittest.TestCase):

    def repo(self):
        dbs = Database().session()
        return GameRepository(dbs), PlayerRepository(dbs)

    def test_add_game(self):
        repo, prepo = self.repo()
        games = [make_game(prepo, name=f"game {n}") for n in range(10)]
        for game in games:
            game.set_defaults()
            repo.save(game)
        saved_games = repo.get_many(10)
        for game in games:
            asserts.assert_in(game, saved_games)

    def test_delete_game(self):
        repo, prepo = self.repo()
        g = make_game(prepo, name="deleteme")
        repo.save(g)
        g = repo.get(1)
        asserts.assert_is_not_none(g)
        assert g is not None  # Para pyright ugh
        repo.delete(g)
        asserts.assert_is_none(repo.get(1))

    def test_get_available_games(self):
        repo, prepo = self.repo()
        games = [
            make_game(
                prepo,
                name="game1",
                started=False,
                players=[Player(name=f"{n}") for n in range(2)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game2",
                started=False,
                players=[Player(name=f"{n}") for n in range(4)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game3",
                started=True,
                players=[Player(name=f"{n}") for n in range(2)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game4",
                started=False,
                players=[Player(name=f"{n}") for n in range(1)],
                max_players=2,
            ),
        ]
        for game in games:
            game.set_defaults()
            repo.save(game)

        available_games = repo.get_available(4)
        asserts.assert_in(games[0], available_games)
        asserts.assert_in(games[3], available_games)
        asserts.assert_not_in(games[1], available_games)
        asserts.assert_not_in(games[2], available_games)

    def test_get_available_games_name(self):
        repo, prepo = self.repo()
        games = [
            make_game(
                prepo,
                name="game1",
                started=False,
                players=[Player(name=f"{n}") for n in range(2)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game2",
                started=False,
                players=[Player(name=f"{n}") for n in range(4)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game3",
                started=True,
                players=[Player(name=f"{n}") for n in range(2)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game4",
                started=False,
                players=[Player(name=f"{n}") for n in range(1)],
                max_players=2,
            ),
        ]
        for game in games:
            game.set_defaults()
            repo.save(game)

        available_games = repo.get_available(name="me4")
        asserts.assert_in(games[3], available_games)

    def test_get_available_games_max_players(self):
        repo, prepo = self.repo()
        games = [
            make_game(
                prepo,
                name="game1",
                started=False,
                players=[Player(name=f"{n}") for n in range(2)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game2",
                started=False,
                players=[Player(name=f"{n}") for n in range(4)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game3",
                started=True,
                players=[Player(name=f"{n}") for n in range(2)],
                max_players=4,
            ),
            make_game(
                prepo,
                name="game4",
                started=False,
                players=[Player(name=f"{n}") for n in range(1)],
                max_players=2,
            ),
        ]
        for game in games:
            game.set_defaults()
            repo.save(game)

        available_games = repo.get_available(max_players=1)
        asserts.assert_in(games[3], available_games)

    def test_turn_order(self):
        grepo, prepo = self.repo()
        players = [
            Player(name="p1"),
            Player(name="p2"),
            Player(name="p3"),
            Player(name="p4"),
        ]
        for p in players:
            prepo.save(p)
        g = make_game(grepo, name="test_game", players=players)
        grepo.save(g)
        saved_game = grepo.get(g.id)
        assert saved_game is not None
        self.assertEqual(players, saved_game.ordered_players())

    def test_player_info(self):
        grepo, prepo = self.repo()
        players = [
            Player(name="p1"),
            Player(name="p2"),
            Player(name="p3"),
        ]
        for p in players:
            prepo.save(p)
        g = make_game(grepo, name="test_game", players=players[0:2])
        grepo.save(g)
        saved_game = grepo.get(g.id)
        assert saved_game is not None
        assert len(saved_game.player_info) == 2
        saved_game.add_player(players[2])
        grepo.save(saved_game)
        saved_game = grepo.get(g.id)
        assert saved_game is not None
        assert len(saved_game.player_info) == 3

import unittest

import asserts

from model import Game, Player
from repositories import GameRepository
from database import Database


class TestGameRepo(unittest.TestCase):

    def repo(self):
        return GameRepository(Database().session())

    def test_add_game(self):
        repo = self.repo()
        games = [Game(name=f"game {n}") for n in range(10)]
        for game in games:
            game.set_defaults()
            repo.save(game)
        saved_games = repo.get_many(10)
        for game in games:
            asserts.assert_in(game, saved_games)

    def test_delete_game(self):
        repo = self.repo()
        g = Game(name="deleteme")
        repo.save(g)
        g = repo.get(1)
        asserts.assert_is_not_none(g)
        assert g is not None  # Para pyright ugh
        repo.delete(g)
        asserts.assert_is_none(repo.get(1))

    def test_get_available_games(self):
        repo = self.repo()
        games = [
            Game(
                name="game1",
                started=False,
                players=[Player(name=f"{n}") for n in range(2)],
                max_players=4,
            ),
            Game(
                name="game2",
                started=False,
                players=[Player(name=f"{n}") for n in range(4)],
                max_players=4,
            ),
            Game(
                name="game3",
                started=True,
                players=[Player(name=f"{n}") for n in range(2)],
                max_players=4,
            ),
            Game(
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

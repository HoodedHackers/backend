import unittest

import asserts

from model.game import Game
from repositories import GameRepository
from database import Database


def get_db():
    db = Database()
    db.create_tables()
    return db


class TestGameRepo(unittest.TestCase):

    def repo(self):
        return GameRepository(get_db().session())

    def test_add_game(self):
        repo = self.repo()
        games = [Game(name=f"game {n}") for n in range(10)]
        for game in games:
            game.set_defaults()
            repo.save(game)
        repo.flush()
        saved_games = repo.get_many(10)
        for game in games:
            asserts.assert_in(game, saved_games)

    def test_delete_game(self):
        repo = self.repo()
        g = Game(name="deleteme")
        repo.save(g)
        repo.flush()
        g = repo.get(1)
        asserts.assert_is_not_none(g)
        assert g is not None  # Para pyright ugh
        repo.delete(g)
        repo.flush()
        asserts.assert_is_none(repo.get(1))

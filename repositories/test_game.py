import unittest

import asserts

from model import Game, Player
from repositories import GameRepository
from repositories import PlayerRepository
from database import Database


def make_game(
    player_repo, name=None, max_players=None, min_players=None, started=None, players=[]
):
    host = Player(name="host")
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

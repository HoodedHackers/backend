import unittest

import asserts

from model import Player
from repositories import PlayerRepository
from database import Database


class TestGameRepo(unittest.TestCase):
    def repo(self):
        return PlayerRepository(Database().session())

    def test_new_player(self):
        repo = self.repo()
        p = Player(name="Alice", identifier="sdsda")
        repo.save(p)
        self.assertIsNotNone(p.identifier)
        saved_player = repo.get(p.identifier)
        assert saved_player is not None
        self.assertEqual(p.name, saved_player.name)

    def test_delete_player(self):
        repo = self.repo()
        players = [
            Player(name="Alice", identifier="sdfda"),
            Player(name="Bob", identifier="sdgda"),
            Player(name="Carl", identifier="sdhda"),
        ]
        for p in players:
            repo.save(p)
        alice = players[0]
        repo.delete(alice)
        saved_player = repo.get(alice.identifier)
        self.assertIsNone(saved_player)

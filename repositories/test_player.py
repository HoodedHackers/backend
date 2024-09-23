import unittest
from uuid import uuid4

import asserts

from model import Player
from repositories import PlayerRepository
from database import Database


def make_player(name: str) -> Player:
    return Player(name=name, identifier=uuid4())


class TestGameRepo(unittest.TestCase):
    def repo(self):
        return PlayerRepository(Database().session())

    def test_new_player(self):
        repo = self.repo()
        p = make_player("Alice")
        repo.save(p)
        self.assertIsNotNone(p.id)
        saved_player = repo.get(p.id)
        assert saved_player is not None
        self.assertEqual(p.name, saved_player.name)

    def test_delete_player(self):
        repo = self.repo()
        players = [make_player("Alice"), make_player("Bob"), make_player("Carl")]
        for p in players:
            repo.save(p)
        alice = players[0]
        repo.delete(alice)
        saved_player = repo.get(alice.id)
        self.assertIsNone(saved_player)

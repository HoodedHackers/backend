import unittest
from uuid import uuid4

import asserts

from database import Database
from model import Player
from repositories import PlayerRepository


class TestPlayerRepo(unittest.TestCase):
    def repo(self):
        return PlayerRepository(Database().session())

    def test_new_player(self):
        repo = self.repo()
        identifier = uuid4()
        p = Player(name="Alice", identifier=identifier)
        repo.save(p)
        self.assertIsNotNone(p.id)
        saved_player = repo.get(p.id)
        assert saved_player is not None
        self.assertEqual(p.name, saved_player.name)

    def test_delete_player(self):
        repo = self.repo()
        identifier_1 = uuid4()
        identifier_2 = uuid4()
        players = [
            Player(name="Alice", identifier=identifier_1),
            Player(name="Bob", identifier=identifier_2),
        ]
        for p in players:
            repo.save(p)
        alice = players[0]
        repo.delete(alice)
        saved_player = repo.get(alice.id)
        self.assertIsNone(saved_player)

    def test_get_player_by_identifier(self):
        repo = self.repo()
        identifier = uuid4()
        p = Player(name="Alice", identifier=identifier)
        repo.save(p)
        saved_p = repo.get_by_identifier(identifier)
        self.assertEqual(p, saved_p)

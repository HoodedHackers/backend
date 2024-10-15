"""
import unittest
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, Player
from repositories import GameRepository, PlayerRepository


class TestNotifyLobby(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.dbs = Database().session()
        self.games_repo = GameRepository(self.dbs)
        self.player_repo = PlayerRepository(self.dbs)

        self.host = Player(name="Ely")
        self.player_repo.save(self.host)

        self.players = [
            Player(name="Lou"),
            Player(name="Lou^2"),
            Player(name="Andy"),
        ]
        for p in self.players:
            self.player_repo.save(p)

        self.game_1 = Game(
            id=1,
            name="Game of Falls",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[],
            host=self.host,
            host_id=self.host.id,
        )

        self.games_repo.save(self.game_1)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_connect_from_lobby(self):

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            

            self.game_1.add_player(self.players[0])
            self.game_1.add_player(self.players[1])
            self.game_1.started = True

            with self.client.websocket_connect(f"/ws/lobby/1?player_id={self.game_1.players[0].id}") as websocket0:

                # uno se va
                self.client.patch("/api/lobby/1", json={"player_id": self.game_1.players[0].id})

                # deveriamos escuchar un mensaje de que ganamos
                data=websocket0.receive_json()
                assert data == {"action": "Hay un ganador"}

"""

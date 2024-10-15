import unittest
from os import name
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, Player
from repositories import GameRepository, PlayerRepository

client = TestClient(app)


class TestGameStart(unittest.TestCase):

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
            name="Game of Falls",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[self.players[0]],
            host=self.host,
            host_id=self.host.id,
        )

        self.game_2 = Game(
            name="Game of Thrones",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=self.players[1:3],
            host=self.host,
            host_id=self.host.id,
        )

        self.games_repo.save(self.game_1)
        self.games_repo.save(self.game_2)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_start_game_bad_game_id(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.put(
                "/api/lobby/8975/start",
                json={"identifier": "00000000-0000-0000-0000-000000000000"},
            )
            assert response.status_code == 404
            assert response.json() == {"detail": "Game dont found"}

    def test_start_game_without_enough_players(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.put(
                f"/api/lobby/{self.game_1.id}/start",
                json={"identifier": str(self.host.identifier)},
            )
            assert response.status_code == 400
            assert response.json() == {
                "detail": "Doesnt meet the minimum number of players"
            }

    def test_start_game_success(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.put(
                f"/api/lobby/{self.game_2.id}/start",
                json={"identifier": str(self.host.identifier)},
            )
            print(response.json())
            assert response.status_code == 200
            assert response.json() == {"status": "success!"}

    def test_start_game_message(self):
        player = self.players[1]
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), self.client.websocket_connect(
            f"/ws/lobby/{self.game_2.id}/status?player_id={player.id}"
        ) as ws:
            response = self.client.put(
                f"/api/lobby/{self.game_2.id}/start",
                json={"identifier": str(self.host.identifier)},
            )
            self.assertEqual(response.status_code, 200)
            msg = ws.receive_json()
            self.assertIn("status", msg)
            self.assertEqual(msg["status"], "started")

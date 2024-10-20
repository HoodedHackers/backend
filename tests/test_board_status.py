import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, Player
from repositories import GameRepository, PlayerRepository

client = TestClient(app)


class TestBoardStatus(unittest.TestCase):

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

    def test_board_status_invalid_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), self.client.websocket_connect(
            f"/ws/lobby/9999/board?player_id={self.players[0].id}"
        ) as ws:
            ws.send_json({"request": "status"})
            msg = ws.receive_json()
            self.assertIn("error", msg)
            self.assertEqual(msg["error"], "invalid game id")

    def test_board_status_invalid_request(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), self.client.websocket_connect(
            f"/ws/lobby/{self.game_1.id}/board?player_id={self.players[0].id}"
        ) as ws:
            ws.send_json({"request": "invalid"})
            msg = ws.receive_json()
            self.assertIn("error", msg)
            self.assertEqual(msg["error"], "invalid request")

    def test_board_status_valid_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), self.client.websocket_connect(
            f"/ws/lobby/{self.game_1.id}/board?player_id={self.players[0].id}"
        ) as ws:
            ws.send_json({"request": "status"})
            msg = ws.receive_json()
            self.assertIn("game_id", msg)
            self.assertIn("board", msg)
            self.assertEqual(msg["game_id"], self.game_1.id)
            self.assertEqual(msg["board"], [tile.value for tile in self.game_1.board])

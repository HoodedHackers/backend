import random
import unittest
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, History, Player
from repositories import GameRepository, HistoryRepository, PlayerRepository


class TestPlayCard(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.dbs = Database().session()
        self.games_repo = GameRepository(self.dbs)
        self.player_repo = PlayerRepository(self.dbs)
        self.history_repo = HistoryRepository(self.dbs)

        self.host = Player(name="Ely")
        self.player_repo.save(self.host)

        self.players = [
            Player(name="Lou"),
            Player(name="Lou^2"),
            Player(name="Andy"),
        ]
        for p in self.players:
            self.player_repo.save(p)

        self.game = Game(
            name="Game of Falls",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[],
            host=self.host,
            host_id=self.host.id,
        )

        self.games_repo.save(self.game)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.query(History).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_play(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.history_repo", self.history_repo):
            self.game.add_player(self.players[0])

            cards_mov = [1, 2, 3]
            self.game.add_hand_mov(cards_mov, cards_mov, self.players[0].id)

            status = self.client.post(
                f"/api/game/{self.game.id}/play_card",
                json={
                    "identifier": str(self.players[0].identifier),
                    "origin_tile": 0,
                    "dest_tile": 1,
                    "card_mov_id": 3,
                    "index_hand": 1,
                },
            )
            assert status.status_code == 200

            history = self.client.get(f"/api/history/{self.game.id}")
            assert history.status_code == 200
            assert history.json()[0]["origin_x"] == 0
            assert history.json()[0]["dest_x"] == 1
            assert history.json()[0]["fig_mov_id"] == 3

    def test_ws_board_play(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.history_repo", self.history_repo):

            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])

            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/board?player_id={self.game.players[0].id}"
            ) as websocket:
                with self.client.websocket_connect(
                    f"/ws/lobby/{self.game.id}/board?player_id={self.game.players[1].id}"
                ) as websocket2:

                    self.game.add_player(self.players[0])

                    cards_mov = [1, 2, 3]
                    self.game.add_hand_mov(cards_mov, cards_mov, self.players[0].id)

                    status = self.client.post(
                        f"/api/game/{self.game.id}/play_card",
                        json={
                            "identifier": str(self.players[0].identifier),
                            "origin_tile": 0,
                            "dest_tile": 1,
                            "card_mov_id": 3,
                            "index_hand": 1,
                        },
                    )
                    assert status.status_code == 200

                    board = [tile.value for tile in self.game.board]
                    rsp = websocket.receive_json()
                    assert rsp["game_id"] == self.game.id
                    assert rsp["board"] == board

                    rsp = websocket2.receive_json()
                    assert rsp["game_id"] == self.game.id
                    assert rsp["board"] == board

    def test_ws_hand_play(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.history_repo", self.history_repo):

            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])

            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/select?player_id={self.game.players[0].id}"
            ) as websocket:
                with self.client.websocket_connect(
                    f"/ws/lobby/{self.game.id}/select?player_id={self.game.players[1].id}"
                ) as websocket2:

                    self.game.add_player(self.players[0])

                    cards_mov = [1, 2, 3]
                    self.game.add_hand_mov(cards_mov, cards_mov, self.players[0].id)

                    status = self.client.post(
                        f"/api/game/{self.game.id}/play_card",
                        json={
                            "identifier": str(self.players[0].identifier),
                            "origin_tile": 0,
                            "dest_tile": 1,
                            "card_mov_id": 3,
                            "index_hand": 1,
                        },
                    )
                    assert status.status_code == 200
                    assert websocket.receive_json() == {
                        "action": "use_card",
                        "player_id": self.players[0].id,
                        "card_id": 3,
                        "index": 1,
                        "len": 1,
                    }
                    assert websocket2.receive_json() == {
                        "action": "use_card",
                        "player_id": self.players[0].id,
                        "card_id": 3,
                        "index": 1,
                        "len": 1,
                    }

    def test_play_invalid_move(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.history_repo", self.history_repo):
            self.game.add_player(self.players[0])

            cards_mov = [1, 2, 3]
            self.game.add_hand_mov(cards_mov, cards_mov, self.players[0].id)

            status = self.client.post(
                f"/api/game/{self.game.id}/play_card",
                json={
                    "identifier": str(self.players[0].identifier),
                    "origin_tile": 0,
                    "dest_tile": 0,
                    "card_mov_id": 3,
                    "index_hand": 1,
                },
            )
            assert status.status_code == 404
            assert status.json() == {"detail": "Invalid move"}

    def test_play_invalid_card(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.history_repo", self.history_repo):
            self.game.add_player(self.players[0])

            cards_mov = [1, 2, 3]
            self.game.add_hand_mov(cards_mov, cards_mov, self.players[0].id)

            status = self.client.post(
                f"/api/game/{self.game.id}/play_card",
                json={
                    "identifier": str(self.players[0].identifier),
                    "origin_tile": 0,
                    "dest_tile": 1,
                    "card_mov_id": 4,
                    "index_hand": 1,
                },
            )
            assert status.status_code == 404
            assert status.json() == {"detail": "Card not in hand"}
            history = self.client.get(f"/api/history/{self.game.id}")
            assert history.status_code == 200
            assert history.json() == []

    def test_play_invalid_player(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.history_repo", self.history_repo):
            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])

            cards_mov = [1, 2, 3]
            self.game.add_hand_mov(cards_mov, cards_mov, self.players[0].id)

            status = self.client.post(
                f"/api/game/{self.game.id}/play_card",
                json={
                    "identifier": str(self.players[2].identifier),
                    "origin_tile": 0,
                    "dest_tile": 1,
                    "card_mov_id": 3,
                    "index_hand": 1,
                },
            )
            assert status.status_code == 404
            assert status.json() == {"detail": "Player not in game"}

            status = self.client.post(
                f"/api/game/{self.game.id}/play_card",
                json={
                    "identifier": str(self.players[1].identifier),
                    "origin_tile": 0,
                    "dest_tile": 1,
                    "card_mov_id": 3,
                    "index_hand": 1,
                },
            )
            assert status.status_code == 401
            assert status.json() == {"detail": "It's not your turn"}

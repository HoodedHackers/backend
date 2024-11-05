import random
import unittest
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, History, Player, board
from repositories import GameRepository, HistoryRepository, PlayerRepository


class TestPlayCardAndUndoMove(unittest.TestCase):

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

        rng = random.Random(413)
        self.game = Game(
            name="Game of Falls",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[],
            host=self.host,
            host_id=self.host.id,
            board=[board.Color(rng.randint(1, 4)) for _ in range(36)],
        )

        self.games_repo.save(self.game)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.query(History).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_undo(self):
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

            history = self.client.get(f"/api/history/{self.game.id}")
            print("HISTORY BEFORE UNDO: ", history.json())

            status = self.client.post(
                f"/api/game/{self.game.id}/undo",
                json={"identifier": str(self.players[0].identifier)},
            )

            print("STATUS: ", status.json())

            assert status.status_code == 200

            history = self.client.get(f"/api/history/{self.game.id}")
            print("HISTORY AFTER UNDO: ", history.json())

            assert history.status_code == 200
            assert history.json() == []
            assert self.game.player_info[self.players[0].id].hand_mov == [1, 2, 3]

    def test_ws_board_undo(self):
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

                    board_before = [tile.value for tile in self.game.board]

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

                    status = self.client.post(
                        f"/api/game/{self.game.id}/undo",
                        json={
                            "identifier": str(self.players[0].identifier),
                        },
                    )

                    g = self.games_repo.get(self.game.id)
                    assert g is not None
                    db_board = [tile.value for tile in g.board]
                    self.assertEqual(board_before, db_board)

                    assert status.status_code == 200
                    rsp = websocket.receive_json()
                    assert rsp["game_id"] == self.game.id
                    assert rsp["board"] == board_before
                    rsp = websocket2.receive_json()
                    assert rsp["game_id"] == self.game.id
                    assert rsp["board"] == board_before

    def test_ws_hand_undo(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.history_repo", self.history_repo):

            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])

            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/movement_cards?player_UUID={self.players[0].identifier}"
            ) as websocket:
                with self.client.websocket_connect(
                    f"/ws/lobby/{self.game.id}/movement_cards?player_UUID={self.players[1].identifier}"
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
                    websocket.receive_json()
                    websocket2.receive_json()
                    status = self.client.post(
                        f"/api/game/{self.game.id}/undo",
                        json={
                            "identifier": str(self.players[0].identifier),
                        },
                    )
                    assert status.status_code == 200
                    assert websocket.receive_json() == {
                        "action": "recover_card",
                        "player_id": self.players[0].id,
                        "card_id": 3,
                        "index": 0,
                        "len": 0,
                    }
                    assert websocket2.receive_json() == {
                        "action": "recover_card",
                        "player_id": self.players[0].id,
                        "card_id": 3,
                        "index": 0,
                        "len": 0,
                    }

    def test_nothing_undo(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.history_repo", self.history_repo):

            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])
            cards_mov = [1, 2, 3]
            self.game.add_hand_mov(cards_mov, cards_mov, self.players[0].id)
            self.game.start()

            self.client.post(
                f"/api/game/{self.game.id}/play_card",
                json={
                    "identifier": str(self.players[0].identifier),
                    "origin_tile": 0,
                    "dest_tile": 1,
                    "card_mov_id": 3,
                    "index_hand": 1,
                },
            )

            self.game.advance_turn()

            status = self.client.post(
                f"/api/game/{self.game.id}/undo",
                json={
                    "identifier": str(self.players[1].identifier),
                },
            )
            assert status.status_code == 404
            assert status.json() == {"detail": "Nothing to undo"}

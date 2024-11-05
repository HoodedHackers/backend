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
            id=1,
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
            id=2,
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=self.players[0:3],
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

    def test_start_game_hand_cards_broadcast(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]
            id0 = player1.id
            id1 = player2.id

            self.game_1.add_player(player1)
            self.game_1.add_player(player2)
            # self.game_1.player_info[id0].hand_fig = [1]
            # self.game_1.player_info[id1].hand_fig = [2, 3, 4]

            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={id0}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={id1}"
            ) as websocket2:
                try:
                    response = self.client.put(
                        f"/api/lobby/1/start",
                        json={"identifier": str(self.host.identifier)},
                    )
                    websocket1.send_json({"receive": "cards"})

                    assert response.status_code == 200
                    rsp1 = websocket1.receive_json()
                    self.assertIn("players", rsp1)
                    self.assertIsInstance(rsp1["players"], list)
                    assert len(rsp1["players"]) == 2

                    rsp2 = websocket2.receive_json()
                    self.assertIn("players", rsp2)
                    self.assertIsInstance(rsp2["players"], list)
                    assert len(rsp2["players"]) == 2
                    # print(rsp1)
                    # assert 1 ==2

                finally:
                    websocket1.close()
                    websocket2.close()

    def test_start_game_hand_mov(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player0 = self.players[0]
            player1 = self.players[1]
            self.game_1.add_player(self.players[0])
            self.game_1.add_player(self.players[1])
            with client.websocket_connect(
                f"/ws/lobby/{self.game_1.id}/movement_cards?player_UUID={player0.identifier}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/{self.game_1.id}/movement_cards?player_UUID={player1.identifier}"
            ) as websocket2:
                response = self.client.put(
                    f"/api/lobby/1/start",
                    json={"identifier": str(self.host.identifier)},
                )
                assert response.status_code == 200

                # Comprobamos que se haya efectuado el broadcast
                data1 = websocket1.receive_json()
                assert len(self.game_1.all_movs) == 43
                assert data1 == {
                    "action": "deal",
                    "card_mov": self.game_1.player_info[player0.id].hand_mov,
                    "player_id": player0.id,
                    "card_id": 0,
                    "index": 0,
                    "len": 3,
                }
                data2 = websocket2.receive_json()
                assert data2 == {
                    "action": "deal",
                    "card_mov": self.game_1.player_info[player1.id].hand_mov,
                    "player_id": player1.id,
                    "card_id": 0,
                    "index": 0,
                    "len": 3,
                }
                result_list0 = data1["card_mov"]
                result_list1 = data2["card_mov"]
                bool = any(i in result_list1 for i in result_list0)
                assert bool == False

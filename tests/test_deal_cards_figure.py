import unittest
from os import getenv
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

import asserts
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from database import Database
from main import app, game_repo, get_games_repo, player_repo
from model import Game, Player
from repositories import GameRepository, PlayerRepository
from repositories.player import PlayerRepository
from services import Managers, ManagerTypes

client = TestClient(app)


class TestGameExits(unittest.TestCase):
    def setUp(self) -> None:
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

        self.game = Game(
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
        self.games_repo.save(self.game)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_deal_cards(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]
            id0 = self.players[0].id
            id1 = self.players[1].id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]

            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={id0}"
            ) as websocket:
                try:
                    websocket.send_json({"receive": "cards"})
                    rsp = websocket.receive_json()

                    #self.assertIn("player_id", rsp)
                    #self.assertIn("cards", rsp)
                    #self.assertIsInstance(rsp["cards"], list)
                    #assert len(rsp["cards"]) == 1
                    self.assertIn("players", rsp)
                    self.assertIsInstance(rsp["players"], list)
                finally:
                    websocket.close()

    def test_deal_cards_invalid_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]
            id0 = self.players[0].id
            id1 = self.players[1].id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]

            with client.websocket_connect(
                f"/ws/lobby/777/figs?player_id={id0}"
            ) as websocket:
                try:
                    websocket.send_json({"receive": "cards"})
                    rsp = websocket.receive_json()

                    self.assertIn("error", rsp)
                    self.assertEqual(rsp["error"], "Game not found")
                finally:
                    websocket.close()

    def test_deal_cards_invalid_player(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]
            id0 = self.players[0].id
            id1 = self.players[1].id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]

            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id=777"
            ) as websocket:
                try:
                    websocket.send_json({"receive": "cards"})
                    rsp = websocket.receive_json()

                    self.assertIn("error", rsp)
                    self.assertEqual(rsp["error"], "Player not found")
                finally:
                    websocket.close()

    def test_deal_cards_invalid_player_not_in_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]
            id0 = self.players[0].id
            id1 = self.players[1].id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]

            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={self.players[2].id}"
            ) as websocket:
                try:
                    websocket.send_json({"receive": "cards"})
                    rsp = websocket.receive_json()

                    self.assertIn("error", rsp)
                    self.assertEqual(rsp["error"], "Player not in game")
                finally:
                    websocket.close()

    def test_deal_cards_border(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]
            id0 = self.players[0].id
            id1 = self.players[1].id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].fig = [1]
            self.game.player_info[id0].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]

            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={id0}"
            ) as websocket:
                try:
                    websocket.send_json({"receive": "cards"})
                    rsp = websocket.receive_json()

                    #self.assertIn("player_id", rsp)
                    #self.assertIn("cards", rsp)
                    self.assertIn("players", rsp)
                    #self.assertIsInstance(rsp["cards"], list)
                    self.assertIsInstance(rsp["players"], list)
                    #assert len(rsp["cards"]) == 1
                    #assert rsp["cards"] == [1]
                    assert len(self.game.player_info[id0].fig) == 1
                finally:
                    websocket.close()

    def test_broadcast(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            print("player1")
            print(self.players[0].id)
            print(self.players[0].name)
            player2 = self.players[1]
            print("player2")
            print(self.players[1].id)
            print(self.players[1].name)
            id0 = player1.id
            id1 = player2.id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].hand_fig = [1]

            manager = Managers.get_manager(ManagerTypes.CARDS_FIGURE)

            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={id0}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={id1}"
            ) as websocket2:
                try:
                    websocket1.send_json({"receive": "cards"})

                    rsp1 = websocket1.receive_json()
                    #self.assertIn("player_id", rsp1)
                    #self.assertIn("cards", rsp1)
                    #self.assertEqual(rsp1["player_id"], id0)
                    print(rsp1)
                    self.assertIn("players", rsp1)
                    self.assertIsInstance(rsp1["players"], list)
                    #self.assertEqual(rsp1["players"], [1])
                    assert rsp1["players"] == [{"player_id":2, "cards":[1]}, {"player_id":3, "cards":[]}]

                    rsp2 = websocket2.receive_json()
                    #self.assertIn("cards", rsp2)
                    #self.assertEqual(rsp2["cards"], rsp1["cards"])
                    self.assertIn("players", rsp2)
                    self.assertIsInstance(rsp2["players"], list)

                finally:
                    websocket1.close()
                    websocket2.close()

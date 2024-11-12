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

    def test_broadcast(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]
            id0 = player1.id
            id1 = player2.id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]

            with client.websocket_connect(
                f"/ws/lobby/1/chat?player_id={id0}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/1/chat?player_id={id1}"
            ) as websocket2:
                try:
                    websocket1.send_json({"message": "verduras"})

                    rsp1 = websocket1.receive_json()
                    asserts.assert_equal(rsp1["message"], "verduras")

                    rsp2 = websocket2.receive_json()
                    asserts.assert_equal(rsp2["message"], "verduras")

                finally:
                    websocket1.close()
                    websocket2.close()

    def test_invalid_message(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]
            id0 = player1.id
            id1 = player2.id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]

            with client.websocket_connect(
                f"/ws/lobby/1/chat?player_id={id0}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/1/chat?player_id={id1}"
            ) as websocket2:
                try:
                    websocket1.send_json({"cualquier_cosa": "verduras"})

                    rsp1 = websocket1.receive_json()
                    asserts.assert_equal(rsp1["error"], "invalid message")

                    rsp2 = websocket2.receive_json()
                    asserts.assert_equal(rsp2["error"], "invalid message")
                finally:
                    websocket1.close()
                    websocket2.close()
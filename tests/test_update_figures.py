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

    def test_websocket_update_cards_figure(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):

            player1 = self.players[0]
            player2 = self.players[1]
            player3 = self.players[2]

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.add_player(player3)

            self.game.player_info[player1.id].hand_fig = [1, 2, 3]
            self.game.player_info[player2.id].hand_fig = [1]
            self.game.player_info[player3.id].hand_fig = [2, 3, 4]
            self.games_repo.save(self.game)

            with client.websocket_connect(
                f"/ws/lobby/figs/{self.game.id}?player_id={player1.id}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/figs/{self.game.id}?player_id={player2.id}"
            ) as websocket2:
                print("estoy en el test")
                print(player2.identifier)
                websocket1.send_json({"identifier": str(player2.identifier)})

                response1 = websocket1.receive_json()
                print(response1)

                self.assertIn("player_id", response1)
                self.assertIn("cards", response1)
                assert response1 == {"player_id": player2.id, "cards": [1]}
                self.assertEqual(response1["player_id"], player2.id)
                self.assertIsInstance(response1["cards"], list)
                response2 = websocket2.receive_json()
                print(response2)
                self.assertIn("player_id", response1)
                self.assertIn("cards", response1)
                assert response2 == {"player_id": player2.id, "cards": [1]}

            with client.websocket_connect(
                f"/ws/lobby/figs/{self.game.id}?player_id={player3.id}"
            ) as websocket:
                websocket.send_json({"identifier": str(uuid4())})
                response = websocket.receive_json()

                self.assertIn("error", response)
                self.assertEqual(response["error"], "Player not found")

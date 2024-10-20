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
            player3 = self.players[2]
            id0 = self.players[0].id
            id1 = self.players[1].id
            id2 = self.players[2].id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.add_player(player3)
            self.game.player_info[id0].hand_fig = [1, 2, 3]
            self.game.player_info[id2].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]
            hand = self.game.player_info[id0].hand_fig

            response = self.client.post(
                f"/api/lobby/1/figs",
                json={"player_identifier": str(player3.identifier)},
            )

            # Verifica la respuesta del endpoint
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "success"})

            with client.websocket_connect(
                f"/ws/lobby/figs/1?player_id={player3.id}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/figs/1?player_id={player2.id}"
            ) as websocket2, client.websocket_connect(
                f"/ws/lobby/figs/1?player_id={player1.id}"
            ) as websocket3:
                try:
                    websocket1.send_json({"identifier": str(player3.identifier)})
                    rsp1 = websocket1.receive_json()
                    print(rsp1)

                    self.assertIn("player_id", rsp1)
                    self.assertIn("cards", rsp1)
                    self.assertIsInstance(rsp1["cards"], list)
                    self.assertEqual(len(rsp1["cards"]), 3)

                    rsp2 = websocket2.receive_json()
                    print(rsp2)

                    self.assertIn("player_id", rsp2)
                    self.assertIn("cards", rsp2)
                    self.assertEqual(rsp2["player_id"], id2)
                    self.assertEqual(rsp2["cards"], rsp1["cards"])

                    rsp3 = websocket3.receive_json()
                    print(rsp3)
                    self.assertIn("player_id", rsp3)
                    self.assertIn("cards", rsp3)
                    self.assertEqual(rsp3["player_id"], id2)
                    self.assertEqual(rsp3["cards"], rsp1["cards"])
                finally:
                    websocket1.close()
                    websocket2.close()

    def test_player_not_found(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.post(
                f"/api/lobby/1/figs",
                json={"player_identifier": str(uuid4())},
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": "Jugador no encontrade"})

    def test_player_not_in_game(self):
        new_player = Player(name="New Player")
        self.player_repo.save(new_player)

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.post(
                f"/api/lobby/1/figs",
                json={"player_identifier": str(new_player.identifier)},
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json(), {"detail": "Jugador no presente en la partida"}
            )

    def test_broadcast_cards(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]

            self.game.add_player(player1)
            self.game.add_player(player2)

            with client.websocket_connect(
                f"/ws/lobby/figs/1?player_id={player1.id}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/figs/1?player_id={player2.id}"
            ) as websocket2:
                try:
                    websocket1.send_json({"identifier": str(player1.identifier)})

                    rsp1 = websocket1.receive_json()
                    rsp2 = websocket2.receive_json()
                    self.assertEqual(rsp1["cards"], rsp2["cards"])
                finally:
                    websocket1.close()
                    websocket2.close()

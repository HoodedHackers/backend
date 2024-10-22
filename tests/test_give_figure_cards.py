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

    def test_give_figure_cards(self):
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
                f"/ws/lobby/1/figs?player_id={id0}"
            ) as websocket:
                try:
                    websocket.send_json({"receive": "cards"})
                    rsp = websocket.receive_json()
                    rsp_post = self.client.post(
                        f"/api/lobby/in_course/fig/1",
                        json={"identifier": str(self.players[0].identifier)},
                    )
                    self.assertEqual(rsp_post.status_code, 200)
                    print(rsp_post.json())
                    self.assertEqual(rsp["player_id"], id0)
                    self.assertIn("cards", rsp)
                    self.assertIsInstance(rsp["cards"], list)
                    self.assertEqual(len(rsp["cards"]), 3)
                finally:
                    websocket.close()

    def test_give_figure_cards_game_not_found(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            game_request = {"identifier": str(self.players[0].identifier)}

            response = self.client.post(
                f"/api/lobby/in_course/fig/999", json=game_request
            )  # ID no existente

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": "Game dont found"})

        def test_give_figure_cards_player_not_found(self):
            game_request = {
                "identifier": str("00000000-0000-0000-0000-000000000000")
            }  # UUID no existente

            response = self.client.post(
                f"/api/lobby/in_course/fig/{self.game.id}", json=game_request
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": "Requesting player not found"})

    def test_give_figure_cards_player_not_in_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            # Crear un nuevo jugador que no esté en el juego
            new_player = Player(name="New Player")
            self.player_repo.save(new_player)

            game_request = {"identifier": str(new_player.identifier)}

            response = self.client.post(
                f"/api/lobby/in_course/fig/1", json=game_request
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": "Non player in game"})

    def test_give_figure_cards_check_assigned_cards(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            self.game.add_player(player1)

            player1 = self.players[0]
            player2 = self.players[1]
            id0 = player1.id
            id1 = player2.id

            self.game.add_player(player1)
            self.game.add_player(player2)
            self.game.player_info[id0].hand_fig = [1]
            self.game.player_info[id1].hand_fig = [2, 3, 4]
            # Crear una solicitud válida
            game_request = {"identifier": str(player1.identifier)}

            # Realizar la solicitud POST
            response = self.client.post(
                f"/api/lobby/in_course/fig/1",
                json={"identifier": str(self.players[1].identifier)},
            )

            # Verificar el estado de las cartas del jugador
            self.assertEqual(response.status_code, 200)

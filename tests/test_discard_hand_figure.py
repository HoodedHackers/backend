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

    # tests con el ws
    #@patch("main.get_possible_figures", return_value=[1, 2, 3])
    def test_discard_cards_figs_vacio(self):
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
            self.game.player_info[id1].hand_fig = [2, 3, 4]
            self.game.player_info[id2].hand_fig = [1]
            self.game.get_possible_figures = MagicMock(return_value=[1, 2, 3])
            response = self.client.post(
                f"/api/lobby/in-course/1/discard_figs",
                json={"player_identifier": str(player3.identifier), "card_id": 1},
            )

            # Verifica la respuesta del endpoint
            self.assertEqual(response.status_code, 200)
            #self.assertEqual(response.json()["player_id"], player3.id)
            #self.assertEqual(response.json()["cards"], [])

    #@patch("main.get_possible_figures", return_value=[1, 2, 3])
    def test_discard_cards_figs(self):
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
            self.game.player_info[id1].hand_fig = [2, 3, 4]
            self.game.player_info[id2].hand_fig = [1]

           # figs= game.get_possible_figures()
            self.game.get_possible_figures = MagicMock(return_value=[1, 2, 3])
            response = self.client.post(
                f"/api/lobby/in-course/1/discard_figs",
                json={"player_identifier": str(player2.identifier), "card_id": 3},
            )
            print(response.json())
            self.assertEqual(response.status_code, 200)
            #self.assertEqual(response.json()["player_id"], player2.id)
            #cards = response.json()["cards"]
            #assert len(cards) == 2
            #sself.assertEqual(response.json()["cards"], [2, 4])

    def test_player_not_found(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.post(
                f"/api/lobby/in-course/1/discard_figs",
                json={"player_identifier": str(uuid4()), "card_id": 1},
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
                f"/api/lobby/in-course/1/discard_figs",
                json={"player_identifier": str(new_player.identifier), "card_id": 1},
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json(), {"detail": "Jugador no presente en la partida"}
            )

    def test_enpoint_not_card_id(self):

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
            self.game.player_info[id1].hand_fig = [2, 3, 4]
            self.game.player_info[id2].hand_fig = [1]

            hand = self.game.player_info[id0].hand_fig

            response = self.client.post(
                f"/api/lobby/in-course/1/discard_figs",
                json={"player_identifier": str(player1.identifier), "card_id": 5},
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json(),
                {"detail": "Carta no encontrada en la mano del jugador"},
            )

    # tests sin el ws
    #@patch("main.get_possible_figures", return_value=[1, 2, 3])
    def test_discard_hand_figure_success(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            self.game.add_player(player1)
            self.game.player_info[player1.id].hand_fig = [
                1,
                2,
                3,
            ]  # El jugador tiene estas cartas
            self.game.get_possible_figures = MagicMock(return_value=[1, 2, 3])
            response = self.client.post(
                "/api/lobby/in-course/1/discard_figs",
                json={"player_identifier": str(player1.identifier), "card_id": 1},
            )

            self.assertEqual(response.status_code, 200)
            #self.assertEqual(response.json()["cards"], [2, 3])
            #FALTA AGREGAR ALGO ACA
    def test_card_not_in_hand(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            self.game.add_player(player1)
            self.game.player_info[player1.id].hand_fig = [
                2,
                3,
            ]  # El jugador solo tiene estas cartas

            response = self.client.post(
                "/api/lobby/in-course/1/discard_figs",
                json={"player_identifier": str(player1.identifier), "card_id": 1},
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json(),
                {"detail": "Carta no encontrada en la mano del jugador"},
            )

    def test_game_not_found(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.post(
                "/api/lobby/in-course/999/discard_figs",
                json={
                    "player_identifier": str(self.players[0].identifier),
                    "card_id": 1,
                },
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": "Partida no encontrada"})

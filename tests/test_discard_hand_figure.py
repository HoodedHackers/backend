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


class TestDiscardCardFigure(unittest.TestCase):
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
            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player1.id}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player2.id}"
            ) as websocket2:

                self.game.ids_get_possible_figures = MagicMock(return_value=[1, 2, 3])
                response = self.client.post(
                    f"/api/lobby/in-course/1/discard_figs",
                    json={"player_identifier": str(player3.identifier), "card_id": 1},
                )

                # Verifica la respuesta del endpoint
                self.assertEqual(response.status_code, 200)
                websocket1.send_json({"receive": "cards"})
                rsp1 = websocket1.receive_json()
                websocket2.send_json({"receive": "cards"})
                rsp2 = websocket1.receive_json()
                print(rsp1)
                assert rsp1["players"] == [
                    {
                        "player_id": 2,
                        "cards": [1, 2, 3],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": 3,
                        "cards": [2, 3, 4],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": 4,
                        "cards": [],
                        "block_card": 0,
                        "invisible_block": -1,
                    },
                ]
                assert rsp2["players"] == [
                    {
                        "player_id": 2,
                        "cards": [1, 2, 3],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": 3,
                        "cards": [2, 3, 4],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": 4,
                        "cards": [],
                        "block_card": 0,
                        "invisible_block": -1,
                    },
                ]

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

            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player1.id}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player2.id}"
            ) as websocket2:

                self.game.ids_get_possible_figures = MagicMock(return_value=[1, 2, 3])
                response = self.client.post(
                    f"/api/lobby/in-course/1/discard_figs",
                    json={"player_identifier": str(player2.identifier), "card_id": 3},
                )
                self.assertEqual(response.status_code, 200)
                websocket1.send_json({"receive": "cards"})
                rsp1 = websocket1.receive_json()
                websocket2.send_json({"receive": "cards"})
                rsp2 = websocket1.receive_json()
                print(rsp1)
                assert rsp1["players"] == [
                    {
                        "player_id": 2,
                        "cards": [1, 2, 3],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": 3,
                        "cards": [2, 4],
                        "block_card": 0,
                        "invisible_block": 1,
                    },
                    {
                        "player_id": 4,
                        "cards": [1],
                        "block_card": 0,
                        "invisible_block": 0,
                    },
                ]
                assert rsp2["players"] == [
                    {
                        "player_id": 2,
                        "cards": [1, 2, 3],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": 3,
                        "cards": [2, 4],
                        "block_card": 0,
                        "invisible_block": 1,
                    },
                    {
                        "player_id": 4,
                        "cards": [1],
                        "block_card": 0,
                        "invisible_block": 0,
                    },
                ]

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
            ]
            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player1.id}"
            ) as websocket:
                self.game.ids_get_possible_figures = MagicMock(return_value=[1, 2, 3])
                response = self.client.post(
                    "/api/lobby/in-course/1/discard_figs",
                    json={"player_identifier": str(player1.identifier), "card_id": 1},
                )
                self.assertEqual(response.status_code, 200)
                websocket.send_json({"receive": "cards"})
                rsp = websocket.receive_json()
                assert rsp["players"] == [
                    {
                        "player_id": 2,
                        "cards": [2, 3],
                        "block_card": 0,
                        "invisible_block": 1,
                    }
                ]

    def test_card_not_in_hand(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            self.game.add_player(player1)
            self.game.player_info[player1.id].hand_fig = [
                2,
                3,
            ]
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

    def test_discard_cards_figs_invalid(self):
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

            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player1.id}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player2.id}"
            ) as websocket2:

                self.game.ids_get_possible_figures = MagicMock(return_value=[1, 2, 3])
                response = self.client.post(
                    f"/api/lobby/in-course/1/discard_figs",
                    json={"player_identifier": str(player2.identifier), "card_id": 4},
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {"detail": "Figura invalida"})
                """"
                websocket1.send_json({"receive": "cards"})
                rsp1 = websocket1.receive_json()
                websocket2.send_json({"receive": "cards"})
                rsp2 = websocket1.receive_json()
                print(rsp1)
                assert rsp1 == {"error": "Invalid figure"}
                assert rsp2["players"] == [
                    {
                        "player_id": 2,
                        "cards": [1, 2, 3],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": 3,
                        "cards": [2, 3, 4],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": 4,
                        "cards": [1],
                        "block_card": 0,
                        "invisible_block": 0,
                    },
                ]
                """

    def test_discard_cards_mov(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            self.game.add_player(player1)
            self.game.player_info[player1.id].hand_fig = [1, 2, 3]
            self.game.player_info[player1.id].hand_mov = [1, 2, 3]
            self.game.player_info[player1.id].mov_parcial = [1, 2]
            self.game.ids_get_possible_figures = MagicMock(return_value=[1, 2, 3])
            response = self.client.post(
                "/api/lobby/in-course/1/discard_figs",
                json={"player_identifier": str(player1.identifier), "card_id": 1},
            )
            spect_hand_mov = self.game.player_info[player1.id].hand_mov
            assert response.status_code == 200
            assert spect_hand_mov == [3]

    def test_unblock(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]

            self.game.add_player(player1)
            self.game.add_player(player2)

            self.games_repo.save(self.game)
            with client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player1.id}"
            ) as websocket1, client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={player2.id}"
            ) as websocket2:
                self.game.distribute_deck()
                elems = self.game.add_random_card(player1.id)
                self.game.block_card(player1.id, elems[0])
                self.game.discard_card_hand_figures(player1.id, elems[1])
                self.game.discard_card_hand_figures(player1.id, elems[2])

                self.games_repo.save(self.game)

                self.game.player_info[player2.id].hand_fig = [2, 3, 4]
                self.game.ids_get_possible_figures = MagicMock(
                    return_value=[1, 2, elems[0]]
                )

                response = self.client.post(
                    "/api/lobby/in-course/1/discard_figs",
                    json={
                        "player_identifier": str(player1.identifier),
                        "card_id": elems[0],
                    },
                )
                print(response.json)
                assert response.status_code == 200

                assert len(self.game.get_player_hand_figures(player1.id)) == 0
                assert websocket1.receive_json()["players"] == [
                    {
                        "player_id": player1.id,
                        "cards": self.game.get_player_hand_figures(player1.id),
                        "block_card": 0,
                        "invisible_block": -1,
                    },
                    {
                        "player_id": 3,
                        "cards": [2, 3, 4],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                ]

import unittest
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, Player
from repositories import GameRepository, PlayerRepository


class TestNotifyLobby(unittest.TestCase):

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

        self.game_public = Game(
            id=1,
            name="Game of Falls",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[],
            host=self.host,
            host_id=self.host.id,
            is_private=False,
        )

        self.game_private = Game(
            id=2,
            name="Game of Thrones Private",
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=[],
            host=self.host,
            host_id=self.host.id,
            is_private=True,
            password="1234",
        )

        self.games_repo.save(self.game_public)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_connect_from_lobby_public(self):

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):

            identifier0 = self.players[0].identifier
            indetifier1 = self.players[1].identifier
            id0 = self.players[0].id
            id1 = self.players[1].id

            with self.client.websocket_connect(
                f"/ws/lobby/1?player_id={id0}"
            ) as websocket0:

                websocket0.send_json({"user_identifier": str(identifier0)})

                # Chequeamos que estemos solos
                response = websocket0.receive_json()
                assert response == {
                    "players": [
                        {
                            "player_id": id0,
                            "player_name": self.game_public.players[0].name,
                        }
                    ]
                }

                with self.client.websocket_connect(
                    f"/ws/lobby/1?player_id={id1}"
                ) as websocket1:

                    websocket1.send_json({"user_identifier": str(indetifier1)})

                    # Chequeamos que estemos los dos
                    response = websocket1.receive_json()
                    assert response == {
                        "players": [
                            {
                                "player_id": id0,
                                "player_name": self.game_public.players[0].name,
                            },
                            {
                                "player_id": id1,
                                "player_name": self.game_public.players[1].name,
                            },
                        ],
                    }

        def test_connect_from_lobby_private(self):

            with patch("main.game_repo", self.games_repo), patch(
                "main.player_repo", self.player_repo
            ):

                identifier0 = self.players[0].identifier
                indetifier1 = self.players[1].identifier
                id0 = self.players[0].id
                id1 = self.players[1].id

                with self.client.websocket_connect(
                    f"/ws/lobby/2?player_id={id0}"
                ) as websocket0:

                    websocket0.send_json({"user_identifier": str(identifier0)})

                    # Chequeamos que estemos solos
                    response = websocket0.receive_json()
                    assert response == {
                        "players": [
                            {
                                "player_id": id0,
                                "player_name": self.game_private.players[0].name,
                            }
                        ]
                    }

                    with self.client.websocket_connect(
                        f"/ws/lobby/2?player_id={id1}"
                    ) as websocket1:

                        websocket1.send_json(
                            {"user_identifier": str(indetifier1), "password": "1234"}
                        )

                        # Chequeamos que estemos los dos y que la contraseña es correcta
                        response = websocket1.receive_json()
                        assert response == {
                            "players": [
                                {
                                    "player_id": id0,
                                    "player_name": self.game_private.players[0].name,
                                },
                                {
                                    "player_id": id1,
                                    "player_name": self.game_private.players[1].name,
                                },
                            ],
                        }

        def test_connect_from_lobby_private_password_incorrect(self):

            with patch("main.game_repo", self.games_repo), patch(
                "main.player_repo", self.player_repo
            ):

                identifier0 = self.players[0].identifier
                indetifier1 = self.players[1].identifier
                id0 = self.players[0].id
                id1 = self.players[1].id

                with self.client.websocket_connect(
                    f"/ws/lobby/2?player_id={id0}"
                ) as websocket0:

                    websocket0.send_json({"user_identifier": str(identifier0)})

                    # Chequeamos que estemos solos
                    response = websocket0.receive_json()
                    assert response == {
                        "players": [
                            {
                                "player_id": id0,
                                "player_name": self.game_private.players[0].name,
                            }
                        ]
                    }

                    with self.client.websocket_connect(
                        f"/ws/lobby/2?player_id={id1}"
                    ) as websocket1:

                        websocket1.send_json(
                            {"user_identifier": str(indetifier1), "password": "12345"}
                        )

                        # Chequeamos que la efectivamente la contraseña es incorrecta
                        response = websocket1.receive_json()
                        assert response == {
                            "error": "Incorrect password",
                        }

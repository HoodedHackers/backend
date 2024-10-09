from fastapi.testclient import TestClient
import unittest
from unittest.mock import patch
import pytest
from repositories import GameRepository, PlayerRepository
from database import Database

from main import app
from model import Player, Game


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

        self.game_1 = Game(
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

        self.games_repo.save(self.game_1)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_connect_from_lobby(self):

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):

            identifier0 = str(self.players[0].identifier)
            indetifier1 = str(self.players[1].identifier)
            id0 = self.players[0].id
            id1 = self.players[1].id

            # Se une el Lou
            self.game_1.players.append(self.players[0])
            with self.client.websocket_connect(
                f"/ws/lobby/1"
            ) as websocket0:

                websocket0.send_json(
                    {"user_identifier": identifier0, "action": "connect"}
                )

                # Chequeamos que estemos solos
                response = websocket0.receive_json()
                assert response == {
                    "players": [
                        {"id": id0, "name": self.game_1.players[0].name}
                    ]
                }

                # Se une el Lou^2
                self.game_1.players.append(self.players[1])
                with self.client.websocket_connect(
                    f"/ws/lobby/1"
                ) as websocket1:

                    websocket1.send_json(
                        {"user_identifier": indetifier1, "action": "connect"}
                    )

                    # Chequeamos que estemos los dos
                    response = websocket1.receive_json()
                    assert response == {
                        "players": [
                            {
                                "id": id0,
                                "name": self.game_1.players[0].name,
                            },
                            {
                                "id": id1,
                                "name": self.game_1.players[1].name,
                            },
                        ],
                    }
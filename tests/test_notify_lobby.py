from fastapi.testclient import TestClient
import unittest
from unittest.mock import patch
import pytest
from repositories import GameRepository, PlayerRepository
from database import Database

from main import app
from model import Player, Game

client = TestClient(app)


player_mock = Player(name="Matias", identifier="805423e9-30e3-4e9c-9745-6d3deb5d478d")

game_mocks = [
    Game(
        id=1010,
        name="Game of throne",
        current_player_turn=0,
        max_players=4,
        min_players=2,
        started=False,
        players=[player_mock],
        host_id=1,
    ),
    Game(
        id=1010,
        name="Game of throne",
        current_player_turn=0,
        max_players=4,
        min_players=2,
        started=False,
        players=[],
        host_id=1,
    ),
]


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
            current_player_turn=0,
            max_players=4,
            min_players=2,
            started=False,
            players=self.players[1:3],
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

    def test_connect_from_lobby(self):

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):

            identifier = str(self.game_1.players[0].identifier)

            with client.websocket_connect(f"/ws/lobby/{self.game_1.id}") as websocket:
                message_connect = {
                    "user_identifier": identifier,
                    "action": "connect",
                }

                message_disconnect = {
                    "user_identifier": identifier,
                    "action": "disconnect",
                }

                websocket.send_json(message_connect)

                response = websocket.receive_json()
                assert response == {
                    "players": [
                        {"identifier": identifier, "name": self.game_1.players[0].name}
                    ]
                }

                # websocket.send_json(message_disconnect)

                # response = websocket.receive_json()
                # assert response == {"error": "Game not found"}

                # websocket.close()

import unittest
from unittest.mock import patch
from uuid import UUID

import asserts
from fastapi.testclient import TestClient

from database import Database
from main import app, game_repo, player_repo
from model import Game, Player
from repositories import GameRepository, PlayerRepository

client = TestClient(app)


class TestSelectCard(unittest.TestCase):

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

    def test_deal_mov(self):

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):

            self.game.add_player(self.players[0])

            id_game = self.game.id
            str_player = str(self.players[0].identifier)
            response = client.post(
                "/api/partida/en_curso/movimiento",
                json={
                    "game_id": id_game,
                    "player": str_player,
                },
            )
            asserts.assert_equal(response.status_code, 200)

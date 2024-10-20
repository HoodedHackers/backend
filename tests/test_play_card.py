import random
import unittest
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, History, Player
from repositories import GameRepository, HistoryRepository, PlayerRepository


class TestPlayCard(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.dbs = Database().session()
        self.games_repo = GameRepository(self.dbs)
        self.player_repo = PlayerRepository(self.dbs)
        self.history_repo = HistoryRepository(self.dbs)

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

        history_base = History(
            game_id=self.game.id,
            board=self.game.board,
            player_id=self.players[2].id,
            fig_mov_id=3,
            origin_x=0,
            origin_y=0,
            dest_x=1,
            dest_y=0,
        )

        self.history_repo.save(history_base)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.query(History).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_play(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            self.game.add_player(self.players[0])

            cards_mov = [1, 2, 3]
            self.game.add_hand_mov(cards_mov, cards_mov, self.players[0].id)

            print("ORIGIN:", self.game.board, "\n")

            status = self.client.post(
                f"/api/game/{self.game.id}/play_card",
                json={
                    "player_id": self.players[0].id,
                    "origin_x": 0,
                    "origin_y": 0,
                    "destination_x": 1,
                    "destination_y": 0,
                    "card_fig_id": 3,
                },
            )
            assert status.status_code == 200

            history = self.history_repo.get_all(self.game.id)
            print("\nHISTORY:", history)

            print("\nAFTER:", self.game.board)
            assert 3 == 4

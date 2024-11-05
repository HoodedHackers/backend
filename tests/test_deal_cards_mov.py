import unittest
from unittest.mock import patch
from uuid import UUID

import asserts
from fastapi.testclient import TestClient

from database import Database
from main import app, game_repo, player_repo
from model import TOTAL_HAND_MOV, TOTAL_MOV, Game, Player
from repositories import GameRepository, PlayerRepository

client = TestClient(app)


class TestDealCard(unittest.TestCase):

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

    def test_deal_mov_empty(self):

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):

            self.game.add_player(self.players[0])
            id_game = self.game.id
            str_player = str(self.players[0].identifier)
            response = client.post(
                f"/api/lobby/{id_game}/movs",
                json={
                    "game_id": id_game,
                    "player": str_player,
                },
            )
            all_cards_mov = self.game.all_movs
            asserts.assert_equal(response.status_code, 200)
            result = response.json()
            id_p = self.players[0].id
            asserts.assert_equal(result["player_id"], id_p)
            asserts.assert_equal(len(result["all_cards"]), TOTAL_HAND_MOV)
            asserts.assert_equal(len(all_cards_mov), TOTAL_MOV - TOTAL_HAND_MOV)

    def test_deal_mov_nonempty(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            self.game.add_player(self.players[1])
            id_p = self.players[1].id
            id_game = self.game.id
            str_player = str(self.players[1].identifier)
            list = [1, 2]
            self.game.player_info[id_p].hand_mov = list
            response = client.post(
                f"/api/lobby/{id_game}/movs",
                json={
                    "game_id": id_game,
                    "player": str_player,
                },
            )
            all_cards_mov = self.game.all_movs
            asserts.assert_equal(response.status_code, 200)
            result = response.json()
            asserts.assert_equal(result["player_id"], id_p)
            asserts.assert_equal(len(result["all_cards"]), TOTAL_HAND_MOV)
            asserts.assert_equal(len(all_cards_mov), TOTAL_MOV - 1)

    def test_deal_unique(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])
            id0_p = self.players[0].id
            id1_p = self.players[1].id
            id_game = self.game.id
            str_player0 = str(self.players[0].identifier)
            str_player1 = str(self.players[1].identifier)
            response0 = client.post(
                f"/api/lobby/{id_game}/movs",
                json={
                    "game_id": id_game,
                    "player": str_player0,
                },
            )
            response1 = client.post(
                f"/api/lobby/{id_game}/movs",
                json={
                    "game_id": id_game,
                    "player": str_player1,
                },
            )
            all_cards_mov = self.game.all_movs
            result_list0 = response0.json()["all_cards"]
            result_list1 = response1.json()["all_cards"]
            bool = any(i in result_list1 for i in result_list0)
            asserts.assert_equal(bool, False)

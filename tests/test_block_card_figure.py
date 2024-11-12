import unittest
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, Player
from repositories import GameRepository, PlayerRepository


class TestBlockUnblockCard(unittest.TestCase):

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

    def test_block_figure(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player0 = self.players[0]
            player1 = self.players[1]
            id0 = self.players[0].id
            id1 = self.players[1].id

            self.game.add_player(player0)
            self.game.add_player(player1)

            self.game.player_info[player0.id].hand_fig = [4, 5, 6]
            self.game.player_info[player0.id].hand_mov = [11, 10, 9]
            self.game.player_info[player0.id].mov_parcial = [11, 9]

            self.game.player_info[player1.id].hand_fig = [1, 2, 3]
            self.game.player_info[player1.id].hand_mov = [1, 2, 3]
            self.game.player_info[player1.id].mov_parcial = [1, 2]

            self.game.ids_get_possible_figures = MagicMock(return_value=[1, 2, 3])

            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/figs?player_id={id0}"
            ) as websocket0, self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/figs?player_id={id1}"
            ) as websocket1:
                result = self.client.post(
                    f"/api/lobby/{self.game.id}/block",
                    json={
                        "identifier": str(self.players[0].identifier),
                        "id_player_block": id1,
                        "id_card_block": 2,
                    },
                )
                assert result.status_code == 200
                assert self.game.player_info[id0].hand_mov == [10]
                assert self.game.player_info[id1].block_card == 2

                assert websocket0.receive_json()["players"] == [
                    {
                        "player_id": id0,
                        "cards": [4, 5, 6],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": id1,
                        "cards": [1, 2, 3],
                        "block_card": 2,
                        "invisible_block": 2,
                    },
                ]
                assert websocket1.receive_json()["players"] == [
                    {
                        "player_id": id0,
                        "cards": [4, 5, 6],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": id1,
                        "cards": [1, 2, 3],
                        "block_card": 2,
                        "invisible_block": 2,
                    },
                ]

    def test_cannot_block(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player0 = self.players[0]
            player1 = self.players[1]
            id0 = self.players[0].id
            id1 = self.players[1].id

            self.game.add_player(player0)
            self.game.add_player(player1)

            self.game.player_info[id0].hand_fig = [4, 5, 6]
            self.game.player_info[id0].hand_mov = [11, 10, 9]
            self.game.player_info[id0].mov_parcial = [11, 9]

            self.game.player_info[id1].hand_fig = [1, 2, 3]
            self.game.player_info[id1].hand_mov = [1, 2, 3]
            self.game.player_info[id1].mov_parcial = [1, 2]
            self.game.player_info[id1].block_card = 3

            self.game.ids_get_possible_figures = MagicMock(return_value=[1, 2, 3])

            with self.client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={id0}"
            ) as websocket0, self.client.websocket_connect(
                f"/ws/lobby/1/figs?player_id={id1}"
            ) as websocket1:
                result = self.client.post(
                    f"/api/lobby/{self.game.id}/block",
                    json={
                        "identifier": str(self.players[0].identifier),
                        "id_player_block": id1,
                        "id_card_block": 2,
                    },
                )
                assert result.status_code == 404
                assert result.json() == {
                    "detail": "The player has a card that is already blocked"
                }

    def test_advance_pos_unblock(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            player1 = self.players[0]
            player2 = self.players[1]

            self.game.add_player(player1)
            self.game.add_player(player2)

            self.games_repo.save(self.game)
            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/figs?player_id={player1.id}"
            ) as websocket1, self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/figs?player_id={player2.id}"
            ) as websocket2:
                self.game.started = True
                self.game.distribute_deck()
                elems = self.game.add_random_card(player1.id)
                self.game.block_card(player1.id, elems[0])
                self.game.discard_card_hand_figures(player1.id, elems[1])
                self.game.discard_card_hand_figures(player1.id, elems[2])

                self.games_repo.save(self.game)

                self.game.player_info[player2.id].hand_fig = [2, 3, 4]
                self.game.ids_get_possible_figures = MagicMock(
                    return_value=[x for x in elems]
                )

                response = self.client.post(
                    f"/api/lobby/in-course/{self.game.id}/discard_figs",
                    json={
                        "player_identifier": str(player1.identifier),
                        "card_id": elems[0],
                        "color": 1,
                    },
                )

                assert response.status_code == 200

                websocket1.receive_json()
                websocket2.receive_json()

                response2 = self.client.post(
                    f"/api/lobby/{self.game.id}/advance",
                    json={"identifier": str(player1.identifier)},
                )

                assert response2.status_code == 200

                assert websocket1.receive_json()["players"] == [
                    {
                        "player_id": player1.id,
                        "cards": self.game.get_player_hand_figures(player1.id),
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": player2.id,
                        "cards": [2, 3, 4],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                ]
                assert websocket2.receive_json()["players"] == [
                    {
                        "player_id": player1.id,
                        "cards": self.game.get_player_hand_figures(player1.id),
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                    {
                        "player_id": player2.id,
                        "cards": [2, 3, 4],
                        "block_card": 0,
                        "invisible_block": 2,
                    },
                ]

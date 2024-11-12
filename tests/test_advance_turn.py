import unittest
from unittest.mock import patch
from uuid import uuid1

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, Player
from repositories import GameRepository, PlayerRepository


class TestAdvanceTurn(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.dbs = Database().session()
        self.games_repo = GameRepository(self.dbs)
        self.player_repo = PlayerRepository(self.dbs)
        self.add_test_entitnies()

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.commit()
        self.dbs.close()

    def add_test_entitnies(self):
        host = Player(name="Ely")
        self.player_repo.save(host)
        self.players = [
            host,
            Player(name="Lou"),
            Player(name="Lou^2"),
            Player(name="Andy"),
        ]
        for p in self.players:
            self.player_repo.save(p)

        g = Game(name="test game", host=host, id=1)
        g.add_player(host)
        self.games_repo.save(g)
        self.host = host
        self.game = g

    def test_successful_advance(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            self.game.started = True
            self.games_repo.save(self.game)
            response = self.client.post(
                f"/api/lobby/{self.game.id}/advance",
                json={"identifier": str(self.host.identifier)},
            )
            assert response.status_code == 200
            assert response.json() == {"status": "success"}

    def test_game_not_started(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.post(
                f"/api/lobby/{self.game.id}/advance",
                json={"identifier": str(self.host.identifier)},
            )
            assert response.status_code == 401

    def test_wrong_player(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            other_player = Player(name="El Profe")
            self.player_repo.save(other_player)
            response = self.client.post(
                f"/api/lobby/{self.game.id}/advance",
                json={"identifier": str(other_player.identifier)},
            )
            assert response.status_code == 404

    def test_not_player_turn(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            other_player = Player(name="El Profe")
            self.player_repo.save(other_player)
            self.game.add_player(other_player)
            response = self.client.post(
                f"/api/lobby/{self.game.id}/advance",
                json={"identifier": str(other_player.identifier)},
            )
            assert response.status_code == 401

    def test_bad_player(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.post(
                f"/api/lobby/{self.game.id}/advance",
                json={"identifier": str(uuid1(0, 0))},
            )
            assert response.status_code == 404

    def test_bad_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            response = self.client.post(
                f"/api/lobby/-1/advance",
                json={"identifier": str(self.host.identifier)},
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_ws_message(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), self.client.websocket_connect(f"/ws/lobby/{self.game.id}/turns") as ws:
            self.client.post(
                f"/api/lobby/{self.game.id}/advance",
                json={"identifier": str(self.host.identifier)},
            )
            message = ws.receive_json()
            assert message.get("game_id") == self.game.host_id
            assert message.get("current_turn") == self.game.current_player_turn
            current_player = self.game.current_player()
            assert current_player is not None
            assert message.get("player_id") == current_player.id
            ws.close()

    def test_ws_message_hand_card_fig(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/figs?player_id={self.host.id}"
            ) as ws:
                try:
                    self.game.started = True
                    self.game.player_info[self.host.id].hand_fig = [1, 2]
                    self.game.player_info[self.host.id].fig = [3, 4, 5]

                    response = self.client.post(
                        f"/api/lobby/{self.game.id}/advance",
                        json={"identifier": str(self.host.identifier)},
                    )
                    ws.send_json({"receive": "cards"})
                    patos = self.game.get_player_hand_figures(self.host.id)
                    assert response.status_code == 200
                    message = ws.receive_json()
                    assert len(patos) == 3
                    self.assertIsInstance(message["players"], list)
                    assert len(message["players"]) == 1
                    assert len(message["players"][0]["cards"]) == 3
                finally:
                    ws.close()

    def test_ws_message_hand_card_mov(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/movement_cards?player_UUID={self.host.identifier}"
            ) as websocket1:
                self.game.started = True
                new_cards = [1, 2]
                discard = []
                self.game.add_hand_mov(new_cards, discard, self.host.id)

                self.games_repo.save(self.game)

                response = self.client.post(
                    f"/api/lobby/{self.game.id}/advance",
                    json={"identifier": str(self.host.identifier)},
                )
                assert response.status_code == 200

                # Comprobamos que se haya efectuado el broadcast
                data = websocket1.receive_json()
                assert len(self.game.all_movs) == 48

                assert data == {
                    "action": "deal",
                    "card_mov": self.game.player_info[self.host.id].hand_mov,
                }

    def test_block_invisible(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/figs?player_id={self.host.id}"
            ) as ws:
                self.game.started = True
                new_cards = [1, 2]
                discard = []
                self.game.add_hand_mov(new_cards, discard, self.host.id)
                self.game.distribute_deck()
                elems = self.game.add_random_card(self.host.id)
                self.game.block_card(self.host.id, elems[0])
                self.game.discard_card_hand_figures(self.host.id, elems[1])
                self.games_repo.save(self.game)

                response = self.client.post(
                    f"/api/lobby/{self.game.id}/advance",
                    json={"identifier": str(self.host.identifier)},
                )
                assert response.status_code == 200

                assert len(self.game.all_movs) == 48
                assert len(self.game.get_player_hand_figures(self.host.id)) == 2
                assert ws.receive_json()["players"] == [
                    {
                        "player_id": self.host.id,
                        "cards": self.game.get_player_hand_figures(self.host.id),
                        "block_card": elems[0],
                        "invisible_block": 1,
                    }
                ]

    def test_block_visible(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/figs?player_id={self.host.id}"
            ) as ws:
                self.game.started = True
                new_cards = [1, 2]
                discard = []
                self.game.add_hand_mov(new_cards, discard, self.host.id)
                self.game.distribute_deck()
                elems = self.game.add_random_card(self.host.id)
                self.game.block_card(self.host.id, elems[0])
                self.game.discard_card_hand_figures(self.host.id, elems[1])
                self.game.discard_card_hand_figures(self.host.id, elems[2])
                self.games_repo.save(self.game)

                response = self.client.post(
                    f"/api/lobby/{self.game.id}/advance",
                    json={"identifier": str(self.host.identifier)},
                )
                assert response.status_code == 200

                assert len(self.game.all_movs) == 48
                assert len(self.game.get_player_hand_figures(self.host.id)) == 1
                assert ws.receive_json()["players"] == [
                    {
                        "player_id": self.host.id,
                        "cards": self.game.get_player_hand_figures(self.host.id),
                        "block_card": elems[0],
                        "invisible_block": 0,
                    }
                ]

    def test_undo_movs_board(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            other_player = self.players[0]
            self.game.add_player(other_player)
            self.games_repo.save(self.game)
            with self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/board?player_id={self.host.id}"
            ) as ws_host, self.client.websocket_connect(
                f"/ws/lobby/{self.game.id}/board?player_id={self.players[0].id}"
            ) as ws_other:
                self.game.started = True
                new_cards = [3, 10, 17]
                discard = []
                self.game.add_hand_mov(new_cards, discard, self.host.id)
                self.game.distribute_deck()
                elems = self.game.add_random_card(self.host.id)

                self.games_repo.save(self.game)

                board_before = [tile.value for tile in self.game.board]

                origin = 0
                dest = 1
                assert self.game.started == True
                for i in range(len(new_cards)):
                    response = self.client.post(
                        f"/api/game/{self.game.id}/play_card",
                        json={
                            "identifier": str(self.host.identifier),
                            "origin_tile": origin,
                            "dest_tile": dest,
                            "card_mov_id": new_cards[i],
                            "index_hand": 1,
                        },
                    )
                    assert response.status_code == 200
                    origin = origin + 2
                    dest = dest + 2
                    ws_host.receive_json()
                    ws_other.receive_json()

                response = self.client.post(
                    f"/api/lobby/{self.game.id}/advance",
                    json={"identifier": str(self.host.identifier)},
                )

                assert response.status_code == 200

                board_after = [tile.value for tile in self.game.board]
                assert board_after == board_before

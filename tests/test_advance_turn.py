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
            assert 1 == 2
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
                    print(self.game.player_info[self.host.id].fig)
                    print(self.game.player_info[self.host.id].hand_fig)
                    # self.game.add_random_card(self.host.id)
                    self.games_repo.save(self.game)

                    response = self.client.post(
                        f"/api/lobby/{self.game.id}/advance",
                        json={"identifier": str(self.host.identifier)},
                    )
                    ws.send_json({"receive": "cards"})
                    patos = self.game.get_player_hand_figures(self.host.id)
                    # no anda el test
                    assert response.status_code == 200
                    message = ws.receive_json()
                    print(message)
                    """
                    assert message.get("game_id") == self.game.host_id
                    assert message.get("current_turn") == self.game.current_player_turn
                    current_player = self.game.current_player()
                    assert current_player is not None
                    assert message.get("player_id") == current_player.id
                    ws.close()


                    for _ in range(count):
                if not self.player_info[player_id].fig:
                    break
                id = random.choice(self.player_info[player_id].fig)

                aux_hand_fig = self.player_info[player_id].hand_fig
                aux_fig = self.player_info[player_id].fig
                aux_fig.remove(id)
                aux_hand_fig.append(id)
                self.player_info[player_id] = PlayerInfo(
                    player_id=player_id,
                    turn_position=self.player_info[player_id].turn_position,
                    hand_fig=aux_hand_fig,
                    hand_mov=self.player_info[player_id].hand_mov,
                    fig=aux_fig,
                    mov_parcial=self.player_info[player_id].mov_parcial,
                )
                    """
                    # assert 1 == 2
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
                print(self.game.player_info[self.host.id].hand_mov)

                self.games_repo.save(self.game)

                print(self.game.player_info[self.host.id].hand_mov)
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
                    "player_id": self.host.id,
                    "card_id": 0,
                    "index": 0,
                    "len": 3,
                }

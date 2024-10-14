"""
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
        g = Game(name="test game", host=host)
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
        ), self.client.websocket_connect(f"/api/lobby/{self.game.id}/turns") as ws:
            self.client.post(
                f"/api/lobby/{self.game.id}/advance",
                json={"identifier": str(self.host.identifier)},
            )
            message = await ws.receive_json()
            assert message.get("game_id") == self.game.host_id
            assert message.get("current_turn") == self.game.current_player_turn
            current_player = self.game.current_player()
            assert current_player is not None
            assert message.get("player_id") == current_player.id
            ws.close()
"""

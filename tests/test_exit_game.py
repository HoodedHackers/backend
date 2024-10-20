import unittest
from os import getenv
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

import asserts
import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket, WebSocketDisconnect

from database import Database
from main import app, game_repo, get_games_repo, player_repo
from model import Game, Player
from repositories import GameRepository, PlayerRepository
from repositories.player import PlayerRepository
from services import Managers, ManagerTypes

client = TestClient(app)


class TestGameExits(unittest.TestCase):
    def setUp(self) -> None:
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

    def test_exit_invalid_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            rsp = self.client.post(
                f"/api/lobby/777/exit",
                json={"identifier": str(self.game.host.identifier)},
            )
            self.assertEqual(rsp.status_code, 404)

    def test_exit_invalid_player(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            rsp = self.client.post(
                f"/api/lobby/{self.game.id}/exit", json={"identifier": str(uuid4())}
            )
            self.assertEqual(rsp.status_code, 404)

    def test_exit_player_not_in_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            rsp = self.client.post(
                f"/api/lobby/{self.game.id}/exit",
                json={"identifier": str(self.host.identifier)},
            )
            self.assertEqual(rsp.status_code, 404)

    def test_exit_player_in_game(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])
            self.games_repo.save(self.game)
            rsp = self.client.post(
                f"/api/lobby/{self.game.id}/exit",
                json={"identifier": str(self.players[0].identifier)},
            )
            self.assertEqual(rsp.status_code, 200)
            game = self.games_repo.get(self.game.id)
            assert game is not None
            self.assertEqual(len(game.players), 1)

    def test_exit_host(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):
            self.game.add_player(self.players[0])
            self.game.add_player(self.host)
            self.games_repo.save(self.game)
            rsp = self.client.post(
                f"/api/lobby/{self.game.id}/exit",
                json={"identifier": str(self.host.identifier)},
            )
            self.assertEqual(rsp.status_code, 200)
            game = self.games_repo.get(self.game.id)
            assert game is None

    def test_exit_player_in_game_ws(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), self.client.websocket_connect(
            f"/ws/lobby/{self.game.id}?player_id={self.players[1].id}"
        ) as ws:
            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])
            self.games_repo.save(self.game)
            rsp = self.client.post(
                f"/api/lobby/{self.game.id}/exit",
                json={"identifier": str(self.players[0].identifier)},
            )
            self.assertEqual(rsp.status_code, 200)
            message = ws.receive_json()
            self.assertIn("players", message)
            self.assertEqual(message.get("players"), [self.players[1].id])

    def test_exit_winner_in_game_ws(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), self.client.websocket_connect(
            f"/ws/lobby/{self.game.id}?player_id={self.players[1].id}"
        ) as ws:
            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])
            self.game.started = True
            self.games_repo.save(self.game)
            rsp = self.client.post(
                f"/api/lobby/{self.game.id}/exit",
                json={"identifier": str(self.players[1].identifier)},
            )

            self.assertEqual(rsp.status_code, 200)
            message = ws.receive_json()
            assert message is not None
            print(message)
            assert message["response"] == self.players[0].id

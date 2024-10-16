import unittest
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Game, Player, PlayerInfo
from repositories import GameRepository, PlayerRepository


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
            id=101010,
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

    def test_select(self):
        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ):

            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])

            player0 = self.players[0]
            player1 = self.players[1]

            # agregamos cartas en la manos de los jugadores en juego
            for idx, player in enumerate(self.game.players, start=1):
                player_info = PlayerInfo(
                    player_id=player.id,
                    turn_position=idx,
                    hand_mov=[idx + 1, idx + 2, idx + 3],
                )
                self.game.player_info[player.id] = player_info

            # conectamos ambos jugadores
            with self.client.websocket_connect(
                f"/ws/lobby/101010/select?player_id={player0.id}"
            ) as websocket0:
                with self.client.websocket_connect(
                    f"/ws/lobby/101010/select?player_id={player1.id}"
                ) as websocket1:

                    # El jugador 0 selecciona una de sus cartas
                    card0 = self.game.player_info[player0.id].hand_mov[0]
                    print("CARD0", card0)
                    print("PLAYER0", str(player0.identifier))
                    websocket0.send_json(
                        {"card_id": card0, "player_identifier": str(player0.identifier)}
                    )

                    # Comprobamos que se haya efectuado el broadcast
                    data1 = websocket0.receive_json()
                    assert data1 == {"player_id": player0.id, "card_id": card0}
                    data2 = websocket1.receive_json()
                    assert data2 == {"player_id": player0.id, "card_id": card0}

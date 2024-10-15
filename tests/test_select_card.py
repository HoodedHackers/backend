import unittest
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import FigCards, Game, Player
from repositories import FigRepository, GameRepository, PlayerRepository


class TestSelectCard(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.dbs = Database().session()
        self.games_repo = GameRepository(self.dbs)
        self.player_repo = PlayerRepository(self.dbs)
        self.fig_cards_repo = FigRepository(self.dbs)

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

        self.fig_cards = [
            FigCards(id=1, name="Card 1"),
            FigCards(id=2, name="Card 2"),
            FigCards(id=3, name="Card 3"),
        ]

        for fig_card in self.fig_cards:
            self.fig_cards_repo.save(fig_card)

    def tearDown(self):
        self.dbs.query(Game).delete()
        self.dbs.query(Player).delete()
        self.dbs.query(FigCards).delete()
        self.dbs.commit()
        self.dbs.close()

    def test_connect_from_lobby(self):

        with patch("main.game_repo", self.games_repo), patch(
            "main.player_repo", self.player_repo
        ), patch("main.card_repo", self.fig_cards_repo):

            player_id0 = self.players[0].id
            player_id1 = self.players[1].id
            card_id0 = self.fig_cards[0].id

            # Debe haber al menos dos jugadores en el juego
            self.game.add_player(self.players[0])
            self.game.add_player(self.players[1])

            # Conectamos ambos jugadores
            with self.client.websocket_connect(
                f"/ws/lobby/1?player_id={player_id0}"
            ) as websocket0:
                with self.client.websocket_connect(
                    f"/ws/lobby/1?player_id={player_id1}"
                ) as websocket1:

                    # El jugador uno usa la URL /api/lobby/{game_id}/select
                    response = self.client.put(
                        f"/api/lobby/1/select?player_id={player_id0}&card_id={card_id0}",
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data == {"status": "success"}

                    # Comprobamos que se haya efectuado el broadcast
                    data1 = websocket0.receive_json()
                    assert data1 == {
                        "player_name": self.players[0].name,
                        "player_id": player_id0,
                        "card_id": card_id0,
                        "card_name": self.fig_cards[0].name,
                    }
                    data2 = websocket1.receive_json()
                    assert data2 == {
                        "player_name": self.players[0].name,
                        "player_id": player_id0,
                        "card_id": card_id0,
                        "card_name": self.fig_cards[0].name,
                    }

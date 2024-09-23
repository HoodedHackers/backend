from fastapi.testclient import TestClient

import asserts
from unittest.mock import MagicMock
from main import get_games_repo
from pydantic import BaseModel
from model import Game, Player
from unittest.mock import AsyncMock, patch

from main import app

client = TestClient(app)


def test_borrame():
    response = client.get("/api/borrame")
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(response.json(), {"games": []})





class PlayerOutRandom(BaseModel):
    id: int
    name: str


@patch("main.GameRepository")
@patch("random.shuffle")
def test_sortear_jugadores(mock_game_repo, mock_shuffle):
    game_id = 1
    player1 = PlayerOutRandom(id=0, name="Player 1")
    player2 = PlayerOutRandom(id=1, name="Player 2")
    game = Game(
        id=game_id,
        name="ayiiiuuuudaaaa",
        players=[player1, player2],
        min_players=2,
        max_players=4,
        started=True,
        host=True,
    )

    mock_game_repo.return_value.get.return_value = game
    mock_game_repo.return_value.save = AsyncMock()

    response = client.post(f"/api/start_game?game_id={game_id}")

    print("que chuchaaaaaaaaaaaaaaaaaaaaaaaa")
    print(response.json())

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["game_id"] == game_id
    assert "players" in response_data
    assert len(response_data["players"]) == len(game.players)

    # Verifica que los jugadores han sido sorteados
    assert sorted([p.name for p in game.players]) == sorted(
        [p["name"] for p in response_data["players"]]
    )
    assert response_data["players"] != [
        {"id": p.id, "name": p.name} for p in game.players
    ]  # Verifica que el orden ha cambiado


# Prueba que maneja el caso cuando no hay suficientes jugadores
@patch("main.GameRepository")
def test_sortear_jugadores_no_sufficient_players(mock_game_repo):
    game_id = 1
    player1 = PlayerOutRandom(id=0, name="Player 1")
    game = Game(
        id=game_id,
        name="LaWea",
        players=[player1],
        min_players=2,
        max_players=4,
        started=True,
        host=True,
    )

    mock_game_repo.return_value.get.return_value = game

    response = client.post(f"/api/start_game?game_id={game_id}")

    print(response.json())

    assert response.status_code == 412
    assert response.json() == {
        "detail": "No se puede sortear jugadores si no hay suficientes jugadores"
    }


# Prueba que maneja el caso cuando no se encuentra el juego
@patch("main.GameRepository")
def test_sortear_jugadores_game_not_found(mock_game_repo):
    mock_game_repo.return_value.get.return_value = None

    response = client.post("/api/start_game", json={"game_id": 9999})
    
    print(response.json())

    assert response.status_code == 404
    assert response.json() == {"detail": "Partida no encontrada"}


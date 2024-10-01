from fastapi.testclient import TestClient

import asserts
from unittest.mock import MagicMock
from main import get_games_repo
from pydantic import BaseModel
from model import Game, Player
from unittest.mock import AsyncMock, patch

from main import app

client = TestClient(app)


class PlayerOutRandom(BaseModel):
    id: int
    name: str


@patch("main.GameRepository")
@patch("random.shuffle")
def test_sortear_jugadores(mock_game_repo, mock_shuffle):
    game_id = 1
    player1 = Player(id=0, name="Player 1")
    player2 = Player(id=1, name="Player 2")
    player3 = Player(id=2, name="Player 3")
    host_player = player1
    game = Game(
        id=game_id,
        name="ayiiiuuuudaaaa",
        players=[player1, player2, player3],
        min_players=2,
        max_players=4,
        started=True,
        host=host_player,
    )

    mock_game_repo.return_value.get.return_value = game
    mock_game_repo.return_value.save = AsyncMock()  # O MagicMock() si no es async

    response = client.post(f"/api/start_game/{game_id}, ")
    print(response)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["game_id"] == game_id
    assert "players" in response_data
    assert len(response_data["players"]) == len(game.players)

    # Verificar que el orden de los jugadores ha cambiado después del shuffle
    mock_shuffle.assert_called_once_with(game.players)
    assert [p["name"] for p in response_data["players"]] != [p.name for p in game.players]

"""""
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

    assert response.status_code == 412
    assert response.json() == {
        "detail": "No se puede sortear jugadores si no hay suficientes jugadores"
    }


@patch("main.GameRepository")
def test_sortear_jugadores_game_not_found(mock_game_repo):
    mock_game_repo.return_value.get.return_value = None

    response = client.post(f"/api/start_game?game_id=9999")
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Partida no encontrada"}
"""""
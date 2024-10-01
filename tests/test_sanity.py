from fastapi.testclient import TestClient

import asserts
from unittest.mock import MagicMock
from main import get_games_repo
from pydantic import BaseModel
from model import Game, Player
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from main import app, player_repo, game_repo
from uuid import UUID
client = TestClient(app)


def set_player_name(name: str):
    response = client.post("/api/name", json={"name": name})
    assert response.status_code == 200
    return response.json()


# crear un juego
def create_game(identifier: UUID, name: str, min_players: int, max_players: int):
    response = client.post(
        "/api/lobby",
        json={
            "identifier": identifier,
            "name": name,
            "min_players": min_players,
            "max_players": max_players,
        },
    )
    assert response.status_code == 200
    return response.json()


# unirse a un juego
def endpoint_unirse_a_partida(game_id: int, player_identifier: str):
    response = client.put(
        f"/api/lobby/{game_id}",
        json={"id_game": game_id, "identifier_player": player_identifier},
    )
    assert response.status_code == 200
    return response.json()


def start_game(game_id: int):
    response = client.put(f"/api/lobby/{game_id}/start")
    assert response.status_code == 200
    return response.json()


def test_sortear_jugadores():
    player1 = set_player_name("Player 1")
    player2 = set_player_name("Player 2")
    player3 = set_player_name("Player 3")

    # Crear el juego
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    # Unirse al juego
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    endpoint_unirse_a_partida(game["id"], player3["identifier"])

    start_game(game["id"])

    game_now = game_repo.get(game["id"])
    players_before = [player.name for player in game_now.players]

    for player in players_before:
        print(f"- {player}")

    print("Jugadores antes del sorteo:")
    for player in game_now.players:
        print(f"- {player.name} (ID: {player.identifier})")

    response = client.post(f"/api/start_game/{game['id']}")
    
    assert response.status_code == 200
    response_data = response.json()
    print("Jugadores después del sorteo:")
    """"
    players_after = [player["name"] for player in response_data["players"]]
    
    for player in players_after:
        print( player['name'])
    """
    NOW_GAME = game_repo.get(game["id"])
    players_after = [player.name for player in NOW_GAME.players]
    for player in NOW_GAME.players:
        print(f"- {player.name} (ID: {player.identifier})")

    assert response_data["game_id"] == game["id"]
    #assert response_data["players"] != players_before
     # Verificar que el orden es diferente
    #assert players_after != players_before, "El orden de los jugadores no cambió tras el sorteo"
    
    # Comprobar que hay al menos un cambio en la posición
    order_changed = any(p1 != p2 for p1, p2 in zip(players_before, players_after))
    assert order_changed, "El orden de los jugadores es el mismo después del sorteo"


"""""
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

    response = client.post(f"/api/start_game/{game_id}")
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
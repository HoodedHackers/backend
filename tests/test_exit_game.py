from fastapi.testclient import TestClient
from main import app
from uuid import uuid4
from main import game_repo
from uuid import UUID

from main import game_repo

client = TestClient(app)


def set_player_name(name: str):
    response = client.post("/api/name", json={"name": name})
    assert response.status_code == 200
    return response.json()


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


def endpoint_unirse_a_partida(game_id: int, player_identifier: str):
    response = client.put(
        f"/api/lobby/{game_id}",
        json={"id_game": game_id, "identifier_player": player_identifier},
    )
    assert response.status_code == 200
    return response.json()


def test_exit_game_not_started():
    player1 = set_player_name("Test Player")
    player2 = set_player_name("Test player 2")
    player3 = set_player_name("Test player 3")
    print(
        f"Jugadores actuales: {player1['identifier']}, {player2['identifier']}, {player3['identifier']}"
    )
    game = create_game(
        identifier=player2["identifier"], name="Test Game", min_players=2, max_players=3
    )
    print(f"Juego creado: {game['name']}")
    print(f"Jugadores actuales: {game['players']}")
    endpoint_unirse_a_partida(game["id"], player1["identifier"])
    endpoint_unirse_a_partida(game["id"], player3["identifier"])
    response4 = client.get(f"/api/lobby/{game['id']}")
    assert response4.status_code == 200
    updated_game = response4.json()
    assert len(updated_game["players"]) == 3
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player1["identifier"]}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["started"] == False
    assert len(result["players"]) == 2


def test_exit_game_not_started_host():
    player1 = set_player_name("Test Player")
    player2 = set_player_name("Test player 2")
    player3 = set_player_name("Test player 3")

    print(
        f"Jugadores actuales: {player1['identifier']}, {player2['identifier']}, {player3['identifier']}"
    )
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    print(f"Juego creado: {game['name']}")
    print(f"Jugadores actuales: {game['players']}")
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    endpoint_unirse_a_partida(game["id"], player3["identifier"])
    response4 = client.get(f"/api/lobby/{game['id']}")
    assert response4.status_code == 200
    updated_game = response4.json()
    assert len(updated_game["players"]) == 3
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player1["identifier"]}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["started"] == False
    assert len(result["players"]) == 0


def test_exit_game_not_found():
    response = client.patch("/api/lobby/9999", json={"identifier": str(uuid4())})
    assert response.status_code == 404


def test_exit_game_already_started():
    player1 = set_player_name("Test Player")
    player2 = set_player_name("Test player 2")
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    game_instance = game_repo.get(game["id"])
    assert game_instance is not None
    game_instance.started = True
    game_repo.save(game_instance)
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player1["identifier"]}
    )
    assert response.status_code == 412
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player1["identifier"]}
    )
    assert response.status_code == 412
    assert response.json()["detail"] == "Game already started"


def test_exit_game_after_lobby_deleted():
    player1 = set_player_name("Test Player")
    player2 = set_player_name("Test player 2")
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player1["identifier"]}
    )
    assert response.status_code == 200
    response = client.patch(
        f"/api/lobby/{game['id']}", json={"identifier": player2["identifier"]}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Lobby not found"

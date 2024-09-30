from fastapi.testclient import TestClient
import asserts
from main import app
import asserts
from unittest.mock import MagicMock
from fastapi import Request, Depends, HTTPException

from main import get_games_repo

from model import Game, Player
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI, HTTPException, Depends
from repositories import GameRepository, PlayerRepository
from uuid import uuid4, UUID
from repositories.player import PlayerRepository
from os import getenv
from database import Database
from main import game_repo, player_repo
from unittest.mock import Mock
import pytest
from main import PlayerOutRandom

client = TestClient(app)



# crear un jugador
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


def test_exit_game_success():
    player1 = set_player_name("Player 1")
    player2 = set_player_name("Player 2")
    player3 = set_player_name("Player 3")

    # Crear el juego
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    print(game['name'])
    # Unirse al juego
    endpoint_unirse_a_partida(game["id"], player2["identifier"])
    endpoint_unirse_a_partida(game['id'], player3["identifier"])   

    start_game(game['id'])
    print("Jugadores antes de salir:", game['players'])

    # El jugador sale de la partida
    response = client.patch(
        f"/api/lobby/salir/{game['id']}",
        json={"identifier": player2["identifier"]}
    )
    
    assert response.status_code == 200
    result = response.json()

    assert result["game_id"] == game["id"]
    assert len(result["players"]) == 2 

    # Verificar estado del juego
    assert result["activo"] == True  # Asegúrate de que el estado sea correcto
    # Verificar que el jugador que salió ya no está
    assert player2["identifier"] not in [player["identifier"] for player in result["players"]]

    # Verificar que el jugador que queda es el correcto
    remaining_players = [player["identifier"] for player in result["players"]]
    assert len(remaining_players) == 2
    assert player1["identifier"] in remaining_players


def test_exit_game_not_started():
    player1 = set_player_name("Player 1")
    player2 = set_player_name("Player 2")

    # Crear el juego
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    
    endpoint_unirse_a_partida(game["id"], player1["identifier"])
    endpoint_unirse_a_partida(game["id"], player2["identifier"])

    # Intentar salir antes de iniciar el juego
    response = client.patch(
        f"/api/lobby/salir/{game['id']}",
        json={"identifier": player1["identifier"]}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "El juego no empezo"


def test_exit_game_not_found():
    exit_request = {"identifier": str(uuid4())}  # UUID aleatorio

    response = client.patch(
        "/api/lobby/salir/9999",  # ID de juego que no existe
        json=exit_request
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Partida no encontrada"

def test_exit_game_min_players():
    player1 = set_player_name("Player 1")
    player2 = set_player_name("Player 2")

    # Crear el juego con un mínimo de 2 jugadores
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    
    endpoint_unirse_a_partida(game["id"], player1["identifier"])
    endpoint_unirse_a_partida(game["id"], player2["identifier"])

    # Iniciar el juego
    start_game(game["id"])

    # El jugador 1 sale de la partida
    response = client.patch(
        f"/api/lobby/salir/{game['id']}",
        json={"identifier": player1["identifier"]}
    )

    # Ahora deberíamos tener solo un jugador (jugador 2)
    assert response.status_code == 400
    assert response.json()["detail"] == "numero de jugadores menor al esperado"


def test_exit_game_player_not_in_game():
    player1 = set_player_name("Player 1")
    player2 = set_player_name("Player 2")

    # Crear el juego
    game = create_game(
        identifier=player1["identifier"], name="Test Game", min_players=2, max_players=3
    )
    
    endpoint_unirse_a_partida(game["id"], player1["identifier"])

    # Intentar salir con un jugador que no está en el juego
    response = client.patch(
        f"/api/lobby/salir/{game['id']}",
        json={"identifier": player2["identifier"]}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "El jugador no existe"


from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest
from main import app  # Asegúrate de que la aplicación esté correctamente importada

# Crear un cliente de pruebas
client = TestClient(app)

# Datos simulados para la respuesta del repositorio
data_out = {
    "id": 1,
    "max_players": 4,
    "started": False,
    "name": "Game of Thrones",
    "current_player_turn": 0,
    "min_players": 2
}

def test_get_game():
    with patch("repositories.game.GameRepository.get") as mock_get:
        mock_get.return_value = data_out
        response = client.get("/api/lobby/1")
        assert response.status_code == 200
        assert response.json() == data_out
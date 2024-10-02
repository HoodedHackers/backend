from fastapi.testclient import TestClient
from unittest.mock import patch
from services.connection_manager import LobbyConnectionHandler
import pytest
import asyncio

from main import app
from model import Player

client = TestClient(app)

player_mock = Player(name="Matias", identifier="805423e9-30e3-4e9c-9745-6d3deb5d478d")


@pytest.mark.asyncio
async def test_connect_from_lobby(mocker):

    mocker.patch(
        "repositories.player.PlayerRepository.get_by_identifier",
        return_value=player_mock,
    )
    with client.websocket_connect("/ws/lobby/1010") as websocket:

        message_connect = {
            "user_identifier": "805423e9-30e3-4e9c-9745-6d3deb5d478d",
            "action": "connect",
        }

        message_disconnect = {
            "user_identifier": "805423e9-30e3-4e9c-9745-6d3deb5d478d",
            "action": "disconnect",
        }

        websocket.send_json(message_connect)

        await asyncio.sleep(0.5)

        response = websocket.receive_json()
        assert response == {"user_name": "Matias", "action": "connect"}

        websocket.send_json(message_disconnect)

        await asyncio.sleep(0.5)

        response = websocket.receive_json()
        assert response == {"user_name": "Matias", "action": "disconnect"}

        websocket.close()

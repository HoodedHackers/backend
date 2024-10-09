import asyncio
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from services.counter import Counter

client = TestClient(app)


@pytest.mark.asyncio
async def test_timer_start_websocket(mocker):
    mock_counter = Counter()
    mock_counter.set_timeout(1)

    mocker.patch("services.counter.Counter", return_value=mock_counter)
    with client.websocket_connect("/ws/timer") as websocket:

        message = {"action": "start"}
        websocket.send_json(message)

        await asyncio.sleep(0.5)

        response = websocket.receive_json()
        assert response == {"message": "Timeout"}
        assert mock_counter.running == False


@pytest.mark.asyncio
async def test_timer_stop_websocket(mocker):
    mock_counter = Counter()
    mock_counter.set_timeout(1)

    mocker.patch("services.counter.Counter", return_value=mock_counter)
    with client.websocket_connect("/ws/timer") as websocket:

        message = {"action": "start"}
        websocket.send_json(message)

        await asyncio.sleep(0.5)

        message = {"action": "stop"}
        websocket.send_json(message)

        response = websocket.receive_json()
        assert response == {"message": "Timer stopped"}
        assert mock_counter.running == False


@pytest.mark.asyncio
async def test_timer_unknown_action_websocket(mocker):
    mock_counter = Counter()
    mock_counter.set_timeout(1)

    mocker.patch("services.counter.Counter", return_value=mock_counter)
    with client.websocket_connect("/ws/timer") as websocket:

        message = {"action": "unknown"}
        websocket.send_json(message)

        response = websocket.receive_json()
        assert response == {"error": "Unknown action"}
        assert mock_counter.running == False

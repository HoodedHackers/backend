from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID
import pytest
import asserts
from database import Database
from model import Player
from main import app

client = TestClient(app)


@patch("main.uuid4")
def test_set_name(mocked_uuid):
    value = uuid4()
    mocked_uuid.return_value = value
    response = client.post("/api/name", json={"name": "Alice"})
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(response.json(), {"name": "Alice", "identifier": str(value)})

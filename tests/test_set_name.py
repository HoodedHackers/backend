from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import asserts
import pytest
from fastapi.testclient import TestClient

from database import Database
from main import app
from model import Player

client = TestClient(app)


def test_set_name():
    response = client.post("/api/name", json={"name": "Alice"})
    asserts.assert_equal(response.status_code, 200)
    values = response.json()
    asserts.assert_in("name", values)
    assert values["name"] == "Alice"
    asserts.assert_in("identifier", values)
    asserts.assert_in("id", values)

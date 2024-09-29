from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from uuid import uuid1, UUID
import pytest
import asserts
from database import Database
from model import Player
from main import app

client = TestClient(app)

db = Database()
db.create_tables()
Session = db.get_session()


@patch("main.uuid4")
def test_set_name(mocked_uuid):
    value = uuid1(32, 100)
    mocked_uuid.return_value = value
    response = client.post("/api/name", json={"name": "Alice"})
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(
        response.json(), {"name": "Alice", "identifier": str(value)}
    )  # POR QUE ES UN STRING?

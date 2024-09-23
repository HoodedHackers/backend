from fastapi.testclient import TestClient

import asserts

from main import app

client = TestClient(app)


def test_borrame():
    response = client.post("/api/name", json={"name": "pepe"})
    asserts.assert_equal(response.status_code, 200)
    rsp = response.json()
    asserts.assert_equal(rsp["name"], "pepe")

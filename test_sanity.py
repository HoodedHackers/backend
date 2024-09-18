from fastapi.testclient import TestClient
import asserts

from main import app, db

client = TestClient(app)


def test_borrame():
    db.create_tables()
    response = client.get("/api/borrame")
    asserts.assert_equal(response.status_code, 200)
    asserts.assert_equal(response.json(), {"players": []})

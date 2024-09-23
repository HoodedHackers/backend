from fastapi.testclient import TestClient

import asserts

from main import app

client = TestClient(app)


# def test_borrame():
#     response = client.get("/api/borrame")
#     asserts.assert_equal(response.status_code, 200)
#     asserts.assert_equal(response.json(), {"games": []})

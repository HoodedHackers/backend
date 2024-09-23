from fastapi.testclient import TestClient

import asserts

from main import app

client = TestClient(app)

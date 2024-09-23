from fastapi.testclient import TestClient

import asserts

from main import app

client = TestClient(app)

def test_estado_codigo():
    response = client.get("/api/lobby")
    assert response.status_code == 200

def test_partidas_disponibles():
    response = client.get("/api/lobby")
    date = response.json()
    for party in date:
        assert party['started'] == False
        assert len(party['players']) < party['max_players']

def test_orden_cantidad_jugadores():
    response = client.get("/api/lobby")
    data = response.json()

    players_count = [len(lobby['players']) for lobby in data]
    
    assert players_count == sorted(players_count)
    

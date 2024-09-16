from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_crear_partida():
    response = client.post("/", json={"nombre": "partida1", "max_jugadores": 4, "min_jugadores": 2})
    assert response.status_code == 200
    assert response.json() == {"id": 0, "nombre": "partida1", "max_jugadores": 4, "min_jugadores": 2, "jugadores": [], "host": "partida1"}

def test_crear_partida_error():
    response = client.post("/", json={"nombre": "partida1", "max_jugadores": 4, "min_jugadores": 5})
    assert response.status_code == 412
    assert response.json() == {"detail": "El número mínimo de jugadores no puede ser mayor al máximo"}
    

def test_crear_partida_error2():
    response = client.post("/", json={"nombre": "partida1", "max_jugadores": 4, "min_jugadores": 4})
    assert response.status_code == 412
    assert response.json() == {"detail": "El número mínimo de jugadores no puede ser igual al máximo"}

def test_crear_partida_error3():
    response = client.post("/", json={"nombre": "partida1", "max_jugadores": 4, "min_jugadores": 1})
    assert response.status_code == 412
    assert response.json() == {"detail": "El número de jugadores debe ser entre 2 y 4"}

def test_crear_partida_error4():
    response = client.post("/", json={"nombre": "", "max_jugadores": 4, "min_jugadores": 2})
    assert response.status_code == 412
    assert response.json() == {"detail": "No se permiten campos vacíos"}

def test_crear_partida_error5():
    response = client.post("/", json={"nombre": '', "max_jugadores": None, "min_jugadores": None})
    assert response.status_code == 422  # El código esperado es 422
    

from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch


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
    


"""Preguntar"""
'''
def test_salir_partida_error():
    response = client.post("/", json={"id_jugador": "adbcsbdc", "id_partida": "jznciwn"} )
    assert response.status_code = 
'''

        
"""
from random import random


def get_a_random_number_well_formatted():
    now = random()
    message = f"El número exacto es {now:.4f}!!!"
    return message


if __name__ == '__main__':
    msg = get_a_random_number_well_formatted()
    print(msg)
"""






'''tests  sortear_posicion_de_jugador'''

@patch("main.random.shuffle")
def test_sortear_posicion_de_jugador(mocked_shuffle):
    partidas = {
        "partida_1": {
            "jugadores": {
                "jugador_1": {"nombre": "Alice", "host": True, "en_partida": True},
                "jugador_2": {"nombre": "Bob", "host": False, "en_partida": True},
                "jugador_3": {"nombre": "Charlie", "host": False, "en_partida": True},
            }
        }
    }
       
    '''lambda x: x se utiliza como una simulación de la función shuffle para que no modifique el orden de los elementos'''
    mocked_shuffle.side_effect = lambda x: x
         # Simulamos una petición POST al endpoint
    response = client.post("/partida/partida_1/jugador")
    assert response.status_code == 200
    assert response.json() == {"partida": "partida_1", "jugadores_sorteados": {"jugador_1": {"nombre": "Alice", "host": True, "en_partida": True}, "jugador_2": {"nombre": "Bob", "host": False, "en_partida": True}, "jugador_3": {"nombre": "Charlie", "host": False, "en_partida": True}}}

def test_sortear_posicion_de_jugador_partida_no_existente()
    response = client.post("/partida/partida_2/jugador")
    assert response.status_code == 404
    assert response.json() == {"detail": "La partida no existe"}

def test_sortear_posicion_partida_sin_jugadores():
    partidas = {
        "partida_1": {
            "jugadores": {}
        }
    }
    response = client.post("/partida/partida_1/jugador")
    assert response.status_code == 404
    assert response.json() == {"detail": "No hay jugadores en la partida"}

def test_sortear_posicion_partida_sin_jugadores():
    partidas = {
        "partida_1": {
            "jugadores": {}
            }
    }
    response = client.post("/partida/partida_1/jugador")
    assert response.status_code == 200
    assert response.json() == {"jugadores": {}}


"""ver que si hay un solo jugador no reliace el shuffle"""
@patch("main.random.shuffle")
def test_sortear_posicion_un_jugador(mocked_shuffle):
    # Creamos una partida con solo un jugador
    partidas["partida_3"] = {
        "jugadores": {
            "jugador_1": {"nombre": "Alice", "host": True, "en_partida": True}
        }
    }

    # Simulamos una petición POST al endpoint
    response = client.post("/partida/partida_3/jugador")

    # Verificamos que no se haya llamado a shuffle
    mocked_shuffle.assert_not_called()
    
    # Verificamos que la respuesta sea correcta
    assert response.status_code == 200
    assert response.json() == {
        "jugadores": {
            "jugador_1": {"nombre": "Alice", "host": True, "en_partida": True}
        }
    }


@patch("main.random.shuffle")
def test_sortear_posicion_jugadores_shuffled(mocked_shuffle):
    # Mockeamos el comportamiento de shuffle para que invierta el orden
    mocked_shuffle.side_effect = lambda jugadores: jugadores.reverse()
    
    partidas["partida_4"] = {
        "jugadores": {
            "jugador_1": {"nombre": "Alice", "host": True, "en_partida": True},
            "jugador_2": {"nombre": "Bob", "host": False, "en_partida": True},
            "jugador_3": {"nombre": "Charlie", "host": False, "en_partida": True},
        }
    }

    response = client.post("/partida/partida_4/jugador")
    
    assert response.status_code == 200
    
    # Verificamos que el orden se haya invertido (simulado)
    assert response.json() == {
        "jugadores": {
            "jugador_1": {"nombre": "Charlie", "host": False, "en_partida": True},
            "jugador_2": {"nombre": "Bob", "host": False, "en_partida": True},
            "jugador_3": {"nombre": "Alice", "host": True, "en_partida": True}
        }
    }


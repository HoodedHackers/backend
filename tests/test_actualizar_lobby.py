from fastapi.testclient import TestClient
import signal

from main import app

client = TestClient(app)


def test_conectar_y_desconectar():
    '''Los jugadores reciben notificaciones cuando alguien se conecta o se desconecta.'''
    with TestClient(app) as client:
        with client.websocket_connect("/ws/lobby/1") as clientws1:
            with client.websocket_connect("/ws/lobby/1") as clientws2:
                
                data1 = clientws1.receive_text()
                assert data1 == "Un nuevo jugador ha ingresado al lobby 1."
                data2 = clientws2.receive_text()
                assert data2 == "Un nuevo jugador ha ingresado al lobby 1."
                
                # El jugador 1 se desconecta y los demás jugadores deben recibir una notificación
                clientws1.close()
                data3 = clientws2.receive_text()
                assert data3 == "Un jugador ha abandonado el lobby 1."

def handler(signum, frame):
    '''Manejador de señales para el timeout'''
    raise TimeoutError("El tiempo de espera ha sido excedido")

def receive_text_with_timeout(ws, timeout=1):
    '''Recibir un mensaje de texto de un WebSocket con un timeout'''
    # Configurar la señal para que lance el manejador después del timeout
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    
    try:
        data = ws.receive_text()
        signal.alarm(0)  # Desactivar la alarma si se completa antes del timeout
        return data
    except TimeoutError as e:
        print(e)
        return None

def test_broadcast():
    '''Los jugadores no deben recibir notificaciones si no están en el mismo lobby.'''
    client = TestClient(app)

    with client.websocket_connect("/ws/lobby/1") as clientws1:
        # Ignorar el primer mensaje de conexión
        _ = clientws1.receive_text()

        with client.websocket_connect("/ws/lobby/2") as clientws2:
            
            data = receive_text_with_timeout(clientws1)
            assert data is None
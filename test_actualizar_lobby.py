from fastapi.testclient import TestClient
import signal

from actualizar_lobby import app

client = TestClient(app)

# ------ TEST 1 ------ #
# Los jugadores reciben notificaciones cuando alguien se conecta o se
# desconecta.

def test_conectar_y_desconectar():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/lobby/1") as clientws1:
            with client.websocket_connect("/ws/lobby/1") as clientws2:
                # El jugador 1 se conecta
                data1 = clientws1.receive_text()
                assert data1 == "Un nuevo jugador ha ingresado al lobby 1."
                
                # El jugador 2 se conecta
                data2 = clientws2.receive_text()
                assert data2 == "Un nuevo jugador ha ingresado al lobby 1."
                
                # El jugador 1 se desconecta
                clientws1.close()
                data3 = clientws2.receive_text()
                assert data3 == "Un jugador ha abandonado el lobby 1."

# ------ TEST 2 ------ #
# Los mensajes de un lobby no se envían a los jugadores de otro lobby.

# Manejador de timeout
def handler(signum, frame):
    raise TimeoutError("El tiempo de espera ha sido excedido")

def receive_text_with_timeout(ws, timeout=1):
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
    client = TestClient(app)

    with client.websocket_connect("/ws/lobby/1") as clientws1:
        # Ignorar el primer mensaje de conexión
        _ = clientws1.receive_text()

        with client.websocket_connect("/ws/lobby/2") as clientws2:
            
            data = receive_text_with_timeout(clientws1)
            assert data is None
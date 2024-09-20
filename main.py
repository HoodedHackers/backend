from fastapi import FastAPI, HTTPException, WebSocket, Form
from pydantic import BaseModel
#import uuid
#from uuid import UUID
#from uuid import uuid4
import random


#crear partida

app = FastAPI()
#algo provisional para almacenar las partidas
partidas = {}
contador_id = 0

#es lo que responde el back al front
class PartidaOut(BaseModel):
    id: int
    nombre: str
    max_jugadores: int
    min_jugadores: int
    jugadores: list
    #host

class PartidaIn(BaseModel):
    nombre: str
    max_jugadores: int
    min_jugadores: int
   # host

class Partida(BaseModel):
    id_partida: int
    nombre: str
    jugadores: list
    turno: int

class Jugador(BaseModel):
    id_jugador: int
    nombre: str
    host: bool = False 
    en_partida: bool = False
    
"""
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""



@app.post('/', response_model=PartidaOut)
async def crear_partida(partida: PartidaIn, jugador: Jugador):
    global contador_id

    nombre = partida.nombre
    max_jugadores = partida.max_jugadores
    min_jugadores = partida.min_jugadores

    if min_jugadores < 2 or max_jugadores > 4:
        raise HTTPException(status_code=412, detail="El número de jugadores debe ser entre 2 y 4")
    elif min_jugadores > max_jugadores:
        raise HTTPException(status_code=412, detail="El número mínimo de jugadores no puede ser mayor al máximo")
    elif min_jugadores == max_jugadores:
        raise HTTPException(status_code=412, detail="El número mínimo de jugadores no puede ser igual al máximo")
    elif nombre == "" or min_jugadores == "" or max_jugadores == "":
        raise HTTPException(status_code=412, detail="No se permiten campos vacíos")
    elif nombre == None and min_jugadores == None and max_jugadores == None:
        raise HTTPException(status_code=422, detail="No se permiten campos vacíos")
    elif len(partida.nombre) > 64 or len(partida.max_jugadores)>64 or len(partida.min_jugadores) > 64:
        raise HTTPException(status_code=412, detail="El número de caracteres no puede ser mayor a 64")
    
    jugador.host = True
    jugador.en_partida = True

    nueva_partida = PartidaOut(id= random.randint(1000, 9999), nombre=nombre, max_jugadores=max_jugadores, min_jugadores=min_jugadores, jugadores=[])
    
    """esto se borra"""
    partidas[contador_id] = nueva_partida
    """esto se borra"""
    contador_id += 1
    return nueva_partida

"""# Validaciones

Verificar si nombre no está vacío: Asegúrate de que el nombre no sea una cadena vacía.
if not nombre or not isinstance(nombre, str) or len(nombre) == 0:
    raise HTTPException(status_code=412, detail="El nombre no puede estar vacío")

    para ver que los valores ingresados son enteros
if not isinstance(min_jugadores, int) or not isinstance(max_jugadores, int):
    raise HTTPException(status_code=412, detail="Los jugadores deben ser enteros")
if min_jugadores < 2 or max_jugadores > 4:
    raise HTTPException(status_code=412, detail="El número de jugadores debe ser entre 2 y 4")
elif min_jugadores > max_jugadores:
    raise HTTPException(status_code=412, detail="El número mínimo de jugadores no puede ser mayor al máximo")
elif min_jugadores == max_jugadores:
    raise HTTPException(status_code=412, detail="El número mínimo de jugadores no puede ser igual al máximo")
"""



#uvicorn main:app --reload
#crear endpoint de sali de partida

# Simular una "base de datos" en memoria con UUID como string
partidas = {

    str(uuid.uuid4()): {
        "id_partida": str(uuid.uuid4()),
        "jugadores": {
            "jugador_1": {"nombre": "Alice", "host": True, "en_partida": True},
            "jugador_2": {"nombre": "Bob", "host": False, "en_partida": True},
            "jugador_3": {"nombre": "Charlie", "host": False, "en_partida": True}
        }
    },
    str(uuid.uuid4()): {
        "id_partida": str(uuid.uuid4()),
        "jugadores": {
            "jugador_4": {"nombre": "Dave", "host": True, "en_partida": True},
            "jugador_5": {"nombre": "Eve", "host": False, "en_partida": True}
        }
    }
}
#sortear posicion de los jugadores, funca bien
@app.post('/partida/{id_partida}/jugador')
async def sortear_posicion_de_jugador(id_partida: str):
    if id_partida not in partidas:
        raise HTTPException(status_code=404, detail= "la partida no existe")
    else:
        #sortear posicion de los jugadores
        #cant_jugadores = len(partidas[id_partida]["jugadores"])
        #busco sortear a estos jugadores
            # Extraer jugadores del diccionario
        jugadores = list(partidas[id_partida]["jugadores"].items())  # items() devuelve pares (clave, valor)

        random.shuffle(jugadores)

        # Reasignar los jugadores sorteados al diccionario manteniendo las claves originales
        partidas[id_partida]["jugadores"] = {f"jugador_{i+1}": jugador[1] for i, jugador in enumerate(jugadores)}
    #cambiar
    return { partidas[id_partida]["jugadores"]}


# Simular una "base de datos" en memoria con UUID como string
@app.delete('/partida/{id_partida}')

#existira una base de datos, hasta entonces simulo que partidas esta en mi base de datos
async def salir_partida(id_jugador: str , id_partida: str):
    #simulo que partidas es la base de datos
    if id_partida not in partidas:
        raise HTTPException(status_code=404, detail= "la partida no existe")
    elif id_jugador not in partidas["jugadores"]:
        raise HTTPException(status_code=404, detail= "el jugador no existe")
    elif id_partida in partidas and len(partida.jugadores) > 2: 
        """
        busco en la base de datos el id del jugador y reseteo su estado
        tambien busco la base de datos la partida del jugador y la actualizo
        """
    elif id_partida in partidas and len(partida.jugadores) == 2 :
         """
        busco en la base de datos el id del jugador y reseteo su estado
        tambien busco la base de datos la partida del jugador y la reseteo 
        """


@app.post('/partida/{id_partida}/jugador')
async def desbloquear_partida_no_iniciada(id_partida: str):


    


"""

#Borrar luego, es lo que me envia el front
class PartidaIn(BaseModel):
    nombre: str
    password: str
    max_jugadores: int
    min_jugadores: int
   # host

    def validar_num_jugador(self):
        if self.min_jugadores < 2 or self.max_jugadores > 4:
            raise HTTPException(status_code=412, detail="El número de jugadores debe ser entre 2 y 4")




@app.post('/', response_model=PartidaOut)
async def crear_partida(websocket:WebSocket, form: PartidaIn):  
    #crear partida
    if PartidaIn.min_jugadores < 2 or PartidaIn.max_jugadores > 4:
        #return {"Error": "El número de jugadores debe ser entre 2 y 4"}
        raise HTTPException(status_code=412, detail="El número de jugadores debe ser entre 2 y 4")
    else:
        #return {"Partida": partida.nombre, "Creada": "Exitosamente"}
        try:
             PartidaIn.validar_num_jugador()
             nueva_partida = PartidaOut(id=1, nombre=PartidaIn.nombre, max_jugadores=partida.max_jugadores, min_jugadores=partida.min_jugadores, jugadores=[], host=partida.nombre)

        except HTTPException as e:
            raise HTTPException(status_code=412, detail=str(e))
"""

from fastapi import FastAPI, HTTPException, WebSocket, Form
from pydantic import BaseModel
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
    host: str
    #host

class PartidaIn(BaseModel):
    nombre: str
    max_jugadores: int
    min_jugadores: int
   # host

@app.post('/', response_model=PartidaOut)
async def crear_partida(partida: PartidaIn):
    global contador_id
    nombre = partida.nombre
    max_jugadores = partida.max_jugadores
    min_jugadores = partida.min_jugadores

    if min_jugadores < 2 or max_jugadores > 4:
        raise HTTPException(status_code=412, detail="El número de jugadores debe ser entre 2 y 4")
    if min_jugadores > max_jugadores:
        raise HTTPException(status_code=412, detail="El número mínimo de jugadores no puede ser mayor al máximo")
    if min_jugadores == max_jugadores:
        raise HTTPException(status_code=412, detail="El número mínimo de jugadores no puede ser igual al máximo")
    if nombre == "" or min_jugadores == "" or max_jugadores == "":
        raise HTTPException(status_code=412, detail="No se permiten campos vacíos")
    if nombre == None and min_jugadores == None and max_jugadores == None:
        raise HTTPException(status_code=422, detail="No se permiten campos vacíos")
    nueva_partida = PartidaOut(id=contador_id, nombre=nombre, max_jugadores=max_jugadores, min_jugadores=min_jugadores, jugadores=[], host=nombre)

    partidas[contador_id] = nueva_partida
    contador_id += 1
    return nueva_partida

#uvicorn main:app --reload

"""""

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
"""""

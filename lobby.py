from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

partidas = [
    {
        "id": 1,
        "name": "Partida 1",
        "max_players": 4,
        "min_players": 2,
        "started": False,
        "players": [{"name": "Ema"}, {"name": "Cami"}, {"name": "Lou"}]
    },
    {
        "id": 2,
        "name": "Partida 2",
        "max_players": 4,
        "min_players": 2,
        "started": False,
        "players": [{"name": "Andy"}, {"name": "Lou^2"}]
    },
    {
        "id": 3,
        "name": "Partida 3 (Llena)",
        "max_players": 2,
        "min_players": 2,
        "started": True,
        "players": [{"name": "Mati"}, {"name": "Cami"}]
    }
]

class Jugador(BaseModel):
    name: str

class Lobby(BaseModel):
    id: int
    name: str
    max_players: int
    min_players: int
    started: bool
    players: List[Jugador]

@app.get("/api/lobby", response_model=List[Lobby])
def listar_partidas():

    available_lobbies = [lobby for lobby in partidas if not lobby['started']
                        and len(lobby['players']) < lobby['max_players']]
    
    sorted_lobbies = sorted(available_lobbies, key=lambda x: len(x['players']))

    return sorted_lobbies
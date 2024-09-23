from os import getenv
from fastapi import FastAPI, Response, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Database
from repositories import GameRepository, PlayerRepository
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

db_uri = getenv("DB_URI")
if db_uri is not None:
    db = Database(db_uri=db_uri)
else:
    db = Database()
db.create_tables()
hola = db.session()
app = FastAPI()

game_repo = GameRepository(hola)
player_repo = PlayerRepository(hola)


@app.middleware("http")
async def add_game_repo_to_request(request: Request, call_next):
    request.state.game_repo = game_repo
    request.state.player_repo = player_repo 
    response = await call_next(request)
    return response


def get_games_repo(request: Request) -> GameRepository:
    return request.state.game_repo

def get_player_repo(request: Request) -> PlayerRepository:
    return request.state.player_repo

class req_in(BaseModel):  
    id_game: int
    id_player: int

@app.put("/api/lobby/{id_game}")
async def endpoint_unirse_a_partida(
    req: req_in, 
    games_repo: GameRepository= Depends(get_games_repo), 
    player_repo: PlayerRepository = Depends(get_player_repo)
    ):
    selec_player = player_repo.get(req.id_player)
    selec_game = games_repo.get(req.id_game)
    if selec_player is None or selec_game is None:
        raise HTTPException(status_code=404, detail="xd")
    selec_game.add_player(selec_player)
    games_repo.save(selec_game)
    return jsonable_encoder(selec_game)

        
    
    

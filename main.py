from os import getenv
from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy.orm import Session
from database import Database
from repositories import GameRepository, PlayerRepository
from unirse_a_partida import req_in, unirse_partida

db_uri = getenv("DB_URI")
if db_uri is not None:
    db = Database(db_uri=db_uri)
else:
    db = Database()
db.create_tables()
app = FastAPI()
game_repo = GameRepository(db.session())


@app.middleware("http")
async def add_game_repo_to_request(request: Request, call_next):
    request.state.game_repo = game_repo
    response = await call_next(request)
    return response


def get_games_repo(request: Request) -> GameRepository:
    return request.state.game_repo

def get_player_repo(request: Request) -> PlayerRepository:
    return request.state.player_repo


@app.put("/api/lobby7{id_game}")
async def endpoint_unirse_a_partida(
    req: req_in, 
    games_repo: GameRepository= Depends(get_games_repo), 
    player_repo: PlayerRepository = Depends(get_player_repo)
    ):
    selec_player = player_repo.get(req.id_player)
    selec_game = games_repo.get(req.id_game)
    return unirse_partida(req, selec_game, selec_player)
    

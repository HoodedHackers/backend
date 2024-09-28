from os import getenv
from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict

from uuid import UUID, uuid4
from database import Database
from repositories import GameRepository, PlayerRepository, FigRepository
from create_cards import create_all_figs

db_uri = getenv("DB_URI")
if db_uri is not None:
    db = Database(db_uri=db_uri)
else:
    db = Database()

db.create_tables()

app = FastAPI()
game_repo = GameRepository(db.session())
card_repo = FigRepository(db.session())


create_all_figs(card_repo)


@app.middleware("http")
async def add_game_repo_to_request(request: Request, call_next):
    request.state.game_repo = game_repo
    request.state.card_repo = card_repo
    response = await call_next(request)
    return response


def get_games_repo(request: Request) -> GameRepository:
    return request.state.game_repo


def get_card_repo(request: Request) -> FigRepository:
    return request.state.card_repo


# endpoing juguete, borralo cuando haya uno de verdad
@app.get("/api/borrame")
async def borrame(games_repo: GameRepository = Depends(get_games_repo)):
    games = games_repo.get_many(10)
    return {"games": games}


class GameIn(BaseModel):
    game_id: int
    players: List[str]


class CardsFigOut(BaseModel):
    card_id: int
    card_name: str


class PlayerOut(BaseModel):
    player: str
    cards_out: List[CardsFigOut]


class SetCardsResponse(BaseModel):
    all_cards: List[PlayerOut]


@app.post("/api/partida/en_curso", response_model=SetCardsResponse)
async def repartir_cartas_figura(
    req: GameIn, card_repo: FigRepository = Depends(get_card_repo)
):
    all_cards = []
    for player in req.players:
        cards = card_repo.get_many(3)
        new_cards = []
        for card in cards:
            new_card = CardsFigOut(card_id=card.id, card_name=card.name)
            new_cards.append(new_card)
        new_dic = PlayerOut(player=player, cards_out=new_cards)
        all_cards.append(new_dic)
    return SetCardsResponse(all_cards=all_cards)

from typing import Optional, List
from repositories.general import Repository
from model import MoveCards
from sqlalchemy import func


class CardsMovRepository(Repository):

    def save(self, mov_cards: MoveCards):
        self.db.add(mov_cards)
        self.db.commit()

    def delete(self, mov_cards: MoveCards):
        self.db.delete(mov_cards)
        self.db.commit()

    def get(self, id: int) -> Optional[MoveCards]:
        return self.db.get(MoveCards, id)

    def get_many(self, count: int) -> List[MoveCards]:
        return self.db.query(MoveCards).order_by(func.random()).limit(count).all()

from typing import List, Optional

from sqlalchemy import func

from model import BUNDLE_MOV, MoveCards, all_dist
from repositories.general import Repository


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


# Esta funcion creara solo un numero limitado de cartas para el primer sprint, pero deberia escalar
def create_all_mov(card_repo: CardsMovRepository):
    for i in range(BUNDLE_MOV):
        for key in all_dist:
            new_mov = MoveCards(id=(key + (i * BUNDLE_MOV)), dist=all_dist[key])
            card_repo.save(new_mov)

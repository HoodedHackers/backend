from typing import List, Optional

from sqlalchemy import func

from model import FigCards, all_coord
from repositories.general import Repository


class FigRepository(Repository):

    def save(self, figCards: FigCards):
        self.db.add(figCards)
        self.db.commit()

    def delete(self, figCards: FigCards):
        self.db.delete(figCards)
        self.db.commit()

    def get(self, id: int) -> Optional[FigCards]:
        return self.db.get(FigCards, id)

    def get_many(self, count: int) -> List[FigCards]:
        return self.db.query(FigCards).order_by(func.random()).limit(count).all()


def create_all_figs(card_repo: FigRepository):
    for i in range(1, len(all_coord)+1):
        c = 1 if len(all_coord[i]) == 4 else 0
        new_card = FigCards(id=i, coord=all_coord[i], color=c)
        card_repo.save(new_card)

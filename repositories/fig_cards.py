import random
from typing import List, Optional

from sqlalchemy import func

from model import BLUE_COORD, TOTAL_FIG_CARDS, FigCards, all_coord
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

    def get_many(self, count: int, figs: List[int]) -> List[FigCards]:
        hand = []
        for i in range(count):
            card = self.get(random.choice(figs))
            if card is None:
                raise Exception("exploto")
            hand.append(card)
        return hand


def create_all_figs(card_repo: FigRepository):
    for i in range(1, TOTAL_FIG_CARDS + 1):
        c = 1 if len(all_coord[i]) == BLUE_COORD else 0
        new_card = FigCards(id=i, coord=all_coord[i], color=c)
        card_repo.save(new_card)

from typing import Optional, List

from model import FigCards
from repositories.general import Repository
from sqlalchemy import func


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

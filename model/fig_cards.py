from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import Integer, String
from typing import List
from database import Base
from sqlalchemy.types import VARCHAR, TypeDecorator
from repositories import FigRepository
from main import session

repo = FigRepository(session)
class FigCards(Base):
    __tablename__ = "figCards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))

class HandType(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value: List[FigCards] | None, dialect):
        if value is None:
            return None
        return "".join(f"{c.id}" for c in value)
    
    def process_result_value(self, value, dialect) -> List[FigCards]:
        cards = []
        if value is None:
            return cards
        for c in value:
            c = int(c)
            card = repo.get(c)
            if card is None:
                continue
            cards.append(card)
        return cards
    
class Hand(Base):
    __tablename__ = "figHand"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cards = relationship("FigCards")
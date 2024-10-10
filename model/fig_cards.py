from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import Integer, String
from typing import List
from database import Base
from sqlalchemy.types import VARCHAR, TypeDecorator

class CoordType(TypeDecorator):

    impl = VARCHAR

    def process_bind_param(self, value: List[tuple[int, int]] | None, dialect):
        if value is None:
            return None
        return ','.join(f'({x}, {y})' for x, y in value)

    def process_result_value(self, value, dialect) -> List[tuple[int, int]]:
        if not value:
            return []
        tuples = value.split('),(')
        coord= []
        for item in tuples:
            item = item.strip('() ')
            x, y = map(int, item.split(','))
            coord.append((x, y))
        return coord

class FigCards(Base):
    __tablename__ = "figCards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coord: Mapped[List[tuple[int, int]]] = mapped_column(CoordType)
    color: Mapped[int] = mapped_column(Integer)

all_coord = {
    1: [(0,0), (1,0), (2,0), (1,1), (1,2)],
    2: [(0,0), (0,1), (1,1), (1,2), (1,3)],
    3: [(1,0), (1,1), (1,2), (0,2), (0,3)],
}


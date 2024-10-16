from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import VARCHAR, Integer, String, TypeDecorator

from database import Base

TOTAL_FIG_CARDS = 25
AVERAGE_COORD = 5
BLUE_COORD = 4
TOTAL_HAND_FIG = 3


class CoordType(TypeDecorator):

    impl = VARCHAR

    def process_bind_param(self, value: List[tuple[int, int]] | None, dialect):
        if value is None:
            return None
        return ",".join(f"({x}, {y})" for x, y in value)

    def process_result_value(self, value, dialect) -> List[tuple[int, int]]:
        if not value:
            return []
        tuples = value.split("),(")
        coord = []
        for item in tuples:
            item = item.strip("() ")
            x, y = map(int, item.split(","))
            coord.append((x, y))
        return coord


class FigCards(Base):
    __tablename__ = "figCards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coord: Mapped[List[tuple[int, int]]] = mapped_column(CoordType)
    color: Mapped[int] = mapped_column(Integer)


all_coord = {
    1: [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
    2: [(0, 0), (0, 1), (1, 1), (1, 2), (1, 3)],
    3: [(1, 0), (1, 1), (1, 2), (0, 2), (0, 3)],
    4: [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
    5: [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],
    6: [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    7: [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3)],
    8: [(1, 0), (1, 1), (1, 2), (1, 3), (0, 3)],
    9: [(1, 0), (1, 1), (1, 2), (2, 1), (0, 2)],
    10: [(1, 0), (1, 1), (1, 2), (2, 0), (0, 2)],
    11: [(1, 0), (1, 1), (1, 2), (0, 0), (2, 1)],
    12: [(1, 0), (1, 1), (1, 2), (0, 0), (2, 2)],
    13: [(0, 0), (0, 1), (0, 2), (0, 3), (1, 2)],
    14: [(1, 0), (1, 1), (1, 2), (1, 3), (0, 2)],
    15: [(1, 0), (1, 1), (1, 2), (0, 1), (0, 2)],
    16: [(1, 0), (1, 1), (1, 2), (0, 0), (0, 2)],
    17: [(1, 0), (1, 1), (1, 2), (0, 1), (2, 1)],
    18: [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2)],
    # a partir de aca son tipo azul de fondo
    19: [(1, 0), (1, 1), (0, 1), (0, 2)],
    20: [(0, 0), (0, 1), (1, 0), (1, 1)],
    21: [(0, 0), (0, 1), (1, 1), (1, 2)],
    22: [(1, 0), (1, 1), (1, 2), (0, 1)],
    23: [(0, 0), (0, 1), (0, 2), (1, 2)],
    24: [(0, 0), (0, 1), (0, 2), (0, 3)],
    25: [(1, 0), (1, 1), (1, 2), (0, 2)],
}

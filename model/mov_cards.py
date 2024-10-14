import math
from typing import List

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import VARCHAR, Integer, String, TypeDecorator

from database import Base
from model.board import SIZE_BOARD

BOARD_SIDE = math.sqrt(SIZE_BOARD) - 1
BUNDLE_MOV = 7


class DistType(TypeDecorator):

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


class MoveCards(Base):
    __tablename__ = "moveCards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dist: Mapped[List[tuple[int, int]]] = mapped_column(DistType)


all_dist = {
    # (i+-num, j+-num) si no tiene signo es un valor, no una distancia
    1: [(-+2, -+2)],
    2: [(-+2, None), (None, -+2)],
    3: [(-+1, None), (None, -+1)],
    4: [(-+1, -+1)],
    5: [(-2, +1), (-1, -2), (+2, -1), (+1, +2)],
    6: [(-2, -1), (-1, +2), (+2, +1), (+1, -2)],
    7: [(0, None), (None, 0), (SIZE_BOARD, None), (None, SIZE_BOARD)],
}

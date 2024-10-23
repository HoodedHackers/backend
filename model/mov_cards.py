import math
from typing import List

from pydantic import BaseModel
from sqlalchemy.types import VARCHAR, TypeDecorator

from model.board import SIZE_BOARD

BOARD_MAX_SIDE = int(math.sqrt(SIZE_BOARD) - 1)
BOARD_MIN_SIDE = 0
BUNDLE_MOV = 7
TOTAL_MOV = 50
TOTAL_HAND_MOV = 3

all_dist = {
    # (i+-num, j+-num) si no tiene signo es un valor, no una distancia
    1: [(2, 2), (-2, -2), (2, -2), (-2, 2)],  # Diagonal doble
    2: [(2, 0), (-2, 0), (0, 2), (0, -2)],  # Horizontal y vertical doble
    3: [(1, 0), (-1, 0), (0, 1), (0, -1)],  # Horizontal y vertical simple
    4: [(1, 1), (1, -1), (-1, 1), (-1, -1)],  # Diagonal simple
    5: [(-2, 1), (-1, -2), (2, -1), (1, 2)],  # L antihorario
    6: [(-2, -1), (-1, 2), (2, 1), (1, -2)],  # L horario
    7: [  # Bordes
        (BOARD_MIN_SIDE, 0),
        (0, BOARD_MIN_SIDE),
        (BOARD_MAX_SIDE, 0),
        (0, BOARD_MAX_SIDE),
    ],
}


class IdMov(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value: List[int] | None, dialect):
        if value is None:
            return None
        return " ".join(f"{c}" for c in value)

    def process_result_value(self, value, dialect) -> List[int]:
        if value is None:
            return []
        list = value.split(" ")
        return [(int(c)) for c in list]

    @staticmethod
    def total() -> List[int]:
        return [i for i in range(1, TOTAL_MOV + 1)]


class MoveCards(BaseModel):
    id: int
    dist: List[tuple[int, int]]

    def create_card(self, id: int):
        self.id = id
        valor = BUNDLE_MOV if id % BUNDLE_MOV == 0 else id % len(all_dist)
        self.dist = all_dist[valor]

    def sum_dist(self, tuple_origin: tuple):
        if self.id % 7 == 0:
            tuples_valid = (
                [(tuple_origin[0], BOARD_MIN_SIDE)]
                + [(tuple_origin[0], BOARD_MAX_SIDE)]
                + [(BOARD_MIN_SIDE, tuple_origin[1])]
                + [(BOARD_MAX_SIDE, tuple_origin[1])]
            )
        else:
            tuples_valid = [
                (x + tuple_origin[0], y + tuple_origin[1]) for x, y in self.dist
            ]
        return tuples_valid

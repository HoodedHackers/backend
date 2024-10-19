import itertools
from enum import Enum
from random import shuffle

from sqlalchemy.types import VARCHAR, TypeDecorator
from typing_extensions import List

SIZE_BOARD = 36


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3
    YELLOW = 4


class Board(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value: List[Color] | None, dialect):
        if value is None:
            return None
        return "".join(f"{c.value}" for c in value)

    def process_result_value(self, value, dialect) -> List[Color]:
        if value is None:
            return []
        return [Color(int(c)) for c in value]

    @staticmethod
    def random_board(count=SIZE_BOARD) -> List[Color]:
        assert count % 4 == 0, "Count should ALWAYS be divisible by 4"
        subcount = count // 4
        tiles = list(
            itertools.chain.from_iterable(
                [[Color(n) for _ in range(subcount)] for n in range(1, 5)],
            )
        )
        shuffle(tiles)
        return tiles

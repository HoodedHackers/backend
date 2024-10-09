from enum import Enum
from random import randint

from sqlalchemy.types import VARCHAR, TypeDecorator
from typing_extensions import List


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
    def random_board(count=36) -> List[Color]:
        return [Color(randint(1, 4)) for _ in range(count)]

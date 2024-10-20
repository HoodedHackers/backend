from enum import Enum
from random import randint

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
        return [Color(randint(1, 4)) for _ in range(count)]

    @staticmethod
    def draw(board):
        color_map = {
            Color.RED: "\033[31m",  # ANSI escape code for red
            Color.GREEN: "\033[32m",  # ANSI escape code for green
            Color.BLUE: "\033[34m",  # ANSI escape code for blue
            Color.YELLOW: "\033[33m",  # ANSI escape code for yellow
        }

        reset_color = "\033[0m"  # ANSI escape code to reset color

        for i in range(0, len(board), 6):
            for j in range(i, i + 6):
                print(color_map[board[j]] + "■", end=" ")
            print(reset_color)
        print()

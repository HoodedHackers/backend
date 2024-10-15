from dataclasses import dataclass
from typing import List, Tuple


@dataclass(eq=False)
class Figure:
    positions: List[Tuple[int, int]]

    def __eq__(self, other):
        if isinstance(other, Figure):
            return set(self.positions) == set(other.positions)
        return False

    def draw(self):
        max_x = max(p[0] for p in self.positions)
        max_y = max(p[1] for p in self.positions)
        for y in range(max_y + 1):
            for x in range(max_x + 1):
                if (x, y) in self.positions:
                    print("*", end="")
                else:
                    print(" ", end="")
            print()

    def rotations(self):
        yield self
        for i in range(1, 4):
            yield rotate(self, times=i)


def rotate_90(p: Tuple[int, int]) -> Tuple[int, int]:
    return (-p[1], p[0])


def rotate_180(p: Tuple[int, int]) -> Tuple[int, int]:
    return (-p[0], -p[1])


def rotate_270(p: Tuple[int, int]) -> Tuple[int, int]:
    return (p[1], -p[0])


def add(p1: Tuple[int, int], p2: Tuple[int, int]) -> Tuple[int, int]:
    return (p1[0] + p2[0], p1[1] + p2[1])


def rotate(f: Figure, times=1) -> Figure:
    rotfunc = rotate_90
    if times == 2:
        rotfunc = rotate_180
    if times == 3:
        rotfunc = rotate_270
    raw_pos = list(map(rotfunc, f.positions))
    offset_x = max(-min(p[0] for p in raw_pos), 0)
    offset_y = max(-min(p[1] for p in raw_pos), 0)
    normal_pos = [add(p, (offset_x, offset_y)) for p in raw_pos]
    return Figure(normal_pos)


figures = [Figure(positions=[(0, 0), (0, 1), (0, 2), (1, 2)])]

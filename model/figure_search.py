from dataclasses import dataclass
from typing import List, Tuple

from model.board import Color


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

    def width(self) -> int:
        return max(x for (x, y) in self.positions) + 1

    def height(self) -> int:
        return max(x for (x, y) in self.positions) + 1


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


@dataclass
class CandidateShape:
    figure: Figure
    offset: Tuple[int, int]
    color: Color

    def edges(self) -> List[Tuple[int, int]]:
        positions = []
        for p in self.figure.positions:
            for q in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                j = add(add(self.offset, q), p)
                x, y = j
                if x < 0 or x >= 6 or y < 0 or y >= 6:
                    continue
                if j in self.figure.positions or j in positions:
                    continue
                positions.append(j)
        return positions


def find_figures(board: List[Color], figures: List[Figure]):
    offsets = [(x, y) for x in range(6) for y in range(6)]
    candidate_shapes: List[CandidateShape] = []
    for fig in figures:
        for offset in offsets:
            (x, y) = offset
            if x + fig.width() >= 6 or y + fig.height() >= 6:
                continue
            offset_positions = map(lambda pos: add(offset, pos), fig.positions)
            indices = map(lambda pos: pos[0] + pos[1] * 6, offset_positions)
            colors = set(board[index] for index in indices)
            if len(colors) == 1:
                candidate_shapes.append(
                    CandidateShape(figure=fig, offset=offset, color=colors.pop())
                )
    final_shapes = []
    for c in candidate_shapes:
        indices = map(lambda pos: pos[0] + pos[1] * 6, c.edges())
        colors = set(board[index] for index in indices)
        if all(color != c.color for color in colors):
            final_shapes.append(c)
    return final_shapes


figures = [Figure(positions=[(0, 0), (0, 1), (0, 2), (1, 2)])]

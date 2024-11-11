from dataclasses import dataclass
from typing import List, Tuple

from model.board import Color


@dataclass(eq=False)
class Figure:
    id: int
    positions: List[Tuple[int, int]]

    def __eq__(self, other):
        if isinstance(other, Figure):
            return set(self.positions) == set(other.positions)
        return False

    def draw(self):
        max_x = max(p[0] for p in self.positions)
        max_y = max(p[1] for p in self.positions)
        for x in range(max_x + 1):
            for y in range(max_y + 1):
                if (x, y) in self.positions:
                    print("*", end="")
                else:
                    print(" ", end="")
            print()

    def offset(self, offset: Tuple[int, int]) -> List[Tuple[int, int]]:
        return list(map(lambda pos: add(offset, pos), self.positions))

    def rotations(self):
        yield self
        for i in range(1, 4):
            yield rotate(self, times=i)

    def width(self) -> int:
        return max(x for (x, y) in self.positions) + 1

    def height(self) -> int:
        return max(y for (x, y) in self.positions) + 1


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
    return Figure(f.id, normal_pos)


@dataclass
class CandidateShape:
    figure: Figure
    offset: Tuple[int, int]
    color: Color

    def true_positions(self) -> List[Tuple[int, int]]:
        return list(add(self.offset, pos) for pos in self.figure.positions)

    def true_positions_canonical(self) -> List[int]:
        return list(map(lambda pos: coord_to_index(6, pos), self.true_positions()))

    def figure_id(self) -> int:
        return self.figure.id

    def edges(self, width=6) -> List[Tuple[int, int]]:
        positions = []
        true_positions = self.true_positions()
        for pos in true_positions:
            for direction in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                x, y = j = add(direction, pos)
                if x < 0 or x >= width or y < 0 or y >= width:
                    continue
                if j in true_positions or j in positions:
                    continue
                print(pos, direction, self.offset)
                positions.append(j)
        return positions


def calculate_offsets(
    board_size: int, width: int, height: int
) -> List[Tuple[int, int]]:
    offsets = [
        (x, y)
        for x in range(0, board_size - width + 1)
        for y in range(0, board_size - height + 1)
    ]
    return offsets


def coord_to_index(width: int, pos: Tuple[int, int]) -> int:
    x, y = pos
    return x + y * width


def find_figures(board: List[Color], figures: List[Figure]) -> List[CandidateShape]:
    candidate_shapes: List[CandidateShape] = []
    for fig in figures:
        offsets = calculate_offsets(6, fig.width(), fig.height())
        for offset in offsets:
            offset_positions = fig.offset(offset)
            indices = list(map(lambda pos: coord_to_index(6, pos), offset_positions))
            colors = set(board[index] for index in indices)
            if len(colors) == 1:
                candidate_shapes.append(
                    CandidateShape(figure=fig, offset=offset, color=colors.pop())
                )
    final_shapes = []
    for c in candidate_shapes:
        indices = map(lambda pos: coord_to_index(6, pos), c.edges())
        colors = set(board[index] for index in indices)
        if all(color != c.color for color in colors):
            final_shapes.append(c)
    print(final_shapes)
    return final_shapes

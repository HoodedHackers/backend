import unittest

import pytest

from .board import Board, Color
from .figure_search import (CandidateShape, Figure, calculate_offsets,
                            coord_to_index, find_figures, rotate)


class TestFigure(unittest.TestCase):
    def setUp(self):
        self.L_up = Figure(id=0, positions=[(0, 0), (1, 0), (2, 0), (2, 1)])
        self.L_down = Figure(id=0, positions=[(0, 0), (0, 1), (1, 1), (2, 1)])
        self.L_right = Figure(id=0, positions=[(1, 0), (1, 1), (1, 2), (0, 2)])
        self.L_left = Figure(id=0, positions=[(0, 0), (0, 1), (0, 2), (1, 0)])

    def test_rotate(self):
        res = rotate(self.L_up, times=1)
        self.assertSetEqual(set(res.positions), set(self.L_right.positions))
        res = rotate(self.L_up, times=2)
        self.assertSetEqual(set(res.positions), set(self.L_down.positions))
        res = rotate(self.L_up, times=3)
        self.assertSetEqual(set(res.positions), set(self.L_left.positions))

    def test_equality(self):
        res = rotate(self.L_down)
        self.assertIn(res, [self.L_up, self.L_down, self.L_right, self.L_left])

    def test_offset(self):
        positions = self.L_up.offset((10, 10))
        expected = [(10, 10), (11, 10), (12, 10), (12, 11)]
        self.assertEqual(set(positions), set(expected))

    def test_coord_to_index(self):
        res = coord_to_index(10, (1, 1))
        self.assertEqual(res, 11)
        res = coord_to_index(6, (5, 5))
        self.assertEqual(res, 35)


class TestCandidateShapeEdges(unittest.TestCase):
    def setUp(self):
        self.tile = CandidateShape(
            figure=Figure(0, [(0, 0)]), offset=(1, 1), color=Color.RED
        )
        self.square = CandidateShape(
            figure=Figure(0, [(0, 0), (0, 1), (1, 0), (1, 1)]),
            offset=(0, 0),
            color=Color.RED,
        )
        self.L_shape = CandidateShape(
            figure=Figure(0, [(0, 0), (1, 0), (2, 0), (2, 1)]),
            offset=(0, 0),
            color=Color.RED,
        )

    def test_edges_sanity(self):
        t = CandidateShape(figure=Figure(0, [(0, 0)]), offset=(0, 0), color=Color.RED)
        edges = t.edges(1)
        self.assertEqual(set(edges), set())

    def test_edges_line(self):
        t = CandidateShape(
            figure=Figure(0, [(0, 0), (0, 1)]), offset=(0, 0), color=Color.RED
        )
        edges = t.edges(2)
        self.assertEqual(set(edges), set([(1, 0), (1, 1)]))

    def test_edges_line_offset(self):
        t = CandidateShape(
            figure=Figure(0, [(0, 0), (0, 1)]), offset=(1, 0), color=Color.RED
        )
        edges = t.edges(2)
        self.assertEqual(set(edges), set([(0, 0), (0, 1)]))

    def test_edges_1x1(self):
        expected_edges = [(1, 0), (0, 1), (1, 2), (2, 1)]
        self.assertSetEqual(set(self.tile.edges()), set(expected_edges))

    def test_edges_2x2(self):
        expected_edges = [(2, 0), (2, 1), (0, 2), (1, 2)]
        self.assertSetEqual(set(self.square.edges()), set(expected_edges))

    def test_edges_L_shape(self):
        expected_edges = [(3, 0), (3, 1), (0, 1), (1, 1), (2, 2)]
        self.assertSetEqual(set(self.L_shape.edges()), set(expected_edges))


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board().process_result_value(
            # Hay una figura ╦ te lo prometo
            "323111424414433343121211222143323143",
            None,  # type: ignore
        )
        self.tetris = Figure(0, [(0, 0), (0, 1), (0, 2), (1, 1)])
        self.figures = list(self.tetris.rotations())

    def test_find_figures(self):
        figures = find_figures(self.board, self.figures)
        Board.draw(self.board)
        self.assertEqual(len(figures), 1)

    def test_offsets_sanity(self):
        offsets = calculate_offsets(1, 1, 1)
        expected = [(0, 0)]
        self.assertEqual(set(offsets), set(expected))

    def test_offsets_2x2(self):
        offsets = calculate_offsets(2, 1, 1)
        expected = [(0, 0), (1, 0), (0, 1), (1, 1)]
        self.assertEqual(set(offsets), set(expected))

    def test_offsets_line(self):
        offsets = calculate_offsets(2, 2, 1)
        expected = [(0, 0), (0, 1)]
        self.assertEqual(set(offsets), set(expected))


class TestSearchRegressions(unittest.TestCase):
    def setUp(self):
        self.board = Board().process_result_value(
            "121211334434213121142422432124333443",
            None,  # type: ignore
        )
        self.tetris = Figure(22, [(1, 0), (1, 1), (1, 2), (0, 1)])
        self.figures = list(self.tetris.rotations())

    def test_find_figues(self):
        res = find_figures(self.board, self.figures)
        assert len(res) == 2
        colors = set([f.color for f in res])
        self.assertSetEqual(colors, {Color.BLUE, Color.GREEN})

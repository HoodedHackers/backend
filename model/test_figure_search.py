import unittest

from .board import Color
from .figure_search import CandidateShape, Figure, rotate


class TestFigureRotations(unittest.TestCase):
    def setUp(self):
        self.L_up = Figure(positions=[(0, 0), (1, 0), (2, 0), (2, 1)])
        self.L_down = Figure(positions=[(0, 0), (0, 1), (1, 1), (2, 1)])
        self.L_right = Figure(positions=[(1, 0), (1, 1), (1, 2), (0, 2)])
        self.L_left = Figure(positions=[(0, 0), (0, 1), (0, 2), (1, 0)])

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


class TestCandidateShapeEdges(unittest.TestCase):
    def setUp(self):
        self.tile = CandidateShape(
            figure=Figure([(0, 0)]), offset=(1, 1), color=Color.RED
        )
        self.square = CandidateShape(
            figure=Figure([(0, 0), (0, 1), (1, 0), (1, 1)]),
            offset=(0, 0),
            color=Color.RED,
        )
        self.L_shape = CandidateShape(
            figure=Figure([(0, 0), (1, 0), (2, 0), (2, 1)]),
            offset=(0, 0),
            color=Color.RED,
        )

    def test_edges_1x1(self):
        expected_edges = [(1, 0), (0, 1), (1, 2), (2, 1)]
        self.assertSetEqual(set(self.tile.edges()), set(expected_edges))

    def test_edges_2x2(self):
        expected_edges = [(2, 0), (2, 1), (0, 2), (1, 2)]
        self.assertSetEqual(set(self.square.edges()), set(expected_edges))

    def test_edges_L_shape(self):
        expected_edges = [(3, 0), (3, 1), (0, 1), (1, 1), (2, 2)]
        self.assertSetEqual(set(self.L_shape.edges()), set(expected_edges))

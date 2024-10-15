import unittest

from .figure_search import Figure, rotate


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

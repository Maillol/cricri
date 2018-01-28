import unittest
from cricri.algo import walk


class TestWalk(unittest.TestCase):
    graph_0 = {
        'A': [],
    }

    expected_0 = (('A',),)

    graph_1 = {
        'A': ['B'],
        'B': ['C'],
        'C': []
    }

    expected_1 = (
        ('A', 'B', 'C'),
    )

    expected_1_loop_2 = expected_1

    graph_2 = {
        'A': ['A', 'B'],
        'B': ['A', 'B'],
    }

    expected_2 = (
        ('A', 'A', 'B', 'A'),
        ('A', 'A', 'B', 'B', 'A'),
        ('A', 'B', 'A', 'A'),
        ('A', 'B', 'B', 'A', 'A'),
    )

    graph_3 = {
        'A': ['B'],
        'B': ['A', 'B'],
    }

    expected_3 = {
        ('A', 'B', 'A'),
        ('A', 'B', 'B', 'A')
    }

    expected_3_loop_1 = {
        ('A', 'B', 'A', 'B', 'B', 'A', 'B', 'A'),
        ('A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A'),
        ('A', 'B', 'A', 'B', 'B', 'B', 'B', 'A', 'B', 'A'),
        ('A', 'B', 'A', 'B', 'A', 'B', 'B', 'B', 'A', 'B', 'A'),
        ('A', 'B', 'A', 'B', 'B', 'B', 'A', 'B', 'A', 'B', 'A'),
        ('A', 'B', 'A', 'B', 'A', 'B', 'B', 'A', 'B', 'A', 'B', 'A')
    }

    graph_4 = {
        'A': ['B'],
        'B': ['A'],
    }

    expected_4 = [
        ('A', 'B', 'A'),
    ]

    expected_4_loop_1 = [
        ('A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A')
    ]

    expected_4_loop_2 = [
        ('A', 'B', 'A', 'B', 'A',
         'B', 'A', 'B', 'A', 'B',
         'A', 'B', 'A', 'B', 'A')
    ]

    def test_graph_0(self):
        pathes = walk(self.graph_0, 'A')
        self.assertCountEqual(pathes, self.expected_0)

    def test_graph_1(self):
        pathes = walk(self.graph_1, 'A')
        self.assertCountEqual(pathes, self.expected_1)

    def test_graph_2(self):
        pathes = walk(self.graph_2, 'A')
        self.assertCountEqual(pathes, self.expected_2)

    def test_graph_3(self):
        pathes = walk(self.graph_3, 'A')
        self.assertCountEqual(pathes, self.expected_3)

    def test_graph_3_loop_1(self):
        pathes = walk(self.graph_3, 'A', nb_loop=1)
        self.assertCountEqual(pathes, self.expected_3_loop_1)

    def test_graph_4(self):
        pathes = walk(self.graph_4, 'A')
        self.assertCountEqual(pathes, self.expected_4)

    def test_graph_4_loop_1(self):
        pathes = walk(self.graph_4, 'A', nb_loop=1)
        self.assertCountEqual(pathes, self.expected_4_loop_1)

    def test_graph_4_loop_2(self):
        pathes = walk(self.graph_4, 'A', nb_loop=2)
        self.assertCountEqual(pathes, self.expected_4_loop_2)

import unittest
from gentest import MultiDict, walk, previous


class TestWalk(unittest.TestCase):

    g = {
        'A': ['B'],
        'B': ['C', 'G'],
        'C': ['D', 'E', 'G'],
        'D': ['G'],
        'E': ['F', 'G'],
        'F': ['G'],
        'G': []
    }

    def test_walk(self):
        paths = walk(self.g, 'A')
        expected = (
            ('A', 'B', 'C', 'D', 'G'),
            ('A', 'B', 'C', 'E', 'F', 'G'),
            ('A', 'B', 'C', 'E', 'G'),
            ('A', 'B', 'C', 'G'),
            ('A', 'B', 'G'),
        )
 
        self.assertCountEqual(paths, expected)


class TestPrevious(unittest.TestCase):

    def test_decorate_function(self):

        @previous(['A', 'B'])
        def foo():
            ...

        self.assertEqual(foo.previous_steps, ['A', 'B'])


class TestMultiDict(unittest.TestCase):

    def setUp(self):
        self.multidict = MultiDict(dict(input='inputs'))

    def test_add_multi_value(self):
        self.multidict['input'] = 1
        self.multidict['input'] = 2
        self.assertEqual(self.multidict, dict(inputs=[1, 2]))

    def test_add_simple_value(self):
        self.multidict['a'] = 1
        self.multidict['a'] = 2
        self.assertEqual(self.multidict, dict(inputs=[], a=2))


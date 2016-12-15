import unittest
import unittest.mock
from unittest.mock import call
from gentest import MultiDict, walk, previous, TestState


class TestTestStateSubClassing(unittest.TestCase):

    mock = unittest.mock.Mock()
    def setUp(self):
        type(self).mock.reset_mock()

    class FooTestState(TestState):
        spy_attr = 427

    class A(FooTestState, start=True):

        def start(cls):
            TestTestStateSubClassing.mock(1)

        def input(self):
            TestTestStateSubClassing.mock(2)

        def test_1(self):
            TestTestStateSubClassing.mock(3)

        def test_2(self):
            TestTestStateSubClassing.mock(4)

    class B(FooTestState, previous=['A']):
        def input(self):
            TestTestStateSubClassing.mock(5)

        def test_1(self):
            TestTestStateSubClassing.mock(6)

        def test_2(self):
            TestTestStateSubClassing.mock(7)

    class C(FooTestState, previous=['A', 'B']):

        @previous(['A'])
        def input(self):
            TestTestStateSubClassing.mock(8)

        @previous(['B'])
        def input(self):
            TestTestStateSubClassing.mock(9)

        def test_1(self):
            TestTestStateSubClassing.mock(10)

        def test_2(self):
            TestTestStateSubClassing.mock(11)

    test_cases = FooTestState.get_test_cases(1)
    expected_abc_calls = [call(n) for n in (1, 2, 3, 4, 5, 6, 7, 9, 10, 11)]
    expected_ac_calls = [call(n) for n in (1, 2, 3, 4, 8, 10, 11)]

    @staticmethod
    def _execute_test_case(test_case):
        test_loader = unittest.TestLoader()
        suite = test_loader.loadTestsFromTestCase(test_case)
        suite.run(unittest.TestResult())

    def test_generated_tests_are_footeststate(self):
        """generated tests must be subclass of FooTestState"""
        cls = type(self)
        self.assertTrue(issubclass(cls.test_cases[0], type(self).FooTestState))
        self.assertTrue(issubclass(cls.test_cases[1], type(self).FooTestState))

    def test_two_tests_are_generated(self):
        cls = type(self)
        self.assertEqual(len(cls.test_cases), 2)
        self.assertTrue(issubclass(cls.test_cases[0], unittest.TestCase))
        self.assertTrue(issubclass(cls.test_cases[1], unittest.TestCase))

    def test_run_test_case_1(self):
        cls = type(self)
        test = cls.test_cases[0]
        self._execute_test_case(test)

        if test.__name__ == 'ABC':
            cls.mock.assert_has_calls(cls.expected_abc_calls)
        else:
            cls.mock.assert_has_calls(cls.expected_ac_calls)

    def test_run_test_case_2(self):
        cls = type(self)
        test = cls.test_cases[1]
        self._execute_test_case(test)

        if test.__name__ == 'ABC':
            cls.mock.assert_has_calls(cls.expected_abc_calls)
        else:
            cls.mock.assert_has_calls(cls.expected_ac_calls)


class TestWalk(unittest.TestCase):

    simple_graph = {
        'A': ['B'],
        'B': ['C', 'G'],
        'C': ['D', 'E', 'G'],
        'D': ['G'],
        'E': ['F', 'G'],
        'F': ['G'],
        'G': []
    }

    graph_with_loop = {
        'A': ['B'],
        'B': ['C'],
        'C': ['D', 'E'],
        'D': ['B'],
        'E': ['F', 'G'],
        'F': ['D'],
        'G': []
    }

    def test_walk_simple_graph(self):
        paths = walk(self.simple_graph, 'A')
        expected = (
            ('A', 'B', 'C', 'D', 'G'),
            ('A', 'B', 'C', 'E', 'F', 'G'),
            ('A', 'B', 'C', 'E', 'G'),
            ('A', 'B', 'C', 'G'),
            ('A', 'B', 'G'),
        )

        self.assertCountEqual(paths, expected)

    def test_walk_graph_with_1_loop(self):
        paths = walk(self.graph_with_loop, 'A')
        expected = (
            ('A', 'B', 'C', 'D', 'B'),
            ('A', 'B', 'C', 'E', 'F', 'D', 'B'),
            ('A', 'B', 'C', 'E', 'G'),
        )

        self.assertCountEqual(paths, expected)

    def test_walk_graph_with_2_loop(self):
        paths = walk(self.graph_with_loop, 'A', 2)
        expected = (
            ('A', 'B', 'C', 'D', 'B', 'C', 'D', 'B'),
            ('A', 'B', 'C', 'D', 'B', 'C', 'E', 'F', 'D', 'B'),
            ('A', 'B', 'C', 'E', 'F', 'D', 'B', 'C', 'D', 'B'),
            ('A', 'B', 'C', 'E', 'F', 'D', 'B', 'C', 'E', 'F', 'D', 'B'),
            ('A', 'B', 'C', 'E', 'G'),
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


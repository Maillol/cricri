import unittest
import unittest.mock
from unittest.mock import call
from gentest import previous, TestState
from functools import wraps


spy = unittest.mock.Mock()

class SpyTestState(unittest.TestCase):
    """
    SpyTestState reset spy before each test.

    Subclass this class and write TestState in the body.
    The TestState base must be named BaseTestState.
    """

    def setUp(self):
        spy.reset_mock()

    @classmethod
    def setUpClass(cls):
        cls.test_cases = {test.__name__: test
              for test
              in cls.BaseTestState.get_test_cases(1)}

    def _execute_test_case(self, test_name):
        cls = type(self)
        test_case = cls.test_cases[test_name]
        test_loader = unittest.TestLoader()
        suite = test_loader.loadTestsFromTestCase(test_case)
        suite.run(unittest.TestResult())

    def assertExec(self, test_name, spy_calls):
        """
        Execute test_name and check spy calls.
        """
        self.assertIn(test_name, type(self).test_cases)
        self._execute_test_case(test_name)
        calls = [call(spy_call) for spy_call in spy_calls]
        spy.assert_has_calls(calls)


class TestPreviousOnTestMethod(SpyTestState):


    class BaseTestState(TestState):
        ...

    class A(BaseTestState, start=True):
        ...

    class B1(BaseTestState, previous=['A']):
        def test_1(self):
            spy("B1.test")

    class B2(BaseTestState, previous=['A']):
        def test_1(self):
            spy("B2.test")

    class C(BaseTestState, previous=['B1', 'B2']):

        @previous(['B1'])
        def test_b1(self):
            spy("C.test_b1")

        @previous(['B2'])
        def test_b2(self):
            spy("C.test_b2")

    def test_two_test_are_generated(self):
        cls = type(self)
        self.assertEqual(len(cls.test_cases), 2)

    def test_execute_a_b1_c(self):
        self.assertExec('AB1C', ("B1.test", "C.test_b1"))

    def test_execute_a_b2_c(self):
        self.assertExec('AB2C', ("B2.test", "C.test_b2"))


class TestPreviousOnInputMethod(SpyTestState):

    class BaseTestState(TestState):
        spy_attr = 427

    class A(BaseTestState, start=True):

        def start(cls):
            spy("A.start")

        def input(self):
            spy("A.input")

        def test_1(self):
            spy("A.test_1")

        def test_2(self):
            spy("A.test_2")

    class B(BaseTestState, previous=['A']):
        def input(self):
            spy("B.input")

        def test_1(self):
            spy("B.test_1")

        def test_2(self):
            spy("B.test_2")

    class C(BaseTestState, previous=['A', 'B']):

        @previous(['A'])
        def input(self):
            spy("C.input /A")

        @previous(['B'])
        def input(self):
            spy("C.input /B")

        def test_1(self):
            spy("C.test_1")

        def test_2(self):
            spy("C.test_2")

    def test_generated_tests_are_BaseTestState(self):
        """generated tests must be subclass of BaseTestState"""
        cls = type(self)
        self.assertTrue(issubclass(cls.test_cases['ABC'], type(self).BaseTestState))
        self.assertTrue(issubclass(cls.test_cases['AC'], type(self).BaseTestState))

    def test_two_tests_are_generated(self):
        cls = type(self)
        self.assertEqual(len(cls.test_cases), 2)
        self.assertTrue(issubclass(cls.test_cases['ABC'], unittest.TestCase))
        self.assertTrue(issubclass(cls.test_cases['AC'], unittest.TestCase))

    def test_execute_abc(self):
        self.assertExec('ABC',
                        ("A.start",
                         "A.input",
                         "A.test_1",
                         "A.test_2",
                         "B.input",
                         "B.test_1",
                         "B.test_2",
                         "C.input /B",
                         "C.test_1",
                         "C.test_2"))

    def test_execute_ac(self):
        self.assertExec('AC',
                        ("A.start",
                         "A.input",
                         "A.test_1",
                         "A.test_2",
                         "C.input /A",
                         "C.test_1",
                         "C.test_2"))


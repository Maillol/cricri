import unittest
import unittest.mock
from unittest.mock import call
from cricri import previous, TestState, condition, Path


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
                          in cls.BaseTestState.get_test_cases(0)}

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
        if spy.mock_calls != calls:
            raise AssertionError('Calls not found.\n'
                                 'Expected: {}\n'
                                 'Actual: {}\n'.format(calls, spy.mock_calls))


class TestCaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        spy('TestCaseTest.setUpClass')

    @classmethod
    def tearDownClass(cls):
        spy('TestCaseTest.tearDownClass')
        super().tearDownClass()


class TestCustomTestCase(SpyTestState):

    class BaseTestState(TestState):
        base_class = TestCaseTest

        @classmethod
        def start_scenario(cls):
            spy('BaseTestState.start_scenario')

        @classmethod
        def stop_scenario(cls):
            spy('BaseTestState.stop_scenario')

    class A(BaseTestState, start=True):
        def input(self):
            pass

    class B(BaseTestState, previous=['A']):
        def input(self):
            pass

        def test_1(self):
            spy("B1.test")

    def test_execute_setup_teardown(self):
        self.assertExec('AB', (
            "TestCaseTest.setUpClass",
            "BaseTestState.start_scenario",
            "B1.test",
            "BaseTestState.stop_scenario",
            "TestCaseTest.tearDownClass",
        ))


class TestPreviousOnTestMethod(SpyTestState):

    class BaseTestState(TestState):
        ...

    class A(BaseTestState, start=True):
        def input(self):
            pass

    class B1(BaseTestState, previous=['A']):
        def input(self):
            pass

        def test_1(self):
            spy("B1.test")

    class B2(BaseTestState, previous=['A']):
        def input(self):
            pass

        def test_1(self):
            spy("B2.test")

    class C(BaseTestState, previous=['B1', 'B2']):
        def input(self):
            pass

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
        @classmethod
        def start_scenario(cls):
            spy("A.start")

    class A(BaseTestState, start=True):
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
        self.assertTrue(issubclass(cls.test_cases['ABC'],
                                   type(self).BaseTestState))
        self.assertTrue(issubclass(cls.test_cases['AC'],
                                   type(self).BaseTestState))

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


class TestPathCondition(SpyTestState):

    class BaseTestState(TestState):
        ...

    class A(BaseTestState, start=True):
        def input(self):
            pass

        def test_1(self):
            spy('A.test_1')

    class B(BaseTestState, previous=['A']):
        def input(self):
            pass

        def test_1(self):
            spy('B.test_1')

    class C(BaseTestState, previous=['B', 'A']):
        def input(self):
            pass

        def test_1(self):
            spy('C.test_1')

    class D(BaseTestState, previous=['C']):
        def input(self):
            pass

        @condition(Path("A", "C"))
        def test_1(self):
            spy('D.test_1 /AC')

        @condition(- Path("A", "C"))
        def test_2(self):
            spy('D.test_2 /-AC')

    def test_execute_abc(self):
        self.assertExec('ABCD',
                        ("A.test_1", "B.test_1", "C.test_1", "D.test_2 /-AC"))

    def test_execute_acd(self):
        self.assertExec('ACD',
                        ("A.test_1", "C.test_1", "D.test_1 /AC"))


class TestStartStopMethods(SpyTestState):

    class BaseTestState(TestState):
        def input(self):
            pass

        @classmethod
        def start_scenario(cls):
            cls.attr = 'ok'
            spy('A.start')

        @classmethod
        def stop_scenario(cls):
            spy('A.stop')

    class A(BaseTestState, start=True, previous=['B']):
        def input(self):
            pass

        def test_1(self):
            attr = getattr(self, 'attr',
                           'should get attr defined from start_scenario')
            spy('A.test_1 {}'.format(attr))

    class B(BaseTestState, previous=['A']):
        def input(self):
            pass

        def test_1(self):
            spy('B.test_1')

    def test_execute_abab(self):
        self.assertExec('ABA',
                        ("A.start", "A.test_1 ok",
                         "B.test_1", "A.test_1 ok", "A.stop"))


class TestInputCrash(SpyTestState):

    class BaseTestState(TestState):
        ...

    class A(BaseTestState, start=True):
        def input(self):
            pass

        def test_1(self):
            spy('A.test_1')

    class B(BaseTestState, previous=['A']):
        def input(self):
            raise ValueError('Answer is 42')

        def test_1(self):
            spy('B.test_1')

    class C(BaseTestState, previous=['B', 'A']):
        def input(self):
            pass

        def test_1(self):
            spy('C.test_1')

    def test_execute_ac(self):
        self.assertExec('AC',
                        ("A.test_1", "C.test_1"))

    def test_execute_abc(self):
        self.assertExec('ABC', ("A.test_1",))


class TestInputWithCondition(SpyTestState):

    class BaseTestState(TestState):
        ...

    class A(BaseTestState, start=True):
        def input(self):
            pass

        def test_1(self):
            spy('A.test_1')

    class B1(BaseTestState, previous=['A']):
        def input(self):
            pass

        def test_1(self):
            spy('B1.test_1')

    class B2(BaseTestState, previous=['A']):
        def input(self):
            pass

        def test_1(self):
            spy('B2.test_1')

    class C(BaseTestState, previous=['B1', 'B2']):

        @condition(Path('B1'))
        def input(self):
            spy('C.input')

        def test_1(self):
            spy('C.test_1')

    class D(BaseTestState, previous=['C']):
        def input(self):
            pass

        def test_1(self):
            spy('D.test_1')

    def test_execute_ab1cd(self):
        self.assertExec('AB1CD',
                        ("A.test_1",
                         "B1.test_1",
                         "C.input", "C.test_1",
                         "D.test_1"))

    def test_execute_ab2cd(self):
        self.assertExec('AB2CD',
                        ("A.test_1",
                         "B2.test_1",
                         "D.test_1"))


class TestWithoutDefinedInputShouldRun(SpyTestState):

    class BaseTestState(TestState):
        ...

    class A(BaseTestState, start=True):
        def test_1(self):
            spy('A.test_1')

    def test_execute_ab2cd(self):
        self.assertExec('A',
                        ("A.test_1",))


class TestShouldRaiseIfCannotChooseInput(unittest.TestCase):

    class BaseTestState(TestState):
        ...

    class A(BaseTestState, start=True):
        def input(self):
            pass

    class B(BaseTestState, previous=['A']):

        @previous(['A'])
        def input(self):
            pass

        @condition(Path('A'))
        def input(self):
            pass

    def test_should_raise(self):
        with self.assertRaises(AttributeError) as cm:
            self.BaseTestState.get_test_cases(0)

        self.assertEqual(str(cm.exception),
                         'Multiple inputs methods are valid in '
                         'TestShouldRaiseIfCannotChooseInput.B')


class TestShouldRaiseIfPreviousStepDoesntExist(unittest.TestCase):

    class BaseTestState(TestState):
        ...

    class A(BaseTestState, start=True):
        def input(self):
            pass

    class B(BaseTestState, previous=['X']):
        def input(self):
            pass

    def test_should_raise(self):
        with self.assertRaises(ValueError) as cm:
            self.BaseTestState.get_test_cases(0)

        self.assertEqual(str(cm.exception),
                         "The previous `X` defined in"
                         " TestShouldRaiseIfPreviousStepDoesntExist.B class"
                         " doesn't exist")

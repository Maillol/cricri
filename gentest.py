"""
Module to generate test scenarios from scenario step.
"""

from collections import defaultdict
import unittest


class MultiDict(dict):
    """
    MultiDict(multi_values_mapping[, ...]) --> dict with multiple values per key.

    >>> md = MultiDict(dict(foo=fooes), a=42)
    >>> md['foo'] = 1
    >>> md['foo'] = 4
    >>> md
    {'fooes': [1, 4], 'a': 42}
    """

    def __init__(self, *args, **kwargs):
        if args:
            self._multi_values = args[0]
            if not isinstance(self._multi_values, dict):
                raise TypeError("first argument must be dict")
            args = args[1:]
        else:
            self._multi_values = {}

        for key in self._multi_values.values():
            dict.__setitem__(self, key, [])

    def __setitem__(self, key, value):
        try:
            new_key = self._multi_values[key]
        except KeyError:
            dict.__setitem__(self, key, value)
        else:
            self[new_key].append(value)


def walk(graph, start):
    """
    Find all path through graph.

    graph - must be a dict mappinp graph node to next graph node.
    start - must be a first graph node
    """

    paths = []

    def _walk(start, path):
        if not graph[start]:
            paths.append(path + (start,))
        else:
            for node in graph[start]:
                _walk(node, path + (start,))

    _walk(start, ())
    return paths


class MetaTestState(type):
    """
    Generate all possible test scenarios from TestState subclass.
    Each test scenario is defined as unittest.TestCase subclass.

    The get_load_tests method generate test suite and return
    unittest load_tests function.
    """

    steps = {}
    start_step = None

    @staticmethod
    def _build_test_method(input_method, names_and_methods):
        """
        Build and return test method for unittest.TestCase class.
        """

        def test(self):
            if input_method is not None:
                input_method(self)
            for name, method in names_and_methods:
                with self.subTest(name=name):
                    method(self)
        return test

    @classmethod
    def _generate_senarios(mcs):
        """
        Return list of senario, each senario is a list of states.
        """
        step_from_previous = defaultdict(list)
        for step in mcs.steps.values():
            for previous_step in step.previous:
                step_from_previous[previous_step].append(step.__name__)

        return walk(step_from_previous, mcs.start_step)

    @staticmethod
    def _select_input_method(inputs, previous_step):
        """
        Select input method using previous_steps.

        inputs - list of input method decorated with previous decorator.
        previous_step - string, name of previous steps
        """
        if len(inputs) == 1:
            return inputs[0]

        for input_method in inputs:
            if previous_step in input_method.previous_steps:
                return input_method

    @classmethod
    def get_load_tests(mcs):
        """
        Build and return load_tests function.
        """

        test_loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()

        for senario in mcs._generate_senarios():
            attrs = {}
            previous_step_name = None
            for step_num, step_name in enumerate(senario):
                step = mcs.steps[step_name]
                input_method = mcs._select_input_method(step.inputs,
                                                        previous_step_name)

                test_methods = tuple(
                    sorted((name, attr)
                           for name, attr
                           in vars(step).items()
                           if name.startswith('test')))

                method_name = "test_{:>04}_{}".format(step_num, step_name.lower())
                attrs[method_name] = mcs._build_test_method(input_method,
                                                            test_methods)

                previous_step_name = step_name

            test_case_subcls = type(''.join(senario),
                                    (unittest.TestCase,), attrs)

            tests = test_loader.loadTestsFromTestCase(test_case_subcls)
            suite.addTests(tests)

        def load_tests(loader, tests, pattern):
            return suite

        return load_tests

    def __init__(cls, cls_name, bases, attrs, **kwargs):
        type.__init__(cls, cls_name, bases, attrs)

    def __new__(mcs, cls_name, bases, attrs, previous=None, start=False):
        cls = type.__new__(mcs, cls_name, bases, attrs)
        if bases:
            if previous is None:
                cls.previous = []
            else:
                cls.previous = previous

            for attr_name, attr in attrs.items():
                if attr_name == 'inputs':
                    for input_method in attr:
                        if not hasattr(input_method, 'previous_steps'):
                            input_method.previous_steps = cls.previous

            mcs.steps[cls_name] = cls
            if start:
                if mcs.start_step is not None:
                    raise AssertionError("States '{}' and '{}' are start states. "
                                         "Only one start state is allowed."
                                         .format(mcs.start_step, cls_name))
                mcs.start_step = cls_name

        return cls

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return MultiDict(dict(input='inputs'))


def previous(previous_steps):
    """
    This decorator define previous steps of decorated input methods.

    previous_steps - list of previous TestState subclasses names.
    """
    if not isinstance(previous_steps, list):
        raise TypeError('previous() take list of class names (got {})'
                        .format(type(previous_steps).__name__))

    def decorator(func):
        func.previous_steps = previous_steps
        return func

    return decorator


class TestState(metaclass=MetaTestState):
    """
    Test authors should subclass this class in order to define a step
    of test scenario.

    TestState subclass must define one or several `input` methods.
    If several `input` methods are defined, they must be decorate with
    `previous` decorator in order to indicate which methods must be call
    before test methods.

    TestState subclass must define `start` or `previous` keyword. `start` is
    True if TestState is a start state otherwise `previous` must be define,
    this is a list containing names of previous TestState.

    Test authors can define one or several "test_*()" methods such as in
    unittest.TestCase subclass.

    Example:

               m1()           m1()
        ((A)) -------> (B) -------> (C)
          |    m2()                  |
          +---------------->---------+

        class StateA(TestState, start=True):
            def input(self):
                type(self).machine = Machine()


        class StateB(TestState, previous=['StateA']):
            def input(self):
                type(self).machine.m1()


        class StateC(TestState, previous=['StateA', 'StateB']):

            @previous(['StateA'])
            def input(self):
                type(self).machine.m2()

            @previous(['StateB'])
            def input(self):
                type(self).machine.m1()

    """


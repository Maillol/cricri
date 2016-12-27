"""
Module to generate test scenarios from scenario step.
"""

from collections import defaultdict
import unittest


__version__ = '1.0b1'


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

        super().__init__(*args, **kwargs)
        for key in self._multi_values.values():
            dict.__setitem__(self, key, [])

    def __setitem__(self, key, value):
        try:
            new_key = self._multi_values[key]
        except KeyError:
            dict.__setitem__(self, key, value)
        else:
            self[new_key].append(value)


def walk(graph, start, max_loop=1):
    """
    Find all path through graph.

    graph - must be a dict mappinp graph node to next graph node.
    start - must be a first graph node
    """

    paths = []
    loops_from_first = defaultdict(list)

    def _walk(start, path):
        """
        Find path all through graph and detect loop.
        """
        try:
            index = path.index(start)
        except ValueError:
            if not graph[start]:
                paths.append(path + (start,))
            else:
                for node in graph[start]:
                    _walk(node, path + (start,))
        else:
            loops_from_first[start].append(path[index + 1:] + (start,))
            paths.append(path + (start,))

    _walk(start, ())

    # Create cartesian product of loops regarding max_loop.
    original = loops_from_first.copy()
    for _ in range(max_loop - 2):
        tmp = defaultdict(list)
        for start, loops in loops_from_first.items():
            for loop_1 in loops:
                for loop_2 in original[start]:
                    tmp[start].append(loop_1 + loop_2)
        loops_from_first = tmp

    # Add loops to paths.
    if max_loop > 1:
        new_paths = []
        for path in paths:
            loops = loops_from_first[path[-1]]
            if not loops:
                new_paths.append(path)
            else:
                for loop in loops:
                    new_paths.append(path + loop)

        paths = new_paths

    return paths


class MetaTestState(type):
    """
    Generate all possible test scenarios from TestState subclass.
    Each test scenario is defined as unittest.TestCase subclass.

    The get_load_tests method generate test suite and return
    unittest load_tests function.
    """

    steps = defaultdict(dict)
    start_step = {}

    @staticmethod
    def _build_test_method(input_method, names_and_methods, start, previous_steps):
        """
        Build and return test method for unittest.TestCase class.

            previous_steps - list of previous step executed.
        """

        def test(self):
            """
            Execute start if exists, input if exists and test methods.
            """

            if start is not None:
                start(type(self))
            if input_method is not None:
                input_method(self)
            for name, method in names_and_methods:
                if (hasattr(method, 'previous_steps') and previous_steps and
                        previous_steps[-1] not in method.previous_steps):
                    continue

                func_condition = getattr(method, 'condition', lambda s: True)
                if func_condition(previous_steps):
                    with self.subTest(name=name):
                        method(self)
        return test

    @classmethod
    def _generate_senarios(mcs, subcls, max_loop):
        """
        Return list of senario, each senario is a list of states.
        """
        step_from_previous = defaultdict(list)
        for step in mcs.steps[subcls].values():
            for previous_step in step.previous:
                step_from_previous[previous_step].append(step.__name__)

        return walk(step_from_previous, mcs.start_step[subcls], max_loop)

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

    def get_test_cases(cls, max_loop):
        """
        Build and return unittest.TestCase subclasses.
        """
        mcs = type(cls)
        test_case_list = []
        for senario in mcs._generate_senarios(cls, max_loop):
            attrs = {}
            previous_step_name = None
            previous_steps_names = []
            for step_num, step_name in enumerate(senario):
                step = mcs.steps[cls][step_name]
                input_method = mcs._select_input_method(step.inputs,
                                                        previous_step_name)

                test_methods = tuple(
                    sorted((name, attr)
                           for name, attr
                           in vars(step).items()
                           if name.startswith('test')))

                method_name = "test_{:>04}_{}".format(
                    step_num, step_name.split('.')[-1].lower())

                attrs[method_name] = mcs._build_test_method(input_method,
                                                            test_methods,
                                                            getattr(step, 'start', None),
                                                            tuple(previous_steps_names))

                previous_step_name = step_name
                previous_steps_names.append(step_name)

            test_case_list.append(type(''.join(senario),
                                       (unittest.TestCase,) + step.__bases__,
                                       attrs))
        return test_case_list

    def get_load_tests(cls, max_loop=1):
        """
        Build and return load_tests function.
        """
        def load_tests(loader, tests, pattern):
            suite = unittest.TestSuite()
            for test in cls.get_test_cases(max_loop):
                suite.addTests(loader.loadTestsFromTestCase(test))
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

            base = next(base for base in bases
                        if issubclass(base, TestState))

            mcs.steps[base][cls_name] = cls
            if start:
                if base in mcs.start_step:
                    raise AssertionError("States '{}' and '{}' are start states. "
                                         "Only one start state is allowed."
                                         .format(mcs.start_step[base], cls_name))

                mcs.start_step[base] = cls_name

        return cls

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return MultiDict(dict(input='inputs'))


def previous(previous_steps):
    """
    This decorator define previous steps of decorated input methods.
    You can use previous to decorate a test method.

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


class Condition:
    """
    Condition is class base to set of condition for condition decorator.
    """

    def __neg__(self):
        return _NotWrap(self)

    def __and__(self, other):
        return _AndWrap(self, other)

    def __or__(self, other):
        return _OrWrap(self, other)


class _NotWrap(Condition):
    """
    Wrap condition and return a new condition.

    Wrapped condition call return not condition.
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, previous_steps):
        return not self.func(previous_steps)


class _AndWrap(Condition):
    """
    Wrap two condition and return a new condition.

    Wrapped condition calls return condition_1 and condition_2.
    """

    def __init__(self, func_1, func_2):
        self.func_1 = func_1
        self.func_2 = func_2

    def __call__(self, previous_steps):
        return self.func_1(previous_steps) and self.func_2(previous_steps)


class _OrWrap(Condition):
    """
    Wrap two condition and return a new condition.

    Wrapped condition calls return condition_1 or condition_2.
    """

    def __init__(self, func_1, func_2):
        self.func_1 = func_1
        self.func_2 = func_2

    def __call__(self, previous_steps):
        return self.func_1(previous_steps) or self.func_2(previous_steps)


class Path(Condition):
    """
    True if steps path is in previous steps.
    """

    def __init__(self, *steps):
        self.steps = tuple(steps)

    def __call__(self, previous_steps):
        previous_steps = tuple(previous_steps)
        length = len(self.steps)
        for i in range(len(previous_steps) - length + 1):
            if previous_steps[i : i + length] == self.steps:
                return True
        return False


class Newer(Condition):
    """
    True if step_2 is newer than step_1 or step_1 doesn't exist.
    """

    def __init__(self, step_1, step_2):
        self.step_1 = step_1
        self.step_2 = step_2

    def __call__(self, previous_steps):
        previous_steps = tuple(reversed(previous_steps))
        try:
            index_2 = previous_steps.index(self.step_2)
        except ValueError:
            return False

        try:
            index_1 = previous_steps.index(self.step_1)
        except ValueError:
            return True

        return index_1 > index_2


def condition(cond):
    """
    This decorator define condition to execute the decorated test method.
    """
    if not isinstance(cond, Condition):
        raise TypeError("First argument must be a Condition object such as Path or Newer.")

    def decorator(func):
        """
        Set condition attribute to decorated method.
        """
        func.condition = cond
        return func

    return decorator

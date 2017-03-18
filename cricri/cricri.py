"""
Module to generate test scenarios from scenario step.
"""

from collections import defaultdict
import socket
from subprocess import Popen, PIPE
import time
import types
import unittest
import operator
import re
import selectors

from voluptuous import ALLOW_EXTRA, All, Any, Invalid, Match, \
                       Optional, Range, Required, Schema


__all__ = ['MetaServerTestState', 'MetaTestState', 'TestServer', 'TestState']


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
    def _build_test_method(input_method, names_and_methods, previous_steps):
        """
        Build and return test method for unittest.TestCase class.

            previous_steps - list of previous step executed.
        """

        def test(self):
            """
            Execute input if exists, test methods
            """
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
    def _generate_scenarios(mcs, subcls, max_loop):
        """
        Return list of scenario, each scenario is a list of states.
        """
        try:
            start_step = mcs.start_step[subcls]
        except KeyError:
            raise ValueError("You must set 'start' attribut to "
                             "define the first '{}' subclass."
                             .format(subcls.__qualname__))

        step_from_previous = defaultdict(list)
        for step in mcs.steps[subcls].values():
            for previous_step in step.previous:
                step_from_previous[previous_step].append(step.__name__)

        return walk(step_from_previous, start_step, max_loop)

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

        for scenario in mcs._generate_scenarios(cls, max_loop):
            attrs = {}
            previous_step_name = None
            previous_steps_names = []
            for step_num, step_name in enumerate(scenario):
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
                                                            tuple(previous_steps_names))

                previous_step_name = step_name
                previous_steps_names.append(step_name)

            start_scenario = getattr(cls, 'start_scenario', None)
            if start_scenario is not None:
                if not isinstance(start_scenario, types.MethodType):
                    raise TypeError("{}.start_scenario must be a classmethod"
                                    .format(cls))

                attrs['setUpClass'] = start_scenario

            stop_scenario = getattr(cls, 'stop_scenario', None)
            if stop_scenario is not None:
                if not isinstance(start_scenario, types.MethodType):
                    raise TypeError("{}.stop_scenario must be a classmethod"
                                    .format(cls))

                attrs['tearDownClass'] = stop_scenario

            test_case_list.append(type(''.join(scenario),
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
                        if isinstance(base, mcs))

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

class MetaServerTestState(MetaTestState):
    """
    MetaTestState designed to test tcp server.
    """

    _port_def = Any(Match(r"\{.+\}$",
                          "int or string starts with '{' and ends with '}'"),
                    int)

    valid_attributes = Schema(
        {
            Required("tcp_clients", 'required class attribute'): [
                {
                    Required("name"): str,
                    Required("port"): _port_def,
                    Optional("timeout", default=2): Range(0, min_included=False),
                    Optional("tries", default=3): All(int, Range(0, min_included=False)),
                    Optional("wait", default=0.125): Range(0, min_included=False)
                }
            ],
            Required("commands", 'required class attribute'): [
                {
                    Required("name"): str,
                    Required("cmd"): [str],
                }
            ]
        },
        extra=ALLOW_EXTRA
    )

    def __new__(mcs, cls_name, bases, attrs, previous=None, start=False):

        if bases and TestServer in bases:
            try:
                attrs = mcs.valid_attributes(attrs)
            except Invalid as error:
                msg = "{} @ {}.{}".format(error.error_message,
                                          cls_name, error.path[0])
                msg += ''.join('[{!r}]'.format(element)
                               for element in error.path[1:])

                raise AttributeError(msg)

        return super().__new__(mcs, cls_name, bases, attrs,
                               previous, start)


class TestServer(metaclass=MetaServerTestState):
    """
    TestServer subclasses must define *tcp_clients* and
    *commands* attributes

    tcp_clients must be a list containing dict with *name* and *port* keys.
    The *port* must be an integer you can use a string surrounded by curly
    brackets and the OS will then pick a free port. The *timeout*, *tries* and
    *wait* keys are optional and allow you to manage TCP connection.

    The *commands* must be a list containing dict with *name* and *cmd* keys.
    cmd is list of sequence of program arguments the first element is a program.

    Example::

        class MyTestServer(TestServer):

            tcp_clients = [
                {
                    "name": "Alice",
                    "port": "{port-1}",
                },
                {
                    "name": "Bob",
                    "port": "{port-1}",
                }
            ]

            commands = [
                {
                    "name": "my_server",
                    "cmd": ["python3", "server.py", "{port-1}"],
                }
            ]
    """

    tcp_clients = []
    commands = []

    class _Server:
        """
        Wrap server process and provide assert methods.
        """

        def __init__(self, parameters):
            self.popen = Popen(
                parameters,
                stdout=PIPE,
                stderr=PIPE
            )

            self.selector = selectors.DefaultSelector()
            self.selector.register(self.popen.stdout,
                                   selectors.EVENT_READ,
                                   ('stdout', "server-2"))
            self.selector.register(self.popen.stderr,
                                   selectors.EVENT_READ,
                                   ('stderr', "server-3"))

        def assert_stdout_is(self, expected, timeout):
            """
            Test that server logs *expected* on the stdout before *timeout*
            """
            self._assert_output(operator.eq, '{read} != {expected}',
                                'stdout', expected, timeout)

        def assert_stderr_is(self, expected, timeout):
            """
            Test that server logs *expected* on the stderr before *timeout*
            """
            self._assert_output(operator.eq, '{read} != {expected}',
                                'stderr', expected, timeout)

        def assert_stdout_regex(self, regex, timeout):
            """
            Test that server logs on stdout before *timeout*
            and message matches *regex*
            """
            self._assert_output(lambda a, b: re.search(b, a),
                                "{read} doesn't match {expected}",
                                'stdout', regex, timeout)

        def assert_stderr_regex(self, regex, timeout):
            """
            Test that server logs on stderr before *timeout*
            and message matches *regex*
            """
            self._assert_output(lambda a, b: re.search(b, a),
                                "{read} doesn't match {expected}",
                                'stderr', regex, timeout)

        def _assert_output(self, test_func, assert_msg,
                           output, expected, timeout):
            read = None
            start = time.time()
            not_expected_reads = b''
            while read is None:
                keys = self.selector.select(timeout=timeout)
                if not keys:
                    break

                for key, events in keys:
                    if key.data[0] == output:
                        read = key.fileobj.read1(4096)
                        if test_func(read.decode('utf-8'), expected):
                            return

                        not_expected_reads += read
                        read = None
                        break

                timeout -= (time.time() - start)

            if read is None:
                raise AssertionError("Timeout: No data received")
            else:
                raise AssertionError(
                    assert_msg.format(expected=expected,
                                      read=not_expected_reads.decode('utf-8')))

        def kill(self):
            """
            Kill the process with SIGKILL
            """
            self.popen.kill()


    class _Client:
        def __init__(self, port, timeout, tries, wait):
            self.socket = socket.socket(socket.AF_INET,
                                        socket.SOCK_STREAM)

            self.socket.settimeout(timeout)

            socket_error = None
            for _ in range(tries):
                start = time.time()
                try:
                    self.socket.connect(("127.0.0.1", int(port)))
                except socket.timeout as error:
                    socket_error = error
                except OSError as error:
                    socket_error = error
                    if wait is None:
                        time.sleep(timeout - (time.time() - start))
                    else:
                        time.sleep(wait)
                else:
                    socket_error = None
                    break

            if socket_error is not None:
                print(str(socket_error))

        def close(self):
            """
            Close the socket client.
            """
            self.socket.close()

        def send(self, msg):
            """
            send *msg*
            """
            self.socket.send(msg.encode('utf-8'))

        def assert_receive(self, expected, timeout=2):
            """
            Test that client received *expected* before *timeout*.
            """
            self.socket.settimeout(timeout)
            try:
                msg = self.socket.recv(256)
            except socket.timeout:
                raise AssertionError("Timeout: No data received")

            if msg.decode('utf-8') != expected:
                raise AssertionError('{} != {}'
                                     .format(msg.decode('utf-8'),
                                             expected))

        def assert_receive_regex(self, regex, timeout=2):
            """
            Test that client received data before *timeout* and data
            matches *regex*.
            """
            self.socket.settimeout(timeout)
            try:
                msg = self.socket.recv(256)
            except socket.timeout:
                raise AssertionError("Timeout: No data received")

            if re.search(regex, msg.decode('utf-8')):
                raise AssertionError("{} doesn't match {}"
                                     .format(msg.decode('utf-8'),
                                             regex))

    virtual_ports = {}
    clients = {}
    servers = {}

    @staticmethod
    def get_free_tcp_port():
        """
        Return an unused local tcp port.
        """
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind(('', 0))
        port = tcp.getsockname()[1]
        tcp.close()
        return port

    @classmethod
    def start_scenario(cls):
        """
        Launches defined servers and provides *clients*, *servers* and
        *virtual_ports* class attributes.
        """
        for command in cls.commands:
            parameters = []
            for parameter in command['cmd']:
                if parameter.startswith('{') and parameter.endswith('}'):
                    port = cls.virtual_ports.get(parameter)
                    if port is None:
                        port = cls.get_free_tcp_port()
                        cls.virtual_ports[parameter] = port
                    parameters.append(str(port))
                else:
                    parameters.append(parameter)

            cls.servers[command['name']] = cls._Server(parameters)

        for tcp_client in cls.tcp_clients:
            port = tcp_client['port']
            if port.startswith('{') and port.endswith('}'):
                port = cls.virtual_ports[port]

            client = cls._Client(port,
                                 tcp_client['timeout'],
                                 tcp_client['tries'],
                                 tcp_client['wait'])

            cls.clients[tcp_client['name']] = client

    @classmethod
    def stop_scenario(cls):
        """
        Kill servers
        """
        for client in cls.clients.values():
            client.close()
        for server in cls.servers.values():
            server.kill()

        cls.virtual_ports.clear()
        cls.clients.clear()
        cls.servers.clear()

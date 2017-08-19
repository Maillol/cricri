"""
Module to generate test scenarios from scenario step.
"""

import operator
import re
import selectors
import signal
import socket
import time
import types
import unittest
from collections import defaultdict
from subprocess import PIPE, Popen

from voluptuous import (ALLOW_EXTRA, All, Any, Invalid, Match, Optional, Range,
                        Required, Schema)

from .algo import walk
from .http_client import HTTPClient
from .tcp_client import TCPClient

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


class MetaTestState(type):
    """
    Generate all possible test scenarios from TestState subclass.
    Each test scenario is defined as unittest.TestCase subclass.

    The get_load_tests method generate test suite and return
    unittest load_tests function.
    """

    steps = defaultdict(dict)
    start_step = {}

    class PrefixTestMethod:
        """
        Provide method to prefix testCase method in order to keep
        them sorted.

        You could use PrefixTestMethod.set_prefix_size(new_prefix_size)
        if your generated testCase needs more than 99999 - default prefix size
        is 5 - tests methods.
        """

        _count_digit = 0
        _prefix = 'test_'
        _suffix = '_'
        _template = ''
        _regex = None

        @classmethod
        def add(cls, num, name):
            """
            Adds prefix to name using num.
            """
            return cls._template.format(num, name)

        @classmethod
        def strip(cls, name):
            """
            Strips prefix to name.
            """
            return cls._regex.sub('', name)

        @classmethod
        def len(cls):
            """
            Returns the lenght of generated prefix.
            """
            return len(cls._prefix) + cls._count_digit + len(cls._suffix)

        @classmethod
        def set_prefix_size(cls, count_digit):
            """
            Set a new prefix size. The parameters define the
            number of fixed digit between `test_` and `_`

            set_prefix_size(4) allow prefix between `test_0000_`
            and `test_9999_`
            """
            cls._count_digit = count_digit
            cls._template = '{cls._prefix}' \
                            '{{:>0{cls._count_digit}}}' \
                            '{cls._suffix}{{}}'.format(cls=cls)
            cls._regex = re.compile(
                r'{}\d{{{}}}{}'.format(
                    cls._prefix, cls._count_digit, cls._suffix))

    PrefixTestMethod.set_prefix_size(5)

    @staticmethod
    def _build_test_method(input_method, names_and_methods, skipper):
        """
        Build and return test method for unittest.TestCase class.
        """

        def test(self):
            """
            Execute input if exists, test methods
            """
            if skipper.skip:
                self.skipTest(skipper.reason)

            if input_method is not None:
                try:
                    input_method(self)
                except Exception:
                    skipper.skip = True
                    skipper.reason = 'Exception occurred in {}' \
                        .format(input_method.__qualname__)
                    raise

                for name, method in names_and_methods:
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
    def method_is_enable(mtd, previous_steps):
        """
        Return True if mtd is enable regarding previous_step.
        """
        condition = getattr(mtd, 'condition',
                            lambda _steps: True)
        if condition(previous_steps):
            if not hasattr(mtd, 'previous_steps'):
                return True
            if previous_steps:
                return previous_steps[-1] in mtd.previous_steps
            return True
        return False

    @staticmethod
    def _select_input_method(inputs, previous_steps):
        """
        Select input method using previous_steps.

        inputs - list of input method decorated with previous decorator.
        previous_step - string, name of previous steps.
        """

        valids_inputs = [input_mtd
                         for input_mtd
                         in inputs
                         if MetaTestState.method_is_enable(input_mtd,
                                                           previous_steps)]

        if len(valids_inputs) > 1:
            step_name = valids_inputs[0].__qualname__.rsplit('.', 1)[0]
            raise AttributeError('Multiple inputs methods are valid in {}'
                                 .format(step_name))

        if valids_inputs:
            return valids_inputs[0]

    def _set_mtd(cls, mtd_name, attrs, key_name):
        """
        Add mtd_name to attrs dict.

            attrs[key_name] = cls.mtd_name
        """
        mtd = getattr(cls, mtd_name, None)
        if mtd is not None:
            if not isinstance(mtd, types.MethodType):
                raise TypeError("{}.{} must be a classmethod"
                                .format(cls, mtd_name))
            attrs[key_name] = mtd

    @classmethod
    def _build_str_method(mcs, attrs):
        """
        Build and add `__str__` method to `attrs` dict.
        """

        sorted_test_methods = sorted(
            attr for attr in attrs if attr.startswith('test_'))

        offset = 0
        test_method_indices = {}
        for indice, attr in enumerate(sorted_test_methods, 1):
            offset = max(offset, len(attr))
            test_method_indices[attr] = indice
        offset -= mcs.PrefixTestMethod.len()

        count_test_method = len(test_method_indices)
        template = '{{:<{}}} ({{:>0{}}}/{})'.format(
            offset, len(str(count_test_method)), count_test_method)

        def __str__(self):
            try:
                method_name = mcs.PrefixTestMethod.strip(self._testMethodName)
                return template.format(
                    method_name, test_method_indices[self._testMethodName])
            except (KeyError, AttributeError):
                return unittest.TestCase.__str__(self)

        attrs['__str__'] = __str__

    def get_test_cases(cls, max_loop):
        """
        Build and return unittest.TestCase subclasses.
        """
        mcs = type(cls)
        test_case_list = []

        for scenario in mcs._generate_scenarios(cls, max_loop):
            attrs = {}
            previous_steps_names = []
            skipper = types.SimpleNamespace(skip=False, reason='')

            for step_num, step_name in enumerate(scenario):
                step = mcs.steps[cls][step_name]
                input_method = mcs._select_input_method(step.inputs,
                                                        previous_steps_names)

                test_methods = tuple(
                    sorted((name, attr)
                           for name, attr
                           in vars(step).items()
                           if name.startswith('test')
                           and mcs.method_is_enable(attr,
                                                    previous_steps_names)))

                method_name = mcs.PrefixTestMethod.add(
                    step_num, step_name.split('.')[-1].lower())

                attrs[method_name] = mcs._build_test_method(input_method,
                                                            test_methods,
                                                            skipper)

                previous_steps_names.append(step_name)

            cls._set_mtd('start_scenario', attrs, 'setUpClass')
            cls._set_mtd('stop_scenario', attrs, 'tearDownClass')

            mcs._build_str_method(attrs)
            test_case_list.append(type(''.join(scenario),
                                       (unittest.TestCase,) + step.__bases__,
                                       attrs))
        return test_case_list

    def get_load_tests(cls, max_loop=0):
        """
        Build and return load_tests function.
        """
        def load_tests(loader, tests, pattern):
            """
            unittest hook responsible for loading
            all tests in the package.
            """
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
    def __prepare__(mcs, _name, _bases, **kwargs):
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
            Optional("http_clients", 'required class attribute'): [
                {
                    Required("name"): str,
                    Required("host"): str,
                    Required("port"): _port_def,
                    Optional("timeout", default=2): Range(0, min_included=False),
                    Optional("tries", default=3): All(int, Range(0, min_included=False)),
                    Optional("wait", default=1): Range(0, min_included=False),
                    Optional("headers", default=[]): list,
                    Optional("extra_headers", default=None): Any(list, None)
                }
            ],

            Optional("tcp_clients", 'required class attribute'): [
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
                    Optional("kill-signal", default=signal.SIGINT): int
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

    The *commands* must be a list containing dict with *name*, *cmd* and
    "kill-signal" keys.
    *cmd* is list of sequence of program arguments the first element is a
    program.
    *kill-signal* should be a enumeration members of
    :py:class: `signal.Signals`

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

    http_clients = []
    tcp_clients = []
    commands = []

    class _Server:
        """
        Wrap server process and provide assert methods.
        """

        def __init__(self, parameters, kill_signal):
            """
            parameters - The list of Popen parameters.
            kill_signal - The signal used to kill the process.
            """
            self.popen = Popen(
                parameters,
                stdout=PIPE,
                stderr=PIPE
            )

            self.kill_signal = kill_signal
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

                for key, _ in keys:
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
            Kill the process using `kill_signal` attribute.
            """
            self.selector.unregister(self.popen.stdout)
            self.selector.unregister(self.popen.stderr)
            self.popen.stderr.close()
            self.popen.stdout.close()
            self.selector.close()
            self.popen.send_signal(self.kill_signal)

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
                for virtual_port in set(re.findall('{.+?}', parameter)):
                    port = cls.virtual_ports.get(virtual_port)
                    if port is None:
                        port = cls.get_free_tcp_port()
                        cls.virtual_ports[virtual_port] = port

                    parameter = parameter.replace(virtual_port, str(port))

                parameters.append(parameter)

            cls.servers[command['name']] = cls._Server(
                parameters, command['kill-signal'])

        for tcp_client in cls.tcp_clients:
            port = tcp_client['port']
            if port.startswith('{') and port.endswith('}'):
                port = cls.virtual_ports[port]

            cls.clients[tcp_client['name']] = TCPClient(
                port,
                tcp_client['timeout'],
                tcp_client['tries'],
                tcp_client['wait'])

        for http_client in cls.http_clients:
            port = http_client['port']
            if port.startswith('{') and port.endswith('}'):
                port = cls.virtual_ports[port]

            cls.clients[http_client['name']] = HTTPClient(
                http_client['host'],
                port,
                http_client['timeout'],
                http_client['tries'],
                http_client['wait'],
                http_client['headers'],
                http_client['extra_headers'])

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

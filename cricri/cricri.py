"""
Module to generate test scenarios from scenario step.
"""

import os
import re
import signal
import socket
import types
import unittest
from collections import defaultdict

from voluptuous import ALLOW_EXTRA, Any, Invalid, Optional, Required, Schema

from .algo import walk
from .inet import Client, Server
from .inet.http_client import HTTPClient
from .inet.tcp_client import TCPClient

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


def to_underscore(name):
    """
    >>> to_underscore("FooBar")
    'foo_bar'
    >>> to_underscore("HTTPServer")
    'http_server'
    """
    if not name:
        return name
    iterator = iter(name)
    out = [next(iterator).lower()]
    last_is_upper = True
    parse_abbreviation = False
    for char in iterator:
        if char.isupper():
            if last_is_upper:
                parse_abbreviation = True
                out.append(char.lower())
            else:
                out.append('_' + char.lower())
            last_is_upper = True
        else:
            if parse_abbreviation:
                out.insert(-1, '_')
                parse_abbreviation = False
            out.append(char)
            last_is_upper = False
    return "".join(out)


class MetaTestState(type):
    """
    Generate all possible test scenarios from TestState subclass.
    Each test scenario is defined as unittest.TestCase subclass.

    The get_load_tests method generate test suite and return
    unittest load_tests function.
    """

    steps = defaultdict(dict)
    start_step = {}
    _roots = set()

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

        step_classes_from_name = mcs.steps[subcls]
        step_from_previous = defaultdict(list)
        for step in step_classes_from_name.values():
            for previous_step in step.previous:
                if previous_step not in step_classes_from_name:
                    raise ValueError("The previous `{}` defined in {}"
                                     " class doesn't exist".
                                     format(previous_step, step.__qualname__))
                step_from_previous[previous_step].append(step.__name__)

        return walk(step_from_previous, start_step, max_loop)

    @staticmethod
    def method_is_enable(mtd, previous_steps):
        """
        Return True if mtd is enable regarding previous_step.
        """
        condition = getattr(mtd, 'condition',
                            lambda _steps: True)
        return condition(previous_steps)

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
        return None

    def _set_mtd(cls, mtd_name, attrs, key_name, super_at_start=True):
        """
        Add mtd_name to attrs dict.

            attrs[key_name] = cls.mtd_name
        """
        mtd = getattr(cls, mtd_name, None)
        if mtd is not None:
            if not isinstance(mtd, types.MethodType):
                raise TypeError("{}.{} must be a classmethod"
                                .format(cls, mtd_name))
            unbound_super = getattr(cls.base_class, key_name).__func__

            if super_at_start:
                def func(cls):
                    unbound_super(cls)
                    mtd()
            else:
                def func(cls):
                    mtd()
                    unbound_super(cls)

            func.__name__ = key_name
            attrs[key_name] = classmethod(func)

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
                    method_name.replace('_', ' '),
                    test_method_indices[self._testMethodName])
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

                if not step.inputs:
                    def input_method(self):
                        return None
                else:
                    input_method = mcs._select_input_method(
                        step.inputs, previous_steps_names)

                test_methods = tuple(
                    sorted((name, attr)
                           for name, attr
                           in vars(step).items()
                           if name.startswith('test')
                           and mcs.method_is_enable(attr,
                                                    previous_steps_names)))

                method_name = mcs.PrefixTestMethod.add(
                    step_num, to_underscore(step_name.split('.')[-1]))

                attrs[method_name] = mcs._build_test_method(input_method,
                                                            test_methods,
                                                            skipper)

                previous_steps_names.append(step_name)

            cls._set_mtd('start_scenario', attrs, 'setUpClass', True)
            cls._set_mtd('stop_scenario', attrs, 'tearDownClass', False)

            attrs['__generated_by_cricri__'] = True
            mcs._build_str_method(attrs)
            test_case_list.append(type(''.join(scenario),
                                       (cls.base_class,) + step.__bases__,
                                       attrs))
        return test_case_list

    def get_load_tests(cls, max_loop=0):
        """
        Build and return load_tests function.
        """
        def load_tests(loader, standard_tests, pattern):
            """
            unittest hook responsible for loading
            all tests in the package.
            """

            if loader.__module__.startswith('nose2.'):
                unittest_loader = unittest.TestLoader()
                for test in cls.get_test_cases(max_loop):
                    standard_tests.addTests(
                        unittest_loader.loadTestsFromTestCase(test))

                def suite_factory(extra_tests=()):
                    return standard_tests

                loader.suiteClass = suite_factory

            else:
                for test in cls.get_test_cases(max_loop):
                    standard_tests.addTests(loader.loadTestsFromTestCase(test))

            return standard_tests

        return load_tests

    def __init__(cls, cls_name, bases, attrs, **kwargs):
        type.__init__(cls, cls_name, bases, attrs)

    def __new__(mcs, cls_name, bases, attrs, previous=None, start=False):
        cls = type.__new__(mcs, cls_name, bases, attrs)
        if '__generated_by_cricri__' in attrs:
            return cls

        if bases:
            base = next(base for base in bases
                        if isinstance(base, mcs))

            #  If cls is a direct TestState/TestServer subclass.
            if base in mcs._roots:
                setattr(cls, 'base_class', getattr(
                    cls, 'base_class', unittest.TestCase))
                return cls

            if previous is None:
                cls.previous = []
            else:
                cls.previous = previous

            for step in cls.previous:
                if not isinstance(step, str):
                    raise TypeError('The element of previous should be a str'
                                    ' (`{}` found in `{}`)'.
                                    format(step, cls_name))

            mcs.steps[base][cls_name] = cls
            if start:
                if base in mcs.start_step:
                    raise AssertionError("States '{}' and '{}' are start states. "
                                         "Only one start state is allowed."
                                         .format(mcs.start_step[base], cls_name))

                mcs.start_step[base] = cls_name

        else:
            mcs._roots.add(cls)

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

        class Base(TestState):
            pass

        class StateA(Base, start=True):
            def input(self):
                type(self).machine = Machine()


        class StateB(Base, previous=['StateA']):
            def input(self):
                type(self).machine.m1()


        class StateC(Base, previous=['StateA', 'StateB']):

            @previous(['StateA'])
            def input(self):
                type(self).machine.m2()

            @previous(['StateB'])
            def input(self):
                type(self).machine.m1()
    """


class MetaServerTestState(MetaTestState):
    """
    MetaTestState designed to test servers.
    """

    _class_clients = {}

    @classmethod
    def bind_class_client(mcs, class_client):
        """
        You can use the `bind_class_client̀` method to allow each `TestServer`
        subclass to manage a new `Client`.

        To crete a new `Client`, you should subclass `cricri.inet.Client` and
        define the `validator` static method and the `close` method.

        .. testcode::

            from urllib.request import urlopen

            from cricri import MetaServerTestState
            from cricri.inet import Client


            class MyCustomClient(Client):

                attr_name = 'my_custom_clients'

                def __init__(self, host):
                    self.host = host
                    self.response = None

                @staticmethod
                def validator():
                    return {
                        'host': str
                    }

                def close(self):
                    if self.response is not None:
                        self.response.close()

                def url_open(self, page):
                    self.response = self.urlopen(self.host + '/' + page)
                    self.content = self.response.read()

                def assert_page_content(self, text):
                    if text not in self.content:
                        raise AssertionError(
                            '{} in not {}'.format(text, self.content))


            MetaServerTestState.bind_class_client(MyCustomClient)

        """
        if not issubclass(class_client, Client):
            raise TypeError('First parameters should be a `Client` subclass')

        client_already_bound = mcs._class_clients.get(class_client.attr_name)
        if client_already_bound:
            raise ValueError(
                'attribute `{clt.attr_name}` already is bound to'
                ' `{clt_bound.__qualname__}` client. If you want bind'
                ' `{clt.__qualname__}` to an other attribute, set'
                ' `{clt.__qualname__}.attr_name` with an other value than'
                ' {clt.attr_name}'.format(clt=class_client,
                                          clt_bound=client_already_bound))

        mcs._class_clients[class_client.attr_name] = class_client

    @classmethod
    def forget_client(mcs, attr_name_or_client):
        """
        Forget a `Client`.

        Args:
            attr_name_or_client: The client or the attr_name bound to forget.
        """
        if isinstance(attr_name_or_client, str):
            mcs._class_clients.pop(attr_name_or_client)
        else:
            mcs._class_clients.pop(attr_name_or_client.attr_name)

    @classmethod
    def _build_attributes_validator(mcs):
        """
        Returns validator to validate the sub-classes attributes.
        """

        valid_attributes = {
            Required("commands", 'required class attribute'): [
                {
                    Required("name"): str,
                    Required("cmd"): [str],
                    Optional("kill-signal", default=signal.SIGINT): int,
                    Optional("env", default=None): Any(None, dict),
                    Optional("extra-env", default=None): Any(None, dict)
                }
            ]
        }

        for attr_name, class_client in mcs._class_clients.items():
            client_validator = {
                Required("name"): str,
            }
            client_validator.update(class_client.validator())

            key = Optional(attr_name, 'required class attribute')
            valid_attributes[key] = [client_validator]

        return Schema(valid_attributes, extra=ALLOW_EXTRA)

    def __new__(mcs, cls_name, bases, attrs, previous=None, start=False):
        if bases and TestServer in bases:

            for attr_name in mcs._class_clients:
                attrs.setdefault(attr_name, [])

            validate_attributes = mcs._build_attributes_validator()
            try:
                attrs = validate_attributes(attrs)

            except Invalid as error:
                msg = "{} @ {}.{}".format(error.error_message,
                                          cls_name, error.path[0])
                msg += ''.join('[{!r}]'.format(element)
                               for element in error.path[1:])

                raise AttributeError(msg)

        return MetaTestState.__new__(mcs, cls_name, bases, attrs, previous,
                                     start)


MetaServerTestState.bind_class_client(HTTPClient)
MetaServerTestState.bind_class_client(TCPClient)


class TestServer(metaclass=MetaServerTestState):
    """
    TestServer subclasses must define *tcp_clients* and
    *commands* attributes

    tcp_clients must be a list containing dict with *name* and *port* keys.
    The *port* must be an integer you can use a string surrounded by curly
    brackets and the OS will then pick a free port. The *timeout*, *tries* and
    *wait* keys are optional and allow you to manage TCP connection.

    The *commands* must be a list containing dict with:
        - name (required) the name of command
        - cmd (required) list of sequence of program arguments the first
            element is a program.
        - kill-signal (optional) should be an enumeration members of
            :py:class: `signal.Signals`
        - env (optional) A dict that defines the environment variables
        - extra-env (optional) A dict that add environment variables

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
                    "env": {
                        "PYTHONPATH": "path/to/project"
                    }
                    "cmd": ["python3", "server.py", "{port-1}"],
                }
            ]
    """

    commands = []
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

            if command['extra-env']:
                command['env'] = os.environ.copy()
                command['env'].update(command['extra-env'])

            cls.servers[command['name']] = Server(
                parameters, command['kill-signal'], command['env'])

        for attr_name, class_client in type(cls)._class_clients.items():
            for client_init_values in getattr(cls, attr_name):
                client_init_values = client_init_values.copy()
                port = client_init_values.get('port')
                if port is not None:
                    if isinstance(port, str) and port.startswith(
                            '{') and port.endswith('}'):
                        client_init_values['port'] = cls.virtual_ports[port]

                client_name = client_init_values.pop('name')
                cls.clients[client_name] = class_client(**client_init_values)

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

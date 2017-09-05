import unittest

import voluptuous

from cricri.cricri import (MetaServerTestState, MetaTestState, MultiDict,
                           TestServer, walk)
from cricri.inet import Client


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


class TestPrefixTestMethod(unittest.TestCase):
    def setUp(self):
        MetaTestState.PrefixTestMethod.set_prefix_size(4)

    def test_add(self):
        result = MetaTestState.PrefixTestMethod.add(7, 'pif_paf')
        self.assertEqual('test_0007_pif_paf', result)

    def test_strip(self):
        result = MetaTestState.PrefixTestMethod.strip('test_0007_pifpaf')
        self.assertEqual('pifpaf', result)

    def test_len(self):
        self.assertEqual(MetaTestState.PrefixTestMethod.len(), 10)


class TestCustomClientCreation(unittest.TestCase):

    def setUp(self):
        spy = unittest.mock.Mock()

        class MyClient(Client):
            attr_name = 'my_clients'

            @staticmethod
            def validator():
                return {
                    voluptuous.Required('foo'): int,
                    voluptuous.Optional('bar', default='def bar'): str
                }

            def __init__(self, **kwargs):
                spy(kwargs)

            def close(self):
                spy('close')

        self.spy = spy
        MetaServerTestState.bind_class_client(MyClient)
        self.addCleanup(lambda: MetaServerTestState.forget_client(MyClient))

    def test_test_server_sub_class_should_have_my_clients_attr(self):

        class MySubClass(TestServer):
            commands = []

        self.assertTrue(hasattr(MySubClass, 'my_clients'))

    def test_start_scenario_should_instantiate_client(self):

        class MySubClass(TestServer):
            commands = []
            my_clients = [{
                "name": "my-client-1",
                "foo": 38938
            }]

        MySubClass.start_scenario()
        self.spy.assert_called_with(
            {'foo': 38938, 'bar': 'def bar'})

    def test_stop_scenario_should_stop_client(self):

        class MySubClass(TestServer):
            commands = []
            my_clients = [{
                "name": "my-client-1",
                "foo": 38938
            }]

        MySubClass.start_scenario()
        MySubClass.stop_scenario()
        self.spy.assert_called_with('close')

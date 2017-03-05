.. gentest documentation master file, created by
   sphinx-quickstart on Sun Dec 18 08:26:14 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Gentest's documentation
==================================

Gentest is a test scenario generator. You define steps using TestState class.
Each step has input method, set of tests methods, and one or multiple previous steps.
Gentest finds all paths in the steps and generates one Test Case for each
path. You can disable test steps depending on the path traveled.


Installation
=============

Installing with pip::

    pip install gentest

Installing with git::

    git clone https://github.com/Maillol/scenario.git gentest
    cd gentest
    python3 setup.py install


Basic example
=============

Here is a simple example with three steps to generate two scenario wich test list method::

    from gentest import TestState, previous


    class BaseTestState(TestState):

        @classmethod
        def start_scenario(cls):
            cls.l = [1, 3, 2, 4]

    class Create(BaseTestState, start=True):

        def test_1(self):
            self.assertEqual(self.l, [1, 3, 2, 4])


    class Reverse(BaseTestState, previous=['Create']):
        def input(self):
            self.l.reverse()

        def test_1(self):
            self.assertEqual(self.l, [4, 2, 3, 1])


    class Sort(BaseTestState, previous=['Create', 'Reverse']):
        def input(self):
            self.l.sort()

        def test_1(self):
            self.assertEqual(self.l, [1, 2, 3, 4])


    load_tests = BaseTestState.get_load_tests()


The *BaseTestState* is created by subclassing *gentest.TestState*.
This subclass defines *start_scenario* method in order to store the object
to be tested in a class attribute.
The *start_scenario* method will be called once at the beginning of each generated scenario.

Each *BaseTestState* subclass defines a scenario step.
*start attribute* allow you to define the first step. Here *Create* class is the first step.
*previous attribute* allow you to define when step is executed. Here *Reverse* step is executed
when *Create* step is done and *Sort* step can be executed when *Create* or *Reverse* step is done.

This three steps define two scenario:
    - Create, Reverse and Sort list.
    - Create and Sort list.

Each step has input method. This method is called before test methods of step.

The last statement allows unittest to manage this module. It generate all unittest.TestCase classes.

To run this script, use unittest command-line interface::

    $ python3 -m unittest -v test_scenario_list

You will see the following output::

    test_0000_create (gentest.CreateReverseSort) ... ok
    test_0001_reverse (gentest.CreateReverseSort) ... ok
    test_0002_sort (gentest.CreateReverseSort) ... ok
    test_0000_create (gentest.CreateSort) ... ok
    test_0001_sort (gentest.CreateSort) ... ok

    ----------------------------------------------------------------------
    Ran 5 tests in 0.001s

    OK


Test TCP server
===============

gentest provides *TestServer* class to test TCP server. You must subclasse
*TestServer* and define your servers and clients::

    class TestChatServer(TestServer):

        commands = [
            {
                "name": "chat-server",
                "cmd": ["python3", "-u", "chat_server.py", "{port-1}"],
            }
        ]

        tcp_clients = [
            {
                "name": "Alice",
                "port": "{port-1}",
            }
        ]

This example define *TestChatServer* class, which define command to launch server and
tcp client. Before each scenario running, 'python3 -u chat_server.py {port-1}' is executed
and a tcp client is connected to '{port-1}'. The string '{port-1}' will be bound by the
fist free TCP port.

You may reference defined clients and servers in your *TestChatServer* subclasses using *clients*
and *servers* attributes::

    class Start(TestChatServer, start=True):

        def test_server_listen(self):
            self.servers['chat-server'].assert_stdout_is(
                'server listen', timeout=2
            )

    class AliceAskedNickname(TestChatServer, previous=["Start"]):

        def input(self):
            self.clients["Alice"].send("MY_NAME_IS;Alice;")

        def test_alice_should_receive_ok(self):
            self.clients["Alice"].assert_receive('OK')


In this example, the *Start* step class test that server write 'server listen' to stdout.
The *AliceAskedNickname* class send 'MY_NAME_IS;Alice;' string to the server and test that
Alice receive 'OK'.


Assert client methods
---------------------

.. method:: assert_receive(self, expected, timeout=2)

    Test that client received *expected* before *timeout*.

.. method:: assert_receive_regex(self, regex, timeout=2)

    Test that client received data before *timeout* and data matches *regex*.


Assert server methods
---------------------

.. method:: assert_stdout_is(expected, timeout=2)

    Test that server logs *expected* on the stdout before *timeout*.

.. method:: assert_stderr_is(expected, timeout=2)

    Test that server logs *expected* on the stderr before *timeout*.

.. method:: assert_stdout_regex(regex, timeout=2)

    Test that server logs on stdout before *timeout* and message matches *regex*.

.. method:: assert_stderr_regex(regex, timeout=2)

    Test that server logs on stderr before *timeout* and message matches *regex*.


previous decorator
==================

The previous decorator allows you to have a conditional execution of input or test method.
this function takes a list of steps names::


    class B1(BaseTestState):
        ...

    class B2(BaseTestState):
        ...

    class C(BaseTestState, previous=['B1', 'B2']):

        @previous(['B1'])  # Called when previous step is B1
        def input(self):
            ...

        @previous(['B2'])  # Called when previous step is B2
        def input(self):
            ...

        @previous(['B1'])  # Called when previous step is B1
        def test_1(self):
            ...

        @previous(['B2'])  # Called when previous step is B2
        def test_2(self):
            ...


Note that TestState subsubclass can have severals input method if previous decorator is used.


condition decorator
===================

The conditional decorator allows you to have a conditional execution of test method.
this function takes a Condition objects such as Path or Newer.

Example::


    class Connect(BaseTestState, start=True, previous=['Disconnect']):
        ...

    class Disconnect(BaseTestState, previous=['Connect']):
        ...

    class PrepareMsg(BaseTestState, previous=['Disconnect', 'Connect']):
        ...

    class Send(BaseTestState, previous=['PrepareMsg']):

        # Called when Connect call is newer than Disconnect call.
        @condition(Newer('Disconnect', 'Connect'))
        def test_error(self):
            ...

        # Called when Disconnect call is newer than Connect call.
        @condition(Newer('Connect', 'Disconnect'))
        def test_msg_send(self):
            ...

Condition object
================

The Conditions objets are used in condition decorator.

You can combine Condition objects using operator.

+------------+------------+----------------------------------+
| Operator   | Meaning    | Example                          |
+============+============+==================================+
|  \-        | not        | \- Path('A', 'B')                |
+------------+------------+----------------------------------+
|  &         | and        | Path('A', 'B') & Path('F', 'G')  |
+------------+------------+----------------------------------+
|  \|        | or         | Path('A', 'B') \| Path('F', 'G') |
+------------+------------+----------------------------------+

Built-in Condition
------------------

Path
~~~~

Path(step [,step2 [...]]) is enable if the given contigious steps have executed.

Example:

+-----------------------------------------------+
|        @condition(Path("I", "J"))             |
+----------------+------------------------------+
| Executed steps | Decorated method is executed |
+================+==============================+
| I, J           | True                         |
+----------------+------------------------------+
| J, I, J, I     | True                         |
+----------------+------------------------------+
| J, I           | False                        |
+----------------+------------------------------+
| I, K, J        | False                        |
+----------------+------------------------------+
| K, J           | False                        |
+----------------+------------------------------+

Newer
~~~~~

Newer(step1, step2) is enable if step2 execution is newer than step1 execution or step1 has not executed.

Example:

+-----------------------------------------------+
|        @condition(Newer("I", "J"))            |
+----------------+------------------------------+
| Executed steps | Decorated method is executed |
+================+==============================+
| I, J           | True                         |
+----------------+------------------------------+
| J, I, J, I     | False                        |
+----------------+------------------------------+
| J, I           | False                        |
+----------------+------------------------------+
| I, K, J        | True                         |
+----------------+------------------------------+
| K, J           | True                         |
+----------------+------------------------------+

How to create a custom Condition
--------------------------------

You can create a custom Condition by inheriting from Condition class and overriding the \_\_call__ method.
The \_\_call__ method takes *previous_steps* parameter - *previous_steps* parameters is a list of executed step names -
and return True if decorated method must be executed else False.

Here is a Condition wich is enable when step appears a given number of times::

    class Count(Condition):

        def __init__(self, step, count):
            self.step = step
            self.count = count

        def __call__(self, previous_steps):
            previous_steps = tuple(previous_steps)
            return previous_steps.count(self.step) ==  self.count



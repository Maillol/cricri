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
        ...


    class Create(BaseTestState, start=True):
        def start(cls):
            cls.l = [1, 3, 2, 4]

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


A step is created by subclassing gentest.TestState.

start attribute allow you to define the first step. Here Create is the first step.
The first step can define start methode in order to store the object to be tested in a class attribute.
start method is called once at the beginning of scenario.
previous attribute allow you to define when step is executed. Here Reverse step is executed when Create
step is done and Sort step can be executed when Create or Reverse step is done.

This three steps define two scenario:
    - Create, Reverse and Sort list.
    - Create and Sort list.
 
Each step has input method. this method is called before test methods of step.

The last statement allows unittest to manage this module. It generate all unittest.TestCase classes.

To run this script, use unittest command-line interface::

    python3 -m unittest test_module_name  


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

The previous decorator allows you to have a conditional execution of test method.
this function takes a list Condition objects such as Path or Newer.

You can combine Condition object using operator. 

+------------+------------+----------------------------------+
| Operator   | Meaning    | Example                          |
+============+============+==================================+
|  \-        | not        | \- Path('A', 'B')                |
+------------+------------+----------------------------------+
|  &         | and        | Path('A', 'B') & Path('F', 'G')  |
+------------+------------+----------------------------------+
|  \|        | or         | Path('A', 'B') \| Path('F', 'G') |
+------------+------------+----------------------------------+


example::


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


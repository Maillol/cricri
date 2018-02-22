.. cricri documentation master file, created by
   sphinx-quickstart on Sun Dec 18 08:26:14 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Cricri's documentation
=================================

cricri is a test scenario generator. You define steps using TestState class.
Each step has input method, set of tests methods, and one or multiple previous steps.
cricri finds all paths in the steps and generates one Test Case for each
path. You can disable test steps depending on the path traveled.


Installation
=============

You can install the latest stable release with pip::

    pip install cricri

or install the latest development release (unstable) with git::

    git clone https://github.com/Maillol/cricri.git cricri
    cd cricri
    python3 setup.py install


Basic example
=============

Here is a simple example with three steps to generate two scenario wich test list method

.. testcode::

    from cricri import TestState, previous


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


The *BaseTestState* is created by subclassing *cricri.TestState*.
This subclass defines *start_scenario* method in order to store the object
to be tested in a class attribute.
The *start_scenario* method will be called once at the beginning of each generated scenario.

Each *BaseTestState* subclass defines a scenario step.
*start attribute* allow you to define the first step. Here *Create* class is the first step.
*previous attribute* allow you to define when step is executed. Here *Reverse* step is executed
when *Create* step is done and *Sort* step can be executed when *Create* or *Reverse* step is done.

This three steps define two scenario:
    - Create and Sort list.
    - Create, Reverse and Sort list.

Each step has input method. This method is called before test methods of step.

The last statement allows unittest to manage this module. It generate all unittest.TestCase classes.

To run this script, use unittest command-line interface::

    $ python3 -m unittest -v test_scenario_list

You will see the following output::

    create (1/2) ... ok
    sort   (2/2) ... ok
    create  (1/3) ... ok
    reverse (2/3) ... ok
    sort    (3/3) ... ok

    ----------------------------------------------------------------------
    Ran 5 tests in 0.001s

    OK

If you want use **pytest** to launch this script, you should install `pytest-cricri`_

:kbd:`pip install pytest-cricri`

You can launch test with pytest using `--cricri` option

:kbd:`pytest --cricri test_scenario_list.BaseTestState`


condition decorator
===================

The **condition** decorator allows you to have a conditional execution of test method.
this function takes a Condition objects such as Previous or Path.

Example::


    class B1(BaseTestState):
        ...

    class B2(BaseTestState):
        ...

    class C(BaseTestState, previous=['B1', 'B2']):

        @condition(Previous(['B1']))  # Called when previous step is B1
        def input(self):
            ...

        @condition(Previous(['B2'])  # Called when previous step is B2
        def input(self):
            ...

        @condition(Previous(['B1'])  # Called when previous step is B1
        def test_1(self):
            ...

        @condition(Previous(['B2'])  # Called when previous step is B2
        def test_2(self):
            ...


Note that TestState subsubclass can have several input methods if **condition** decorator is used.


Documentation
=============

.. toctree::
   :maxdepth: 2

   condition-object
   test-server/index.rst
   tips


Contributing
============

Contributions are welcome! Clone the repository on `GitHub`_.


.. _GitHub: https://github.com/maillol/cricri
.. _pytest-cricri: https://github.com/Maillol/pytest_cricri


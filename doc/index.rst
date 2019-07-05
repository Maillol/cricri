.. cricri documentation master file, created by
   sphinx-quickstart on Sun Dec 18 08:26:14 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Cricri's documentation
=================================

cricri is a test scenario generator for testing Python module or
services written in any language through its API.


Installation
=============

You can install the latest stable release with pip::

    pip install cricri

or install the latest development release (unstable) with git::

    git clone https://github.com/Maillol/cricri.git cricri
    cd cricri
    python3 setup.py install


Base concept
============

**Test Scenario**: A Test Scenario is a set of Test Case. Each Test Case does an
action as the end user and checks the effect of this action.

Test Cases are wrote by the tester and cricri finds all possible ways to assemble Test
Cases and generate all possible Scenarios.

The tester can add constraints to define how Test Cases can be assembled.


Basic example
=============

Here is a simple example with three Test Case to generate two Scenario that test list method


.. image:: http://www.plantuml.com/plantuml/svg/SoWkIImgAStDuTA8DjHHCDPHCD9HC8dLLD3LjLC02e7vnc0XAuNY_A8IxEfCOEeCGUgAKijIYufJkP35yHdfa9gN0d820000
    :alt: state machine (A) --> (B):m1; (A) --> (C):m2; (B) --> (C):m3
    :align: center


Firstly, we are going to define a Test Case base class in a file named *test_scenario_list.py*.


.. code-block:: python

    from cricri import TestCase


    class BaseListTestCase(TestCase):

        @classmethod
        def start_scenario(cls):
            cls.l = [1, 3, 2, 4]


This subclass defines *start_scenario* method in order to store the object
to be tested in a class attribute.
The *start_scenario* method will be called once at the beginning of each generated scenario.

Now, we can subclass our Test Case base class. Each *BaseListTestCase* subclass will
be used by cricri to generate scenarios to test a list.
Each Test Case can have a method named *input*. We use this method to update the list.


We are going to define three classes:

.. code-block:: python


    class Create(BaseListTestCase, start=True):

        def test_list_should_be_created(self):
            self.assertEqual(self.l, [1, 3, 2, 4])


    class Reverse(BaseListTestCase, previous=['Create']):
        def input(self):
            self.l.reverse()

        def test_list_should_be_reversed(self):
            self.assertEqual(self.l, [4, 2, 3, 1])


    class Sort(BaseListTestCase, previous=['Create', 'Reverse']):
        def input(self):
            self.l.sort()

        def test_list_should_be_sorted(self):
            self.assertEqual(self.l, [1, 2, 3, 4])

The *start attribute* allow you to define the first step. Here *Create* class is the first step.
*previous attribute* allow you to define when step is executed. Here *Reverse* step will be executed
when *Create* step is done and *Sort* step can be executed when *Create* or *Reverse* step is done.


Before launching cricri, we must add this instruction and the end of the file *test_scenario_list.py*:


.. code-block:: python

    load_tests = BaseListTestCase.get_load_tests()


cricri is going to use this three Test Cases to generate two scenarios:
    - Create and Sort list.
    - Create, Reverse and Sort list.


To run this script, we can use unittest command-line interface::

    $ python3 -m unittest -v test_scenario_list

We will see the following output::

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

:kbd:`pytest --cricri test_scenario_list.BaseListTestCase`


Documentation
=============

.. toctree::
   :maxdepth: 2

   tutorial/index.rst
   reference-guides/index.rst
   tips


Contributing
============

Contributions are welcome! Clone the repository on `GitHub`_.


.. _GitHub: https://github.com/maillol/cricri
.. _pytest-cricri: https://github.com/Maillol/pytest_cricri


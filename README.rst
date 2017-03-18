cricri - Generate test scenarios using unittest
===============================================

.. image:: https://badge.fury.io/py/cricri.svg
    :target: https://badge.fury.io/py/cricri

.. image:: https://api.travis-ci.org/Maillol/cricri.svg?branch=master
    :target: https://travis-ci.org/Maillol/cricri

.. image:: https://readthedocs.org/projects/cricri/badge/?version=latest
    :target: http://cricri.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Determine and write all possible test scenarios of finite state machines is a hard task.
**cricri** generates test scenarios from state specification.

What are cricri prerequisites ?
-------------------------------

python 3.4 or newer


How to install
--------------

.. code-block:: bash

    $ pip install cricri


Example:
--------

An example to test a state machine.


.. class:: no-web

    .. image:: https://www.planttext.com/plantuml/img/ur9GSbHIq2tAJCyeqRMBpZMCLL1oKk824N1H1P2maZD85AGMB604L0SK0G00
        :alt: HTTPie compared to cURL
        :align: center
     

A is a initial state, call m1 shifts the state from A to B and call m2 shifts the state from A to C

We define each state using **TestState** subclass:


.. code-block:: python3

    # Define a base class for scenario step.
    class State(TestState):
        pass


    class StateA(State, start=True): # start=True because A is initial state.
        def input(self):
            # code to go to initial state 'A'
            type(self).machine = Machine()

        def test_a(self):
            # You can use unittest assert methods.
            ...

    class StateB(State, previous=['StateA']): # previous=['StateA'] because we can go to this state from 'A'
        def input(self):
            # code to go to 'B' state from 'A'
            type(self).machine.m1()

        def test_b(self):
            # You can use unittest assert methods. 
            ...

    # previous=['StateA', 'StateB'] because we can go to this state from 'A' or 'B'.
    class StateC(State, previous=['StateA', 'StateB']):

        @previous(['StateA'])
        def input(self):
            # Code to go to 'C' state from 'A'
            type(self).machine.m2()

        @previous(['StateB'])
        def input(self):
            # Code to go to 'C' state from 'B'
            type(self).machine.m1()

        def test_c(self):
            # You can use unittest assert methods. 
            ...


    # You must to use this statment at the end of module to generate **load_tests** function::
    load_tests = State.get_load_tests()


Call *python3 -m unittest <test_module_name>* to launch test.

This exemple generate two scenarios:
    
    |  machine = Machine()
    |  test_a()
    |  machine.m1()
    |  test_b()
    |  machine.m1()
    |  test_c()

and:

    |  machine = Machine()
    |  test_a()
    |  machine.m2()
    |  test_c()

For more example, see `demo directory <https://github.com/Maillol/scenario/tree/master/demo>`_


Documentation:
--------------

Documentation is online at http://cricri.readthedocs.io


gentest - Generate test scenarios using unittest
================================================

Determine and write all possible test scenarios of finite state machines is a hard task.
**gentest** generates test scenarios from state specification.


An example to test this state machine.


.. class:: no-web

    .. image:: https://www.planttext.com/plantuml/img/ur9GSbHIq2tAJCyeqRMBpZMCLL1oKk824N1H1P2maZD85AGMB604L0SK0G00
        :alt: HTTPie compared to cURL
        :align: center
     

A is a initial state, call m1 shifts the state from A to B and call m2 shifts the state from A to C

We define each state using **TestState** class::

    from gentest import TestState, previous
    
    class StateA(TestState, start=True): # start=True because A is initial state.
        def input(self):
            # code to go to initial state 'A'
            type(self).machine = Machine()

        def test_a(self):
            # You can use unittest assert methods.

    class StateB(TestState, previous=['StateA']): # previous=['StateA'] because we can go to this state from 'A'
        def input(self):
            # code to go to 'B' state from 'A'
            type(self).machine.m1()

        def test_b(self):
            # You can use unittest assert methods. 

    # previous=['StateA', 'StateB'] because we can go to this state from 'A' or 'B'.
    class StateC(TestState, previous=['StateA', 'StateB']):

        @previous(['StateA'])
        def input(self):
            # code to go to 'C' state from 'A'
            type(self).machine.m2()

        @previous(['StateB'])
        def input(self):
            # code to go to 'C' state from 'B'
            type(self).machine.m1()

        def test_c(self):
            # You can use unittest assert methods. 

After define TestState, you must generate **load_tests** function at the end of module::

    load_tests = TestState.get_load_tests()


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

For more example, see demo directory

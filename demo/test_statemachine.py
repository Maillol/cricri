from gentest import TestState, previous
from statemachine import Machine


class TestMachine(TestState):
    """
    Each subclass of this class will be a scenario step.
    You can define utility methods here...
    """
    def assertX(self, value):
        self.assertEqual(self.machine.x, value)

    def assertY(self, value):
        self.assertEqual(self.machine.y, value)


class A(TestMachine, start=True):
    def input(self):
        type(self).machine = Machine()

    def test_x(self):
        self.assertX(0)

    def test_y(self):
        self.assertEqual(self.machine.y, 0)


class B(TestMachine, previous=['A']):
    def input(self):
        self.machine.mth1()

    def test_x(self):
        self.assertX(0)

    def test_y(self):
        self.assertY(1)


class C(TestMachine, previous=['A', 'B']):

    @previous(['A'])
    def input(self):
        self.machine.mth2()

    @previous(['B'])
    def input(self):
        self.machine.mth1()

    def test_x(self):
        self.assertX(0)

    def test_y(self):
        self.assertY(2)

class D(TestMachine, previous=['B']):
    def input(self):
        self.machine.mth2()

    def test_x(self):
        self.assertX(1)

    def test_y(self):
        self.assertY(0)


class E(TestMachine, previous=['C']):
    def input(self):
        self.machine.mth1()

    def test_x(self):
        self.assertX(1)

    def test_y(self):
        self.assertY(1)


class F(TestMachine, previous=['C', 'D', 'E']):

    @previous(['D', 'E'])
    def input(self):
        self.machine.mth1()

    @previous(['C'])
    def input(self):
        self.machine.mth2()

    def test_x(self):
        self.assertX(1)

    def test_y(self):
        self.assertY(2)


load_tests = TestMachine.get_load_tests()


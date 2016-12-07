from scenariotest import TestState, previous
from statemachine import Machine


class A(TestState, start=True):
    def input(self):
        type(self).machine = Machine()

    def test_x(self):
        self.assertEqual(self.machine.x, 0)  

    def test_y(self):
        self.assertEqual(self.machine.y, 0)


class B(TestState, previous=['A']):
    def input(self):
        self.machine.mth1()

    def test_x(self):
        self.assertEqual(self.machine.x, 0)  

    def test_y(self):
        self.assertEqual(self.machine.y, 1)


class C(TestState, previous=['A', 'B']):

    @previous(['A'])
    def input(self):
        self.machine.mth2()

    @previous(['B'])
    def input(self):
        self.machine.mth1()

    def test_x(self):
        self.assertEqual(self.machine.x, 0)  

    def test_y(self):
        self.assertEqual(self.machine.y, 2)

class D(TestState, previous=['B']):
    def input(self):
        self.machine.mth2()

    def test_x(self):
        self.assertEqual(self.machine.x, 1)  

    def test_y(self):
        self.assertEqual(self.machine.y, 0)

class E(TestState, previous=['C']):
    def input(self):
        self.machine.mth1()

    def test_x(self):
        self.assertEqual(self.machine.x, 1)  

    def test_y(self):
        self.assertEqual(self.machine.y, 1)


class F(TestState, previous=['C', 'D', 'E']):

    @previous(['D', 'E'])
    def input(self):
        self.machine.mth1()

    @previous(['C'])
    def input(self):
        self.machine.mth2()

    def test_x(self):
        self.assertEqual(self.machine.x, 1)  

    def test_y(self):
        self.assertEqual(self.machine.y, 2)


load_tests = TestState.get_load_tests()

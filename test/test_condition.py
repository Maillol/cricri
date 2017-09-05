import unittest
from cricri import previous, Path, Newer, Previous
import voluptuous


class TestPreviousDecorator(unittest.TestCase):

    def test_decorate_function(self):

        @previous('A', 'B')
        def foo():
            ...

        self.assertIsInstance(foo.condition, Previous)
        p = foo.condition
        self.assertTrue(p(["A"]))
        self.assertTrue(p(["B"]))
        self.assertTrue(p(["X", "A"]))
        self.assertTrue(p(["X", "XX", "A"]))
        self.assertTrue(p(["X", "B"]))
        self.assertTrue(p(["X", "XX", "B"]))
        self.assertFalse(p([]))
        self.assertFalse(p(["A", "X"]))
        self.assertFalse(p(["A", "X", "XX"]))
        self.assertFalse(p(["X", "A", "XX"]))
        self.assertFalse(p(["B", "X"]))
        self.assertFalse(p(["B", "X", "XX"]))
        self.assertFalse(p(["X", "B", "XX"]))



class TestPath(unittest.TestCase):

    def test_call(self):
        p = Path("A", "B")
        self.assertTrue(p(["A", "B"]))
        self.assertTrue(p(["A", "B", "C"]))
        self.assertTrue(p(["Z", "A", "B"]))
        self.assertTrue(p(["Z", "A", "B", "C"]))
        self.assertFalse(p(["A"]))
        self.assertFalse(p(["A", "C"]))
        self.assertFalse(p(["A", "C", "B"]))

    def test_not_call(self):
        p = - Path("A", "B")
        self.assertFalse(p(["A", "B"]))
        self.assertFalse(p(["A", "B", "C"]))
        self.assertFalse(p(["Z", "A", "B"]))
        self.assertFalse(p(["Z", "A", "B", "C"]))
        self.assertTrue(p(["A"]))
        self.assertTrue(p(["A", "C"]))
        self.assertTrue(p(["A", "C", "B"]))

    def test_and_call(self):
        p = Path("A", "B") & Path("C", "D")
        self.assertTrue(p(["A", "B", "C", "D"]))
        self.assertTrue(p(["Z", "A", "B", "M", "C", "D", "N"]))
        self.assertFalse(p(["A", "B"]))
        self.assertFalse(p(["C", "D"]))

    def test_or_call(self):
        p = Path("A", "B") | Path("C", "D")
        self.assertTrue(p(["A", "B", "C", "D"]))
        self.assertTrue(p(["Z", "A", "B", "M", "C", "D", "N"]))
        self.assertTrue(p(["A", "B"]))
        self.assertTrue(p(["C", "D"]))
        self.assertFalse(p(["B", "C"]))


class TestNewer(unittest.TestCase):

    def test_call(self):
        n = Newer("A", "B")
        self.assertTrue(n(["A", "B"]))
        self.assertTrue(n(["A", "Z", "B"]))
        self.assertTrue(n(["B", "A", "Z", "B"]))
        self.assertTrue(n(["X", "B"]))
        self.assertTrue(n(["B"]))
        self.assertFalse(n([]))
        self.assertFalse(n(["A"]))
        self.assertFalse(n(["A", "Z", "B", "J", "A"]))

    def test_not_call(self):
        n = - Newer("A", "B")
        self.assertFalse(n(["A", "B"]))
        self.assertFalse(n(["A", "Z", "B"]))
        self.assertFalse(n(["B", "A", "Z", "B"]))
        self.assertFalse(n(["X", "B"]))
        self.assertFalse(n(["B"]))
        self.assertTrue(n([]))
        self.assertTrue(n(["A"]))
        self.assertTrue(n(["A", "Z", "B", "J", "A"]))


class TestPrevious(unittest.TestCase):

    def test_call(self):
        p = Previous("A", "B")
        self.assertTrue(p(["A"]))
        self.assertTrue(p(["B"]))
        self.assertTrue(p(["X", "A"]))
        self.assertTrue(p(["X", "XX", "A"]))
        self.assertTrue(p(["X", "B"]))
        self.assertTrue(p(["X", "XX", "B"]))
        self.assertFalse(p([]))
        self.assertFalse(p(["A", "X"]))
        self.assertFalse(p(["A", "X", "XX"]))
        self.assertFalse(p(["X", "A", "XX"]))
        self.assertFalse(p(["B", "X"]))
        self.assertFalse(p(["B", "X", "XX"]))
        self.assertFalse(p(["X", "B", "XX"]))

    def test_not_call(self):
        p = - Previous("A", "B")
        self.assertFalse(p(["A"]))
        self.assertFalse(p(["B"]))
        self.assertFalse(p(["X", "A"]))
        self.assertFalse(p(["X", "XX", "A"]))
        self.assertFalse(p(["X", "X", "B"]))
        self.assertFalse(p(["X", "XX", "B"]))
        self.assertTrue(p([]))
        self.assertTrue(p(["A", "X"]))
        self.assertTrue(p(["A", "X", "XX"]))
        self.assertTrue(p(["X", "A", "XX"]))
        self.assertTrue(p(["B", "X"]))
        self.assertTrue(p(["B", "X", "XX"]))
        self.assertTrue(p(["X", "B", "XX"]))



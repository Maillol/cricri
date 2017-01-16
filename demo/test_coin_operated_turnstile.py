from gentest import TestState, previous
from coin_operated_turnstile import Turnstile

class TestTurnstile(TestState):

    @classmethod
    def start_scenario(cls):
        cls.machine = Turnstile()
        cls.expect_coin = 0

class Locked(TestTurnstile, previous=['Unlocked'], start=True):

    def input(self):
        self.machine.push()

    def test_nb_coins(self):
        self.assertEqual(self.machine.coins, self.expect_coin)


class Unlocked(TestTurnstile, previous=['Locked']):
    def input(self):
        self.machine.coin()
        type(self).expect_coin += 1

    def test_nb_coins(self):
        self.assertEqual(self.machine.coins, self.expect_coin)

load_tests = TestTurnstile.get_load_tests(max_loop=2)


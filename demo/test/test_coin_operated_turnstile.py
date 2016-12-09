from gentest import TestState, previous
from coin_operated_turnstile import Turnstile


class Locked(TestState, previous=['Unlocked'], start=True):
    def input(self):
        cls = type(self)
        if not hasattr(cls, 'machine'):
            cls.machine = Turnstile()
            cls.expect_coin = 0
        else:
            cls.machine.push()

    def test_nb_coins(self):
        self.assertEqual(self.machine.coins, self.expect_coin)


class Unlocked(TestState, previous=['Locked']):
    def input(self):
        self.machine.coin()
        type(self).expect_coin += 1

    def test_nb_coins(self):
        self.assertEqual(self.machine.coins, self.expect_coin)



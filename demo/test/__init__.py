from .test_coin_operated_turnstile import *
from .test_statemachine import *
from gentest import MetaTestState

load_tests = MetaTestState.get_load_tests(max_loop=2)

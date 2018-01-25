import unittest
import signal

from cricri.inet.server import Server


class TestServer(unittest.TestCase):

    def test_env_should_set_environment_variable(self):
        server = Server( 
            ["python", "-u", "-c", "import os; print(os.environ)"],
            kill_signal=signal.SIGINT,
            env={"CRICRI_VAR": "Hello"}
        )
        
        server.assert_stdout_is("{'CRICRI_VAR': 'Hello'}\n", timeout=1)

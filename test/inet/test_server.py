import asyncio
import unittest
import signal
import sys
from textwrap import dedent

from cricri.inet.server import Server, SubprocessProtocol, IOHistory, STDERR, STDOUT


class TestServer(unittest.TestCase):

    def test_env_should_set_environment_variable(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        server = Server(
            ["python", "-u", "-c", "import os; print(os.environ)"],
            kill_signal=signal.SIGINT,
            env={"CRICRI_VAR": "Hello"},
        )
        server.history.new_section('test-1')
        server.assert_stdout_is("{'CRICRI_VAR': 'Hello'}\n", timeout=1)
        server.kill()
        loop.close()


class BaseTestSubprocessProtocol(unittest.TestCase):
    """
    Subclass this class and edit PROG class attribute.

    Launch python subprocess executing PROG bound to a SubprocessProtocol.
    """

    PROG = ''

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.on_exit = self.loop.create_future()
        self.history = IOHistory()
        self.history.new_section('t1')

        self.transport, self.protocol = self.loop.run_until_complete(
            self.loop.subprocess_exec(
                lambda: SubprocessProtocol(self.on_exit, self.history),
                sys.executable, '-u', '-c', dedent(self.PROG),
                env={}
            )
        )

    def tearDown(self):
        self.transport.close()
        self.loop.close()


class TestSubprocessProtocolStdout(BaseTestSubprocessProtocol):

    PROG = 'print("hello")'

    def test_prog_stdout_should_be_recorded_to_the_history(self):
        self.loop.run_until_complete(self.on_exit)
        self.assertEqual('hello\n', self.history.get_history(STDOUT))


class TestSubprocessProtocolStderr(BaseTestSubprocessProtocol):

    PROG = 'import sys; print("hello", file=sys.stderr)'

    def test_prog_stderr_should_be_recorded_to_the_history(self):
        self.loop.run_until_complete(self.on_exit)
        self.assertEqual('hello\n', self.history.get_history(STDERR))


class TestSubprocessProtocolWaitAQuietProg(BaseTestSubprocessProtocol):

    PROG = 'pass'

    def test_should_raise_a_timeout_error(self):
        with self.assertRaises(asyncio.TimeoutError):
            self.loop.run_until_complete(
                self.protocol.wait_for_output(STDOUT, timeout=1))
        self.assertEqual(self.history.get_history(STDOUT), '')
        self.assertEqual(self.history.get_history(STDERR), '')

        self.loop.run_until_complete(self.on_exit)


class TestSubprocessProtocolWait(BaseTestSubprocessProtocol):

    PROG = """
    import time
    time.sleep(1)
    print('line-1')
    """

    def test(self):
        self.assertEqual(self.history.get_history(STDOUT), '')
        self.loop.run_until_complete(
            self.protocol.wait_for_output(STDOUT, timeout=2)
        )
        self.assertEqual(self.history.get_history(STDOUT), 'line-1\n')
        self.loop.run_until_complete(self.on_exit)

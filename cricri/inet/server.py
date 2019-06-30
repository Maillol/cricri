import asyncio
import operator
import re
import signal
import time
from typing import Dict, Optional, Callable, Union, List

STDOUT = 1
STDERR = 2

Timeout = Union[int, float]


class IOHistory:
    """
    Store Outputs of running server.

    >>> history = IOHistory()
    >>> history.new_section('First Section')
    >>> history.add_stdout_chunk('Hello ')
    >>> history.add_stdout_chunk('World')
    >>> history.get_history(STDOUT)
    'Hello World'

    >>> history.new_section('Second Section')
    >>> history.add_stdout_chunk('Bye')
    >>> history.add_stderr_chunk('Chao')

    >>> history.get_history(STDOUT)
    'Bye'
    >>> history.get_history(STDERR)
    'Chao'
    >>> history.get_history(STDOUT, 'First Section')
    'Hello World'
    """

    def __init__(self):
        self._history = {}
        self._current_section = {}

    def new_section(self, name: str):
        self._current_section = {
            STDERR: '',
            STDOUT: ''
        }
        self._history[name] = self._current_section

    def add_stdout_chunk(self, chunk: str):
        try:
            self._current_section[STDOUT] += chunk
        except KeyError:
            raise RuntimeError('new_section method should be called')

    def add_stderr_chunk(self, chunk: str):
        try:
            self._current_section[STDERR] += chunk
        except KeyError:
            raise RuntimeError('new_section method should be called')

    def add_chunk(self, fd: int, chunk: str):
        if fd == STDOUT:
            self.add_stdout_chunk(chunk)
        elif fd == STDERR:
            self.add_stderr_chunk(chunk)

    def get_history(self, fd: int, section=None):
        if section is None:
            return self._current_section[fd]
        return self._history[section][fd]

    def __iter__(self):
        return iter(self._history.items())


class SubprocessProtocol(asyncio.SubprocessProtocol):
    class OutputWatcher:
        def __init__(self):
            self._future_from_fd: Dict[int: Optional[asyncio.Future]] = {
                STDOUT: None,
                STDERR: None
            }

        def wait_for(self, fd: int) -> asyncio.Future:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            self._future_from_fd[fd] = future
            return future

        def set_result_if_waiting(self, fd, result):
            """
            Set result on future returned by the `wait_for` method.
            """
            future = self._future_from_fd[fd]
            if future is not None:
                if not future.cancelled():
                    self._future_from_fd[fd].set_result(result)
                self._future_from_fd[fd] = None

    def __init__(self,
                 on_exit: asyncio.Future,
                 history: IOHistory):
        self.on_exit = on_exit
        self.history = history
        self._output_waiter = self.OutputWatcher()

    async def wait_for_output(self, fd: int, timeout: Timeout = 3):
        """
        Wait for bytes written on the output.

        Returns a bytes received or raises a asyncio.TimeoutError if
        timeout is reached.
        """
        return await asyncio.wait_for(
            self._output_waiter.wait_for(fd),
            timeout=timeout
        )

    def pipe_data_received(self, fd, data):
        message = data.decode()
        self.history.add_chunk(fd, message)
        self._output_waiter.set_result_if_waiting(fd, message)

    def pipe_connection_lost(self, fd, exc):
        pass

    def process_exited(self):
        self.on_exit.set_result(True)


class Server:
    """
    Wrap server process and provide assert methods.
    """

    _protocol: SubprocessProtocol
    _on_subprocess_exist: asyncio.Future
    kill_signal: signal
    history: IOHistory

    def __init__(self,
                 parameters: List[str],
                 kill_signal=signal.SIGINT,
                 env: Optional[Dict[str, str]] = None):
        """
        parameters - The list of Popen parameters.
        kill_signal - The signal used to kill the process.
        env - environment variables dict
        """
        self.history = IOHistory()
        self.kill_signal = kill_signal

        loop = asyncio.get_event_loop()
        self._on_subprocess_exist = loop.create_future()
        (self._transport, self._protocol) = loop.run_until_complete(
            loop.subprocess_exec(
                lambda: SubprocessProtocol(
                    self._on_subprocess_exist,
                    self.history
                ),
                *parameters,
                env=env
            )
        )

    def assert_stdout_is(self, expected: str, timeout: Timeout):
        """
        Test that server logs *expected* on the stdout before *timeout*
        """
        self._assert_output(operator.eq, '{read!r} != {expected!r}',
                            STDOUT, expected, timeout)

    def assert_stderr_is(self, expected: str, timeout: Timeout):
        """
        Test that server logs *expected* on the stderr before *timeout*
        """
        self._assert_output(operator.eq, '{read!r} != {expected!r}',
                            STDERR, expected, timeout)

    def assert_stdout_regex(self, regex: str, timeout: Timeout):
        """
        Test that server logs on stdout before *timeout*
        and message matches *regex*
        """
        self._assert_output(lambda a, b: re.search(b, a) is not None,
                            "The pattern {expected!r} is not found in the stdout: {read}",
                            STDOUT, regex, timeout)

    def assert_stderr_regex(self, regex: str, timeout: Timeout):
        """
        Test that server logs on stderr before *timeout*
        and message matches *regex*
        """
        self._assert_output(lambda a, b: re.search(b, a) is not None,
                            "The pattern {expected!r} is not found in the stderr: {read}",
                            STDERR, regex, timeout)

    def _assert_output(self,
                       test_func: Callable[[str, str], bool],
                       assert_msg: str,
                       fd: int,
                       expected: str,
                       timeout: Timeout):

        start = time.time()

        remaining = timeout
        data = self.history.get_history(fd)
        if test_func(data, expected):
            return

        while remaining > 0:
            loop = asyncio.get_event_loop()

            try:
                loop.run_until_complete(
                    self._protocol.wait_for_output(fd, remaining)
                )
            except asyncio.TimeoutError:
                pass

            remaining -= (time.time() - start)
            data = self.history.get_history(fd)
            if test_func(data, expected):
                return

        raise AssertionError(assert_msg.format(
            expected=expected, read=data))

    def kill(self):
        """
        Kill the process using `kill_signal` attribute.
        """

        subprocess = self._transport.get_extra_info('subprocess')
        subprocess.send_signal(self.kill_signal)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._on_subprocess_exist)
        self._transport.close()

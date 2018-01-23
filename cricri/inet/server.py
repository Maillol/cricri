import operator
import re
import selectors
import time
from subprocess import PIPE, Popen


class Server:
    """
    Wrap server process and provide assert methods.
    """

    def __init__(self, parameters, kill_signal, env=None):
        """
        parameters - The list of Popen parameters.
        kill_signal - The signal used to kill the process.
        env - environement variables dict
        """
        self.popen = Popen(
            parameters,
            stdout=PIPE,
            stderr=PIPE,
            env=env
        )

        self.kill_signal = kill_signal
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.popen.stdout,
                               selectors.EVENT_READ,
                               ('stdout', "server-2"))
        self.selector.register(self.popen.stderr,
                               selectors.EVENT_READ,
                               ('stderr', "server-3"))

    def assert_stdout_is(self, expected, timeout):
        """
        Test that server logs *expected* on the stdout before *timeout*
        """
        self._assert_output(operator.eq, '{read!r} != {expected!r}',
                            'stdout', expected, timeout)

    def assert_stderr_is(self, expected, timeout):
        """
        Test that server logs *expected* on the stderr before *timeout*
        """
        self._assert_output(operator.eq, '{read!r} != {expected!r}',
                            'stderr', expected, timeout)

    def assert_stdout_regex(self, regex, timeout):
        """
        Test that server logs on stdout before *timeout*
        and message matches *regex*
        """
        self._assert_output(lambda a, b: re.search(b, a),
                            "{read} doesn't match {expected}",
                            'stdout', regex, timeout)

    def assert_stderr_regex(self, regex, timeout):
        """
        Test that server logs on stderr before *timeout*
        and message matches *regex*
        """
        self._assert_output(lambda a, b: re.search(b, a),
                            "{read} doesn't match {expected}",
                            'stderr', regex, timeout)

    def _assert_output(self, test_func, assert_msg,
                       output, expected, timeout):
        read = None
        read_buffer = ''
        start = time.time()
        remaing = timeout
        while read is None:
            keys = self.selector.select(timeout=remaing)
            if not keys:
                break

            for key, _ in keys:
                if key.data[0] == output:
                    read = key.fileobj.read1(4096).decode('utf-8')
                    if read == '':  # EOF
                        break

                    read_buffer += read
                    if test_func(read_buffer, expected):
                        return

                    read = None
                    break

            remaing = timeout - (time.time() - start)
            if remaing <= 0:
                msg = assert_msg.format(expected=expected, read=read_buffer)
                raise AssertionError('Timeout: ' + msg)

        raise AssertionError(assert_msg.format(expected=expected,
                                               read=read_buffer))

    def kill(self):
        """
        Kill the process using `kill_signal` attribute.
        """
        self.selector.unregister(self.popen.stdout)
        self.selector.unregister(self.popen.stderr)
        self.popen.stderr.close()
        self.popen.stdout.close()
        self.selector.close()
        self.popen.send_signal(self.kill_signal)

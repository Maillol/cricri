"""
Utility to test TCP server
"""

import re
import socket
import time


class TCPClient:
    """
    Client to perform TCP request
    """

    def __init__(self, port, timeout, tries, wait):
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)

        self.socket.settimeout(timeout)

        socket_error = None
        for _ in range(tries):
            start = time.time()
            try:
                self.socket.connect(("127.0.0.1", int(port)))
            except socket.timeout as error:
                socket_error = error
            except OSError as error:
                socket_error = error
                if wait is None:
                    time.sleep(timeout - (time.time() - start))
                else:
                    time.sleep(wait)
            else:
                socket_error = None
                break

        if socket_error is not None:
            print(str(socket_error))

    def close(self):
        """
        Close the socket client.
        """
        self.socket.close()

    def send(self, msg):
        """
        send *msg*
        """
        self.socket.send(msg.encode('utf-8'))

    def assert_receive(self, expected, timeout=2):
        """
        Test that client received *expected* before *timeout*.
        """
        self.socket.settimeout(timeout)
        try:
            msg = self.socket.recv(256)
        except socket.timeout:
            raise AssertionError("Timeout: No data received")

        if msg.decode('utf-8') != expected:
            raise AssertionError('{} != {}'
                                 .format(msg.decode('utf-8'),
                                         expected))

    def assert_receive_regex(self, regex, timeout=2):
        """
        Test that client received data before *timeout* and data
        matches *regex*.
        """
        self.socket.settimeout(timeout)
        try:
            msg = self.socket.recv(256)
        except socket.timeout:
            raise AssertionError("Timeout: No data received")

        if re.search(regex, msg.decode('utf-8')):
            raise AssertionError("{} doesn't match {}"
                                 .format(msg.decode('utf-8'),
                                         regex))

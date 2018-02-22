.. _how-to-test-a-tcp-server:

How to test a TCP server
========================

cricri provides *TestServer* class to test TCP server. You must subclasse
*TestServer* and define your servers and clients::

    class TestChatServer(TestServer):

        commands = [
            {
                "name": "chat-server",
                "cmd": ["python3", "-u", "chat_server.py", "{port-1}",
                        "--db-port", "{port-2}"],
                "env": {"PYTHONPATH": "/home/project/chat"}
            },
            {
                "name": "database",
                "cmd": ["docker", "run", "-p", "{port-2}:5420", "db-service"],
            }
        ]

        tcp_clients = [
            {
                "name": "Alice",
                "port": "{port-1}",
            }
        ]

This example define *TestChatServer* class, which define command to launch server and
tcp client. Before each scenario running, 'python3 -u chat_server.py {port-1}' is executed
and a tcp client is connected to '{port-1}'. The string '{port-1}' will be bound by the
fist free TCP port.

You may reference defined clients and servers in your *TestChatServer* subclasses using *clients*
and *servers* attributes::

    class Start(TestChatServer, start=True):

        def test_server_listen(self):
            self.servers['chat-server'].assert_stdout_is(
                'server listen', timeout=2
            )

    class AliceAskedNickname(TestChatServer, previous=["Start"]):

        def input(self):
            self.clients["Alice"].send("MY_NAME_IS;Alice;")

        def test_alice_should_receive_ok(self):
            self.clients["Alice"].assert_receive('OK')


In this example, the *Start* step class test that server write 'server listen' to stdout.
The *AliceAskedNickname* class send 'MY_NAME_IS;Alice;' string to the server and test that
Alice receive 'OK'.



Assert TCP client methods
-------------------------

.. method:: assert_receive(self, expected, timeout=2)

    Test that client received *expected* before *timeout*.

.. method:: assert_receive_regex(self, regex, timeout=2)

    Test that client received data before *timeout* and data matches *regex*.


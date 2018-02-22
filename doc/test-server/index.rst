Test TCP server
===============

cricri provides *TestServer* class to test server. You must subclasse
*TestServer* and define your servers and clients::


    class TestMyServer(TestServer):

        commands = [
            {
                "name": "application",
                "cmd": ["python3", "-u", "application.py", "{port-1}",
                        "--db-port", "{port-2}"],
                "env": {"PYTHONPATH": "/home/project/chat"}
            },
            {
                "name": "database",
                "cmd": ["docker", "run", "-p", "{port-2}:5420", "db-service"],
            }
        ]

Servers are defined in commands list. You will can reference server in test methods 
by the name using `self.servers['name-defined-in-commands-list']`


commands available parameters
-----------------------------

The *commands* must be a list containing dict with:
    - name (required) the name of command
    - cmd (required) list of sequence of program arguments the first
        element is a program.
    - kill-signal (optional) should be an enumeration members of
        :py:class: `signal.Signals`
    - env (optional) A dict that defines the environment variables
    - extra-env (optional) A dict that add environment variables


Assert server methods
---------------------

.. method:: assert_stdout_is(expected, timeout=2)

    Test that server logs *expected* on the stdout before *timeout*.

.. method:: assert_stderr_is(expected, timeout=2)

    Test that server logs *expected* on the stderr before *timeout*.

.. method:: assert_stdout_regex(regex, timeout=2)

    Test that server logs on stdout before *timeout* and message matches *regex*.

.. method:: assert_stderr_regex(regex, timeout=2)

    Test that server logs on stderr before *timeout* and message matches *regex*.


clients configuration
=====================

.. toctree::
   :maxdepth: 2

   how-to-test-a-http-server-or-rest-api
   how-to-test-a-tcp-server


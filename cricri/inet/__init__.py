from voluptuous import Any, Match

from .server import Server


port_def = Any(
    Match(r"\{.+\}$", "int or string starts with '{' and ends with '}'"), int)


class Client:
    """
    `cricri.inet.TestServer` instanciates Client sub-classes.

    Client sub-classes should have `attr_name` attribute containing a string.
    `cricri.inet.TestServer` will use `attr_name` to create an entry point to
    intantiate clients. If attr_name is 'foo_clients', you can create a
    foo_clients list in TestServer sub class to instanciate FooClient.

    Example::

        class FooClient(Client):

            attr_name = foo_clients


        class MyTestServer(TestServer):

            foo_clients = [
                {
                    name: 'my-foo'
                }
            ]
    """

    attr_name = NotImplemented

    def close(self):
        """
        This method will call during the `stop_scenario`, before
        deleting client.
        """
        raise NotImplementedError

    @staticmethod
    def validator():
        """
        This method should return a dict.
        The dict will used as `voluptuous.Schema` first parameter.
        """
        raise NotImplementedError

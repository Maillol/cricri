.. _how-to-test-a-http-server-or-rest-api:

How to test a HTTP server or REST API
=====================================

You can create HTTP client using http_clients attribute in a *TestServer* subclasse::

    class TestRestServer(TestServer):

        http_clients = [
            {
                "name": "Alice",
                "host": "127.0.0.1",
                "port": "{port-1}",
                "extra_headers": [
                    ('Content-Type', 'application/json')
                ]
            }
        ]


http_client available parameters
--------------------------------

.. automethod:: cricri.inet.http_client.HTTPClient.__init__

Your HTTP clients are instantiate in *clients* class attribute and you may use them in the *input
method*::

    class GetHotels(TestRestServer, start=True):

        def input(self):
            self.clients["Alice"].get("/hotels")


HTTPClient methods
------------------

.. automethod:: cricri.inet.http_client.HTTPClient.request
.. automethod:: cricri.inet.http_client.HTTPClient.get
.. automethod:: cricri.inet.http_client.HTTPClient.post
.. automethod:: cricri.inet.http_client.HTTPClient.put
.. automethod:: cricri.inet.http_client.HTTPClient.delete
.. automethod:: cricri.inet.http_client.HTTPClient.patch

Response testing
----------------

The client stores HTTP response in response attribute using HTTPResponse
object. This HTTPResponse object provide methods useful for test server.

.. automethod:: cricri.inet.http_client.HTTPResponse.assert_header_has
.. automethod:: cricri.inet.http_client.HTTPResponse.assert_header_is
.. automethod:: cricri.inet.http_client.HTTPResponse.assert_status_code
.. automethod:: cricri.inet.http_client.HTTPResponse.assert_reason

Example::

    class GetHotels(TestRestServer, start=True):

        def test_status_code_should_be_200(self):
            self.clients["Alice"].response.assert_status_code(200)

        def test_content_has_hotel_california(self):
            content = self.clients["Alice"].response.content
            expected = ({
                "name": "California",
                "addr": "1976 eagles street"
            },)

            self.assertCountEqual(content, expected)



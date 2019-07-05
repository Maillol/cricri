Response testing
----------------

The client stores HTTP response in response attribute using HTTPResponse
object. This HTTPResponse object provide methods useful for test server.

.. automethod:: cricri.inet.http_client.HTTPResponse.assert_header_has
.. automethod:: cricri.inet.http_client.HTTPResponse.assert_header_is
.. automethod:: cricri.inet.http_client.HTTPResponse.assert_status_code
.. automethod:: cricri.inet.http_client.HTTPResponse.assert_reason
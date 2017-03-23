import unittest
from io import BytesIO
import http.client
from cricri.http_client import (HTTPResponse, 
                                NoResponseProvidedError)


class MockSocket:

    LINES = (b'HTTP/1.1 200 OK\r\n'
             b'Date: Tue, 21 Mar 2017 07:02:52 GMT\r\n'
             b'Server: CherryPy/10.2.1\r\n'
             b'Content-Type: application/json\r\n'
             b'Allow: DELETE, GET, HEAD, POST, PUT\r\n'
             b'Content-Length: 2\r\n'
             b'\r\n'
             b'[]')

    @classmethod
    def makefile(cls, _mode):
        return BytesIO(cls.LINES) 


class TestHTTPResponse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        response = http.client.HTTPResponse(MockSocket)
        response.begin()
        cls.responses = HTTPResponse(response)

    def test_version_should_be_1_1(self):
        self.assertEqual(self.responses.version, 11)

    def test_status_code_must_be_200(self):
        self.assertEqual(self.responses.status_code, 200)

    def test_reason_must_ok(self):
        self.assertEqual(self.responses.reason, 'OK')

    def test_assert_header_has_should_raise(self):
        """
        When HTTPResponse header has not value. 
        """
        with self.assertRaises(AssertionError):
            self.responses.assert_header_has('Allow', 'PATCH')

    def test_assert_header_has_should_not_raise(self):
        """
        When HTTPResponse header has value. 
        """
        self.assertIsNone(
            self.responses.assert_header_has('Allow', 'DELETE')
        )

    def test_assert_header_is_should_raise(self):
        """
        When HTTPResponse header is not exactly. 
        """
        with self.assertRaises(AssertionError):
            self.responses.assert_header_is('Allow',
                                            'GET, DELETE, HEAD, POST, PUT')

    def test_assert_header_is_should_not_raise(self):
        """
        When HTTPResponse header is exactly the given value.
        """
        self.assertIsNone(
            self.responses.assert_header_is('Allow',
                                            'DELETE, GET, HEAD, POST, PUT')
        )

    def test_assert_reason_should_raise(self):
        self.assertIsNone(
            self.responses.assert_reason('OK')
        )

    def test_assert_reason_should_not_raise(self):
        with self.assertRaises(AssertionError):
            self.responses.assert_reason('FAILED')

    def test_assert_status_code_should_raise(self):
        with self.assertRaises(AssertionError):
            self.responses.assert_status_code(201)

    def test_assert_status_code_should_not_raise(self):
        self.assertIsNone(
            self.responses.assert_status_code(200)
        )            

    def test_should_not_use_assert_when_response_is_not_provided(self):
        with self.assertRaises(NoResponseProvidedError):
            response = HTTPResponse()
            self.assertIsNone(
                response.assert_status_code(200)
            )       

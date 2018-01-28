"""
Utility to test HTTP server
"""

import json
import pprint
import socket
import time
from urllib.parse import parse_qsl, urlencode
from urllib.request import HTTPError, Request, urlopen
from xml.dom.minidom import parseString

from voluptuous import (All, Any, Optional, Range, Required, Schema)

from . import Client, port_def
from ..__version__ import __version__


class NoResponseProvidedError(Exception):
    """
    Raised when assert method is called but server
    has not send response.
    """


class HTTPResponse:
    """
    Parse response provided by urllib.request.urlopen using
    conten-type header to deserialize content.

    You can add custom deserializer using deserializers
    class attribute. The deserializers class attribute is dict where
    key is lower content-type header. value is callable that take
    a string in parameter.
    """

    deserializers = {
        'application/json': json.loads,
        'application/x-www-form-urlencoded': parse_qsl,
        'text/plain': str,
        'text/xml': parseString
    }

    def __init__(self, response=None):
        self.response_provided = response is not None
        if self.response_provided:
            self.status_code = response.status
            self.reason = response.reason
            self.headers = response.headers
            self.version = response.version
            self.content = self._get_content(response)
            response.close()

    def _get_content(self, response):
        """
        Get content and deserialize it using content-type header.
        """
        if response.status == 204:
            return None

        charset = self.headers.get_content_charset('utf-8')
        content_type = self.headers.get_content_type()
        deserializer = type(self).deserializers.get(content_type, str)
        return deserializer(response.read().decode(charset))

    def _formated_content(self):
        """
        Format content for traceback
        """
        content = self.content
        if self.status_code == 204 and not content:
            return ''

        if not isinstance(content, str):
            content = pprint.pformat(content, width=76)
        return '    ' + '\n    '.join(content.splitlines())

    def assert_header_has(self, header, expected_value, separator=','):
        """
        Test if header of HTTP response contains the expected_value.
        """
        current_values = []
        for values in self.headers.get_all(header, []):
            current_values.extend(value.strip()
                                  for value
                                  in values.split(separator))

        if expected_value not in current_values:
            raise AssertionError('{} HTTP header has not {} value. found: {}'
                                 .format(header, expected_value,
                                         current_values))

    def assert_header_is(self, header, expected_values, separator=','):
        """
        Test if value header of HTTP response is the *expected_value*.
        """
        current_values = []
        for values in self.headers.get_all(header, []):
            current_values.extend(value.strip()
                                  for value
                                  in values.split(separator))

        if isinstance(expected_values, str):
            expected_values = [value.strip()
                               for value
                               in expected_values.split(separator)]

        if expected_values != current_values:
            raise AssertionError('{} HTTP header expected: {} found: {}'
                                 .format(header,
                                         separator.join(expected_values),
                                         separator.join(current_values)))

    def assert_status_code(self, status_code):
        """
        Test if status code of HTTP response is *status_code*
        """
        if self.status_code != status_code:
            raise AssertionError('status code expected: {} found: ({} {})\n'
                                 '  Content:\n{}'
                                 .format(status_code, self.status_code,
                                         self.reason, self._formated_content()))

    def assert_reason(self, reason):
        """
        Test if reason of HTTP response is *reason*
        """
        if self.reason != reason:
            raise AssertionError('reason expected: {} found: {}'
                                 '  Content:\n{}'
                                 .format(reason, self.reason,
                                         self._formated_content()))

    def __getattribute__(self, name):
        if name.startswith('assert') and not self.response_provided:
            raise NoResponseProvidedError('Server has not send response')
        return super().__getattribute__(name)


class HTTPClient(Client):
    """
    Client to performe HTTP request.
    """

    NO_CONTENT = object()

    user_agent = ('User-Agent', 'cricri/{}'.format(__version__))

    serializers = {
        'application/json': json.dumps,
        'application/x-www-form-urlencoded': urlencode,
        'text/plain': str
    }

    attr_name = 'http_clients'

    @staticmethod
    def validator():
        """
        Return callable to validate __init__ attribute
        """

        return {
            Required("host"): str,
            Required("port"): port_def,
            Optional("timeout", default=2): Range(0, min_included=False),
            Optional("tries", default=3): All(int, Range(0, min_included=False)),
            Optional("wait", default=1): Range(0, min_included=False),
            Optional("headers", default=[]): list,
            Optional("extra_headers", default=None): Any(list, None)
        }

    def __init__(self, host, port, timeout, tries,
                 wait, headers, extra_headers=None):
        """
        :param host: Server host
        :type host: str

        :param port: The number of tries
        :type port: int

        :param tries: The number of tries
        :type tries: int

        :param timeout: Deadline before abort request
        :type timeout: int

        :param headers: The default headers used when you call request method
                        without define headers parameter.
        :type headers: List[Tuple]

        :param extra_headers: Always used when you call request method by default
                              extra_headers contains the User-Agent.
        :type extra_headers: List[Tuple]
        """

        self.host = host
        self.port = port
        self.timeout = timeout
        self.tries = tries
        self.wait = wait
        self.default_headers = headers

        if extra_headers is None:
            self.extra_headers = [self.user_agent]
        else:
            self.extra_headers = extra_headers

        self.response = HTTPResponse()

    def close(self):
        """
        Connection is close when server send http response.
        """

    def _get_serializer(self, headers):
        """
        Select serialiser from content type header.
        by defaut 'text/plain' serializer is used.
        """
        serializer = None
        for key, value in headers:
            if key == 'Content-Type':
                serializer = type(self).serializers.get(value)
                break

        if serializer is None:
            serializer = type(self).serializers['text/plain']

        return serializer

    def request(self, method, path, headers=None,
                timeout=None, data=NO_CONTENT):
        """
        Performe HTTP request to *path*


        :param method: HTTP verb such as 'GET', 'POST', ...
        :type method: str

        :param path: HTTP server path
        :type path: str

        :param headers: HTTP headers must be 2-tuple (header, value)
                        if headers is not define *__init__* headers parameter
                        is used.
        :type headers: List[Tuple]

        :param timeout: Deadline before abort request
        :type timeout: int

        :param data: HTTP request content. data is serialised regarding the
                     content-type define in the HTTP headers. You can change
                     this behavior updating *serializers* class attribute.
        :type data: object
        """

        if headers is None:
            headers = list(self.default_headers)
        headers += self.extra_headers

        if timeout is None:
            timeout = self.timeout

        headers += [('Host', '{}:{}'
                     .format(self.host, self.port)
                     .encode('utf-8'))]

        url = 'http://{}:{}{}'.format(self.host, self.port, path)
        request = Request(url, method=method, headers=dict(headers))
        if data is not self.NO_CONTENT:
            content = self._get_serializer(headers)(data)
            request.data = content.encode('utf-8')

        self.response = None
        for _ in range(self.tries):
            start = time.time()
            try:
                self.response = HTTPResponse(urlopen(request, timeout=timeout))

            except HTTPError as error:
                socket_error = None
                self.response = HTTPResponse(error)
                break

            except socket.timeout as error:
                socket_error = error

            except OSError as error:
                socket_error = error
                if self.wait is None:
                    time.sleep(timeout - (time.time() - start))
                else:
                    time.sleep(self.wait)
            else:
                socket_error = None
                break

        if socket_error is not None:
            raise socket_error

    def get(self, *args, **kwargs):
        """
        Shortcut to request(GET, ...)
        """
        self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Shortcut to request(POST, ...)
        """
        self.request('POST', *args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Shortcut to request(PUT, ...)
        """
        self.request('PUT', *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Shortcut to request(DELETE, ...)
        """
        self.request('DELETE', *args, **kwargs)

    def patch(self, *args, **kwargs):
        """
        Shortcut to request(PATCH, ...)
        """
        self.request('PATCH', *args, **kwargs)

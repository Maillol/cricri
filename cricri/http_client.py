from .__version__ import __version__
import json
import socket
import time
from urllib.parse import parse_qsl, urlencode
from urllib.request import urlopen, Request
from xml.dom.minidom import parseString


class NoResponseProvidedError(Exception):
    """
    Raised when assert method is called but server
    has not send response.
    """


class HTTPResponse:

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

    def assert_header_has(self, header, expected_value, separator=','):
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
        if self.status_code != status_code:
            raise AssertionError('status code expected: {} found: {}'
                                 .format(status_code, self.status_code))

    def assert_reason(self, reason):
        if self.reason != reason:
            raise AssertionError('reason expected: {} found: {}'
                                 .format(reason, self.reason))

    def __getattribute__(self, name):
        if name.startswith('assert') and not self.response_provided:
            raise NoResponseProvidedError('Server has not send response')         
        return super().__getattribute__(name)


class HTTPClient:

    NO_CONTENT = object()

    user_agent = ('User-Agent', 'cricri/{}'.format(__version__))

    serializers = {
        'application/json': json.dumps,
        'application/x-www-form-urlencoded': urlencode,
        'text/plain': str
    }

    def __init__(self, host, port, timeout, tries,
                 wait, headers, extra_headers=None):
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

    def request(self, method, url, headers=None,
                timeout=None, data=NO_CONTENT):
        
        if headers is None:
            headers = list(self.default_headers)
        headers += self.extra_headers 

        if timeout is None:
            timeout = self.timeout

        original_timeout = timeout

        headers += [('Host', '{}:{}'
                     .format(self.host, self.port)
                     .encode('utf-8'))]

        url = 'http://{}:{}{}'.format(self.host, self.port, url)
        request = Request(url, method=method, headers=dict(headers))
        if data is not self.NO_CONTENT:
            content = self._get_serializer(headers)(data)
            request.data = content.encode('utf-8')

        self.response = None
        for _ in range(self.tries):
            start = time.time()
            try:
                self.response = HTTPResponse(urlopen(request, timeout=timeout))

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
        Shortcut to request(self, GET, ...) 
        """
        self.request('GET',  *args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Shortcut to request(self, POST, ...) 
        """
        self.request('POST',  *args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Shortcut to request(self, PUT, ...) 
        """
        self.request('PUT',  *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Shortcut to request(self, DELETE, ...) 
        """
        self.request('DELETE',  *args, **kwargs)

    def patch(self, *args, **kwargs):
        """
        Shortcut to request(self, PATCH, ...) 
        """
        self.request('PATCH',  *args, **kwargs)




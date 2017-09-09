import signal

from cricri import TestServer, previous, Newer, Path, condition
from cricri.inet.http_client import BasicAuth
 

class TestRestServer(TestServer):

    id_from_name = {}

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
    commands = [
        {
            "name": "chat-server",
            "cmd": ["python3", "-u", "http_authentification.py", "{port-1}"],
            "kill-signal": signal.SIGKILL
        }
    ]


HOTEL_CALIFORNIA_EXIST = Newer('DeleteHotelCalifornia', 'CreateHotelCalifornia')


class GetHotels(TestRestServer, start=True, previous=["CreateHotelCalifornia",
                                                      "DeleteHotelCalifornia"]):

    def input(self):
        self.clients["Alice"].get("/hotels", auth=BasicAuth(passwd='secret', user='jon'))

    def test_status_code_should_be_200(self):
        self.clients["Alice"].response.assert_status_code(200)

    @condition(HOTEL_CALIFORNIA_EXIST)
    def test_content_has_hotel_california(self):
        content = self.clients["Alice"].response.content
        expected = ({
            "id": self.id_from_name["California"],
             "name": "California"
        },)

        self.assertCountEqual(content, expected)


class CreateHotelCalifornia(TestRestServer, previous=["GetHotels"]):

    @condition(-HOTEL_CALIFORNIA_EXIST)
    def input(self):
        self.clients["Alice"].post("/hotels", data={"name": "California"}, auth=BasicAuth(passwd='secret', user='jon'))

    def test_status_code_should_be_201(self):
        self.clients["Alice"].response.assert_status_code(201)

    def test_content_should_be_hotel(self):
        content = self.clients["Alice"].response.content
        self.assertEqual(content["name"], "California")
        self.id_from_name['California'] = content["id"]


class DeleteHotelCalifornia(TestRestServer, previous=["GetHotels"]):

    @condition(HOTEL_CALIFORNIA_EXIST)
    def input(self):
        self.clients["Alice"].delete("/hotels/{}".format(self.id_from_name['California']), auth=BasicAuth(passwd='secret', user='jon'))

    def test_status_code_should_be_204(self):
        self.clients["Alice"].response.assert_status_code(204)




load_tests = TestRestServer.get_load_tests()

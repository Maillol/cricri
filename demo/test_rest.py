import signal

from cricri import TestServer, previous, Newer, Path, condition


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
            "cmd": ["python3", "-u", "rest.py", "{port-1}"],
            "kill-signal": signal.SIGKILL
        }
    ]


HOTEL_CALIFORNIA_EXIST = Newer('DeleteHotelCalifornia', 'CreateHotelCalifornia')
HOTEL_DU_NORD_EXIST = Newer('DeleteHotelDuNord', 'CreateHotelDuNord')


class GetHotels(TestRestServer, start=True, previous=["CreateHotelDuNord", "CreateHotelCalifornia",
                                                      "DeleteHotelDuNord", "DeleteHotelCalifornia"]):

    def input(self):
        self.clients["Alice"].get("/hotels")

    def test_status_code_should_be_200(self):
        self.clients["Alice"].response.assert_status_code(200)

    @condition(-HOTEL_DU_NORD_EXIST & HOTEL_CALIFORNIA_EXIST)
    def test_content_has_hotel_california(self):
        content = self.clients["Alice"].response.content
        expected = ({
            "id": self.id_from_name["California"],
             "name": "California"
        },)

        self.assertCountEqual(content, expected)

    @condition(HOTEL_DU_NORD_EXIST & -HOTEL_CALIFORNIA_EXIST)
    def test_content_has_hotel_du_nord(self):
        content = self.clients["Alice"].response.content
        expected = ({
            "id": self.id_from_name["Du nord"],
            "name": "Du nord"
        },)

        self.assertCountEqual(content, expected)

    @condition(HOTEL_DU_NORD_EXIST & HOTEL_CALIFORNIA_EXIST)
    def test_content_has_both_hotels(self):
        content = self.clients["Alice"].response.content
        expected = ({
            "id": self.id_from_name["California"],
             "name": "California"
        }, {
            "id": self.id_from_name["Du nord"],
            "name": "Du nord"
        })

        self.assertCountEqual(content, expected)


class CreateHotelCalifornia(TestRestServer, previous=["GetHotels"]):

    @condition(-HOTEL_CALIFORNIA_EXIST)
    def input(self):
        self.clients["Alice"].post("/hotels", data={"name": "California"})

    def test_status_code_should_be_201(self):
        self.clients["Alice"].response.assert_status_code(201)

    def test_content_should_be_hotel(self):
        content = self.clients["Alice"].response.content
        self.assertEqual(content["name"], "California")
        self.id_from_name['California'] = content["id"]


class CreateHotelDuNord(TestRestServer, previous=["GetHotels"]):

    @condition(-HOTEL_DU_NORD_EXIST)
    def input(self):
        self.clients["Alice"].post("/hotels", data={"name": "Du nord"})

    def test_status_code_should_be_201(self):
        self.clients["Alice"].response.assert_status_code(201)

    def test_content_should_be_hotel(self):
        content = self.clients["Alice"].response.content
        self.assertEqual(content["name"], "Du nord")
        self.id_from_name['Du nord'] = content["id"]


class DeleteHotelCalifornia(TestRestServer, previous=["GetHotels"]):

    @condition(HOTEL_CALIFORNIA_EXIST)
    def input(self):
        self.clients["Alice"].delete("/hotels/{}".format(self.id_from_name['California']))

    def test_status_code_should_be_204(self):
        self.clients["Alice"].response.assert_status_code(204)


class DeleteHotelDuNord(TestRestServer, previous=["GetHotels"]):

    @condition(HOTEL_DU_NORD_EXIST)
    def input(self):
        self.clients["Alice"].delete("/hotels/{}".format(self.id_from_name['Du nord']))

    def test_status_code_should_be_204(self):
        self.clients["Alice"].response.assert_status_code(204)


load_tests = TestRestServer.get_load_tests()

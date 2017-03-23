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
        }
    ]


class GotHotels(TestRestServer, start=True):

    def input(self):
        self.clients["Alice"].get("/hotels")

    def test_status_code_should_be_200(self):
        self.clients["Alice"].response.assert_status_code(200)


class CreateCaliforniaHotels(TestRestServer, previous=["GotHotels"]):

    def input(self):
        self.clients["Alice"].post("/hotels", data={"name": "California"})

    def test_status_code_should_be_200(self):
        self.clients["Alice"].response.assert_status_code(201)


class CreateJadeHotels(TestRestServer, previous=["GotHotels", "CreateCaliforniaHotels"]):

    def input(self):
        self.clients["Alice"].post("/hotels", data={"name": "Jade"})

    def test_status_code_should_be_200(self):
        self.clients["Alice"].response.assert_status_code(201)

    def test_content_should_be_hotel(self):
        content = self.clients["Alice"].response.content
        self.assertEqual(content["name"], "Jade")
        self.id_from_name['Jade'] = content["id"]

class DeleteJadeHotels(TestRestServer, previous=["GotHotels", "CreateJadeHotels"]):

    def input(self):
        self.clients["Alice"].delete("/hotels/{}".format(self.id_from_name['Jade']))

    def test_status_code_should_be_204(self):
        self.clients["Alice"].response.assert_status_code(204)


load_tests = TestRestServer.get_load_tests()

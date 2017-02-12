from gentest import TestServer, previous, Newer, Path, condition


class TestChatServer(TestServer):
    tcp_clients = [
        {
            "name": "Alice",
            "port": "{port-1}",
        },
        {
            "name": "Bob",
            "port": "{port-1}",
        },
        {
            "name": "Bob-plagiarizer",
            "port": "{port-1}",
        }
    ]
    commands = [
        {
            "name": "launch_server",
            "cmd": ["python3", "chat_server.py", "{port-1}"],
        }
    ]


ALICE_IS_CONNECTED = Newer('AliceSaidBye', 'AliceAskedNickname')
ALICE_IS_NOT_CONNECTED = -ALICE_IS_CONNECTED
BOB_IS_CONNECTED = Newer('BobSaidBye', 'BobAskedNickname')
BOB_IS_NOT_CONNECTED = -BOB_IS_CONNECTED


class Start(TestChatServer, start=True):
    pass


class AliceAskedNickname(TestChatServer, previous=["Start", "AliceAskedNickname", "BobAskedNickname"]):

    def input(self):
        self.clients["Alice"].send("MY_NAME_IS;Alice;")

    @condition(ALICE_IS_CONNECTED)
    def test_alice_should_receive_error_if_she_is_already_a_nickname(self):
        self.clients["Alice"].assertReceive('ERROR: I know you')

    @condition(ALICE_IS_NOT_CONNECTED)
    def test_alice_should_receive_ok(self):
        self.clients["Alice"].assertReceive('OK')


class BobAskedNickname(TestChatServer, previous=["Start", "AliceAskedNickname", "BobAskedNickname"]):

    def input(self):
        self.clients["Bob"].send("MY_NAME_IS;Bob;")

    @condition(BOB_IS_CONNECTED)
    def test_bob_should_receive_error_if_he_is_already_a_nickname(self):
        self.clients["Bob"].assertReceive('ERROR: I know you')

    @condition(BOB_IS_NOT_CONNECTED)
    def test_bob_should_receive_ok(self):
        self.clients["Bob"].assertReceive('OK')


class BobPlagiarizerAskedNickname(TestChatServer, previous=["BobAskedNickname"]):

    def input(self):
        self.clients["Bob-plagiarizer"].send("MY_NAME_IS;Bob;")

    def test_bob_plagiarizer_should_receive_error(self):
        self.clients["Bob-plagiarizer"].assertReceive('ERROR: nickname is already used')


class BobSentMessage(TestChatServer, previous=["Start", "BobAskedNickname", "BobSaidBye",
                                               "AliceAskedNickname", "AliceSaidBye"]):

    def input(self):
        self.clients["Bob"].send("SEND_TO;Alice;Hello")

    @condition(BOB_IS_CONNECTED & ALICE_IS_CONNECTED)
    def test_alice_shoult_receive_message(self):
        self.clients["Alice"].assertReceive('Hello')

    @condition(BOB_IS_CONNECTED & ALICE_IS_NOT_CONNECTED)
    def test_bob_should_receive_error_if_alice_is_not_connected(self):
        self.clients["Bob"].assertReceive('ERROR: recipient is not connected')

    @condition(BOB_IS_NOT_CONNECTED)
    def test_bob_should_receive_error_if_is_not_connected(self):
        self.clients["Bob"].assertReceive("ERROR: I don't know you")


class AliceSentMessage(TestChatServer, previous=["Start", "BobAskedNickname", "BobSaidBye",
                                                 "BobSentMessage", 
                                                 "AliceAskedNickname", "AliceSaidBye"]):

    def input(self):
        self.clients["Alice"].send("SEND_TO;Bob;Hi")

    @condition(ALICE_IS_CONNECTED & BOB_IS_CONNECTED)
    def test_bob_shoult_receive_message(self):
        self.clients["Bob"].assertReceive('Hi')

    @condition(ALICE_IS_CONNECTED & BOB_IS_NOT_CONNECTED)
    def test_alice_should_receive_error_if_bob_is_not_connected(self):
        self.clients["Alice"].assertReceive('ERROR: recipient is not connected')

    @condition(ALICE_IS_NOT_CONNECTED)
    def test_alice_should_receive_error_if_is_not_connected(self):
        self.clients["Alice"].assertReceive("ERROR: I don't know you")


class AliceSaidBye(TestChatServer, previous=["Start", "AliceAskedNickname", 
                                             "AliceSentMessage", "AliceSaidBye"]):

    def input(self):
        self.clients["Alice"].send("BYE;;")

    @condition(ALICE_IS_NOT_CONNECTED)
    def test_alice_shoult_receive_error_if_she_does_not_have_a_nickname(self):
        self.clients["Alice"].assertReceive("ERROR: I don't know you")

    @condition(ALICE_IS_CONNECTED)
    def test_alice_shoult_receive_ok(self):
        self.clients["Alice"].assertReceive('BYE')


class BobSaidBye(TestChatServer, previous=["Start", "BobAskedNickname", 
                                           "BobSentMessage", "BobSaidBye"]):

    def input(self):
        self.clients["Bob"].send("BYE;;")

    @condition(BOB_IS_NOT_CONNECTED)
    def test_bob_shoult_receive_error_if_he_does_not_have_a_nickname(self):
        self.clients["Bob"].assertReceive("ERROR: I don't know you")

    @condition(BOB_IS_CONNECTED)
    def test_a_ok(self):
        self.clients["Bob"].assertReceive('BYE')


load_tests = TestChatServer.get_load_tests()


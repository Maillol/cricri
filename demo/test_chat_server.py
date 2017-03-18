from cricri import TestServer, previous, Newer, Path, condition


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
            "name": "chat-server",
            "cmd": ["python3", "-u", "chat_server.py", "{port-1}"],
        }
    ]


ALICE_HAS_NICKNAME = Newer('AliceSaidBye', 'AliceAskedNickname')
ALICE_HAS_NO_NICKNAME = -ALICE_HAS_NICKNAME
BOB_HAS_NICKNAME = Newer('BobSaidBye', 'BobAskedNickname')
BOB_HAS_NO_NICKNAME = -BOB_HAS_NICKNAME


class Start(TestChatServer, start=True):

    def test_server_listen(self):
        self.servers['chat-server'].assert_stdout_regex(
            'server listen on port \d+', timeout=2
        )

class AliceAskedNickname(TestChatServer, previous=["Start", "AliceAskedNickname", "BobAskedNickname"]):

    def input(self):
        self.clients["Alice"].send("MY_NAME_IS;Alice;")

    @condition(ALICE_HAS_NICKNAME)
    def test_alice_should_receive_error_if_she_is_already_a_nickname(self):
        self.clients["Alice"].assert_receive('ERROR: I know you')

    @condition(ALICE_HAS_NO_NICKNAME)
    def test_alice_should_receive_ok(self):
        self.clients["Alice"].assert_receive('OK')


class BobAskedNickname(TestChatServer, previous=["Start", "AliceAskedNickname", "BobAskedNickname"]):

    def input(self):
        self.clients["Bob"].send("MY_NAME_IS;Bob;")

    @condition(BOB_HAS_NICKNAME)
    def test_bob_should_receive_error_if_he_is_already_a_nickname(self):
        self.clients["Bob"].assert_receive('ERROR: I know you')

    @condition(BOB_HAS_NO_NICKNAME)
    def test_bob_should_receive_ok(self):
        self.clients["Bob"].assert_receive('OK')


class BobPlagiarizerAskedNickname(TestChatServer, previous=["BobAskedNickname"]):

    def input(self):
        self.clients["Bob-plagiarizer"].send("MY_NAME_IS;Bob;")

    def test_bob_plagiarizer_should_receive_error(self):
        self.clients["Bob-plagiarizer"].assert_receive('ERROR: nickname is already used')


class BobSentMessage(TestChatServer, previous=["Start", "BobAskedNickname", "BobSaidBye",
                                               "AliceAskedNickname", "AliceSaidBye"]):

    def input(self):
        self.clients["Bob"].send("SEND_TO;Alice;Hello")

    @condition(BOB_HAS_NICKNAME & ALICE_HAS_NICKNAME)
    def test_alice_shoult_receive_message(self):
        self.clients["Alice"].assert_receive('Hello')

    @condition(BOB_HAS_NICKNAME & ALICE_HAS_NO_NICKNAME)
    def test_bob_should_receive_error_if_ALICE_HAS_NO_NICKNAME(self):
        self.clients["Bob"].assert_receive('ERROR: recipient is not connected')

    @condition(BOB_HAS_NO_NICKNAME)
    def test_bob_should_receive_error_if_is_not_connected(self):
        self.clients["Bob"].assert_receive("ERROR: I don't know you")


class AliceSentMessage(TestChatServer, previous=["Start", "BobAskedNickname", "BobSaidBye",
                                                 "BobSentMessage", 
                                                 "AliceAskedNickname", "AliceSaidBye"]):

    def input(self):
        self.clients["Alice"].send("SEND_TO;Bob;Hi")

    @condition(ALICE_HAS_NICKNAME & BOB_HAS_NICKNAME)
    def test_bob_shoult_receive_message(self):
        self.clients["Bob"].assert_receive('Hi')

    @condition(ALICE_HAS_NICKNAME & BOB_HAS_NO_NICKNAME)
    def test_alice_should_receive_error_if_BOB_HAS_NO_NICKNAME(self):
        self.clients["Alice"].assert_receive('ERROR: recipient is not connected')

    @condition(ALICE_HAS_NO_NICKNAME)
    def test_alice_should_receive_error_if_is_not_connected(self):
        self.clients["Alice"].assert_receive("ERROR: I don't know you")


class AliceSaidBye(TestChatServer, previous=["Start", "AliceAskedNickname", 
                                             "AliceSentMessage", "AliceSaidBye"]):

    def input(self):
        self.clients["Alice"].send("BYE;;")

    @condition(ALICE_HAS_NO_NICKNAME)
    def test_alice_shoult_receive_error_if_she_does_not_have_a_nickname(self):
        self.clients["Alice"].assert_receive("ERROR: I don't know you")

    @condition(ALICE_HAS_NICKNAME)
    def test_alice_shoult_receive_ok(self):
        self.clients["Alice"].assert_receive('BYE')


class BobSaidBye(TestChatServer, previous=["Start", "BobAskedNickname", 
                                           "BobSentMessage", "BobSaidBye"]):

    def input(self):
        self.clients["Bob"].send("BYE;;")

    @condition(BOB_HAS_NO_NICKNAME)
    def test_bob_shoult_receive_error_if_he_does_not_have_a_nickname(self):
        self.clients["Bob"].assert_receive("ERROR: I don't know you")

    @condition(BOB_HAS_NICKNAME)
    def test_a_ok(self):
        self.clients["Bob"].assert_receive('BYE')


load_tests = TestChatServer.get_load_tests()


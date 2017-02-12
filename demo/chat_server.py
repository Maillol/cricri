"""
Simple chat server

Protocol message format:

    "{COMMAND};{ARG_1};{ARG_2}"


Available COMMAND:

                ┌───────────────┬─────────┬─────────────────────────┐
                │     ARG_1     │  ARG_2  │      Description        │
   ┌────────────┼───────────────┼─────────┼─────────────────────────┤
   │ MY_NAME_IS │ Nickname      │         │ Connection with uniq    │
   │            │               │         │ nickname                │
   ├────────────┼───────────────┼─────────┼─────────────────────────┤
   │ SEND_DO    │ Nickname of   │ Message │ Send Message to the     │
   │            │ the recipient │ to send │ recipient               │
   ├────────────┼───────────────┼─────────┼─────────────────────────┤
   │ BYE        │               │         │ Sign out                │
   └────────────┴───────────────┴─────────┴─────────────────────────┘

"""

from selectors import DefaultSelector, EVENT_READ
import socket
import sys


class ChatServer:

    def __init__(self, port):
        self.sockets = {}
        self.names = {}
        self.socket_server = socket.socket(socket.AF_INET,
                                           socket.SOCK_STREAM | socket.SOCK_NONBLOCK)
        self.selector = DefaultSelector()
        self.socket_server.bind(("", port))
        self._running = False

    def _accept(self, socket):
        socket_client = socket.accept()[0]
        socket_client.setblocking(False)
        self.selector.register(socket_client, EVENT_READ, self._read)

    def _read(self, socket):
        data = socket.recv(256)
        data = data.decode('utf-8')

        if not data: # socket closed.
            name = self.sockets.pop(socket, None)
            if name is not None:
                self.names.pop(name, None)
            return

        try:
            order, p1, p2 = data.split(';')
        except ValueError:
            socket.send('ERROR: Bad request {!r}'.format(data).encode("utf-8"))
            print('Bad request {!r}'.format(data))
            return

        if order == "MY_NAME_IS" and socket in self.sockets:
            socket.send(b"ERROR: I know you")
            return
        if order in ('SEND_TO', 'BYE') and socket not in self.sockets:
            socket.send(b"ERROR: I don't know you")
            return

        if order == "MY_NAME_IS":
            if p1 in self.names:
                socket.send(b'ERROR: nickname is already used')
            else:
                self.names[p1] = socket
                self.sockets[socket] = p1
                socket.send(b'OK')

        elif order == "SEND_TO":
            if p1 not in self.names:
                socket.send(b'ERROR: recipient is not connected')
            else:
                self.names[p1].send(p2.encode('utf-8'))

        elif order == "BYE":
            name = self.sockets.pop(socket, None)
            self.names.pop(name, None)
            socket.send(b'BYE')


    def run_forever(self):
        self.socket_server.listen(1)
        self.selector.register(self.socket_server, EVENT_READ, self._accept)
        self._running = True
        while self._running:
            for key, events in self.selector.select():
                key.data(key.fileobj)

    def close(self):
        self._running = False
        self.selector.close()
        self.socket_server.close()


if __name__ == '__main__':
    port = int(sys.argv[1])
    server = ChatServer(port)

    try:
        print("server listen on port {}".format(port))
        server.run_forever()
    except KeyboardInterrupt:
        server.close()



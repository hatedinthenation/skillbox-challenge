from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineOnlyReceiver
from collections import deque

DEFAULT_HISTORY_LEN = 10


class Handler(LineOnlyReceiver):
    factory: 'Server'
    login: str  # login:SOME_TEXT

    def connectionLost(self, reason=connectionDone):
        self.factory.clients.remove(self)
        print("Disconnected")

    def connectionMade(self):
        self.login = None
        self.factory.clients.append(self)
        print("Unauthorized client connected")

    def lineReceived(self, line: bytes):
        message = line.decode()
        if self.login:
            self.handle_message(message)
        else:
            self.authenticate_user(message)

    def authenticate_user(self, message):
        if message.startswith("login:"):
            login = message.replace("login:", "")
            if self.is_username_valid(login):
                self.login = login
                print(f"New user authorized: <{login}>")
                self.sendLine(f"Wellcome, {login}!".encode())
                self.send_history()
            else:
                print(f"Login attempt failed. Username <{login}>")
                self.sendLine(f"Login {login} already exist, try another".encode())
        else:
            self.sendLine("Wrong Login".encode())

    def is_username_valid(self, username):
        for user in self.factory.clients:
            if user.login == username:
                return None
        return True

    def handle_message(self, message):
        message = f"<{self.login}>: {message}"
        self.factory.history.append(message)
        for user in self.factory.clients:
            if user is not self and user.login:
                user.sendLine(message.encode())

    def send_history(self):
        for message in self.factory.history:
            self.sendLine(message.encode())


class Server(ServerFactory):
    protocol = Handler
    clients: list
    history: deque
    history_len: int

    def __init__(self, history_len=DEFAULT_HISTORY_LEN):
        self.clients = []
        self.history_len = history_len
        self.history = deque(maxlen=history_len)

    def startFactory(self):
        print("Server started...")


reactor.listenTCP(
    7410,
    Server()
)
reactor.run()
import socket
from getpass import getpass

class Client:
    def __init__(self):
        #self.host = 'localhost'
        self.host = 'ec2-13-52-78-168.us-west-1.compute.amazonaws.com'
        self.port = 1001
        self.loggedIn = False
        self.username = ''
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Welcome to ZotSight")

    def connect(self):
        try:
            print("Connecting to server...")
            self.server.connect((self.host, self.port))
            print("Connection established")
            return True
        except:
            print("Could not establish connection")
            return False

    def receive(self):
        return str(self.server.recv(1024).decode('ascii'))

    def send(self, message, ack = False):
        try:
            self.server.send(message.encode('ascii'))
            if ack:
                assert self.receive() == 'received'
            return True
        except:
            return False

    def login(self):
        print("SIGN INTO EXISTING ACCOUNT")
        self.send("login", True)
        username = input("Username: ")
        self.send(username, True)
        password = getpass()
        self.send(password)
        response = self.receive()
        if response == "login_success":
            print("Successfully logged in as: ", username)
            self.loggedIn = True
            self.username = username
        else:
            print("Login failed")

    def logout(self):
        self.send("logout", True)
        self.loggedIn = False
        self.username = ''

    def createAccount(self):
        print("CREATE ACCOUNT")
        try:
            self.send("create", True)
            username = input("Username: ")
            password = ''
            while True:
                password = getpass()
                if password == getpass("Confirm Password: "):
                    break
                else:
                    print("Passwords do not match")
                    continue
            self.send(username, True)
            self.send(password, True)
            response = self.receive()
            if(response == "creation_succeeded"):
                print("Successfully logged in as: ", username)
                self.loggedIn = True
                self.username = username
            else:
                print("Could not create account")
        except KeyboardInterrupt:
            return

    def mainloop(self):
        while True:
            arg = input(">>>")
            arg = arg.lower()
            if arg == 'status':
                if self.loggedIn:
                    print("You are logged in as ", self.username)
                else:
                    print("You are not logged in")
            elif arg == 'login':
                self.login()
            elif arg == 'logout':
                self.logout()
            elif arg == 'create':
                self.createAccount()
            elif arg == 'exit':
                self.logout()
                return
            elif arg == 'help':
                print("status: check login status\n" \
                        "login: sign into account if you are not logged in\n" \
                        "logout: sign out of account if you are logged in\n" \
                        "create: create new account\n" \
                        "exit: sign out and exit application\n")

if __name__ == '__main__':
    c = Client()
    if c.connect():
        c.mainloop()
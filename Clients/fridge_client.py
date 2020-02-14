import socket
from getpass import getpass
import serial

class Client:
    def __init__(self):
        self.host = 'ec2-13-52-78-168.us-west-1.compute.amazonaws.com'
        self.port = 1050
        self.loggedIn = False
        self.username = ''
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Welcome to ZotSight")

    def connect(self):
        try:
            print("Connecting to server...")
            self.server.connect((self.host, self.port))
            self.send("f", True)
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
            return True
        else:
            print("Login failed")
            return False

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
                return True
            else:
                print("Could not create account")
                return False
        except KeyboardInterrupt:
            return

    def start(self):
        while True:
            arg = input("Login (L) or Create Account (C)?\n").lower()
            if arg == "l":
                if self.login():
                    self.mainLoop()
            elif arg == 'c':
                if self.createAccount():
                    self.mainLoop()

    def mainLoop(self):
        arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout = 0.1)
        while True:
            data = arduino.readline()[:-2]
            if data == b"DoorClosed":
                print("Door Closed")
        

if __name__ == '__main__':
    c = Client()
    if c.connect():
        c.start()
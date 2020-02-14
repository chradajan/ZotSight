import socket
import pymysql
import bcrypt

class Client_Server:
    def __init__(self, clientSocket, db, clientType):
        self.client = clientSocket
        self.loggedIn = False
        self.username = ''
        self.clientType = clientType
        self.db = db
        self.cursor = self.db.cursor()

    def getDecodedMessage(self, ack = False):
        try:
            message = str(self.client.recv(1024).decode('ascii'))
            if ack:
                self.send("received")
            return message
        except:
            return ""

    def send(self, message):
        self.client.send(message.encode('ascii'))

    def login(self):
        username = self.getDecodedMessage(True)
        password = self.getDecodedMessage()
        try:
            self.cursor.execute("SELECT username, hash FROM users WHERE username='{}'".format(username))
            if not self.cursor.rowcount:
                self.send("login_fail")
            else:
                if bcrypt.checkpw(password.encode(), self.cursor.fetchone()[1].encode()):
                    self.loggedIn = True
                    self.username = username
                    self.send("login_success")
                else:
                    self.send("login_fail")
        except:
            self.send("login_fail")

    def logout(self):
        self.loggedIn = False
        self.username = ''

    def createAccount(self):
        username = self.getDecodedMessage(True)
        password = self.getDecodedMessage(True)
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            self.cursor.execute("INSERT INTO users (id, username, hash) VALUES (default, '{}', '{}')".format(username, hashed))
            self.db.commit()
            self.loggedIn = True
            self.username = username
            self.send("creation_succeeded")
        except:
            self.db.rollback()
            self.send("creation_failed")
        

    def mainloop(self):
        while True:
            message = self.getDecodedMessage(True)
            if not message:
                return
            
            if message == "login":
                self.login()
            elif message == "logout":
                self.logout()
            elif message == "create":
                self.createAccount()
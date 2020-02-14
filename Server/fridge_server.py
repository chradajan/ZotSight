import socket
import pymysql
import bcrypt

class Fridge_Server:
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
                return False
            else:
                if bcrypt.checkpw(password.encode(), self.cursor.fetchone()[1].encode()):
                    self.loggedIn = True
                    self.username = username
                    self.send("login_success")
                    return True
                else:
                    self.send("login_fail")
                    return False
        except:
            self.send("login_fail")
            return False

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
            return True
        except:
            self.db.rollback()
            self.send("creation_failed")
            return False
        

    def mainloop(self):
        while True:
            message = self.getDecodedMessage(True)
            if not message:
                continue
            
            if message == "login":
                if self.login():
                    break
            elif message == "create":
                if self.createAccount():
                    break

        while True:
            message = self.getDecodedMessage(True)
            if not message:
                continue

            
import socket
from _thread import *
import threading
import pymysql
import bcrypt

db = pymysql.connect('fridge-db.cq9smwtzhpgg.us-west-1.rds.amazonaws.com', 'admin', 'ZotSight', 'fridge-db')

class ClientConnection:
    def __init__(self, clientSocket):
        self.client = clientSocket
        self.loggedIn = False
        self.username = ''
        self.cursor = db.cursor()

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
            db.commit()
            self.loggedIn = True
            self.username = username
            self.send("creation_succeeded")
        except:
            db.rollback()
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
            
                        

def NewThread(clientSocket):
    connection = ClientConnection(clientSocket)
    connection.mainloop()
    print("Connection closed")
    clientSocket.close()

def main():
    port = 1000
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(("localhost", port))
    serverSocket.listen(10)

    while True:
        print("Socket now listening...")
        clientSocket, addr = serverSocket.accept()
        print("Connected to: ", addr[0], ":", addr[1])
        start_new_thread(NewThread, (clientSocket,))

    serverSocket.close()

if __name__ == '__main__':
    main()
    
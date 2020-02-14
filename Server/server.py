import socket
from _thread import start_new_thread
import threading
import pymysql
import bcrypt
from Client_Server import Client_Server
from Fridge_Server import Fridge_Server
          
def NewThread(clientSocket, db):
    message = str(clientSocket.recv(1024).decode('ascii'))

    if message == 'f':
        connection = Fridge_Server(clientSocket, db, 'f')
        connection.mainloop()
    elif message == 'c':
        connection = Client_Server(clientSocket, db, 'c')
        connection.mainloop()

    print("Connection closed")
    clientSocket.close()

def main():
    port = 1050
    ip = 'ec2-13-52-78-168.us-west-1.compute.amazonaws.com'
    db = pymysql.connect('fridge-db.cq9smwtzhpgg.us-west-1.rds.amazonaws.com', 'admin', 'ZotSight', 'fridge-db')
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((ip, port))
    serverSocket.listen(10)

    while True:
        try:
            print("Socket now listening...")
            clientSocket, addr = serverSocket.accept()
            print("Connected to: ", addr[0], ":", addr[1])
            start_new_thread(NewThread, (clientSocket, db))
        except KeyboardInterrupt:
            break

    serverSocket.close()

if __name__ == '__main__':
    main()
    
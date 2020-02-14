import socket
from getpass import getpass
import serial
from time import sleep
from Location.locationDetector import Layout, LocationDetector
import cv2
import numpy as np
import os
import tqdm

def gstreamer_pipeline( capture_width=1280, capture_height=720,
                        display_width=1280, display_height=720,
                        framerate=60, flip_method=0 ):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=%d, height=%d, "
        "format=NV12, framerate=%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=%d, height=%d, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! " 
        "appsink max-buffers=1 drop=true sync=false"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def get_image( videoCap  ):
    image = None
    if not videoCap.isOpened():
        print("Camera not opened")
    else:
        goodRead, image = videoCap.read( )

    if not goodRead:
        print("Failed to read frame")
        
    return image

def get_rgb( videoCap ):
    image = get_image( videoCap )
    while type(image) != np.ndarray:
        print("Trying to get another image to make pgm")
        image = get_image( videoCap )
    rgbImg = cv2.cvtColor( image, cv2.COLOR_BGR2RGB )
    
    return rgbImg

def apply_Prewitt( img ):
    img_filtered = cv2.GaussianBlur( img, (3,3), 0 )
    xformX = np.array([[1,1,1],[0,0,0],[-1,-1,-1]])
    xformY = np.array([[-1,0,1],[-1,0,1],[-1,0,1]])
    imgPrewittX = cv2.filter2D( img_filtered, -1, xformX )
    imgPrewittY = cv2.filter2D( img_filtered, -1, xformY )
    return imgPrewittX + imgPrewittY

def get_pgm( videoCap ):
    '''captures a frame and saves it in a specified format at some spefied location
       format = { whatever_recogniziton_needs, pgm}
       return file path (or an object with the image in it? like Layout'''
    image = get_image( videoCap )
    while type(image) != np.ndarray:
        print("Trying to get another image to make pgm")
        image = get_image( videoCap )
    grayImg = cv2.cvtColor( image, cv2.COLOR_BGR2GRAY )
    edgeDetectedImg = apply_Prewitt( grayImg )
    
    return Layout( bitmap = edgeDetectedImg )


class Client:
    def __init__(self):
        self.host = 'ec2-13-52-78-168.us-west-1.compute.amazonaws.com'
        self.port = 1050
        self.loggedIn = False
        self.username = ''
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.videoCap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2), cv2.CAP_GSTREAMER)
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
            arg = input("Login (L) or Create Account (C)?\n>>> ").lower()
            if arg == "l":
                if self.login():
                    self.mainLoop()
            elif arg == 'c':
                if self.createAccount():
                    self.mainLoop()

    def sendImage(self):
        pic = get_pgm(self.videoCap)
        locator = LocationDetector(layout = pic)
        locator.saveLayout(saveFileName = './pic/pic.pgm')
        imgPath = './pic/pic.pgm'
        filesize = os.path.getsize(imgPath)
        self.send(str(filesize), True)
        progress = tqdm.tqdm(range(filesize), "Sending pgm", unit='B', unit_scale=True, unit_divisor=1024)

        with open(imgPath, 'rb') as f:
            for _ in progress:
                bytes_read = f.read(4096)
                if not bytes_read:
                    break
                self.server.sendall(bytes_read)
                progress.update(len(bytes_read))

    def mainLoop(self):
        arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout = 0.1)
        while True:
            data = arduino.readline()[:-2]
            if data == b"DoorClosed":
                print("Door Closed")
                self.sendImage()
                print("Image sent")              

if __name__ == '__main__':
    c = Client()
    if c.connect():
        c.start()
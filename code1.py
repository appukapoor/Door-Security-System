import face_recognition
import picamera
import numpy as np
import RPi.GPIO as GPIO
import csv
import time
from datetime import datetime
import cv2
import io
import os

known_face_encodings = []
names = []
camera = picamera.PiCamera()
face_locations = []
face_encodings = []
s1 = 15
s2 = 37
GPIO.setmode(GPIO.BOARD)
GPIO.setup(s1, GPIO.OUT)
GPIO.setup(s2, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
servo1 = GPIO.PWM(s1, 50)
servo2 = GPIO.PWM(s2, 50)
servo1.start(0)
servo2.start(0)
camera.resolution = (320, 240)
output = np.empty((240, 320, 3), dtype=np.uint8)

def load_face_encoding(name, file_name):
    image = face_recognition.load_image_file(file_name)
    face_encoding = face_recognition.face_encodings(image)[0]
    known_face_encodings.append(face_encoding)
    names.append(name)

def load_faces():
    with open("capture.csv") as file:
        print("Loading faces")
        readFile = csv.reader(file, delimiter=",")
        for each in readFile:
            print(each)
            load_face_encoding(each[0], "images/"+each[1])

def getImageList():
    with open("capture.csv") as file:
        readFile = csv.reader(file, delimiter=",")
        for each in readFile:
            print(each[1])
            lastImage = os.path.splitext(each[1])[0]
        return lastImage

def change_status(status):
    with open('status.csv', 'w') as writeFile:
        writer = csv.writer(writeFile)
        currentDT = datetime.now()
        writer.writerow((status, currentDT.strftime("%Y-%m-%d %H:%M:%S")))

def status():
    with open("status.csv") as file:
        readFile = csv.reader(file)
        for each in readFile:
            eachData = each
        print(eachData[0])
        return eachData[0]

def addImageDB(imageName):
    with open("capture.csv", "a") as writeFile:
        writer = csv.writer(writeFile)
        writer.writerow(("user", imageName))

def addUser(channel):
    stream = io.BytesIO()
    camera.capture(stream, format='jpeg')
    buff = np.fromstring(stream.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(buff, 1)
    face_cascade = cv2.CascadeClassifier('/home/pi/Desktop/fyp/haarcascade_frontalface_alt.xml')
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)
    print(len(faces))
    if len(faces) == 1:
        lastImage = getImageList()
        newImage = str(int(lastImage)+1)+".jpg"
        cv2.imwrite("images/"+newImage, image)
        addImageDB(newImage)
        GPIO.output(16,GPIO.HIGH)
        time.sleep(2)
        GPIO.output(16,GPIO.LOW)

def recognize(channel):
    last_status = status()
    output = np.empty((240, 320, 3), dtype=np.uint8)
    if last_status == "LOCK":
        load_faces()
        flag = "True"
        while flag == "True":
            print("Capturing image.")
            camera.capture(output, format="rgb")
            face_locations = face_recognition.face_locations(output)
            face_encodings = face_recognition.face_encodings(output, face_locations)
            for face_encoding in face_encodings:
                matches = face_recognition.face_distance(known_face_encodings, face_encoding)
                min_distance = min(matches)
                if min_distance < 0.6:
                    change_status("UNLOCK")
                    print("Opening the gates")
                    try:
                        servo1.start(0)
                        servo2.start(0)
                        GPIO.output(s1, True)
                        GPIO.output(s2, True)
                        servo2.ChangeDutyCycle(7.5)
                        time.sleep(2)
                        print("servo 1")
                        servo1.ChangeDutyCycle(7.5)
                        time.sleep(2)
                        print("servo 2")
                        GPIO.output(s1, False)
                        GPIO.output(s2, False)
                    except:
                        servo1.stop()
                        servo2.stop()
                    flag = "False"

def lockDoor(channel):
    last_status = status()
    if  last_status == "UNLOCK":
        print("Locking Now")
        try:
            servo1.start(0)
            servo2.start(0)
            GPIO.output(s1, True)
            GPIO.output(s2, True)
            servo2.ChangeDutyCycle(2.5)
            time.sleep(2)
            print("servo 1")
            servo1.ChangeDutyCycle(12.5)
            time.sleep(2)
            print("servo 2")
            GPIO.output(s1, False)
            GPIO.output(s2, False)
            change_status("LOCK")
        except:
            servo1.stop()
            servo2.stop()

GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(10,GPIO.RISING,callback=recognize)
GPIO.add_event_detect(12,GPIO.RISING,callback=addUser)
GPIO.add_event_detect(18,GPIO.RISING,callback=lockDoor)


message = input("")
GPIO.cleanup()

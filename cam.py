import cv2
from picamera import PiCamera
from time import sleep
import datetime

##global cam

def picam():
    date = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    camera = PiCamera()
    camera.rotation = 180
    
    camera.start_preview()
    sleep(2)
    camera.capture("/home/pi/Desktop/Nelson/images/{}.jpg".format(date))
    camera.stop_preview()

def webcam():
    test = 0
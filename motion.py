#!/usr/bin/env python3
import RPi.GPIO as gpio
from time import sleep
import os
import subprocess
import math
##import NDIR
from bme280 import readBME280All
from cam import picam, webcam

# stepper motor constants
DELAY       = 0.00005 # 5us, max 300khz
TOTAL_STEPS = 200     # steps to reach max speed
MICROSTEPPING = 16*200    # 1/16

# geometry constants
RADIUS1 = 34.75  # in mm
RADIUS2 = 12
DISP_PER_REV1 = 0.002*math.pi*RADIUS1   # displacement per revolution in m
DISP_PER_REV2 = 0.002*math.pi*RADIUS2

# telescopic constants
TELESCOPIC_LENGTH = 0.76

step_fb = 0
step_tele = 0
fb_pins = {"dir": 0, "step": 0, "en": 0, "limit": 0}
telescopic_pins = {
    "dir_l": 0,
    "step_l": 0,
    "en_l": 0,
    "dir_r": 0,
    "step_r": 0,
    "en_r": 0,
    "limit_left": 0,
    "limit_right": 0}
servo_pins = {"cam1": 0, "cam1_angle": 0}
limit_sw = 0

def limit(channel):
    global limit_sw
    limit_sw = channel
    sleep(1)

def pinSetup(fb, telescopic, servo):
    global fb_pins, telescopic_pins, servo_pins
    fb_pins["dir"] = fb["dir"]
    fb_pins["step"] = fb["step"]
    fb_pins["en"] = fb["en"]
    fb_pins["limit"] = fb["limit"]
    gpio.add_event_detect(fb_pins["limit"], gpio.FALLING, callback=limit)
    
    telescopic_pins["dir_l"] = telescopic["dir_l"]
    telescopic_pins["step_l"] = telescopic["step_l"]
    telescopic_pins["en_l"] = telescopic["en_l"]

    telescopic_pins["dir_r"] = telescopic["dir_r"]
    telescopic_pins["step_r"] = telescopic["step_r"]
    telescopic_pins["en_r"] = telescopic["en_r"]

    telescopic_pins["limit_left"] = telescopic["limit_left"]
    telescopic_pins["limit_right"] = telescopic["limit_right"]
    gpio.add_event_detect(telescopic_pins["limit_left"], gpio.FALLING, callback=limit)
    gpio.add_event_detect(telescopic_pins["limit_right"], gpio.FALLING, callback=limit)
    
    gpio.output(fb_pins["en"], False)
    gpio.output(telescopic_pins["en_l"], False)
    gpio.output(telescopic_pins["en_r"], False)

    servo_pins["cam1"] = servo["cam1"]
    servo_pins["cam1_angle"] = servo["cam1_angle"]
    
    gpio.output(fb_pins["dir"], True)
    gpio.output(fb_pins["en"], True)
    if gpio.input(fb_pins["limit"]):
        while limit_sw != fb_pins["limit"]:
            motor(fb_pins["step"], DELAY*10)
    gpio.output(fb_pins["en"], False)
    print("FB")
    
    gpio.output(telescopic_pins["dir_l"], True)
    gpio.output(telescopic_pins["en_l"], True)
    if gpio.input(telescopic_pins["limit_left"]):
        while limit_sw != telescopic_pins["limit_left"]:
            motor(telescopic_pins["step_l"], DELAY*5)
    gpio.output(telescopic_pins["en_l"], False)
    print("TL")
    
    gpio.output(telescopic_pins["dir_r"], True)
    gpio.output(telescopic_pins["en_r"], True)
    if gpio.input(telescopic_pins["limit_right"]):
        while limit_sw != telescopic_pins["limit_right"]:
            motor(telescopic_pins["step_r"], DELAY*5)
    gpio.output(telescopic_pins["en_r"], False)
    print("TR")
    
#    servo = gpio.PWM(servo_pins["cam1"], 50)
#    servo.start(2.5)
#    sleep(1)
#    servo.stop()

def motor(pulsePin, duration):
    gpio.output(pulsePin, True)
    sleep(duration)
    gpio.output(pulsePin, False)
    sleep(duration)
    return 1
    
def moveFrontBack(disp):
    global step_fb
    step_fb = 0
    acc = TOTAL_STEPS
    accelerate_signal = False
    gpio.output(fb_pins["en"], True)
    if disp < 0:
        print("backward")
        gpio.output(fb_pins["dir"], True)
    else:
        print("forward")
        gpio.output(fb_pins["dir"], False)
        
    total = abs(disp) / DISP_PER_REV1 * MICROSTEPPING
    maxCap = total-TOTAL_STEPS
    while step_fb <= total:
        if step_fb < TOTAL_STEPS:
            for repeat in range(10,0,-1):
                for iteration in range(20):
                    step_fb += motor(fb_pins["step"], DELAY*repeat)
        elif TOTAL_STEPS <= step_fb and step_fb < maxCap:
            step_fb += motor(fb_pins["step"], DELAY)
        else:
            for repeat in range(1,11,1):
                for iteration in range(20):
                    step_fb += motor(fb_pins["step"], DELAY*repeat)

#        if 0 < acc and acc <= TOTAL_STEPS and not accelerate_signal:   # accelerate
#            acc -= 20
#            for iteration in range(50):
#                step_fb += motor(fb_pins["step"], DELAY*acc)
#        elif TOTAL_STEPS * 5 > total-step_fb and accelerate_signal:     # decelerate
#            acc += 20
#            for iteration in range(50):
#                step_fb += motor(fb_pins["step"], DELAY*acc)
#        else:
#            accelerate_signal = True
#            step_fb += motor(fb_pins["step"], DELAY)
    gpio.output(fb_pins["en"], False)

def telescopicArm():
    global step_tele
    step_tele = 0
    servo1 = gpio.PWM(servo_pins["cam1"], 50)
    servo1.start(2.5)
    
    extension_sequence = [False, True]
    sequence = ["Extend", "Retract"]
    gpio.output(telescopic_pins["en_r"], True)
    gpio.output(telescopic_pins["en_l"], True)
    for i in range(2):
        step_tele = 0
        gpio.output(telescopic_pins["dir_r"], extension_sequence[i])
        gpio.output(telescopic_pins["dir_l"], extension_sequence[i])
        while step_tele <= TELESCOPIC_LENGTH / DISP_PER_REV2 * MICROSTEPPING:
            step_tele += motor(telescopic_pins["step_r"], DELAY)
            motor(telescopic_pins["step_l"], DELAY)
        print(sequence[i])
        if i == 0:
            os.system("killall motion")
            subprocess.call(["/home/pi/webcam/webcam.sh"])
            sleep(1)
#        if i == 0:
#            temperature,pressure,humidity = readBME280All()
#            file = open("/home/pi/Desktop/Nelson/sensor data.txt", "a")
#            file.write("Temp:{0}\nPressure:{1}\nHumidity:{2}\n".format(temperature, pressure, humidity))
#            file.close()
#            servo1.ChangeDutyCycle(servo_pins["cam1_angle"]/18 + 2.5)
#            sleep(1)
##            print("Temperature:{0}\nPressure:{1}\nHumidity:{2}".format(temperature, pressure, humidity))
#            picam()
#            servo1.ChangeDutyCycle(2.5)
#            sleep(1)
#            servo1.stop()
#            del servo1
    gpio.output(telescopic_pins["en_r"], False)
    gpio.output(telescopic_pins["en_l"], False)
    
def servoManual(angle):
    servo = gpio.PWM(servo_pins["cam1"], 50)
    servo.start(0)
    d = angle/18 + 2.5
    servo.ChangeDutyCycle(d)
    sleep(1)
    servo.ChangeDutyCycle(2.5)
    sleep(1)
    servo.stop()
    del servo

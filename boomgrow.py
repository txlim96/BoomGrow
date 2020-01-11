#!/usr/bin/env python3
from motion import *
import RPi.GPIO as gpio
import time
import sys

# pinout defintions
M_FB_DIR    = 13 #13
M_TL_DIR    = 15 #11
M_TR_DIR    = 11 #15

M_FB_PUL    = 21 #19
M_TL_PUL    = 23 #23
M_TR_PUL    = 19 #21

M_FB_EN     = 10 #10
M_TL_EN     = 12 #8
M_TR_EN     = 8  #12

SERVO_CAM1  = 16
SW_FB     = 24
SW_TELE_L = 22
SW_TELE_R = 26

FB_DEF = {
    "dir": M_FB_DIR,
    "step": M_FB_PUL,
    "en": M_FB_EN,
    "limit": SW_FB
    }
SERVO_DEF = {
    "cam1": SERVO_CAM1,
    "cam1_angle": 90
    }
TELESCOPE_DEF = {
    "dir_l": M_TL_DIR,
    "step_l": M_TL_PUL,
    "en_l": M_TL_EN,

    "dir_r": M_TR_DIR,
    "step_r": M_TR_PUL,
    "en_r": M_TR_EN,

    "limit_left": SW_TELE_L,
    "limit_right": SW_TELE_R
    }

def main():
    gpio.setmode(gpio.BOARD)
    gpio.setup(M_FB_DIR, gpio.OUT)
    gpio.setup(M_FB_PUL, gpio.OUT)
    gpio.setup(M_FB_EN, gpio.OUT)
    gpio.setup(M_TL_DIR, gpio.OUT)
    gpio.setup(M_TL_PUL, gpio.OUT)
    gpio.setup(M_TL_EN, gpio.OUT)
    gpio.setup(M_TR_DIR, gpio.OUT)
    gpio.setup(M_TR_PUL, gpio.OUT)
    gpio.setup(M_TR_EN, gpio.OUT)
    gpio.setup(SERVO_CAM1, gpio.OUT)
    gpio.setup(SW_FB, gpio.IN, pull_up_down=gpio.PUD_UP)
    gpio.setup(SW_TELE_L, gpio.IN, pull_up_down=gpio.PUD_UP)
    gpio.setup(SW_TELE_R, gpio.IN, pull_up_down=gpio.PUD_UP)

    pinSetup(FB_DEF, TELESCOPE_DEF, SERVO_DEF)

try:
    if __name__ == "__main__":
        main()
        mode = sys.argv[1]
        if mode.lower() == "auto":
            travel_distance = input("Travelling distance: ")
            moveFrontBack(float(travel_distance))
            time.sleep(1)
            telescopicArm()
            time.sleep(1)
            moveFrontBack(-float(travel_distance))
            
        elif mode.lower() == "manual":
            if sys.argv[2].lower() == "fb":
                while True:
                    travel_distance = input("Travelling distance: ")
                    moveFrontBack(float(travel_distance))
            elif sys.argv[2].lower() == "arm":
                telescopicArm()
            elif sys.argv[2].lower() == "servo":
                angle = input("Enter angle: ")
                servoManual(angle)
            
except KeyboardInterrupt:
    print("Disabled")
    gpio.output(M_FB_EN, False)
except ValueError:
    print("Please key in a valid number!!")
finally:
    print("Cleanup")
    gpio.cleanup()

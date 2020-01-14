import RPi.GPIO as gpio
from time import sleep
from motion import *
from retrieve_reading import *
import VL53L0X
import sys
import os

# version
RELEASE = True

# pinout definitions
M_TL_DIR    = 8
M_TL_PUL    = 10
M_TL_EN     = 12

M_FB_DIR    = 11
M_FB_PUL    = 13
M_FB_EN     = 15

M_TR_DIR    = 19
M_TR_PUL    = 21
M_TR_EN     = 23

SW_FB       = 24
SW_TL       = 26
SW_TR       = 22

PIN = {
    "FB": {
        "A": {
            "DIR":  M_FB_DIR,
            "PUL":  M_FB_PUL,
            "EN":   M_FB_EN,
            "LIM":  SW_FB
            }
        },
    "TELESCOPE": {
        "L": {
            "DIR":  M_TL_DIR,
            "PUL":  M_TL_PUL,
            "EN":   M_TL_EN,
            "LIM":  SW_TL
            },
        "R": {
            "DIR":  M_TR_DIR,
            "PUL":  M_TR_PUL,
            "EN":   M_TR_EN,
            "LIM":  SW_TR
            }
        }
    }

def main():
    gpio.setmode(gpio.BOARD)
    for mode in PIN:
        for direction in PIN[mode]:
            for pinout in PIN[mode][direction]:
                if pinout == "LIM":
                    gpio.setup(PIN[mode][direction][pinout], gpio.IN, pull_up_down=gpio.PUD_UP)
                else:
                    gpio.setup(PIN[mode][direction][pinout], gpio.OUT)

try:
    if __name__ == "__main__":
#        os.killall("motioneye")
#        os.killall("motion")
        main()
        pinSetup(PIN)
        if RELEASE:
            sensorObject = retrieve_reading(VL53L0X.VL53L0X())
            moveFB(1.0)
            sleep(1)
            moveTele(sensorObject)
            sleep(1)
            moveFB(-1.0)
            sensorObject.close()
        else:
            mode = sys.argv[1]
            if mode.upper() == "AUTO":
                sensorObject = retrieve_reading(VL53L0X.VL53L0X())
                travel_dist = float(raw_input("Travelling distance: "))
                moveFB(travel_dist)
                sleep(1)
                moveTele(sensorObject)
                sleep(1)
                moveFB(-travel_dist)
                sensorObject.close()
            elif mode.upper() == "HOME":
                home()
            elif mode.upper() == "MANUAL":
                if sys.argv[2].upper() == "FB":
                    while True:
                        travel_dist = float(raw_input("Travelling distance: "))
                        moveFB(travel_dist)
                elif sys.argv[2].upper() == "ARM":
                    moveTele()

except KeyboardInterrupt:
    print("Disabled")
except ValueError:
    print("Please key in a valid number!")
finally:
    gpio.cleanup()

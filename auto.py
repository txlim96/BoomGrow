import RPi.GPIO as gpio
from time import sleep
from motion import *
from retrieve_reading import *
import VL53L0X
import sys
import paho.mqtt.client as mqtt

# MQTT constants
MQTT_HOST = "178.128.97.253"
MQTT_PORT = 1883
MQTT_TIMEOUT = 60
MQTT_TOPIC_SUBSCRIBE = "/bg/fc/robotarm/cmds"

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

trigger = False
currPos = 0

def main():
    gpio.setmode(gpio.BOARD)
    for mode in PIN:
        for direction in PIN[mode]:
            for pinout in PIN[mode][direction]:
                if pinout == "LIM":
                    gpio.setup(PIN[mode][direction][pinout], gpio.IN, pull_up_down=gpio.PUD_UP)
                else:
                    gpio.setup(PIN[mode][direction][pinout], gpio.OUT)

def auto(dist):
    global currPos
    main()
    pinSetup(PIN)
#    sensorObject = retrieve_reading(VL53L0X.VL53L0X())
    moveFB(currPos,dist)
    sleep(1)
    currPos = moveTele(dist)
    sleep(1)
    gpio.cleanup()

def home():
    main()
    pinSetup(PIN)
    calibrate_sequence = [PIN["TELESCOPE"]["L"], PIN["TELESCOPE"]["R"], PIN["FB"]["A"]]

    for sequence in calibate_sequence:
        calibrate(sequence)
    gpio.cleanup()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_TOPIC_SUBSCRIBE)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    print(payload["position"])
    if payload["name"] == "arm1":
        if payload["position"] == 0:
            home()
        elif payload["position"] == 1:
            d = 3*2*payload["position"]+149.13*(2*payload["position"]-1)+149.13/2
            auto(1.38)
        elif payload["position"] == 2:
            auto(1.68)

try:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_forever()
finally:
    gpio.cleanup()
    client.loop_stop()

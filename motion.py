import RPi.GPIO as gpio
from time import sleep
from math import pi, ceil, floor
import paho.mqtt.client as mqtt
from picamera import PiCamera
import json
#from retrieve_reading import readData

# mqtt constants
MQTT_HOST = "178.128.97.253"
MQTT_PORT = 1883
MQTT_TIMEOUT = 60
MQTT_TOPIC_SUBSCRIBE = "/bg/fc/robotarm/cmds"
MQTT_TOPIC_PUBLISH = "/bg/fc/robotarm/status"

# stepper motor constants
DELAY         = 0.00005
TOTAL_STEPS   = 200
MICROSTEPPING = 16*200

# geometry constants
RADIUS_FB   = 34.75
RADIUS_TELE = 6
DPR_FB      = 0.002*pi*RADIUS_FB
DPR_TELE    = 0.002*pi*RADIUS_TELE

# trigger
TRIGGER_LENGTH = 0.25
TRIGGER_STEP = floor(TRIGGER_LENGTH/DPR_TELE*MICROSTEPPING)

# telescopic constants
TELE_LENGTH = 0.34
CAM_POSITION = [2971,8913,14854,20796,26738]

limit_sw  = 0
step_fb   = 0
step_tele = 0
PIN = {
    "FB": {
        "A": {
            "DIR":  0,
            "PUL":  0,
            "EN":   0,
            "LIM":  0
            }
        },
    "TELESCOPE": {
        "L": {
            "DIR":  0,
            "PUL":  0,
            "EN":   0,
            "LIM":  0
            },
        "R": {
            "DIR":  0,
            "PUL":  0,
            "EN":   0,
            "LIM":  0
            }
        }
    }

def limit(channel):
    global limit_sw
    limit_sw = channel

def motor(pulse1, pulse2, duration):
    if pulse2 == 0:
        gpio.output(pulse1, True)
        sleep(duration)
        gpio.output(pulse1, False)
        sleep(duration)
    else:
        gpio.output(pulse1, True)
        gpio.output(pulse2, True)
        sleep(duration)
        gpio.output(pulse1, False)
        gpio.output(pulse2, False)
        sleep(duration)
    return 1

def calibrate(pins):
    gpio.output(pins["DIR"], True)
    gpio.output(pins["EN"], True)
    if gpio.input(pins["LIM"]):
        while limit_sw != pins["LIM"]:
            motor(pins["PUL"], 0, DELAY*5)
    gpio.output(pins["EN"], False)

def accelerate(pins, mode, steps_to_max=200, acc_steps=10): # steps_to_max must be a integer product of acc_steps
    if mode == "a":
        for repeat in range(acc_steps,0,-1):
            for iteration in range(steps_to_max/acc_steps):
                motor(pins, 0, DELAY*repeat)
        return steps_to_max
    elif mode == "d":
        for repeat in range(1,acc_steps,1):
            for iteration in range(steps_to_max/acc_steps):
                motor(pins, 0, DELAY*repeat)
        return steps_to_max

def pinSetup(pins):
    global PIN
    for mode in pins:
        for direction in pins[mode]:
            for pinout in pins[mode][direction]:
                PIN[mode][direction][pinout] = pins[mode][direction][pinout]

    gpio.add_event_detect(PIN["FB"]["A"]["LIM"], gpio.FALLING, callback=limit)
    gpio.add_event_detect(PIN["TELESCOPE"]["L"]["LIM"], gpio.FALLING, callback=limit)
    gpio.add_event_detect(PIN["TELESCOPE"]["R"]["LIM"], gpio.FALLING, callback=limit)

    gpio.output(PIN["FB"]["A"]["EN"], False)
    gpio.output(PIN["TELESCOPE"]["L"]["EN"], False)
    gpio.output(PIN["TELESCOPE"]["R"]["EN"], False)

#    calibrate_sequence = [PIN["TELESCOPE"]["L"], PIN["TELESCOPE"]["R"], PIN["FB"]["A"]]

#    for sequence in calibrate_sequence:
#        calibrate(sequence)

def moveFB(currentPosition, disp=1.0):
    global step_fb
    step_fb = 0
    total = abs(disp-currentPosition) / DPR_FB * MICROSTEPPING
#    total = abs(disp) / DPR_FB * MICROSTEPPING
    ul = total-TOTAL_STEPS

#    print("{0} {1}".format(currentPosition, disp))
    if currentPosition < disp:
        gpio.output(PIN["FB"]["A"]["DIR"], disp<0)
    else:
        gpio.output(PIN["FB"]["A"]["DIR"], disp>0)

    gpio.output(PIN["FB"]["A"]["EN"], True)
    while step_fb < total:
        if step_fb < TOTAL_STEPS:
            step_fb += accelerate(PIN["FB"]["A"]["PUL"], "a")
        elif TOTAL_STEPS <= step_fb and step_fb < ul:
            step_fb += motor(PIN["FB"]["A"]["PUL"], 0, DELAY)
        else:
            step_fb += accelerate(PIN["FB"]["A"]["PUL"], "d")

    gpio.output(PIN["FB"]["A"]["EN"], False)

def moveTele(dist, sensor):
    global step_tele
    step_tele = 0
    extension_sequence = [False, True]
#    camera = PiCamera()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, MQTT_TIMEOUT)
    client.loop_start()

    gpio.output(PIN["TELESCOPE"]["L"]["EN"], True)
    gpio.output(PIN["TELESCOPE"]["R"]["EN"], True)

    pos = 0
    for i in range(2):
        step_tele = 0
        gpio.output(PIN["TELESCOPE"]["L"]["DIR"], extension_sequence[i])
        gpio.output(PIN["TELESCOPE"]["R"]["DIR"], extension_sequence[i])
        while step_tele <= TELE_LENGTH / DPR_TELE * MICROSTEPPING:
            step_tele += motor(PIN["TELESCOPE"]["L"]["PUL"],PIN["TELESCOPE"]["R"]["PUL"],DELAY*5)
            if (pos < 5 and step_tele == CAM_POSITION[pos] and i == 0):
#                camera.capture('/var/www/html/images/%s.jpg'%pos)
                pos += 1
                sleep(2)
            if (step_tele % 212 == 0 and i == 0):
#                height = sensor.readData()
                height = 5
                x = dist
                z = ceil(step_tele*DPR_TELE/MICROSTEPPING*2000)
                msg = json.dumps({"name":"arm1", "height":height, "x":x, "z":z})
                client.publish(MQTT_TOPIC_PUBLISH, msg)

    gpio.output(PIN["TELESCOPE"]["L"]["EN"], False)
    gpio.output(PIN["TELESCOPE"]["R"]["EN"], False)
    client.loop_stop()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_TOPIC_SUBSCRIBE)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    print("Height: {0}".format(payload["height"]))

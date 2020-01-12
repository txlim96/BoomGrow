import RPi.GPIO as gpio
from time import sleep
from math import pi

# stepper motor constants
DELAY         = 0.00005
TOTAL_STEPS   = 200
MICROSTEPPING = 16*200

# geometry constants
RADIUS_FB   = 34.75
RADIUS_TELE = 12
DPR_FB      = 0.002*pi*RADIUS_FB
DPR_TELE    = 0.002*pi*RADIUS_TELE

# telescopic constants
TELE_LENGTH = 0.76

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

def motor(pulse, duration):
    gpio.output(pulse, True)
    sleep(duration)
    gpio.output(pulse, False)
    sleep(duration)
    return 1

def calibrate(pins):
    gpio.output(pins["DIR"], True)
    gpio.output(pins["EN"], True)
    if gpio.input(pins["LIM"]):
        while limit_sw != pins["LIM"]:
            motor(pins["PUL"], DELAY*5)
    gpio.output(pins["EN"], False)

def accelerate(pins, mode, steps_to_max=200, acc_steps=10): # steps_to_max must be a integer product of acc_steps
    if mode == "a":
        for repeat in range(acc_steps,0,-1):
            for iteration in range(steps_to_max/acc_steps):
                motor(pins, DELAY*repeat)
        return steps_to_max
    elif mode == "d":
        for repeat in range(1,acc_steps,1):
            for iteration in range(steps_to_max/acc_steps):
                motor(pins, DELAY*repeat)
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
#    
#    for sequence in calibrate_sequence:
#        calibrate(sequence)

def moveFB(disp=1.0):
    global step_fb
    step_fb = 0
    total = abs(disp) / DPR_FB * MICROSTEPPING
    ul = total-TOTAL_STEPS
    
    gpio.output(PIN["FB"]["A"]["DIR"], disp<0)
    gpio.output(PIN["FB"]["A"]["EN"], True)
    while step_fb < total:
        if step_fb < TOTAL_STEPS:
            step_fb += accelerate(PIN["FB"]["A"]["PUL"], "a")
        elif TOTAL_STEPS <= step_fb and step_fb < ul:
            step_fb += motor(PIN["FB"]["A"]["PUL"], DELAY)
        else:
            step_fb += accelerate(PIN["FB"]["A"]["PUL"], "d")
            
    gpio.output(PIN["FB"]["A"]["EN"], False)
    
def moveTele():
    global step_tele
    step_tele = 0
    extension_sequence = [False, True]
    
    gpio.output(PIN["TELESCOPE"]["L"]["EN"], True)
    gpio.output(PIN["TELESCOPE"]["R"]["EN"], True)
    
    for i in range(2):
        step_tele = 0
        gpio.output(PIN["TELESCOPE"]["L"]["DIR"], extension_sequence[i])
        gpio.output(PIN["TELESCOPE"]["R"]["DIR"], extension_sequence[i])
        while step_tele <= TELE_LENGTH / DPR_TELE * MICROSTEPPING:
            step_tele += motor(PIN["TELESCOPE"]["L"]["PUL"], DELAY)
            motor(PIN["TELESCOPE"]["R"]["PUL"], DELAY)
    
    gpio.output(PIN["TELESCOPE"]["L"]["EN"], False)
    gpio.output(PIN["TELESCOPE"]["R"]["EN"], False)
from time import sleep
import VL53L0X

class retrieve_reading():
    def __init__(self, tof):
        self.tof = tof
        self.tof.open()
        self.tof.start_ranging(VL53L0X.Vl53l0xAccuracyMode.HIGH_SPEED)
        self.timing = self.tof.get_timing()
        if (self.timing < 20000):
            self.timing = 20000

    def readData(self):
        dist = 8191
        dist = self.tof.get_distance()
#        while dist > 5000:
#            dist = self.tof.get_distance()
#         print(dist)
        sleep(self.timing/1000000000.00)
        return dist

    def close(self):
        self.tof.stop_ranging()
        self.tof.close()

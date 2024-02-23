# *** Custom optical power meter module used in other scripts ***
# ***               Designed for Thorlabs PM400               ***
# ***                Made by: Giedrius Puidokas               ***
# ***              Contact: giedriusp10@gmail.com             ***
# This uses ThorLabs Power Meter (TLPM) library "ThorlabsOPMSetup" from their site.
# It uses TLPM_64.dll from this library and a wrapper TLPM.py.
# If needed, modify “TLPM.py” to find the .dll file location
# Look up "TL_OPM_Manual" section called “Write Your Own Application” for more details.
from ctypes import cdll, c_uint32, byref, create_string_buffer, c_bool, c_double
from TLPM import TLPM
import time


class PowerMeter:

    def __init__(self):
        self.tl_pm = None
        self.resourceName = None

    def connect(self):
        self.tl_pm = TLPM()
        deviceCount = c_uint32()
        self.tl_pm.findRsrc(byref(deviceCount))

        if deviceCount.value == 0:
            raise Exception("No Devices found")

        self.resourceName = create_string_buffer(1024)

        # Connecting to the first device
        self.tl_pm.getRsrcName(0, self.resourceName)

        self.tl_pm.close()

        self.tl_pm = TLPM()
        self.tl_pm.open(self.resourceName, c_bool(True), c_bool(True))

        message = create_string_buffer(1024)
        self.tl_pm.getCalibrationMsg(message)
        print("Connected to optical power meter")
        # Print the calibration message if needed
        # print(message.value.decode())

    def disconnect(self):
        self.tl_pm.close()
        print("OPM disconnected")

    def measure(self, number_of_points=5, delay=0.5, pre_delay=True):
        if pre_delay:
            time.sleep(2)  # Allow device to stabilize before measurements

        power_measurements = []
        for count in range(number_of_points):
            power = c_double()
            self.tl_pm.measPower(byref(power))
            power_measurements.append(power.value)
            time.sleep(delay)

        return power_measurements

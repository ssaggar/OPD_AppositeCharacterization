import pyvisa
import time

# Very basic script designed for one purpose only, but can be built on to do more stuff


class FunctionGenerator:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.FG = None

    def connect(self):
        FG_address = "USB::0x0699::0x034C::C020666::INSTR"
        self.FG = self.rm.open_resource(FG_address)
        time.sleep(0.1)
        # Send the *IDN? command to the SMU
        response = self.FG.query('*IDN?')
        print("Function generator identification:", response)
        # Set the funtion on Channel 1
        self.FG.write('SOURce1:FUNCtion:SHAPe DC')
        # Set the high voltage level to 0V
        self.FG.write('SOURce1:VOLTage:LEVel:IMMediate:HIGH 0')
        # Set the low voltage level to -5V
        self.FG.write('SOURce1:VOLTage:LEVel:IMMediate:LOW -5')

    def disconnect(self):
        if self.FG:
            self.FG.close()
            self.FG = None
            print("Disconnected from Function generator")
        else:
            print("No connection to Function generator")

    def laser_output(self, state=None):
        if state.lower() in ["off", "on"]:  # state.lower() converts input to lowercase
            if state.lower() == "on":
                self.FG.write('OUTPut1 OFF')
            elif state.lower() == "off":
                self.FG.write('OUTPut1 ON')
        else:
            print("Invalid input for laser")


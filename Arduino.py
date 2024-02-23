import serial
import time


class Arduino:

    def __init__(self, port='COM6', baudrate=9600):
        self.ser = serial.Serial(port, baudrate)
        time.sleep(1)  # give the connection a second to settle
        print("Connecting to Arduino")

    def connect(self, port='COM6', baudrate=9600):
        pass

    def laser_output(self, state=None):
        if state.lower() in ["off", "on"]:  # state.lower() converts input to lowercase
            if state.lower() == "on":
                self.ser.write(b'L')
            elif state.lower() == "off":
                self.ser.write(b'H')
        else:
            print("Invalid input for laser")

    def disconnect(self):
        self.ser.close()

# # Upload this script to arduino
# void setup() {
#   // Start the serial communication
#   pinMode(A1, OUTPUT);
#   Serial.begin(9600);
# }
#
# void loop() {
#   // Check if data is available to read
#   if (Serial.available() > 0) {
#     // Read the incoming byte
#     char incomingByte = Serial.read();
#
#     // Check the value of the incoming byte
#     if (incomingByte == 'H') {
#       digitalWrite(A1, HIGH);
#     } else if (incomingByte == 'L') {
#       digitalWrite(A1, LOW);
#     }
#   }
# }
from FlipMirror import FlipMirror
from PowerMeter import PowerMeter
from SMU import SMUDevice
from Wheels import Filters
from Arduino import Arduino
import numpy as np
import matplotlib.pyplot as plt
import time
import tkinter as tk
from tkinter import filedialog
import csv
import os

# *************************************************
# ************ Automated IV script ****************
# *************************************************
start_time = time.time()  # This is just to see how long it takes, can be deleted
device_name = 'SiPD_FD11A_NoOD_Green_1uW_v1'  # replace with your name
# Determines the speed/accuracy of measurement, since it's fast anyway, I recommend LONG
measurement_speed = 1 # Possibilities: SHOR, MED, LONG, *number*
save_plots = True  # If you want plots to be saved as .png files
show_plots = [True, 5]  # If you want plots to be shown after each measurement. Second number is show duration


# Selecting a folder to save the results
root = tk.Tk()
root.withdraw()
folder_path = filedialog.askdirectory()
print("Selected folder path to save results to:", folder_path)
if not folder_path:
    print('File selection cancelled.')
    quit()


# For finding the correct prefix for optical power. For file naming purposes.
# Beware, at low intensities (<~1nW) device may severely overestimate power
def format_power(power_w):
    prefixes = ['p', 'n', 'u', 'm', '', 'k']
    # The exponent -12 is to convert W to pW (picoWatts) for initial calculation
    power_in_pw = power_w * 1e12
    if power_in_pw != 0:
        exp = int(np.floor(np.log10(np.abs(power_in_pw)) / 3))
    else:
        exp = 0
    power = power_in_pw / (10 ** (3 * exp))
    prefix = prefixes[exp]
    return "{:.3g}{}W".format(power, prefix)


# Device initialization
WH = Filters()      # You can change the names to whatever you like. Use refractor
PM = PowerMeter()
FM = FlipMirror()
SMU = SMUDevice()
INO = Arduino()
FM.connect()
PM.connect()
SMU.connect()
INO.laser_output("off")
# WH.calibrate()  # Calibrate function is a bit problematic, check Wheels.py

# ******************Measurements***********************************
# The structure of the script is pretty dumb, because it measures two points at dark and two under illumination
# May be more useful to implement a for loop and a easier selection of positions
# Move to 7-7 (dark)
# WH.move(150)
SMU.trigger_settings(mtype="AINT")
# The measured optical power will be overestimated and meaningless, but is basically there to ceck if it is really dark
FM.move("on")   # 'on' means flip mirror in path of beam
pinc = PM.measure(number_of_points=2)    # Kind of arbitrary. Default is 5
print("Pinc= ", pinc)
pinc = np.mean(pinc)
print("Pavg= ", pinc)
FM.move("off")

# Dark+
 SMU.vs_function(ftype="SINGle", vstart=0, vend=1, points=101, speed=measurement_speed)
 time.sleep(0.2)
 SMU.set_current_range("AUTO")
 time.sleep(0.2)
 SMU.initiate("ALL")     # ACQuire = measurement, TRANsient = source, ALL = both. For IV we need both
 source = SMU.get_source()   # This just gets the measured data from Keysight
 current = SMU.get_current()

 # Create the plot
 plt.figure(figsize=(10, 6))
 plt.grid(True, which="both")    # "both" probably redundant, too lazy to check
 plt.semilogy(source, np.abs(current), 'b-')  # abs(current) to make sure its plottable in log
 # Add title and labels
 plt.title(f'{device_name} Dark 0 to +')
 plt.xlabel('Source')
 plt.ylabel('Current')
 if save_plots:
     plot_path = os.path.join(folder_path, f"IV {device_name} {format_power(pinc)} +.png")
     plt.savefig(plot_path)
 if show_plots[0]:
     plt.show(block=False)
     plt.pause(show_plots[1])
     plt.close()

 # Using convention: IV D*P* ***iW +.csv, change to whatever you like
 file_name = f"IV {device_name} {format_power(pinc)} +.csv"
 file_path = os.path.join(folder_path, file_name)
 # Write data to the CSV file
 with open(file_path, 'w', newline='') as file:
     writer = csv.writer(file, delimiter='\t')
     writer.writerow(["Source", "Current"])  # write header
     for s, c in zip(source, current):
         writer.writerow([s, c])  # write data

# **********************************************************************
 # Dark-
 # Essentially the same as before
 FM.move("on")   # 'on' means flip mirror in path of beam
 pinc = PM.measure(number_of_points=5)    # Kind of arbitrary. Default is 5
 print("Pinc= ", pinc)
 pinc = np.mean(pinc)
 print("Pavg= ", pinc)
 FM.move("off")
 SMU.vs_function(ftype="SINGle", vstart=0, vend=-0.7, points=71, speed=measurement_speed)
 SMU.initiate("ALL")
 source = SMU.get_source()
 current = SMU.get_current()
 # Create the plot
 plt.figure(figsize=(10, 6))
 plt.grid(True, which="both")
 plt.semilogy(source, np.abs(current), 'b-')  # Plot source vs. log(current)
 # Add title and labels
 plt.title(f'{device_name} Dark 0 to -')
 plt.xlabel('Source')
 plt.ylabel('Current')
 if save_plots:
     plot_path = os.path.join(folder_path, f"IV {device_name} {format_power(pinc)} -.png")
     plt.savefig(plot_path)
 if show_plots[0]:
     plt.show(block=False)
     plt.pause(show_plots[1])
     plt.close()

 file_name = f"IV {device_name} {format_power(pinc)} -.csv"
 file_path = os.path.join(folder_path, file_name)
 # Write data to the CSV file
 with open(file_path, 'w', newline='') as file:
     writer = csv.writer(file, delimiter='\t')
     writer.writerow(["Source", "Current"])  # write header
     for s, c in zip(source, current):
         writer.writerow([s, c])  # write data

# ******************************************************************************
INO.laser_output("on")
# Again, same procedure, different wheel position. Talk about ergonomics
# For now I just copy-pasted, at some point (if more intensity points are requered) For loop would be better
# Move to 5-1
# WH.move(-87)
# WH.move(0)
FM.move("on")
pinc = PM.measure(number_of_points=5)
print("Pinc= ", pinc)
pinc = np.mean(pinc)
print("Pavg= ", pinc)
FM.move("off")
SMU.vs_function(ftype="DOUBle", vstart=1, vend=-0.7, points=201, speed=measurement_speed)
SMU.initiate("ALL")
source = SMU.get_source()
current = SMU.get_current()
# At this point I'm wondering why not just write a function for plotting.
plt.figure(figsize=(10, 6))
plt.grid(True, which="both")
plt.semilogy(source, np.abs(current), 'b-')  # Plot source vs. log(current)
plt.title(f'{device_name} {format_power(pinc)}')
plt.xlabel('Source')
plt.ylabel('Current')
if save_plots:
    plot_path = os.path.join(folder_path, f"IV {device_name} {format_power(pinc)}.png")
    plt.savefig(plot_path)
if show_plots[0]:
    plt.show(block=False)
    plt.pause(show_plots[1])
    plt.close()

file_name = f"IV {device_name} {format_power(pinc)}.csv"
file_path = os.path.join(folder_path, file_name)
# Write data to the CSV file
with open(file_path, 'w', newline='') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(["Source", "Current"])  # write header
    for s, c in zip(source, current):
        writer.writerow([s, c])  # write data


# ********************Disconnect************************
INO.laser_output("off")
SMU.vs_function(ftype="OFF")
PM.disconnect()
FM.disconnect()
SMU.disconnect()
WH.disconnect()
INO.disconnect()

duration = time.time() - start_time
print("The script took ", duration, " seconds to run.")

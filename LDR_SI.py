# *** Low intensity photocurrent measurements ***
# ***       Made by: Giedrius Puidokas        ***
# ***     Contact: giedriusp10@gmail.com      ***
from FlipMirror import FlipMirror
from PowerMeter import PowerMeter
from SMU import SMUDevice
from Wheels import Filters
from Arduino import Arduino
import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
import math
import time
import os
import csv
import threading

##### ENTER DATA IN THIS SECTION #####

# This script measures currents in dark and illuminated conditions for each filter position (recommended highest
# laser intensity in the order of 10 nW).
start_time = time.time()  	# This is just to see how long it takes, can be deleted
wavelength = 'Green_532nm'  	# Possibilities: Green_532nm Blue_407nm Red_639nm
device_name = 'SiPD'  # replace with your name
# To save time, filter positions are predefined. 6, 8-8, 5, 4, 3, 2, 1 are necessary for proper movement of filters.
# For speed, some of the positions may be deleted.
filter_positons = ["6", "6-8", "6-7", "6-6", "6-5", "6-4", "6-3", "6-2", "6-1",
                   "8-8", "8-7", "8-6", "8-5", "8-4", "8-3", "8-2", "8-1",
                   "5", "5-8", "5-7", "5-6", "5-5", "5-4", "5-3", "5-2", "5-1",
                   "4", "4-8", "4-7", "4-6", "4-5", "4-4", "4-3", "4-2", "4-1",
                   "3", "3-8", "3-7", "3-6", "3-5", "3-4", "3-3", "3-2", "3-1",
                   "2", "2-8", "2-7", "2-6", "2-5", "2-4", "2-3", "2-2", "2-1",
                   "1", "1-8", "1-7", "1-6", "1-5", "1-4", "1-3", "1-2", "1-1"]

# Measurement speed determines the aperture time of each measurement point
measurement_speed = 3  		# Possibilities: SHOR, MED, LONG, NPLC. NPLC is the number of power line cycles (1PLC=20ms)
points_to_measure = 32  	# This number is for actual measurement under illumination. The actual N value.
voltage = 0.5
measurement_period = 0.1  	# Sampling Time between points in seconds.
save_plots = True  		# If you want plots to be saved as .png files
show_plots = [True, 10]  	# If you want plots to be shown after each measurement. Second number is show duration

# For cutting out measurement results
cut_start_time_dark = 9  	# Cut out duration from start of dark current in seconds
cut_end_time_dark = 0.2 	# Cut out duration before the laser turns on in seconds
cut_start_time_illum = 9  	# Cut out duration after the laser turns on in seconds.
cut_end_time_illum = 0.2  	# Keep it very small, atleast 1 sampling-time.
number_of_measurements = 1  	# The number of times a measurement is repeated

######################################


#Formulation to calculate total points to be measured for each case of filter-combination
cut_start_pts_dark = ((cut_start_time_dark)/(measurement_period))+1
cut_end_pts_dark = ((cut_end_time_dark)/(measurement_period))+1
cut_start_pts_illum = ((cut_start_time_illum)/(measurement_period))+1
cut_end_pts_illum = ((cut_end_time_illum)/(measurement_period))+1
total_points = cut_start_pts_dark + points_to_measure + cut_end_pts_dark + cut_start_pts_illum + points_to_measure + cut_end_pts_illum # Dont change this formula. This number is for dark AND light, so for N points, N/2 of them will be in dark.

# Importing calibration stuff (If trying to understand the code, check out the file)
filter_pos = []
move_pos = []
calibration = []
file_path = "Wheel_Calibration.txt"
with open(file_path, 'r') as file:
    next(file)  # Skip the header line
    for line in file:
        columns = line.strip().split()  # Split the line into columns
        if len(columns) >= 3:  # Check if the line has enough columns
            filter_pos.append(columns[0])
            move_pos.append(int(columns[1]))
            if wavelength.lower() == 'green_532nm':
                calibration.append(float(columns[2]))
            elif wavelength.lower() == 'blue_407nm':
                calibration.append(float(columns[3]))
            elif wavelength.lower() == 'red_639nm':
                calibration.append(float(columns[4]))
            else:
                print("Problem with acquiring wheel calibration data")
        else:
            print("Problem with number of columns in calibration file (check whitespace rows)")
# ********************************************************************************

# Selecting a folder to save the results
root = tk.Tk()
root.withdraw()
folder_path = filedialog.askdirectory()
print("Selected folder path to save results to:", folder_path)
if not folder_path:
    print('File selection cancelled.')
    quit()
# Create folder for results if it doesn't already exist
if not os.path.exists(os.path.join(folder_path, 'Results dump')):
    os.makedirs(os.path.join(folder_path, 'Results dump'))


# Detect range function. It is vulnerable to float conversion errors, change to string handling for redundancy
def detect_range(current):
    allowed_ranges = [2e-12, 20e-12, 200e-12, 2e-9, 20e-9, 200e-9, 2e-6, 20e-6, 200e-6, 2e-3, 20e-3]
    detected_range = None
    for current_range in allowed_ranges:  # Loop through all ranges from lowest to highest
        if np.abs(current) <= current_range:
            detected_range = current_range
            break  # stop when correct range found
    if detected_range is None:
        print("Could not detect current range.")
    return detected_range


# *******************************************************************
# Device initialization
SMU = SMUDevice()  # You can change the names to whatever you like. Use 'Refactor' in Pycharm.
WH = Filters()
PM = PowerMeter()
FM = FlipMirror()
LS = Arduino()
LS.connect()
FM.connect()
PM.connect()
SMU.connect()
SMU.write_command(f":SOURce:VOLTage:LEVel:IMMediate:AMPLitude {voltage}")

for meas_num in range(number_of_measurements):
    LS.laser_output('off')  # Turn off the laser to avoid creating charges while the wheel is moving
    WH.calibrate()  # Calibrate function is a bit problematic, check Wheels.py
    # ***************************

    # This section measures laser power
    FM.move('on')  # Move beam-splitter to laser path
    LS.laser_output("on")  # Turn on laser
    laser_power = np.mean(PM.measure(10))  # Measure 10 points, take average
    print(f"Laser power = {laser_power}")
    calibration = np.array(calibration)  # Python deals with arrays in complicated ways, for simplicity, I use numpy format
    Pinc = calibration[~np.isnan(calibration)]  # Remove 'nan' values. They are used to skip measurements
    # print(Pinc)
    Pinc = np.multiply(Pinc, laser_power)  # Multiplies calculated laser power by transmittance array
    # print(Pinc)
    LS.laser_output("off")  # Turn off laser
    FM.move('off')  # Move beam-splitter out of laser path
    SMU.trigger_settings(mtype="AINT", count=30, period=None)  # This sets up a measurement to stabilize dark current
    time.sleep(0.3)     # This is intended to give device enough time to react, not sure if actually needed
    SMU.measurement_speed("MED")
    time.sleep(0.3)
    SMU.set_current_range("AUTO")
    time.sleep(0.3)
    print("Dummy initiate to stabilize")  # This is to stabilize the dark current
    # (do longer if the current is decreasing during the measurement)
    SMU.initiate('ACQuire', timeout=1000)  # This also helps in determining the range to be used
    I_for_range = SMU.get_current()[-1]  # Takes the final point from the measurement (can be changed)
    # print(f"Range determination from: {I_for_range}")  # For troubleshooting
    IRange = detect_range(1.03 * I_for_range)  # The multiplier is used to give some space not to overflow. Somewhat random
    SMU.set_current_range(IRange)  # set detected range
    # Set up parameters for main measurements
    SMU.trigger_settings(mtype="TIMer", count=total_points, period=measurement_period)
    SMU.measurement_speed(measurement_speed)
    need_range_change = False  # This is a bool used to check whether range change is needed, so no to do it every time

    # Some arrays to store results
    Output_Current = []
    Current_Error = []
    Dark_Current = []
    Dark_Error = []
    Photocurrent = []
    Photocurrent_Error = []

    # Create a figure and axis
    fig, (ax1, ax2) = plt.subplots(2, 1)

    # Loop over each position (see file)
    for i in range(len(filter_pos)):
        WH.move(move_pos[i])
        print("Moving to: ", filter_pos[i], "for measurement loop number", meas_num+1)
        # In some cases, for the wheel to move to the required position, two moves are needed. To avoid measuring after
        # the first of the moves, I use NaN in the transmittance column. When script finds this, it skips the measurement.
        if np.isnan(calibration[i]):
            print("NaN detected - skipping measurement (normal procedure)")
            continue
        if need_range_change:  # This is to prevent sending set range command every time
            SMU.set_current_range(IRange)
            need_range_change = False
        # A single measurement is split into two parts, half of it is in dark, half under illumination.
        # Since the script waits for a measurement to be completed before going to the next line, but we want to turn
        # on the laser at half-time - threading is used. It basically creates a temporary script running parallel.
        timer = threading.Timer(measurement_period * (total_points - 1) / 2, lambda: LS.laser_output('on'))
        timer.start()
        # print("measurement started")
        SMU.initiate('ACQuire', timeout=1000)
        # print("measurement ended")
        meas_curr = SMU.get_current()
        ttime = SMU.get_time()  # double t to avoid confusing with other functions
        timer.cancel()  # Threading timer has to be defined and stopped every time it is used

        # Checks for overflow, if found, increases the range by 1 order and remeasures
        # (probably can be integrated with the previous block).
        while np.any(np.isnan(meas_curr)) or any(x > 1 for x in meas_curr):
            print("Overflow detected, repeating measurement with higher range")
            IRange = IRange * 10
            print(IRange)
            SMU.set_current_range(IRange)
            timer = threading.Timer(measurement_period * (total_points - 1) / 2, lambda: LS.laser_output('on'))
            timer.start()
            # print("measurement started2")
            SMU.initiate('ACQuire', timeout=1000)
            # print("measurement ended2")
            meas_curr = SMU.get_current()
            ttime = SMU.get_time()
            timer.cancel()
        # After measurement is done, the laser is turned off to avoid creating more charges. There might be a bit of an
        # issue because there is no charge extraction being done before the next measurement is executed.
        LS.laser_output('OFF')
        # For each of the values (dark, light, photo), the average and standard deviation is calculated
        Dark_Current.append(np.mean(meas_curr[math.ceil(cut_start_time_dark / measurement_period):int(math.ceil(
            len(meas_curr)/2) - cut_end_time_dark / measurement_period)]))
        Dark_Error.append((np.std(meas_curr[math.ceil(cut_start_time_dark / measurement_period):int(
            math.ceil(len(meas_curr)/2) - cut_end_time_dark / measurement_period)])))
        Output_Current.append(np.mean(meas_curr[int(math.ceil(len(meas_curr)/2) +
                                                    cut_start_time_illum / measurement_period):]))
        Current_Error.append(np.std(meas_curr[int(math.ceil(len(meas_curr)/2) +
                                                  cut_start_time_illum / measurement_period):]))
        Photocurrent.append(Output_Current[-1] - Dark_Current[-1])
        Photocurrent_Error.append(np.sqrt(np.square(Current_Error[-1]) + np.square(Dark_Error[-1])))

        # So this part in some cases will be problematic, because it does not change the current if going from high to low.
        # This may be the case if your dark current is negative (<-20pA), and current goes to positive values
        # during the measurement. This script is built on the assumption that photocurrent is always positive.
        if IRange < detect_range(1.2*Output_Current[-1]):  # 1.2 is arbitrary, using previous average for comparison
            IRange = detect_range(1.2*Output_Current[-1])
            print("need range change")
            need_range_change = True
        # *******************************************************************************

        # Section to save file with raw data
        # Naming convention can be changed according to ones needs
        file_name = f"Results dump/Raw data {device_name} {Pinc[-1]}W low_intensity measurement{meas_num+1}" \
                    f"{filter_pos[i]} {voltage}V {measurement_speed} {total_points}pts {measurement_period}s.csv"
        file_path = os.path.join(folder_path, file_name)
        # Write data to the CSV file
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(["Time", "Current"])  # write header
            for t, c, in zip(ttime, meas_curr):
                writer.writerow([t, c])  # write data
        # *******************************************************************************

        # Plot the data (updating plot)
        # Clear the axes
        ax1.cla()
        ax2.cla()
        # Plot the new line with error bars
        ax1.errorbar(Pinc[:len(Dark_Current)], Dark_Current, yerr=Dark_Error, label='Dark Current', fmt='o')
        ax1.errorbar(Pinc[:len(Dark_Current)], Output_Current, yerr=Current_Error, label='Light Current', fmt='o')
        ax2.errorbar(Pinc[:len(Dark_Current)], Photocurrent, yerr=Photocurrent_Error, fmt='o')
        # Set log-log or log-linear scale
        ax1.set_xscale('log')
        ax2.set_xscale('log')
        ax2.set_yscale('log')
        ax1.grid(True)
        ax2.grid(True)
        # Auto-scale
        ax1.relim()
        ax1.autoscale_view()
        ax1.legend()
        ax2.relim()
        ax2.autoscale_view()
        # Redraw the figure
        fig.canvas.draw()
        fig.canvas.flush_events()
        # Small pause to ensure plot updates
        plt.pause(0.1)
        # *******************************************************************************

    # Current vs intensity data
    file_name = f"Low intensity current output {device_name} {voltage}V measurement{meas_num+1}" \
                f" {measurement_speed} {total_points}pts {measurement_period}s.csv"
    file_path = os.path.join(folder_path, file_name)
    # Write data to the CSV file
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Incident_Power", "Dark_Current", "Dark_Error", "Current", "Current_Error"])  # write header
        for p, d, der, i, er in zip(Pinc, Dark_Current, Dark_Error, Output_Current, Current_Error):
            writer.writerow([p, d, der, i, er])  # write data

    # Photocurrent vs intensity data
    file_name = f"Low intensity photocurrent {device_name} {voltage}V measurement{meas_num+1}" \
                f" {measurement_speed} {total_points}pts {measurement_period}s.csv"
    file_path = os.path.join(folder_path, file_name)
    # Write data to the CSV file
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Incident_Power", "Photocurrent", "Photocurrent_Error"])  # write header
        for p, ph, er in zip(Pinc, Photocurrent, Photocurrent_Error):
            writer.writerow([p, ph, er])  # write data

    if save_plots:
        file_path = os.path.join(folder_path, f"Low intensity measurement {device_name} measurement{meas_num+1}"
                                              f"{voltage}V {measurement_speed} {total_points}pts.png")
        plt.savefig(file_path)
    if show_plots[0]:
        plt.show(block=False)
        plt.pause(show_plots[1])
        plt.close()

# *****Disconnect****************************************
SMU.write_command(":SOURce:VOLTage:LEVel:IMMediate:AMPLitude 0")
LS.disconnect()
PM.disconnect()
FM.disconnect()
SMU.disconnect()
WH.disconnect()

duration = time.time() - start_time
print("The script took ", duration, " seconds to run.")
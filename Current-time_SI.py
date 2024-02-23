from SMU import SMUDevice
import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
import csv
import time
import os


start_time = time.time()  # This is just to see how long it takes, can be deleted
# ENTER DATA HERE
device_name = 'SiPD_FD11A_Sid_Dark_ExtractQs'  # replace with your name
voltage = 0.01 	# applied voltage bias across the DUT
count = 256 	# number of data points to be recorded
period = 0.1	# sampling time interval in units of seconds
save_plots = True  # If you want plots to be saved as .png files
show_plots = [True, 0.1]  # If you want plots to be shown after each measurement. Second number is show duration

# Selecting a folder to save the results
root = tk.Tk()
root.withdraw()
folder_path = filedialog.askdirectory()
print("Selected folder path to save results to:", folder_path)
if not folder_path:
    print('File selection cancelled.')
    quit()
# Create folder for results if it doesn't already exist
if not os.path.exists(os.path.join(folder_path, 'Dark Current')):
    os.makedirs(os.path.join(folder_path, 'Dark Current'))


def detect_range(current):
    allowed_ranges = [2e-12, 20e-12, 200e-12, 2e-9, 20e-9, 200e-9, 2e-6, 20e-6, 200e-6, 2e-3, 20e-3]
    detected_range = None
    for current_range in allowed_ranges:
        if np.abs(current) <= current_range:
            detected_range = current_range
            break
    if detected_range is None:
        print("Could not detect current range.")
    return detected_range


def show_currenttime_plot(otime, ocurrent, sname):
    plt.plot(otime, ocurrent)
    plt.xlabel('Time (s)')
    plt.ylabel('Current (A)')
    plt.title(f'{device_name} ')
    if save_plots:
        fig_path = os.path.join(folder_path, sname)
        plt.savefig(fig_path)
    if show_plots[0]:
        plt.show(block=False)
        plt.pause(show_plots[1])
        plt.close()


SMU = SMUDevice()
SMU.connect()
time.sleep(0.3)
SMU.write_command(f":SOURce:VOLTage:LEVel:IMMediate:AMPLitude {voltage}")
time.sleep(0.3)

output_current = []
output_time = []
SMU.set_current_range("AUTO")
SMU.measurement_speed(3)
SMU.trigger_settings(mtype="AINT", count=300)
SMU.initiate("ACQuire")
IRange = detect_range(np.max(SMU.get_current()))
SMU.set_current_range(IRange)


SMU.measurement_speed(3)
SMU.trigger_settings(mtype="TIMer", count=count, period=period)
for idx in range(15):
    SMU.initiate("ACQuire", timeout=400)
    output_current = SMU.get_current()
    output_time = SMU.get_time()
    print("Measured", device_name, " for N:", count, ", del-T:", period, "; version", idx+1, "/15")
        # *******************Save the raw data**********************************
    file_name = f"Dark Current/IT {device_name} dark {voltage}V {period}s {count}pts {idx+1}.csv"
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Time", "Current"])  # write header
        for t, c in zip(output_time, output_current):
            writer.writerow([t, c])  # write data
    # **********************************************************************
    plot_name = f"Dark Current/{device_name} {voltage}V {period}s {count}pts {idx+1}.png"
    show_currenttime_plot(output_time, output_current, plot_name)


SMU.write_command(":SOURce:VOLTage:LEVel:IMMediate:AMPLitude 0")
time.sleep(0.2)
SMU.disconnect()

duration = time.time() - start_time
print("The script took ", duration, " seconds to run.")


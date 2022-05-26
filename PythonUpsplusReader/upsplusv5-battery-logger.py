#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UPSplus v5 Battery Logger V1.1
Original author: Ed Watson (mail@edwilldesign.com)
Contributors: leandroalbero

Logs uptime, battery voltage, device wattage and battery %remaining from the
GeeekPi UPSv5 (EP-0136) board, connected to a Raspberry Pi,and writes to a
timestamped CSV file for optional graphing via Pandas (if installed).

Usage original:
'python3 upspv5-batt-logger.py' - logs to local [timestamp].csv file
'python3 upspv5-batt-logger.py file.csv "[label for graph title]"' - graph results as local png images

Usage now:
'python3 upspv5-batt-logger.py --csvfile="[path to file.csv]" --runonce #both arguments are optional


Use to capture battery discharge profile. Run immediately after booting the device
following a full charge for best results. Recommend enabling 'Overlay FS' if using
RasPi Debian Buster to make the FS read-only w/ RAM disk. This prevents FS damage
when battery power becomes low, causing power outages. 

Note: "% remaining" is not accurate during charging.
"""

import sys
import os
import time
import csv
import argparse
from datetime import datetime

import smbus2
from ina219 import INA219, DeviceRangeError

I2C_DEVICE_BUS = 1
SMB_DEVICE_ADDR = 0x17
INA_DEVICE_ADDR = 0x40
INA_BATT_ADDR = 0x45
DELAY = 5  # delay between I2C reads (in seconds)
STOP_ON_ERR = 0  # stop logging on bus read error

now = datetime.now()
T = now.strftime("%Y-%m-%d_%H%M%S")

bus = smbus2.SMBus(I2C_DEVICE_BUS)
ina = INA219(0.00725, busnum=I2C_DEVICE_BUS, address=INA_DEVICE_ADDR)
ina.configure()
ina_batteries = INA219(0.005, busnum=I2C_DEVICE_BUS, address=INA_BATT_ADDR)
ina_batteries.configure()
runonce = False
csv_file = "batt_log_" + T + ".csv"


def parse_args():
    parser = argparse.ArgumentParser(description='gets data from a upsplus board attachted to a raspi via i2c')
    parser.add_argument("--runonce", help="signals whether or not the scripts runs one time or forever (till ctrl-c)", action="store_true")
    parser.add_argument("--csvfile", help="writes the data to a csvfile with this filename. will be created when it doesn't exist. will be appended when it exists (assuming it is in the correct format)", required=False, type=str)
    args = parser.parse_args()
    
    global runonce
    runonce = args.runonce
    print(f"runonce? {runonce}")
    
    if args.csvfile:
        #check the extension. the file is created later on, so no check needed if it exists
        if os.path.splitext(args.csvfile)[-1].lower() == ".csv":
            print(f"this seems to be a valid args.csvfile! {args.csvfile}")
            global csv_file
            csv_file = args.csvfile
            

def create_file(csv_file_name):
    #if the file already exist, and its extension is .csv, return
    if os.path.isfile(csv_file_name) and os.path.splitext(csv_file_name)[-1].lower() == ".csv":
        print(f"csv file already exist: {csv_file_name}")
        return

    print(f"creating file: {csv_file_name}")
    # create csv file and write headers 
    with open(csv_file_name, 'x', newline='') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC)
        csvtitles = [
            "RegisterTimestamp",
            "Uptime (s)",
            "Volts (mV)",
            "Power (mW)",
            "Remaining %",
            "Battery Current (mA)",
            "Batt. Temp (ºC)"]
        writer.writerow(csvtitles)
        print(csvtitles)


def main():
    parse_args()
    create_file(csv_file)
    while True:
        # Loop indefinately whilst reading and writing data, until user hits Ctrl-C, or break when run once flag is set
        try:
            a_receive_buf = [0x00]
            for i in range(1, 255):
                a_receive_buf.append(bus.read_byte_data(SMB_DEVICE_ADDR, i))
            csvdata = [
                T,
                "%d" % (a_receive_buf[39] << 24 | a_receive_buf[38] << 16 | a_receive_buf[37] << 8 | a_receive_buf[36]),
                "%d" % (a_receive_buf[6] << 8 | a_receive_buf[5]),
                "%.0f" % ina.power(),
                "%d" % (a_receive_buf[20] << 8 | a_receive_buf[19]),
                "%.0f" % ina_batteries.current(),
                "%d" % (a_receive_buf[12] << 8 | a_receive_buf[11])]
            print(csvdata)
            with open(csv_file, 'a', newline='') as file:
                writer = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow(csvdata)
            #break when we only want to run this once
            if runonce:
                break
            #otherwise, sleep and continue
            time.sleep(DELAY)
        except KeyboardInterrupt:
            sys.exit()
        except:
            if STOP_ON_ERR == 1:
                print("Unexpected error:", sys.exc_info()[0])
                raise
            pass


main()

"""
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
"""

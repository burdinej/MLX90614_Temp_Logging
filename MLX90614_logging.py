#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This program allows you to access emissivitity settings of the mlx90614 ir sensor and to perform temperature logging. This program can be used with up to 2 mlx90614 sensors numbered 1 and 2 where 1 is the sensor with i2c addr 0x03 (0x11 for 2). By default, this program records measurements from all attached sensors (and there is no need or way to specify to the program how many sensors are being used, except no more than 2 can be used).")
"""

import sys
import arduino_serial as ard
import argparse
import time, os, sys
import datetime as dt
import re


DEFAULT_DEV="/dev/ttyUSB0"

def main():
    par = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    par.add_argument("--log_temp", "-l", metavar="RATE", type=float, help="Use to tell the program to start logging data. `RATE` is the number of measurements you want per second (Hz) and can be any value >0 and <10000. --log_file argument required")
    par.add_argument("--set_emis", "-s", metavar=("EMISSIVITY","SENSOR"), type=float, nargs=2, help="Use to change the emissivity setting of a particular MLX90614 sensor. EMISSIVITY must be 0.1 <= E <= 1.0. SENSOR is the the id of the sensor you want to change the emis for (must be 1 or 2)")
    par.add_argument("--get_emis", "-g", type=int, metavar="SENSOR",  help="Used to retrieve the current emissivity setting of a specific sensor. SENSOR is the id of the sensor you want to see the emissivity for")
    par.add_argument("devfile", metavar="DEVFILE", type=str, default=DEFAULT_DEV, help=f"The devfile path to locate usb device for serial. default={DEFAULT_DEV}")
    par.add_argument("--log_file", "-f", metavar='FILE', type=str, help="Path for the file you want to use or create to log data.")
    args = par.parse_args()

    if args.set_emis and not (0.1 <= args.set_emis[0] <= 1.0):
        raise ard.ArduinoError("An emissivity less than 0.1 or greater than 1.0 was requested. Use an allowed emissivity. See -h or --help for help")
    if args.set_emis and (args.set_emis[1] not in [1,2]):
        raise ard.ArduinoError("The sensor chosen to set the emissivity on was something other than 1 or 2. Use an allowed sensor. See -h or --help for help!")
    if args.get_emis and args.get_emis not in [1,2]:
        raise ard.ArduinoError("You may only access sensors with ID of 1 or 2. See -h or --help for help!")
    if args.log_temp and not (0 < args.log_temp <= 10000):
        raise ard.ArduinoError("You chose to sample the temperature either less than 0 Hz or more than 10000 HZ. The poll rate must be 0 < Hz <= 10000. See -h or --help for help!")
    if args.log_temp and not args.log_file:
        raise ard.ArduinoError('--log_file argument required when --log_temp called')
    if not args.get_emis and not args.set_emis and not args.log_temp:
        raise ard.ArduinoError("You supplied a devfile, but issued no command arguments (set_emis, get_emis, or log_temp). You must issue at least one command. See -h or --help for help!")
    
    print(f"\nAttempting to connect to Arduino on {args.devfile}...")
    ardDev = ard.arduino(args.devfile)
    print("Connected!")
    print("Initializing...")
    time.sleep(5)
    ardDev.write(ard.HS_CMD)
    print( readArdResp( ardDev ) )
    time.sleep(1) 

    if args.set_emis:
        print(f"Setting sensor {int(args.set_emis[1])} emissivity to {args.set_emis[0]} ...")
        ardDev.readclear()
        ardDev.write(ard.SET_EMIS_CMD)
        time.sleep(0.005) 
        ardDev.write(b' ')
        time.sleep(0.005)
        ardDev.write(args.set_emis[0]) # Write emissivity
        time.sleep(0.005) 
        ardDev.write(b' ')
        time.sleep(0.005)
        ardDev.write(int(args.set_emis[1])) # Write selected device
        time.sleep(2) 
        print( readArdResp( ardDev ) )
        time.sleep(1)
        print( readArdResp( ardDev ) )
        time.sleep(1)

    if args.get_emis:
        print(f"Getting current emissivity setting from sensor {args.get_emis}...")
        ardDev.write(ard.GET_EMIS_CMD)
        time.sleep(0.005)
        ardDev.write(args.get_emis) # Write device to retrieve Emis from
        time.sleep(2)
        print( readArdResp( ardDev ) )
        time.sleep(1)
        print( readArdResp( ardDev ) )
        time.sleep(1)

    if args.log_temp:
        firstDataReq = True        
        with open(args.log_file, 'a') as file:
            file.write('# datetime\t\t\t\tAmbTemp1 [C]\tObjTemp1 [C]\tAmbTemp2 [C]\tObjTemp2 [C]\n')
            try: 
                while True:
                    ardDev.readclear()
                    ardDev.write(ard.DATA_CMD)
                    if (firstDataReq == True):
                        print( readArdResp ( ardDev ) )
                        firstDataReq = False
                        time.sleep(3.0)
                    temps = readArdResp(ardDev).split(',')
                    temps = [float(temp) for temp in temps]
                    t = time.strftime("%Y-%m-%d-%H:%M:%S")
                    os.system('clear')
                    sys.stdout.write('\033[1;1H') # reset cursor
                    print(f'Logging to {args.log_file}. Press ctrl+c to stop\n')
                    print('LastEntry\t\tAmbTemp1 [C]\tObjTemp1 [C]\tAmbTemp2 [C]\tObjTemp2 [C]')
                    print(f"{t}\t{temps[0]}\t\t{temps[1]}\t\t{temps[2]}\t\t{temps[3]}\n")  
                    file.write(f"{t}\t\t{temps[0]}\t\t\t{temps[1]}\t\t\t{temps[2]}\t\t\t{temps[3]}\n")
                    time.sleep(1.0 / args.log_temp)  
            except KeyboardInterrupt:
                print('\nKeyboardInterrupt. \n\nLogging stopped. Please wait while arduino connection closes')
            except Exception as e:
                print(e)
                sys.exit()
            finally:
                close(ardDev)
    else:
        print("You chose to not log at this time. Shutting down arduino connection, please wait! ...")
        close(ardDev)
    

def close(ardDev):
    ardDev.write(ard.STOP_CMD)
    print( readArdResp ( ardDev ) )
    time.sleep(3)
    print( readArdResp( ardDev ) )
    ardDev.__del__()
    time.sleep(0.2)
    print("Serial to arduino closed. Goodbye!")

def readArdResp(ardDev):
    timeout = 0;
    while (ardDev.ser.inWaiting() < 1):
        if (timeout > 400):
            raise ard.ArduinoError("Fatal timeout, idk whats wrong")
        timeout = timeout + 1
        time.sleep(0.1)
    rline = ardDev.read()  #Read arduino response
    return rline.decode()



if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import time

HS_CMD = b'H'
DATA_CMD = b'B'
STOP_CMD = b'E'
SET_EMIS_CMD = b'S'
GET_EMIS_CMD = b'G'

class ArduinoError(Exception):
    def __init__(self, message):
        self.msg = "ERROR with Arduino: %s" % str(message)
    def __str__(self):
        return self.msg

class arduino(object):
    WAIT = 0.1   # Wait this many seconds after write for ACK
    def __init__(self, devfile):
        self.ser = serial.Serial(devfile, baudrate=115200, timeout=0, writeTimeout=1)
        time.sleep(1)
        if self.ser == None: raise ArduinoError("Arduino initialization error, could not connect! Make sure you used the correct devfile path for the ttyUSB* device the arduino is on, and that it was typed correctly!")
    def __del__(self):
        self.ser.close()
        del self
    
    def write(self, command):
        if isinstance(command, (float, int)):
            self.ser.write(bytes(str(command), 'utf-8'))
        else:
            self.ser.write(command)

    def read(self):
        return self.ser.readline() ## '\n' by default, which is the terminator set in arduino.

    def readclear(self):
        self.ser.reset_input_buffer()
    
    def start_dataLogging(self, cmd):
        self.readclear()
        self.write(b"".cmd)



#!/usr/bin/python3

import binascii
import can
import logging
import os
import serial
import sys
import time

# set up some basic commands here
data_query = bytes([0x80, # header
               0x10, # destination = Subaru ECU
               0xF0, # source = Diagnostic tool
               0x03, # Data size...
               0xA8, # command = Address read
               0x00, # single response
               0x1C]) # battery voltage

#query_test = bytes([128,16,240,23,168,0,0,0,15,0,0,14,0,0,8,0,0,16,0,1,33,255,83,5,0,0,21,2])
ecu_init = bytes([0x80, # header
                  0x10, # destination = Subaru ECU
                  0xF0, # source = Diagnostic tool
                  0x01, # Data size...
                  0xBF]) # command = ECU Init

def checksum(query):
    checksum = 0
    for i in query:
        checksum += i
    return bytes([checksum & 0xff])

def ecu_send(ser, query):
    bytes_to_send = query
    bytes_to_send += checksum(query)
    logging.info("query: {}".format(binascii.hexlify(bytes_to_send)))
    ser.write(bytes_to_send)

def ecu_receive(ser):
    response = ser.read(100)
    logging.info("response: {}".format(binascii.hexlify(response)))

def main():
    bus = can.interface.Bus(channel='can0', bustype='socketcan_native')

    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

    ser =  serial.Serial('/dev/ttyAMA0',
                         baudrate=4800,
                         timeout=2,
                         parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE,
                         bytesize=serial.EIGHTBITS)

    ecu_send(ser, ecu_init)
    response = ecu_receive(ser)
    
    ecu_send(ser, data_query)
    response = ecu_receive(ser)

    msg = can.Message(arbitration_id=0x715,data=[0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07],extended_id=False)
    bus.send(msg)

if __name__ == "__main__":
    main()

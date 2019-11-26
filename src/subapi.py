#!/usr/bin/python3

import binascii
import can
import logging
import os
import serial
import sys
import time

# set up some basic commands here
battery_query = bytes([0x80, # header
                       0x10, # destination = Subaru ECU
                       0xF0, # source = Diagnostic tool
                       0x05, # Data size...
                       0xA8, # command = Address read
                       0x00, # single response
                       0x0, 0x0, 0x1C]) # battery voltage (x*.08)

data_query = bytes([0x80, # header
                       0x10, # destination = Subaru ECU
                       0xF0, # source = Diagnostic tool
                       0x44, # Data size...
                       0xA8, # command = Address read
                       0x00, # single response
                       0x00, 0x00, 0x09,  # AF Correction #1 ((x-128) * 0.78125)
                       0x00, 0x00, 0x0A,  # AF Learning #1 ((x-128) * 0.78125)
                       0x00, 0x00, 0x46,  # AF Sensor #1 (x * 0.11484375)
                       0x02, 0x00, 0xF4,  # Engine load - 2 bytes (x * 0.0001220703125)
                       0x02, 0x00, 0xF5,  # Engine load - 2 bytes (x * 0.0001220703125)
                       0x00, 0x00, 0x13,  # Mass Airflow - 2 bytes (x * 0.01)
                       0x00, 0x00, 0x14,  # Mass Airflow - 2 bytes (x * 0.01)
                       0x02, 0x17, 0xB6,  # Manifold Relative Pressure Direct - 2 bytes ((x-32768) * 0.01933677)
                       0x02, 0x17, 0xB7,  # Manifold Relative Pressure Direct - 2 bytes ((x-32768) * 0.01933677)
                       0x00, 0x00, 0x0E,  # Engine Speed - 2 bytes (x * 0.25)
                       0x00, 0x00, 0x0F,  # Engine Speed - 2 bytes (x * 0.25)
                       0x02, 0x0B, 0x59,  # Fine Learning Knock Correction - (x*0.3515625-45)
                       0x02, 0x0B, 0x54,  # Feedback Knock Correction - (x*0.3515625-45)
                       0x00, 0x00, 0xF9,  # IAM - (x*0.0625)
                       0x00, 0x00, 0x11,  # Ignition Total Timing - ((x-128)*0.5)
                       0x00, 0x00, 0x15,  # Throttle Opening Angle - (x*0.3921569)
                       0x02, 0x0A, 0x3E,  # Fueling Final Base - 2 bytes (30105.6/x)
                       0x02, 0x0A, 0x3F,  # Fueling Final Base - 2 bytes (30105.6/x)
                       0x02, 0x0D, 0xE2,  # CL/OL Fueling - (x)
                       0x00, 0x00, 0x12,  # Intake Air Temperature - (x-40)
                       0x00, 0x00, 0x20,  # IPW - (x*.256)
                       0x00, 0x00, 0x10]) # Vehicle Speed (x * 0.621371192)

data_cont_query = bytes([0x80, # header
                       0x10, # destination = Subaru ECU
                       0xF0, # source = Diagnostic tool
                       0x44, # Data size...
                       0xA8, # command = Address read
                       0x01, # continuous response
                       0x00, 0x00, 0x09,  # AF Correction #1 ((x-128) * 0.78125)
                       0x00, 0x00, 0x0A,  # AF Learning #1 ((x-128) * 0.78125)
                       0x00, 0x00, 0x46,  # AF Sensor #1 (x * 0.11484375)
                       0x02, 0x00, 0xF4,  # Engine load - 2 bytes (x * 0.0001220703125)
                       0x02, 0x00, 0xF5,  # Engine load - 2 bytes (x * 0.0001220703125)
                       0x00, 0x00, 0x13,  # Mass Airflow - 2 bytes (x * 0.01)
                       0x00, 0x00, 0x14,  # Mass Airflow - 2 bytes (x * 0.01)
                       0x02, 0x17, 0xB6,  # Manifold Relative Pressure Direct - 2 bytes ((x-32768) * 0.01933677)
                       0x02, 0x17, 0xB7,  # Manifold Relative Pressure Direct - 2 bytes ((x-32768) * 0.01933677)
                       0x00, 0x00, 0x0E,  # Engine Speed - 2 bytes (x * 0.25)
                       0x00, 0x00, 0x0F,  # Engine Speed - 2 bytes (x * 0.25)
                       0x02, 0x0B, 0x59,  # Fine Learning Knock Correction - (x*0.3515625-45)
                       0x02, 0x0B, 0x54,  # Feedback Knock Correction - (x*0.3515625-45)
                       0x00, 0x00, 0xF9,  # IAM - (x*0.0625)
                       0x00, 0x00, 0x11,  # Ignition Total Timing - ((x-128)*0.5)
                       0x00, 0x00, 0x15,  # Throttle Opening Angle - (x*0.3921569)
                       0x02, 0x0A, 0x3E,  # Fueling Final Base - 2 bytes (30105.6/x)
                       0x02, 0x0A, 0x3F,  # Fueling Final Base - 2 bytes (30105.6/x)
                       0x02, 0x0D, 0xE2,  # CL/OL Fueling - (x)
                       0x00, 0x00, 0x12,  # Intake Air Temperature - (x-40)
                       0x00, 0x00, 0x20,  # IPW - (x*.256)
                       0x00, 0x00, 0x10]) # Vehicle Speed (x * 0.621371192)


ecu_init = bytes([0x80, # header
                  0x10, # destination = Subaru ECU
                  0xF0, # source = Diagnostic tool
                  0x01, # Data size...
                  0xBF]) # command = ECU Init

#baud_change = bytes([0x80, # header
#                     0x10, # destination = Subaru ECU
#                     0xF0, # source = Diagnostic tool
#                     0x05, # Data size..
#                     0xB8, # Write single address
#                     0x00, 0x01, 0x98, # Address for baud?
#                     0x5A]) # Value to write

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

def ecu_receive(ser, length):
    response = ser.read(length)
    logging.info("response of len {}: {}".format(len(response), binascii.hexlify(response)))
    if len(response) != length:
        logging.error("Unexpected receive bytes on read")
    return response

def main():
    bus = can.interface.Bus(channel='can0', bustype='socketcan_native')

    logging.basicConfig(filename='/var/log/subapi',
                        format='%(asctime)s.%(msecs)03d %(message)s',
                        datefmt='%Y-%m-%d,%H:%M:%S',
                        level=logging.DEBUG)

    ser =  serial.Serial('/dev/ttyAMA0',
                         baudrate=4800,
                         timeout=0.5,
                         parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE,
                         bytesize=serial.EIGHTBITS)

    ecu_send(ser, ecu_init)
    response = ecu_receive(ser, 68)

#    ecu_send(ser, baud_change)
#    response = ecu_receive(ser, 100)
    
    ecu_send(ser, battery_query)
    response = ecu_receive(ser, 17)

    ecu_send(ser, data_query)
    response = ecu_receive(ser, 200)

    ecu_send(ser, data_cont_query)
    response = ecu_receive(ser, 101)

    while True:
        response = ecu_receive(ser, 28)
        if len(response) == 28:
            msg0 = can.Message(arbitration_id=0x715,data=response[5:12],extended_id=False)
            msg1 = can.Message(arbitration_id=0x716,data=response[12:19],extended_id=False)
            msg2 = can.Message(arbitration_id=0x717,data=response[19:27],extended_id=False)
            try:
                bus.send(msg0)
                bus.send(msg1)
                bus.send(msg2)
            except:
                pass
        else:
            ecu_send(ser, data_cont_query)
            response = ecu_receive(ser, 101)
            
if __name__ == "__main__":
    main()

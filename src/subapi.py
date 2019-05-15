#!/usr/bin/python3

import binascii
import serial

              
query = bytes([0x80, # header
               0x10, # destination = Subaru ECU
               0xF0, # source = Diagnostic tool
               0x03, # Data size...
               0xA8, # command = Address read
               0x00, # single response
               0x1C, # battery voltage
               0x47]) # Checksum byte

#checksum = 0
#for i in query:
#    checksum += i
#print(checksum)

print("query: {}".format(binascii.hexlify(query)))

ser =  serial.Serial('/dev/ttyAMA0', 4800, timeout=1, write_timeout=0)
ser.write(query)
response = ser.read(20)

print("response: {}".format(binascii.hexlify(response)))

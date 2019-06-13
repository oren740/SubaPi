# SubaPi
Project repo for Raspberry Pi converter from SSM to CAN

# Information links
* http://www.romraider.com/RomRaider/SsmProtocol

# Process
I bought a standard Raspberry Pi 3 and a PiCan2 with SMPS with supporting cables from Copper Hill.
https://copperhilltech.com/pican2-can-interface-for-raspberry-pi-2-3-with-smps/

I soldered on a MCP2025 for k-line following the schematic in the hw directory.  Note, don't connect pin 8 on the MCP2025 even though I show it.  It's not needed, since there is a switched mode power supply (SMPS) and wouldn't provide enough anyway.

I then created the software in the src directory and configured the RaceCapturePro to listen to the three CAN messages I output.
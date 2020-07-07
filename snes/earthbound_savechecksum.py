#!/usr/bin/env python3
#
# EarthBound Save Checksum Calculator
# Osteoclave
# 2011-10-18

import struct
import sys



# Check for incorrect usage.
argc = len(sys.argv)
if argc != 2:
    print("Usage: {0:s} <saveFile>".format(sys.argv[0]))
    sys.exit(1)

# Read the save file.
# There are six blocks of 0x500 bytes each.
# Each game save is mirrored across two blocks.
saveFile = sys.argv[1]
with open(saveFile, "rb") as saveStream:
    saveBytes = saveStream.read(6 * 0x500)

# Examine each block in turn.
for i in range(6):

    # Define some convenience variables.
    blockRoot = 0x500 * i
    blockData = saveBytes[blockRoot+0x20:blockRoot+0x500]

    # 001C-1D: Stored additive checksum.
    # 001E-1F: Stored XOR checksum.
    addChecksum = struct.unpack_from("<H", saveBytes, blockRoot + 0x1C)[0]
    xorChecksum = struct.unpack_from("<H", saveBytes, blockRoot + 0x1E)[0]

    # Calculate the additive sum from the data.
    addRealsum = sum(blockData) & 0xFFFF

    # Calculate the XOR sum from the data.
    xorRealsum = 0
    for x in struct.iter_unpack("<H", blockData):
        xorRealsum ^= x[0]

    # Print the results.
    print("Save block: {0:d}".format(i))
    print("Alleged add checksum: 0x{0:04X}".format(addChecksum))
    print("Alleged XOR checksum: 0x{0:04X}".format(xorChecksum))
    print("Calculated add checksum: 0x{0:04X}".format(addRealsum))
    print("Calculated XOR checksum: 0x{0:04X}".format(xorRealsum))
    print()

# Exit.
sys.exit(0)

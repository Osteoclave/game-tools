# EarthBound Decompressor
# Written by Alchemic
# 2012 Apr 20
# 
# 
# 
# A detailed description of the compression format:
# 
#   - Compressed data consists of a sequence of the following eight 
#     commands, terminated with a 0xFF byte:
# 
#      - 000: Literal bytes
#      - 001: Run of a constant byte
#      - 010: Run of a constant word
#      - 011: Run of incrementing bytes
#      - 100: Copy past bytes
#      - 101: Copy past bytes (with bits in reverse order)
#      - 110: Copy past bytes (backward)
#      - 111: Large-count command
# 
#   - Each command begins with its three identifying bits.
#     e.g. 001 for a run of a constant byte.
# 
#   - After these three bits is the count value. For commands 0-6, 
#     this is five bits long, so the command/count pair uses one 
#     byte: [CCC LLLLL].
# 
#   - Command 7 (Large-count command), on the other hand, looks 
#     like this:
# 
#        [111 CCC LL  LLLLLLLL]
# 
#     Where 111 indicates command 7, C is the three identifying 
#     bits of another command, and L is a ten-bit count for use 
#     with that command. In all, this uses two bytes.
# 
#   - Add one to the count value (regardless of whether the count 
#     was given in five bits or ten) to get the real count value.
# 
#   - After the count value are the command arguments:
# 
#      - 000 is followed by count-many uncompressed bytes, 
#        which are written to the output as-is.
# 
#      - 001 is followed by one uncompressed byte, which is 
#        written out count-many times.
# 
#      - 010 is followed by one uncompressed little-endian 
#        word, which is written out count-many times (low byte, 
#        high byte, low byte, high byte, etc).
# 
#      - 011 is followed by one uncompressed byte. This byte 
#        is written out as-is. The next byte is the first 
#        byte plus one; the byte after that, the first byte 
#        plus two; and so on, until count-many bytes have 
#        been written. The value being written wraps to 0x00 
#        after 0xFF if necessary.
# 
#     - 100, 101 and 110 are followed by a BIG-ENDIAN word 
#       indicating an absolute location in the previously 
#       decompressed data to start working from.
# 
#     - 111 has the arguments of its internal command.
# 
# 
# 
# This code uses python-bitstring:
# http://code.google.com/p/python-bitstring/

from __future__ import division

import sys
import bitstring





def decompress(romFile, startOffset):
    # Open the ROM.
    romStream = bitstring.ConstBitStream(filename=romFile)
    romStream.bytepos += startOffset

    # Allocate memory for the decompression process.
    decomp = bytearray()

    # Main decompression loop.
    # The conditional uses peek(), so the parsing position does not change.
    while romStream.peek('uint:8') != 0xFF:
        # Read the next command.
        nextCommand = romStream.read('uint:3')

        # Read the next count.
        nextCount = 0
        if nextCommand == 7:
            # 7 (111): Large-count command
            nextCommand = romStream.read('uint:3')
            nextCount = romStream.read('uint:10')
        else:
            nextCount = romStream.read('uint:5')
        nextCount += 1

        # Parse the next command.
        if nextCommand == 0:
            # 0 (000): Literal bytes
            for i in xrange(nextCount):
                decomp.append(romStream.read('uint:8'))

        elif nextCommand == 1:
            # 1 (001): Run of a constant byte
            constantByte = romStream.read('uint:8')
            for i in xrange(nextCount):
                decomp.append(constantByte)

        elif nextCommand == 2:
            # 2 (010): Run of a constant word
            constantLow = romStream.read('uint:8')
            constantHigh = romStream.read('uint:8')
            for i in xrange(nextCount):
                decomp.append(constantLow)
                decomp.append(constantHigh)

        elif nextCommand == 3:
            # 3 (011): Run of incrementing bytes
            incrementingByte = romStream.read('uint:8')
            for i in xrange(nextCount):
                decomp.append(incrementingByte)
                incrementingByte += 1
                incrementingByte &= 0xFF

        elif nextCommand == 4:
            # 4 (100): Copy past bytes
            pastIndex = romStream.read('uintbe:16')
            for i in xrange(nextCount):
                decomp.append(decomp[pastIndex])
                pastIndex += 1

        elif nextCommand == 5:
            # 5 (101): Copy past bytes (with bits in reverse order)
            pastIndex = romStream.read('uintbe:16')
            for i in xrange(nextCount):
                # Reverse the bits of a past byte (e.g. 0x80 <---> 0x01)
                pastByte = decomp[pastIndex]
                pastByte = ((pastByte >> 4) & 0x0F) | ((pastByte << 4) & 0xF0)
                pastByte = ((pastByte >> 2) & 0x33) | ((pastByte << 2) & 0xCC)
                pastByte = ((pastByte >> 1) & 0x55) | ((pastByte << 1) & 0xAA)
                decomp.append(pastByte)
                pastIndex += 1

        elif nextCommand == 6:
            # 6 (110): Copy past bytes (backward)
            pastIndex = romStream.read('uintbe:16')
            for i in xrange(nextCount):
                decomp.append(decomp[pastIndex])
                pastIndex -= 1

    # Consume the terminating 0xFF and calculate the end offset.
    romStream.read('uint:8')
    romStream.bytealign()
    endOffset = romStream.bytepos

    # Return the decompressed data and end offset.
    return (decomp, endOffset)





if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc < 3 or argc > 4:
        sys.stdout.write("Usage: ")
        sys.stdout.write("{0:s} ".format(sys.argv[0]))
        sys.stdout.write("<romFile> <startOffset> [outFile]\n")
        sys.exit(1)

    # Copy the arguments.
    romFile = sys.argv[1]
    startOffset = int(sys.argv[2], 16)
    outFile = None
    if argc == 4:
        outFile = sys.argv[3]

    # Decompress the data.
    outBytes, endOffset = decompress(romFile, startOffset)
    outSize = endOffset - startOffset

    # Write the decompressed output, if appropriate.
    if outFile is not None:
        outStream = open(outFile, "wb")
        outStream.write(outBytes)
        outStream.close()

    # Report statistics on the data.
    sys.stdout.write("Last offset read, inclusive: {0:X}\n".format(endOffset - 1))
    sys.stdout.write("Compressed size: 0x{0:X} ({0:d}) bytes\n".format(outSize))
    sys.stdout.write("Uncompressed size: 0x{0:X} ({0:d}) bytes\n".format(len(outBytes)))
    sys.stdout.write("Ratio: {0:f}\n".format(outSize / len(outBytes)))

    # Exit.
    sys.exit(0)

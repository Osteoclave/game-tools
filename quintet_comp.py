# Quintet Compressor
# Written by Alchemic
# 2012 Feb 04
# 
# 
# 
# Several SNES games by Quintet share one data compression format.
# Games that use this format include:
#   - ActRaiser
#   - ActRaiser 2
#   - Illusion of Gaia
#   - Robotrek
#   - Soul Blazer
# 
# The format is described in depth in the decompressor's source.
# 
# 
# 
# This code uses python-bitstring version 2.2.0:
# http://code.google.com/p/python-bitstring/

import os
import sys
import array
import bitstring



def compress( inFile ):
    # Define some useful constants.
    SEARCH_LOG = 8
    SEARCH_SIZE = (1 << SEARCH_LOG)
    LOOKAHEAD_LOG = 4
    LOOKAHEAD_SIZE = (1 << LOOKAHEAD_LOG)
    BIT_PASTCOPY = 0
    BIT_LITERAL = 1

    # Open the input file.
    inStream = open(inFile, "rb")
    inSize = os.fstat(inStream.fileno()).st_size

    # Prepare the memory buffer.
    buffer = array.array('B', [0x20] * SEARCH_SIZE)
    buffer.fromfile(inStream, inSize)

    # Close the input file.
    inStream.close()

    # Prepare for compression.
    output = bitstring.BitArray()
    output.append(bitstring.pack('uintle:16', inSize))
    currentIndex = SEARCH_SIZE

    # Main compression loop.
    while currentIndex < len(buffer):
        bestIndex = 0
        bestLength = 0

        # Look for a match in the search buffer. (Brute force)
        for i in range(SEARCH_SIZE):
            # Don't compare past the end of the lookahead buffer.
            # Don't compare past the end of the memory buffer.
            compareLimit = min(
              LOOKAHEAD_SIZE - 1,
              len(buffer) - currentIndex
            )

            # Compare the search buffer to the lookahead buffer.
            # Count how many sequential bytes match (possibly zero).
            currentLength = 0
            for j in range(compareLimit):
                if buffer[currentIndex - SEARCH_SIZE + i + j] == buffer[currentIndex + j]:
                    currentLength += 1
                else:
                    break

            # Keep track of the largest match we've seen.
            if currentLength > bestLength:
                bestIndex = currentIndex - SEARCH_SIZE + i
                bestLength = currentLength

        # Write the next block of compressed output.
        pastcopyCost = 1 + SEARCH_LOG + LOOKAHEAD_LOG
        literalCost = bestLength * (1+8)

        if pastcopyCost < literalCost:
            # For some reason, the decompressor expects the pastcopy 
            # source values to be offset by 0xEF. I have no idea why.
            bestIndex = (bestIndex + 0xEF) & 0xFF
            output.append(bitstring.pack('bool', BIT_PASTCOPY))
            output.append(bitstring.pack('uint:{0:d}'.format(SEARCH_LOG), bestIndex))
            output.append(bitstring.pack('uint:{0:d}'.format(LOOKAHEAD_LOG), bestLength - 2))
            currentIndex += bestLength
        else:
            output.append(bitstring.pack('bool', BIT_LITERAL))
            output.append(bitstring.pack('uint:8', buffer[currentIndex]))
            currentIndex += 1

    # Return the compressed data.
    return output.tobytes()





if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc < 2 or argc > 4:
        sys.stdout.write("Usage: ")
        sys.stdout.write("{0:s} ".format(sys.argv[0]))
        sys.stdout.write("<inFile> [outFile] [outOffset]\n")
        sys.exit(1)

    # Copy the arguments.
    inFile = sys.argv[1]
    outFile = None
    if argc == 3 or argc == 4:
        outFile = sys.argv[2]
    outOffset = 0
    if argc == 4:
        outOffset = int(sys.argv[3], 16)

    # Compress the data.
    # Maybe this should take an array instead of a file? Unsure.
    outData = compress(inFile)

    # Write the compressed output, if appropriate.
    if outFile is not None:
        outStream = open(outFile, "r+b")
        outStream.seek(outOffset)
        outStream.write(outData)
        outStream.close()

    # Report the size of the compressed data.
    sys.stdout.write("New compressed size: 0x{0:X} ({0:d}) bytes\n".format(len(outData)))

    # Exit.
    sys.exit(0)

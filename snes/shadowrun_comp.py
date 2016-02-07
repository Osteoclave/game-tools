# Shadowrun Compressor
# Written by Alchemic
# 2016 Feb 06
# 
# 
# 
# The format is described in greater detail in the decompressor.
# 
# 
# 
# This code uses python-bitstring:
# https://pypi.python.org/pypi/bitstring

from __future__ import print_function
from __future__ import division

import sys
import bitstring





def compress(inBytes):
    # Define some useful constants.
    BIT_LITERAL = 0
    BIT_PASTCOPY = 1

    # Prepare for compression.
    dataSection = bytearray()
    controlSection = bitstring.BitArray()
    currentIndex = 0
    currentLiteralsQueued = 0

    # Main compression loop.
    while currentIndex < len(inBytes):
        bestIndex = 0
        bestLength = 0

        # Look for a match in the previously-seen data. (Brute force)
        for i in range(0, currentIndex):
            # Don't compare past the end of the input.
            compareLimit = len(inBytes) - currentIndex

            # Count how many sequential bytes match (possibly zero).
            currentLength = 0
            for j in range(compareLimit):
                if inBytes[i + j] == inBytes[currentIndex + j]:
                    currentLength += 1
                else:
                    break

            # Keep track of the largest match we've seen.
            # If you use ">=" here, the output is closer to what's in the ROM.
            if currentLength > bestLength:
                bestIndex = i
                bestLength = currentLength

        # Process the best match.
        if bestLength >= 3:
            # Write any queued literals (possibly none).
            if currentLiteralsQueued > 0:
                controlSection += bitstring.pack('bool', BIT_LITERAL)
                controlSection += bitstring.pack('uie', currentLiteralsQueued - 1)
                currentLiteralsQueued = 0
            else:
                controlSection += bitstring.pack('bool', BIT_PASTCOPY)

            # Write the pastcopy.
            controlSection += bitstring.pack('uint:n=v', n = currentIndex.bit_length(), v = bestIndex)
            controlSection += bitstring.pack('uie', bestLength - 3)
            currentIndex += bestLength

        else:
            dataSection.append(inBytes[currentIndex])
            currentLiteralsQueued += 1
            currentIndex += 1

    # Write any remaining queued literals (possibly none).
    if currentLiteralsQueued > 0:
        controlSection += bitstring.pack('bool', BIT_LITERAL)
        controlSection += bitstring.pack('uie', currentLiteralsQueued - 1)
        currentLiteralsQueued = 0

    # Assemble the output: header, data section, control section.
    output = bitstring.BitArray()
    output += bitstring.pack('uintle:16', len(inBytes))
    output += bitstring.pack('uintle:16', len(dataSection) + 2)
    output += dataSection
    # The first command is always literal, so we don't need to waste a bit saying so.
    output += controlSection[1:]

    # Return the compressed data.
    return output.tobytes()





if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc < 2 or argc > 4:
        print("Usage: {0:s} <inFile> [outFile] [outOffset]".format(sys.argv[0]))
        sys.exit(1)

    # Copy the arguments.
    inFile = sys.argv[1]
    outFile = None
    if argc == 3 or argc == 4:
        outFile = sys.argv[2]
    outOffset = 0
    if argc == 4:
        outOffset = int(sys.argv[3], 16)

    # Open, read and close the input file.
    inStream = open(inFile, "rb")
    inBytes = inStream.read()
    inStream.close()

    # Compress the data.
    outBytes = compress(inBytes)

    # Write the compressed output, if appropriate.
    if outFile is not None:
        # Mode r+b gives an error if the file doesn't already exist.
        open(outFile, "a").close()
        outStream = open(outFile, "r+b")
        outStream.seek(outOffset)
        outStream.write(outBytes)
        outStream.close()

    # Report statistics on the data.
    print("Uncompressed size: 0x{0:X} ({0:d}) bytes".format(len(inBytes)))
    print("Compressed size: 0x{0:X} ({0:d}) bytes".format(len(outBytes)))
    print("Ratio: {0:f}".format(len(outBytes) / len(inBytes)))

    # Exit.
    sys.exit(0)

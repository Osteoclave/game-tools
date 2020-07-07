#!/usr/bin/env python3
#
# Shadowrun Compressor
# Osteoclave
# 2016-02-06
#
# The compression format is described in the decompressor.
#
# This code uses python-bitstring:
# https://pypi.org/project/bitstring/

import os
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
                controlSection += bitstring.pack("uint:1", BIT_LITERAL)
                controlSection += bitstring.pack("uie", currentLiteralsQueued - 1)
                currentLiteralsQueued = 0
            else:
                controlSection += bitstring.pack("uint:1", BIT_PASTCOPY)

            # Write the pastcopy.
            controlSection += bitstring.pack(
                "uint:n=v", n = currentIndex.bit_length(), v = bestIndex
            )
            controlSection += bitstring.pack("uie", bestLength - 3)
            currentIndex += bestLength

        else:
            dataSection.append(inBytes[currentIndex])
            currentLiteralsQueued += 1
            currentIndex += 1

    # Write any remaining queued literals (possibly none).
    if currentLiteralsQueued > 0:
        controlSection += bitstring.pack("uint:1", BIT_LITERAL)
        controlSection += bitstring.pack("uie", currentLiteralsQueued - 1)
        currentLiteralsQueued = 0

    # Assemble the output: header, data section, control section.
    output = bitstring.BitArray()
    output += bitstring.pack("uintle:16", len(inBytes))
    output += bitstring.pack("uintle:16", len(dataSection) + 2)
    output += dataSection
    # The first command is always literal, so we don't need to waste a bit saying so.
    output += controlSection[1:]

    # Return the compressed data.
    return output.tobytes()



# Open a file for reading and writing. If the file doesn't exist, create it.
# (Vanilla open() with mode "r+" raises an error if the file doesn't exist.)
def touchopen(filename, *args, **kwargs):
    fd = os.open(filename, os.O_RDWR | os.O_CREAT)
    return os.fdopen(fd, *args, **kwargs)



if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc < 2 or argc > 4:
        print("Usage: {0:s} <inFile> [outFile] [outOffset]".format(
            sys.argv[0]
        ))
        sys.exit(1)

    # Copy the arguments.
    inFile = sys.argv[1]
    outFile = None
    if argc == 3 or argc == 4:
        outFile = sys.argv[2]
    outOffset = 0
    if argc == 4:
        outOffset = int(sys.argv[3], 16)

    # Read the input file.
    with open(inFile, "rb") as inStream:
        inBytes = bytearray(inStream.read())

    # Compress the data.
    outBytes = compress(inBytes)

    # Write the compressed output, if appropriate.
    if outFile is not None:
        with touchopen(outFile, "r+b") as outStream:
            outStream.seek(outOffset)
            outStream.write(outBytes)
            lastOffset = outStream.tell()
            print("Last offset written, inclusive: {0:X}".format(
                lastOffset - 1
            ))

    # Report statistics on the data.
    print("Uncompressed size: 0x{0:X} ({0:d}) bytes".format(len(inBytes)))
    print("Compressed size: 0x{0:X} ({0:d}) bytes".format(len(outBytes)))
    print("Ratio: {0:f}".format(len(outBytes) / len(inBytes)))

    # Exit.
    sys.exit(0)

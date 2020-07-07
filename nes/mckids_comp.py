#!/usr/bin/env python3
#
# M.C. Kids Text Compressor
# Osteoclave
# 2012-11-16
#
# The compression format is described in the decompressor.
#
# This code uses python-bitstring:
# https://pypi.org/project/bitstring/

import os
import sys
import bitstring



def compress(inBytes, sourceArgSize, lengthArgSize):
    # Define some useful constants.
    BIT_PASTCOPY = 0
    BIT_LITERAL = 1

    # Prepare for compression.
    currentIndex = 0
    endIndex = len(inBytes)
    output = bitstring.BitArray()
    output += bitstring.pack("uint:4", sourceArgSize)
    output += bitstring.pack("uint:4", lengthArgSize)

    # Main compression loop.
    while currentIndex < endIndex:
        bestSource = 0
        bestLength = 0

        # Compare what's coming up to what we've most recently seen.
        searchLimit = min(
            currentIndex,
            (1 << sourceArgSize) - 1
        )
        for i in range(1, searchLimit):
            # Don't look too far ahead at what's coming up:
            # - No further than can be encoded in one command.
            # - Not past the end of the input.
            lookaheadLimit = min(
                (1 << lengthArgSize) - 1 + 3,
                endIndex - currentIndex
            )

            # Count how many sequential bytes match (possibly zero).
            currentLength = 0
            for j in range(lookaheadLimit):
                if inBytes[currentIndex - i + j] == inBytes[currentIndex + j]:
                    currentLength += 1
                else:
                    break

            # Keep track of the largest match we've seen.
            if currentLength > bestLength:
                bestSource = i
                bestLength = currentLength

        # Write the next command.
        if bestLength >= 3:
            output += bitstring.pack("uint:1", BIT_PASTCOPY)
            output += bitstring.pack(
                "uint:n=v", n = sourceArgSize, v = bestSource
            )
            output += bitstring.pack(
                "uint:n=v", n = lengthArgSize, v = bestLength - 3
            )
            currentIndex += bestLength
        else:
            output += bitstring.pack("uint:1", BIT_LITERAL)
            output += bitstring.pack("uint:8", inBytes[currentIndex])
            currentIndex += 1

    # Write the terminating bits.
    output += bitstring.pack("uint:1", BIT_PASTCOPY)
    output += bitstring.pack("uint:n=v", n = sourceArgSize, v = 0)
    output += bitstring.pack("uint:n=v", n = lengthArgSize, v = 0)

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
    compressedOptions = []
    for sourceArgSize in range(10, 12):
        for lengthArgSize in range(3, 6):
            print(
                "Compressing: {0:d},{1:d}".format(
                    sourceArgSize, lengthArgSize
                ),
                end=""
            )
            thisOption = compress(inBytes, sourceArgSize, lengthArgSize)
            print(" = {0:d} bytes".format(len(thisOption)))
            compressedOptions.append(thisOption)
    outBytes = min(compressedOptions, key=len)
    print("Done.")
    print()

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

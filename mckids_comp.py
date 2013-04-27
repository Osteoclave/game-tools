# M.C. Kids Text Compressor
# Written by Alchemic
# 2012 Nov 16
# 
# 
# 
# The format is described in greater detail in the decompressor.
# 
# This code uses python-bitstring version 2.2.0:
# http://code.google.com/p/python-bitstring/

from __future__ import division

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
    output += bitstring.pack('uint:4', sourceArgSize)
    output += bitstring.pack('uint:4', lengthArgSize)

    # Main compression loop.
    while currentIndex < endIndex:
        bestSource = 0
        bestLength = 0

        # Compare what's coming up to what we've most recently seen.
        searchLimit = min(
            currentIndex, 
            (1 << sourceArgSize) - 1
        )
        for i in xrange(1, searchLimit):
            # Don't look too far ahead at what's coming up:
            # - No further than can be encoded in one command.
            # - Not past the end of the input.
            lookaheadLimit = min(
                (1 << lengthArgSize) - 1 + 3,
                endIndex - currentIndex
            )

            # Count how many sequential bytes match (possibly zero).
            currentLength = 0
            for j in xrange(lookaheadLimit):
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
            output += bitstring.pack('uint:1', BIT_PASTCOPY)
            output += bitstring.pack('uint:n=v', n = sourceArgSize, v = bestSource)
            output += bitstring.pack('uint:n=v', n = lengthArgSize, v = bestLength - 3)
            currentIndex += bestLength
        else:
            output += bitstring.pack('uint:1', BIT_LITERAL)
            output += bitstring.pack('uint:8', inBytes[currentIndex])
            currentIndex += 1

    # Write the terminating bits.
    output += bitstring.pack('uint:1', BIT_PASTCOPY)
    output += bitstring.pack('uint:n=v', n = sourceArgSize, v = 0)
    output += bitstring.pack('uint:n=v', n = lengthArgSize, v = 0)

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

    # Open, read and close the input file.
    inStream = open(inFile, "rb")
    inBytes = bytearray(inStream.read())
    inStream.close()

    # Compress the data.
    compressedOptions = []
    for sourceArgSize in xrange(10, 12):
        for lengthArgSize in xrange(3, 6):
            sys.stdout.write("Compressing: {0:d},{1:d}".format(sourceArgSize, lengthArgSize))
            thisOption = compress(inBytes, sourceArgSize, lengthArgSize)
            sys.stdout.write(" = {0:d} bytes\n".format(len(thisOption)))
            compressedOptions.append(thisOption)
    outBytes = min(compressedOptions, key = len)
    sys.stdout.write("Done.\n\n")

    # Write the compressed output, if appropriate.
    if outFile is not None:
        # Mode r+b gives an error if the file doesn't already exist.
        open(outFile, "a").close()
        outStream = open(outFile, "r+b")
        outStream.seek(outOffset)
        outStream.write(outBytes)
        outStream.close()

    # Report statistics on the data.
    sys.stdout.write("Uncompressed size: 0x{0:X} ({0:d}) bytes\n".format(len(inBytes)))
    sys.stdout.write("Compressed size: 0x{0:X} ({0:d}) bytes\n".format(len(outBytes)))
    sys.stdout.write("Ratio: {0:f}\n".format(len(outBytes) / len(inBytes)))

    # Exit.
    sys.exit(0)

#!/usr/bin/env python3
#
# M.C. Kids Text Decompressor
# Osteoclave
# 2012-11-13
#
# A detailed description of the compression format:
#
#   - Compressed data is prefixed with a byte that specifies the
#     size of the pastcopy command's arguments. The high nybble
#     indicates the size of a pastcopy's source; the low nybble,
#     the size of a pastcopy's length.
#
#   - Following this is the compressed data itself: a stream of
#     bits that breaks down into two commands, "pastcopy" and
#     "literal". Bits are read from one byte at a time, most
#     significant to least (0x80, 0x40, 0x20 ... 0x01).
#
#        Pastcopy = [0 (S) (L)]
#        Literal  = [1 NNNNNNNN]
#
#   - Pastcopy copies data from the sliding window.
#      - The S argument indicates the data source, which is a
#        relative to the current position. 1 is the most-recently
#        decompressed byte, 2 is the byte before that, and so on.
#        If S is 0, we've reached the end of the compressed data.
#      - The L argument indicates how many bytes to copy. Since
#        it would be wasteful to copy a small number of bytes
#        (cheaper in bits to use literals), we actually copy
#        L+3 bytes.
#
#   - Literal is exactly what it says on the tin. The N argument
#     is one uncompressed byte.
#
# This code uses python-bitstring:
# https://pypi.org/project/bitstring/

import sys
import bitstring



def decompress(inBytes, startOffset=0):
    # Define some useful constants.
    BIT_PASTCOPY = 0
    BIT_LITERAL = 1

    # Prepare to read the compressed bytes.
    inStream = bitstring.ConstBitStream(bytes=inBytes)
    inStream.bytepos = startOffset

    # Allocate storage for the decompressed output.
    decomp = bytearray()

    # Read the first byte.
    # (It specifies the size of pastcopy's two arguments.)
    copySourceSize = inStream.read("uint:4")
    copyLengthSize = inStream.read("uint:4")

    # Main decompression loop.
    while True:
        nextCommand = inStream.read("uint:1")

        if nextCommand == BIT_PASTCOPY:
            # 0: Pastcopy case.
            copySource = inStream.read(copySourceSize).uint
            copyLength = inStream.read(copyLengthSize).uint
            copyLength += 3

            # A copy source of 0 indicates the end.
            if copySource == 0:
                break

            for i in range(copyLength):
                decomp.append(decomp[-copySource])

        elif nextCommand == BIT_LITERAL:
            # 1: Literal case.
            literalByte = inStream.read("uint:8")
            decomp.append(literalByte)

    # Calculate the end offset.
    inStream.bytealign()
    endOffset = inStream.bytepos

    # Return the decompressed data and end offset.
    return (decomp, endOffset)



if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc < 3 or argc > 4:
        print("Usage: {0:s} <inFile> <startOffset> [outFile]".format(
            sys.argv[0]
        ))
        sys.exit(1)

    # Copy the arguments.
    inFile = sys.argv[1]
    startOffset = int(sys.argv[2], 16)
    outFile = None
    if argc == 4:
        outFile = sys.argv[3]

    # Read the input file.
    with open(inFile, "rb") as inStream:
        inBytes = inStream.read()

    # Decompress the data.
    outBytes, endOffset = decompress(inBytes, startOffset)
    outSize = endOffset - startOffset

    # Write the decompressed output, if appropriate.
    if outFile is not None:
        with open(outFile, "wb") as outStream:
            outStream.write(outBytes)

    # Report statistics on the data.
    print("Last offset read, inclusive: {0:X}".format(endOffset - 1))
    print("Compressed size: 0x{0:X} ({0:d}) bytes".format(outSize))
    print("Uncompressed size: 0x{0:X} ({0:d}) bytes".format(len(outBytes)))
    print("Ratio: {0:f}".format(outSize / len(outBytes)))

    # Exit.
    sys.exit(0)

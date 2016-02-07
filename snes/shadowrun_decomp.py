# Shadowrun Decompressor
# Written by Alchemic
# 2011 Aug 25
# 
# 
# 
# A detailed description of the compression format:
# 
#   - Compressed data can be divided into three parts: the header, 
#     the data section, and the control section.
# 
#   - The header consists of two 16-bit integers. The first indicates 
#     the length of the decompressed data. The second points to the 
#     start of the control section, which is located at:
# 
#        (second integer's address) + (second integer's value)
# 
#   - For example, here's the header for the Oldtown Magic Shop's 
#     compressed drawing data (0x5F163):
# 
#        0x5F163  [8D 00] --> 0x008D
#        0x5F165  [6B 00] --> 0x006B
# 
#        There are 0x008D (141) bytes in the decompressed output.
#        The control section begins at 0x5F165 + 0x006B = 0x5F1D0.
# 
#   - The data section occupies all of the space after the header and 
#     before the control section. It is read sequentially by literal 
#     commands, which we will see in a moment.
# 
#   - The control section is a stream of bits used by the "literal" 
#     and "pastcopy" commands. The bits are read from one byte at a 
#     time, most significant to least (0x80, 0x40, 0x20 ... 0x01). 
#     The first command is always literal.
# 
#   - The literal command copies bytes from the data section to the 
#     decompressed output. The amount of bytes to copy is encoded 
#     using interleaved exponential-Golomb coding. ...Don't run away! 
#     It's basically alternating "stop" and "data" bits. Imagine an 
#     unwritten leading "1" and append the data bits to it until you 
#     read a stop of 1.
# 
#   - Some sample literals:
# 
#                       1 --> Copy  1 byte  (binary      1)
#                    00 1 --> Copy  2 bytes (binary     10)
#                    01 1 --> Copy  3 bytes (binary     11)
#                 00 00 1 --> Copy  4 bytes (binary    100)
#                 00 01 1 --> Copy  5 bytes (binary    101)
#                 01 00 1 --> Copy  6 bytes (binary    110)
#                 01 01 1 --> Copy  7 bytes (binary    111)
#              00 00 00 1 --> Copy  8 bytes (binary   1000)
#        01 00 01 00 00 1 --> Copy 52 bytes (binary 110100)
# 
#   - python-bitstring supports this coding, but starts counting from 
#     0 instead of 1, so we add 1 to each value we read.
# 
#   - If there is still data left to decompress after a literal, a 
#     pastcopy follows.
# 
#   - The pastcopy command consists of three parts.
#      - The first is the source: a sequence of bits of length N, 
#        where N = log2(number of bytes decompressed), indicating an 
#        absolute location to copy from.
#      - The second is the amount. Like the literal command, it uses 
#        interleaved exponential-Golomb coding. Add 2 to this amount 
#        once you have it. (3 here, because of python-bitstring.)
#      - The third is a single bit, indicating what the next command 
#        is: 0 for a literal, and 1 for another pastcopy.
# 
# 
# 
# This code uses python-bitstring:
# https://pypi.python.org/pypi/bitstring

from __future__ import print_function

import sys
import bitstring





def decompress(inBytes, startOffset=0):
    # Define some useful constants.
    BIT_LITERAL = 0
    BIT_PASTCOPY = 1

    # Prepare to read the compressed bytes.
    inStream = bitstring.ConstBitStream(bytes=inBytes)
    inStream.bytepos += startOffset

    # Allocate memory for the decompression process.
    decompSize = inStream.read('uintle:16')
    decomp = bytearray([0x00] * decompSize)
    decompPos = 0
    dataSize = inStream.read('uintle:16') - 2
    data = inStream.read('bytes:{0:d}'.format(dataSize))
    dataPos = 0

    # The first command is always literal.
    nextCommand = BIT_LITERAL

    # Main decompression loop.
    while True:

        # 0: Literal case.
        if nextCommand == BIT_LITERAL:

            # Read the number of bytes to copy.
            copyAmount = inStream.read('uie') + 1

            # Truncate the copy if it would exceed decompSize.
            if (decompPos + copyAmount) >= decompSize:
                copyAmount = decompSize - decompPos

            # Copy the bytes.
            decomp[decompPos:decompPos + copyAmount] = data[dataPos:dataPos + copyAmount]
            decompPos += copyAmount
            dataPos += copyAmount

            # If we're done, break.
            # Otherwise, a pastcopy follows.
            if decompPos == decompSize:
                break

        # 1: Pastcopy case.

        # Read the source.
        copySourceLength = decompPos.bit_length()
        copySource = inStream.read('uint:{0:d}'.format(copySourceLength))

        # Read the amount.
        copyAmount = inStream.read('uie') + 3

        # Truncate the copy if it would exceed decompSize.
        if (decompPos + copyAmount) >= decompSize:
            copyAmount = decompSize - decompPos

        # Copy the bytes.
        # The source and destination range might overlap, so copy one byte at a time.
        for i in range(copyAmount):
            decomp[decompPos] = decomp[copySource]
            decompPos += 1
            copySource += 1

        # If we're done, break.
        if decompPos == decompSize:
            break

        # Otherwise, find out what the next command is.
        nextCommand = inStream.read('bool')

    # Calculate the end offset.
    inStream.bytealign()
    endOffset = inStream.bytepos

    # Return the decompressed data and end offset.
    return (decomp, endOffset)





if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc < 3 or argc > 4:
        print("Usage: {0:s} <inFile> <startOffset> [outFile]".format(sys.argv[0]))
        sys.exit(1)

    # Copy the arguments.
    inFile = sys.argv[1]
    startOffset = int(sys.argv[2], 16)
    outFile = None
    if argc == 4:
        outFile = sys.argv[3]

    # Open, read and close the input file.
    inStream = open(inFile, "rb")
    inBytes = inStream.read()
    inStream.close()

    # Decompress the data.
    outBytes, endOffset = decompress(inBytes, startOffset)

    # Write the decompressed output, if appropriate.
    if outFile is not None:
        outStream = open(outFile, "wb")
        outStream.write(outBytes)
        outStream.close()

    # Report the size of the compressed data and last offset.
    print("Original compressed size: 0x{0:X} ({0:d}) bytes".format(endOffset - startOffset))
    print("Last offset read, inclusive: {0:X}".format(endOffset - 1))

    # Exit.
    sys.exit(0)

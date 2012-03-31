# Shadowrun Decompressor
# Written by Alchemic
# 2011 Aug 25
# 
# 
# 
# A detailed description of the compression format:
# 
#   - Compressed data consists of three parts: the header, the data 
#     section, and the control section.
# 
#   - The header consists of two 16-bit integers. The first contains 
#     the length of the data once decompressed. The second indicates 
#     where the control section starts (this integer's address plus 
#     its value).
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
#   - The control section consists of a stream of bits that break 
#     down into two commands, "literal" and "pastcopy". The bits are 
#     read from one byte at a time, most significant to least (0x80, 
#     0x40, 0x20 ... 0x01). The first command is always literal.
# 
#   - The literal command copies a specified number of bytes 
#     from the data section into the decompressed output.
#     To read a literal:
#      - Set the initial amount to 1.
#      - Read one bit.
#      - If this bit is 0, the literal continues. Shift the amount 
#        left once, add this bit to the amount, and return to the 
#        previous step.
#      - If this bit is 1, the literal is done. Copy the specified 
#        amount of bytes from the data section into the output.
# 
#   - Some sample literals:
# 
#                  1 --> Copy  1 byte  (binary      1)
#                001 --> Copy  2 bytes (binary     10)
#                011 --> Copy  3 bytes (binary     11)
#              00001 --> Copy  4 bytes (binary    100)
#              00011 --> Copy  5 bytes (binary    101)
#              01001 --> Copy  6 bytes (binary    110)
#              01011 --> Copy  7 bytes (binary    111)
#            0000001 --> Copy  8 bytes (binary   1000)
#        01000100001 --> Copy 52 bytes (binary 110100)
# 
#   - If there is still data left to decompress after a literal, 
#     a pastcopy follows.
# 
#   - The pastcopy command consists of three parts.
#      - The first is the source: an uninterrupted sequence of bits
#        of length N, where N = log2(number of bytes decompressed),
#        indicating where to copy from.
#      - The second is the amount, which is encoded using the same 
#        scheme as the amount in the literal case. Add 2 to this 
#        amount once you have it.
#      - The third is a single bit, indicating what the next command
#        is: 0 for a literal, and 1 for another pastcopy.
# 
# 
# 
# This code uses python-bitstring version 2.2.0:
# http://code.google.com/p/python-bitstring/

import sys
import bitstring





def decompress(romFile, startOffset):
    # Define some useful constants.
    BIT_LITERAL = 0
    BIT_PASTCOPY = 1

    # Open the ROM.
    romStream = bitstring.ConstBitStream(filename=romFile)
    romStream.bytepos += startOffset

    # Allocate memory for the decompression process.
    decompSize = romStream.read('uintle:16')
    decomp = bytearray([0x00] * decompSize)
    decompPos = 0
    dataSize = romStream.read('uintle:16') - 2
    data = romStream.read('bytes:{0:d}'.format(dataSize))
    dataPos = 0

    # The first command is always literal.
    nextCommand = BIT_LITERAL

    # Main decompression loop.
    while True:

        # 0: Literal case.
        if nextCommand == BIT_LITERAL:

            # Read the number of bytes to copy.
            copyAmount = 1
            stopBit = romStream.read('bool')
            while stopBit == False:
                copyAmount <<= 1
                dataBit = int(romStream.read('bool'))
                copyAmount += dataBit
                stopBit = romStream.read('bool')

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
        copySourceLength = len(bin(decompPos).lstrip('0b'))
        copySource = romStream.read('uint:{0:d}'.format(copySourceLength))

        # Read the amount.
        copyAmount = 1
        stopBit = romStream.read('bool')
        while stopBit == False:
            copyAmount <<= 1
            dataBit = int(romStream.read('bool'))
            copyAmount += dataBit
            stopBit = romStream.read('bool')
        copyAmount += 2

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
        nextCommand = romStream.read('bool')

    # Calculate the end offset.
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

    # Write the decompressed output, if appropriate.
    if outFile is not None:
        outStream = open(outFile, "wb")
        outStream.write(outBytes)
        outStream.close()

    # Report the size of the compressed data and last offset.
    sys.stdout.write("Original compressed size: 0x{0:X} ({0:d}) bytes\n".format(endOffset - startOffset))
    sys.stdout.write("Last offset read, inclusive: {0:X}\n".format(endOffset - 1))

    # Exit.
    sys.exit(0)

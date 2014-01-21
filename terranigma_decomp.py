# Terranigma Decompressor
# Written by Alchemic
# 2011 Sep 10
# 
# 
# 
# A detailed description of the compression format:
# 
#   - Compressed data is prefixed with a four-byte header:
#      * uint8   Mystery byte
#      * uint16  Length of the data, once decompressed
#      * uint8   First byte of the decompressed output
# 
#   - Following this is the compressed data itself, which is 
#     comprised of blocks. Each block contains one control byte 
#     and a variable number of additional bytes, which act as
#     arguments for the control byte's commands.
# 
#   - The control byte is read from the most significant bit to 
#     the least (0x80, 0x40, 0x20 ... 0x01). Commands may be 
#     split across multiple control bytes.
# 
#   - The commands:
# 
#        Literal    (1)    = [NNNNNNNN]
#        Pastcopy A (01)   = [SSSSSSSS SSSSSLLL]          <-- Normal
#        Pastcopy A (01)   = [SSSSSSSS SSSSSLLL XXXXXXXX] <-- Zero-length case
#        Pastcopy B (00xx) = [SSSSSSSS]
# 
#   - Literal is exactly what it says on the tin. The N argument 
#     is one uncompressed byte.
# 
#   - Pastcopy A reads a BIG-ENDIAN 16-bit integer. The high 13
#     bits indicate the pastcopy source, and the low 3 indicate
#     the pastcopy length.
# 
#     e.g. Pastcopy A with [FF C5] as the argument word:
# 
#          Source = [   11111 11111000]
#          This is sign-extended to a full 16 bits (OR 0xE000):
#          Source = [11111111 11111000]
#                 = -8
# 
#          Length = [101] = 5
#          Add 2 to the length
#          Length = 7
# 
#   - Pastcopy A's behaviour changes if the given length is 0.
#     Read an additional byte - if it's nonzero, add 1 to it
#     to get the new pastcopy length; and if it's zero, we've
#     reached the end of the compressed data.
# 
#   - Pastcopy B reads an 8-bit integer, which indicates the 
#     pastcopy source. The length depends on the last two bits
#     of the actual command.
# 
#     e.g. Pastcopy B via (0010), [F0]
# 
#          Source = [         11110000]
#          This is sign-extended to a full 16 bits (OR 0xFF00):
#          Source = [11111111 11110000]
#                 = -16
# 
#          Length = (10) = 2
#          Add 2 to the length
#          Length = 4
# 
# 
# 
# This program currently only decompresses data with a mystery 
# byte of 0x00 or 0x01. Anecdotally, this covers most (all?) of
# Terranigma's compressed data.
# 
# 
# 
# This code uses python-bitstring version 2.2.0:
# http://code.google.com/p/python-bitstring/

import sys
import bitstring





def decompress(romFile, startOffset):
    # Open the ROM.
    romStream = bitstring.ConstBitStream(filename=romFile)
    romStream.bytepos += startOffset

    # Header - Mystery byte
    mysteryByte = romStream.read('uint:8')
    if (mysteryByte != 0x00) and (mysteryByte != 0x01):
        return (None, startOffset)

    # Header - Size of the decompressed data
    decompSize = romStream.read('uintle:16')
    decomp = bytearray([0x00] * decompSize)
    decompPos = 0
    controlByte = 0x00
    controlMask = 0x00

    # Header - First byte of the decompressed output
    headerLiteral = romStream.read('uint:8')
    decomp[decompPos] = headerLiteral
    decompPos += 1

    # Main decompression loop.
    while True:
        # Get the next control bit
        if controlMask == 0x00:
            controlByte = romStream.read('uint:8')
            controlMask = 0x80
        nextBit = bool(controlByte & controlMask)
        controlMask >>= 1

        # Determine the next command
        if nextBit == True:
            # (1) - Literal case
            literalByte = romStream.read('uint:8')
            decomp[decompPos] = literalByte
            decompPos += 1

        else:
            # (0) - Pastcopy cases
            if controlMask == 0x00:
                controlByte = romStream.read('uint:8')
                controlMask = 0x80
            nextBit = bool(controlByte & controlMask)
            controlMask >>= 1

            copySource = 0
            copyLength = 0

            if nextBit == True:
                # (01) - Pastcopy A case

                # Copy source
                copySource = romStream.read('uint:13')
                copySource -= 0x2000

                # Copy length (remember the zero-length case)
                copyLength = romStream.read('uint:3')
                if copyLength == 0:
                    copyLength = romStream.read('uint:8')
                    if copyLength == 0:
                        break
                    copyLength += 1
                else:
                    copyLength += 2

            else:
                # (00xx) - Pastcopy B case
                # Read the command's argument bits
                copyLength = 0

                # This code would be much cleaner if command bits could not be 
                # split across different control bytes. Sadly, they can.
                if controlMask == 0x00:
                    controlByte = romStream.read('uint:8')
                    controlMask = 0x80
                nextBit = bool(controlByte & controlMask)
                controlMask >>= 1
                if nextBit == True:
                    copyLength += 2

                if controlMask == 0x00:
                    controlByte = romStream.read('uint:8')
                    controlMask = 0x80
                nextBit = bool(controlByte & controlMask)
                controlMask >>= 1
                if nextBit == True:
                    copyLength += 1

                copyLength += 2

                # Copy source
                copySource = romStream.read('uint:8')
                copySource -= 0x100

            # Truncate copies that would exceed "decompSize" bytes
            if (decompPos + copyLength) >= decompSize:
                copyLength = decompSize - decompPos

            # Copy the past data
            for i in range(copyLength):
                decomp[decompPos] = decomp[decompPos + copySource]
                decompPos += 1

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

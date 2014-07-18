# E.V.O.: Search for Eden Decompressor
# Written by Alchemic
# 2011 Jul 22
# 
# 
# 
# A terse description of the compression format:
# 
#    LZSS with a 4096-byte sliding window. Depending on a header 
#    byte, it is possible to copy 0-397 previously-seen bytes. 
#    References to past data are relative to the current output 
#    position. Control bits (which indicate whether the following 
#    commands are pastcopies or literals) are grouped into eights 
#    and packed into their own bytes. Compressed data is padded 
#    to fit in an even number of bytes. (Word-aligned data?)
# 
# 
# 
# In greater detail:
# 
#   - Compressed data is prefixed with a three-byte header: an 
#     8-bit integer related to the size of pastcopies, and a 
#     16-bit integer indicating the length of the data once 
#     decompressed.
# 
#   - Following this is the compressed data, which is comprised
#     of blocks. Each block contains one control byte and eight 
#     commands. The last block may have fewer than eight.
# 
#   - If the last block DOES have eight commands, a null control 
#     byte (0x00) will follow. I think it's just a leftover of 
#     how the programmers' compressor worked ("Write a control
#     byte after writing eight commands, update its bits as you
#     write the next eight"). Since there's no more data, it
#     serves no purpose except to waste 1-2 bytes of storage.
# 
#   - The control byte indicates which of the next eight commands
#     is pastcopy (zero) or literal (one). The control byte is
#     read one bit at a time, least significant to most (0x01, 
#     0x02, 0x04 ... 0x80).
# 
#   - The commands:
# 
#        Pastcopy (0) = [SSSSSSSS LLLLSSSS]          <-- Normal
#        Pastcopy (0) = [SSSSSSSS LLLLSSSS PPPPPPPP] <-- Extended
#        Literal  (1) = [NNNNNNNN]
# 
#   - Let's start with pastcopies.
#     Look at the first two argument bytes as a 16-bit word.
# 
#   - PASTCOPY SOURCE
#     The low twelve bits of this word (0x.SSS) are the source.
#     To get the actual source address, add one to the source
#     value, and subtract this number from the current writing
#     location. So a source of 0 gets the previous byte, 1 gets 
#     the byte before that, and so on.
# 
#   - PASTCOPY LENGTH
#     The high four bits of this word (0xL...) are the length.
#     If the length is 0xF and the 0x80 bit of the first byte of 
#     the header is set, it's an extended pastcopy. Read another 
#     byte and add its value to the length.
#     Finally, regardless of normal or extended type, add
#       (First header byte & 0x7F)
#     to the length.
# 
#   - The maximum length of a pastcopy:
#         F = Maximum possible original L value
#      + FF = Maximum possible extended pastcopy value
#      + 7F = Maximum result of (First header byte & 0x7F)
#     -----
#     0x18D = 397 bytes
# 
#   - Literal is exactly what it says on the tin. The N argument 
#     is one uncompressed byte.

import sys
import struct





def decompress(romFile, startOffset):
    # Open the ROM.
    romStream = open(romFile, "rb")
    romStream.seek(startOffset)

    # Prepare for decompression.
    pastcopyByte = struct.unpack("<B", romStream.read(1))[0]
    decompSize = struct.unpack("<H", romStream.read(2))[0]
    decomp = bytearray([0x00] * decompSize)
    decompPos = 0
    controlByte = struct.unpack("<B", romStream.read(1))[0]
    controlMask = 0x01

    # Main decompression loop.
    while decompPos < decompSize:
        nextCommand = bool(controlByte & controlMask)

        if nextCommand == False:
            # 0: Pastcopy case.
            pastCopy = struct.unpack("<H", romStream.read(2))[0]

            # Copy source
            copySource = pastCopy & 0x0FFF
            copySource += 1

            # Copy length
            copyLength = pastCopy & 0xF000
            copyLength >>= 12
            if (copyLength == 0xF) and bool(pastcopyByte & 0x80):
                copyLength += struct.unpack("<B", romStream.read(1))[0]
            copyLength += (pastcopyByte & 0x7F)

            # Truncate copies that would exceed "decompSize" bytes.
            if (decompPos + copyLength) >= decompSize:
                copyLength = decompSize - decompPos

            # Copy the past data.
            for i in range(copyLength):
                decomp[decompPos] = decomp[decompPos - copySource]
                decompPos += 1

        else:
            # 1: Literal case.
            decomp[decompPos] = struct.unpack("<B", romStream.read(1))[0]
            decompPos += 1

        # Prepare to handle the next control bit.
        controlMask <<= 1
        if controlMask > 0x80:
            controlByte = struct.unpack("<B", romStream.read(1))[0]
            controlMask = 0x01

    # Calculate the end offset.
    # Compressed data is padded to fit in an even number of bytes.
    endOffset = romStream.tell()
    if ((endOffset - startOffset) % 2) == 1:
        endOffset += 1

    # Close the ROM.
    romStream.close()

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

# M.C. Kids Text Decompressor
# Written by Alchemic
# 2012 Nov 13
# 
# 
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
# 
# 
# This code uses python-bitstring version 2.2.0:
# http://code.google.com/p/python-bitstring/

import sys
import bitstring





def decompress(romFile, startOffset):
    # Define some useful constants.
    BIT_PASTCOPY = 0
    BIT_LITERAL = 1

    # Open the ROM.
    romStream = bitstring.ConstBitStream(filename=romFile)
    romStream.bytepos += startOffset

    # Allocate storage for the decompressed output.
    decomp = bytearray()

    # Read the first byte.
    # (It specifies the size of pastcopy's two arguments.)
    copySourceSize = romStream.read('uint:4')
    copyLengthSize = romStream.read('uint:4')

    # Main decompression loop.
    while True:
        nextCommand = romStream.read('bool')

        if nextCommand == BIT_PASTCOPY:
            # 0: Pastcopy case.
            copySource = romStream.read(copySourceSize).uint
            copyLength = romStream.read(copyLengthSize).uint
            copyLength += 3

            # A copy source of 0 indicates the end.
            if copySource == 0:
                break
            
            for i in xrange(copyLength):
                decomp.append(decomp[-copySource])

        elif nextCommand == BIT_LITERAL:
            # 1: Literal case.
            literalByte = romStream.read('uint:8')
            decomp.append(literalByte)

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

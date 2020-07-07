#!/usr/bin/env python3
#
# Dragon Warrior IV Text Dumper
# Osteoclave
# 2012-02-26
#
# This code uses python-bitstring:
# https://pypi.org/project/bitstring/

import sys
import bitstring



# Define the dictionary.
dictHuffman = {
    "000"                : "e",
    "0010"               : "s",
    "0011"               : "n",
    "010000"             : "f",
    "010001000"          : "z",
    "010001001"          : "<PAUSE>",
    "01000101"           : "W",
    "010001100"          : "K",
    "0100011010000"      : "J",
    "0100011010001"      : "Q",
    "0100011010010"      : "<UNKNOWN_0100011010010>",
    "0100011010011"      : "1",
    "01000110101"        : "<S>",
    "0100011011"         : "<NEWLINE>",
    "01000111"           : "H",
    "01001"              : "u",
    "0101"               : "a",
    "0110000"            : ".'",
    "01100010"           : "<NAME>",
    "01100011"           : "<PROMPT>",
    "011001000"          : "E",
    "011001001"          : "M",
    "011001010"          : "N",
    "01100101100"        : "<AMOUNT>",
    "01100101101"        : "F",
    "0110010111"         : "x",
    "0110011"            : "k",
    "011010"             : "w",
    "0110110"            : ", ",
    "01101110000"        : "<ITEM>",
    "011011100010"       : "V",
    "0110111000110000"   : "X",
    "0110111000110001"   : "<UNKNOWN_0110111000110001>",
    "011011100011001"    : "<UNKNOWN_011011100011001>",
    "01101110001101"     : "5",
    "0110111000111"      : "-",
    "0110111001"         : "L",
    "011011101"          : "B",
    "011011110"          : "C",
    "0110111110"         : "j",
    "0110111111"         : "<UNKNOWN_0110111111>",
    "0111"               : "t",
    "10000"              : "l",
    "100010"             : "<END>",
    "100011"             : "c",
    "1001"               : "o",
    "101000"             : "g",
    "1010010"            : "v",
    "101001100"          : "A",
    "101001101"          : "P",
    "10100111"           : "?",
    "10101000"           : "'",
    "1010100100"         : "G",
    "10101001010"        : "q",
    "1010100101100"      : "<UNKNOWN_1010100101100>",
    "101010010110100"    : "4",
    "101010010110101"    : "<DISAPPEAR>",
    "1010100101101100"   : "7",
    "10101001011011010"  : "<UNKNOWN_10101001011011010>",
    "101010010110110110" : "<UNKNOWN_101010010110110110>",
    "101010010110110111" : "8",
    "1010100101101110"   : "2",
    "1010100101101111"   : "3",
    "1010100101110"      : "<STRING>",
    "101010010111100"    : "<SPELL>",
    "101010010111101"    : "<UNKNOWN_101010010111101>",
    "101010010111110"    : "6",
    "101010010111111"    : "<UNKNOWN_101010010111111>",
    "101010011"          : "Y",
    "1010101"            : "!",
    "101011"             : "y",
    "1011000"            : "I",
    "1011001"            : "b",
    "101101"             : "m",
    "10111"              : "h",
    "110"                : " ",
    "11100"              : "i",
    "11101000"           : "...",
    "1110100100"         : "R",
    "1110100101"         : "D",
    "111010011"          : ":",
    "11101010"           : "<NEWPARAGRAPH>'",
    "11101011000"        : "Z",
    "111010110010"       : "U",
    "111010110011"       : "0",
    "1110101101"         : "O",
    "111010111"          : "S",
    "1110110"            : "'",
    "1110111"            : ".<NEWLINE>",
    "11110000"           : "'",
    "11110001"           : "T",
    "1111001"            : "p",
    "111101"             : "d",
    "11111"              : "r",
}



def decompress(inBits, startOffset, numberOfLines):
    # Prepare for decompression.
    inBits.bytepos = startOffset
    outList = []

    # Main decompression loop.
    for i in range(numberOfLines):
        # Record the location where the current line starts.
        lineStartLoc = "{0:5X}.{1:d}".format(
            inBits.pos // 8,
            inBits.pos % 8
        )

        # Read the current line.
        nextLine = ""
        while not nextLine.endswith("<END>"):
            # Read the next key.
            nextKey = ""
            while nextKey not in dictHuffman:
                nextKey += str(inBits.read("uint:1"))
            nextLine += dictHuffman[nextKey]

        # Record the location where the current line ends.
        lineEndLoc = "{0:5X}.{1:d}".format(
            (inBits.pos - 1) // 8,
            (inBits.pos - 1) % 8
        )

        # Add the current line to the output list.
        outList.append((nextLine, lineStartLoc, lineEndLoc))

    # Return the decompressed lines.
    return outList



if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc != 2:
        print("Usage: {0:s} <romFile>".format(sys.argv[0]))
        sys.exit(1)

    # Copy the argument.
    romFile = sys.argv[1]

    # Read the input file.
    with open(romFile, "rb") as romStream:
        romBytes = romStream.read()

    # Create a byte array containing the game's text.
    inBytes = bytearray()
    inBytes += romBytes[0x10:0x3FE8]
    inBytes += romBytes[0x4010:0x7FE8]
    inBytes += romBytes[0x8010:0xBFE8]
    inBytes += romBytes[0xC010:0xFFE8]
    inBytes += romBytes[0x10010:0x13FE8]
    inBytes += romBytes[0x68010:0x6BFE8]
    inBytes += romBytes[0x6F79A:0x6FFE5]

    # Make a bitstream from the byte array.
    inBits = bitstring.ConstBitStream(inBytes)

    # Define the start offsets.
    # 58961 to 58A10 = Pointers to compressed text
    startOffsets = [
        0x00000, 0x001B6, 0x003B5, 0x005D6, 0x00813, 0x00915, 0x00B13, 0x00D1A,
        0x00F3B, 0x0115D, 0x013D7, 0x015F5, 0x017D8, 0x019D7, 0x01CB6, 0x020C7,
        0x023F2, 0x02701, 0x02A8D, 0x02D71, 0x02FC2, 0x032D2, 0x03BD8, 0x03FFE,
        0x046E0, 0x04BF3, 0x0515E, 0x056ED, 0x05BEF, 0x06229, 0x06661, 0x06C20,
        0x0714C, 0x075E4, 0x079F4, 0x07E0D, 0x08393, 0x0874C, 0x08B5E, 0x08F44,
        0x093E5, 0x09807, 0x09D02, 0x0A0A2, 0x0A4D1, 0x0A938, 0x0AD04, 0x0B15F,
        0x0B6EA, 0x0BCA3, 0x0C2C4, 0x0C73D, 0x0CD0F, 0x0D4DB, 0x0DC1A, 0x0E2C1,
        0x0E865, 0x0EDEF, 0x0F254, 0x0F704, 0x0FCB3, 0x1012F, 0x10697, 0x10C36,
        0x11146, 0x11841, 0x11E7F, 0x124D0, 0x12B46, 0x131BF, 0x13864, 0x13FA9,
        0x14622, 0x14CAD, 0x151A4, 0x15765, 0x15F21, 0x16516, 0x16A7A, 0x16FD0,
        0x1756D, 0x17A95, 0x1821A, 0x186FB,
    ]

    # Dump the text.
    outList = None
    for startOffset in startOffsets:
        # Quick ugly last-block (0x186FB) detection.
        # The last block is short: 4 lines instead of the usual 32.
        if startOffset == 0x186FB:
            outList = decompress(inBits, startOffset, 4)
        else:
            outList = decompress(inBits, startOffset, 32)

        for currentLine in outList:
            print("{1:s} to {2:s}    {0:s}".format(*currentLine))
        print()

    # Exit.
    sys.exit(0)

#!/usr/bin/env python3
#
# Dragon Warrior II Text Dumper
# Osteoclave
# 2012-02-11
#
# This code uses python-bitstring:
# https://pypi.org/project/bitstring/

import sys
import bitstring



# Define the dictionaries.
#   B44B to B49A = Text compression word-length nybbles
#   B49B to B686 = Text compression words
#
# Text control codes:
#   [F2] = <S>
#   [F3] = ?
#   [F4] = ?
#   [F5] = <AMOUNT>
#   [F6] = <SPELL>
#   [F7] = <ITEM>
#   [F8] = <NAME>
#   [F9] = <STRING>
#
#   [FB] = <PROMPT>
#   [FC] = <END>
#   [FD] = ? <-- Related to menus?
#   [FE] = <NEWLINE>
#   [FF] = ?

dict_Main = {
    0x00 : "<END>",
    0x01 : ".<END>",
    0x02 : "?'[FD][FD]<END>",
    0x03 : ".'<END>",
    0x04 : "[FF]",
    0x05 : "y",
    0x06 : "c",
    0x07 : "o",
    0x08 : "d",
    0x09 : "e",
    0x0A : "f",
    0x0B : "g",
    0x0C : "h",
    0x0D : "i",
    0x0E : "j",
    0x0F : " ",
    0x10 : "l",
    0x11 : "m",
    0x12 : "n",
    0x13 : "<NEWLINE>",
    0x14 : ".'",
    0x15 : "'",
    0x16 : "r",
    0x17 : "s",
    0x18 : "t",
    0x19 : "u",
    0x1A : "a",
    0x1B : "w",
    0x1C : "[C0]",
    0x1D : "[C1]",
    0x1E : "[C2]",
    0x1F : "[C3]",
}

dict_C0 = {
    0x00 : "A",
    0x01 : "B",
    0x02 : "Ca",
    0x03 : "D",
    0x04 : "E",
    0x05 : "F",
    0x06 : "G",
    0x07 : "H",
    0x08 : "I",
    0x09 : "J",
    0x0A : "King",
    0x0B : "L",
    0x0C : "Moonbrooke",
    0x0D : "N",
    0x0E : "O",
    0x0F : "<ITEM>",
    0x10 : "The ",
    0x11 : "Rhone ",
    0x12 : "S",
    0x13 : ";",
    0x14 : "U",
    0x15 : "\"",
    0x16 : "Water Flying Cl",
    0x17 : "C",
    0x18 : "Y",
    0x19 : "Z",
    0x1A : "x",
    0x1B : "Village ",
    0x1C : "z",
    0x1D : "<STRING>",
    0x1E : "\"",
    0x1F : "K",
}

dict_C1 = {
    0x00 : "v",
    0x01 : "q",
    0x02 : "'<PROMPT><NEWLINE>",
    0x03 : "R",
    0x04 : ".",
    0x05 : "[FD][FD]",
    0x06 : "P",
    0x07 : "b",
    0x08 : "T",
    0x09 : "!",
    0x0A : "<SUN>",
    0x0B : "<STAR>",
    0x0C : "<MOON>",
    0x0D : "W",
    0x0E : "k",
    0x0F : "p",
    0x10 : "?",
    0x11 : ",",
    0x12 : "[F4]",
    0x13 : "....",
    0x14 : ":",
    0x15 : "'",
    0x16 : "-",
    0x17 : "'",
    0x18 : "<SPELL>",
    0x19 : "[F3]",
    0x1A : " ",
    0x1B : "<PROMPT>",
    0x1C : "M",
    0x1D : "<NAME>",
    0x1E : "<AMOUNT>",
    0x1F : "[FD]",
}

dict_C2 = {
    0x00 : "Thou hast",
    0x01 : "hest",
    0x02 : "Midenhall",
    0x03 : "hou ",
    0x04 : " of ",
    0x05 : " is ",
    0x06 : " thou has",
    0x07 : " and ",
    0x08 : "to th",
    0x09 : " thee",
    0x0A : "ast",
    0x0B : " do",
    0x0C : "hat ",
    0x0D : " shall ",
    0x0E : " was ",
    0x0F : "hou has",
    0x10 : "d the",
    0x11 : " has ",
    0x12 : "gon",
    0x13 : ".<PROMPT><NEWLINE>",
    0x14 : " have ",
    0x15 : "come to ",
    0x16 : "ing",
    0x17 : " hast",
    0x18 : "ost thou",
    0x19 : "this",
    0x1A : " of the ",
    0x1B : "Hargon",
    0x1C : "in the ",
    0x1D : "thing",
    0x1E : "he ",
    0x1F : " with",
}

dict_C3 = {
    0x00 : "reasure ",
    0x01 : "'Hast ",
    0x02 : "Erdrick",
    0x03 : "come",
    0x04 : "ere is ",
    0x05 : "Welcome ",
    0x06 : "rince",
    0x07 : " great",
    0x08 : "arr",
    0x09 : " for th",
    0x0A : "piece<S> of gold",
    0x0B : ".'<PROMPT><NEWLINE>",
    0x0C : "But ",
    0x0D : "here",
    0x0E : "can ",
    0x0F : "ove",
    0x10 : "hee",
    0x11 : "not",
    0x12 : "for",
    0x13 : "one",
    0x14 : " any",
    0x15 : " to ",
    0x16 : "descendant",
    0x17 : "Roge Fastfinger",
    0x18 : "all",
    0x19 : "thy",
    0x1A : "'W",
    0x1B : "thank thee",
    0x1C : " it",
    0x1D : " tha",
    0x1E : " thou ",
    0x1F : " the",
}



def decompress(inBits, startOffset, numberOfLines):
    # Prepare for decompression.
    inBits.bytepos = startOffset
    outList = []

    # Main decompression loop.
    for i in range(numberOfLines):
        # Record the location where the current line starts.
        lineStartLoc = "{0:4X}.{1:d}".format(
            inBits.pos // 8,
            inBits.pos % 8
        )

        # Read the current line.
        nextLine = ""
        while not nextLine.endswith("<END>"):
            indice = inBits.read("uint:5")
            if indice < 0x1C:
                nextLine += dict_Main[indice]
            elif indice == 0x1C:
                subIndice = inBits.read("uint:5")
                nextLine += dict_C0[subIndice]
            elif indice == 0x1D:
                subIndice = inBits.read("uint:5")
                nextLine += dict_C1[subIndice]
            elif indice == 0x1E:
                subIndice = inBits.read("uint:5")
                nextLine += dict_C2[subIndice]
            elif indice == 0x1F:
                subIndice = inBits.read("uint:5")
                nextLine += dict_C3[subIndice]

        # Record the location where the current line ends.
        lineEndLoc = "{0:4X}.{1:d}".format(
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
    inBytes += romBytes[0x14010:0x17FE7]
    inBytes += romBytes[0xB7C2:0xBE10]

    # Make a bitstream from the byte array.
    inBits = bitstring.ConstBitStream(inBytes)

    # Define the start offsets.
    # B762 to B7C1 = Pointers to compressed text
    startOffsets = [
        0x0000, 0x00B3, 0x0177, 0x029B, 0x03D6, 0x0520, 0x0628, 0x080D,
        0x0CEF, 0x0EF0, 0x0EFA, 0x0F04, 0x0F0E, 0x0F18, 0x0F22, 0x0F2C,
        0x0F36, 0x103F, 0x1143, 0x129C, 0x13F9, 0x151E, 0x16AB, 0x17EF,
        0x1941, 0x1ADC, 0x1D0B, 0x1E94, 0x2051, 0x205B, 0x2065, 0x206F,
        0x2079, 0x22AF, 0x267E, 0x2978, 0x2C4A, 0x2F17, 0x3123, 0x32EF,
        0x353E, 0x3761, 0x394F, 0x3BC3, 0x3DDA, 0x3FAE, 0x41A3, 0x43BC,
    ]

    # Dump the text.
    for startOffset in startOffsets:
        outList = decompress(inBits, startOffset, 16)
        for currentLine in outList:
            print("{1:s} to {2:s}    {0:s}".format(*currentLine))
        print()

    # Exit.
    sys.exit(0)

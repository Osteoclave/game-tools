# Dragon Warrior II Text Dumper
# Written by Alchemic
# 2012 Feb 11
# 
# 
# 
# The 0x17FBE text block is split by a bank boundary.
# The text continues up to the last (0x01) bit of 17FE6, then 
# resumes with the first (0x80) bit of B7C2.
# 
# 
# 
# This code uses python-bitstring version 2.2.0:
# http://code.google.com/p/python-bitstring/

import sys
import bitstring



def decompress(romFile, startOffset):
    # Define the dictionaries.
    # B44B to B49A = Text compression word lengths
    # B49B to B686 = Text compression words

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
      0x13 : "\n",
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
      0x1F : "[C3]"
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
      0x1D : "[F9]",
      0x1E : "\"",
      0x1F : "K"
    }

    dict_C1 = {
      0x00 : "v",
      0x01 : "q",
      0x02 : "'<PROMPT>\n",
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
      0x1F : "[FD]"
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
      0x13 : ".<PROMPT>\n",
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
      0x1F : " with"
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
      0x0B : ".'<PROMPT>\n",
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
      0x1F : " the"
    }

    # Open the ROM.
    romStream = bitstring.ConstBitStream(filename=romFile)
    romStream.bytepos = startOffset

    # Prepare for decompression.
    outString = "### Start: {0:X} ###\n\n".format(romStream.bytepos)

    # Main decompression loop.
    for i in range(16):
        # Output the current line's start address (down to the bit)
        outString += "{0:X}.{1:d}\n".format(
          romStream.pos / 8, 
          7 - (romStream.pos % 8)
        )

        # Read the current line
        nextLine = ""
        while not nextLine.endswith("<END>"):
            indice = romStream.read('uint:5')
            if indice < 0x1C:
                nextLine += dict_Main[indice]
            elif indice == 0x1C:
                subIndice = romStream.read('uint:5')
                nextLine += dict_C0[subIndice]
            elif indice == 0x1D:
                subIndice = romStream.read('uint:5')
                nextLine += dict_C1[subIndice]
            elif indice == 0x1E:
                subIndice = romStream.read('uint:5')
                nextLine += dict_C2[subIndice]
            elif indice == 0x1F:
                subIndice = romStream.read('uint:5')
                nextLine += dict_C3[subIndice]

        # Truncate the <END> marker and output the line
        nextLine = nextLine[:-5]
        outString += nextLine
        outString += "\n\n"

    # Report the last byte read.
    romStream.bytealign()
    outString += "### End, inclusive: {0:X} ###\n".format(romStream.bytepos - 1)

    # Return the decompressed text.
    return outString





if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc != 2:
        sys.stdout.write("Usage: ")
        sys.stdout.write("{0:s} ".format(sys.argv[0]))
        sys.stdout.write("<romFile>\n")
        sys.exit(1)

    # Copy the arguments.
    romFile = sys.argv[1]

    # Define the start offsets.
    # B762 to B7C1 = Pointers to compressed text
    startOffsets = [
      0x14010, 0x140C3, 0x14187, 0x142AB, 0x143E6, 0x14530, 0x14638, 0x1481D, 
      0x14CFF, 0x14F00, 0x14F0A, 0x14F14, 0x14F1E, 0x14F28, 0x14F32, 0x14F3C, 
      0x14F46, 0x1504F, 0x15153, 0x152AC, 0x15409, 0x1552E, 0x156BB, 0x157FF, 
      0x15951, 0x15AEC, 0x15D1B, 0x15EA4, 0x16061, 0x1606B, 0x16075, 0x1607F, 
      0x16089, 0x162BF, 0x1668E, 0x16988, 0x16C5A, 0x16F27, 0x17133, 0x172FF, 
      0x1754E, 0x17771, 0x1795F, 0x17BD3, 0x17DEA, 0x17FBE,  0xB98E,  0xBBA7
    ]

    # Dump the text.
    for i in startOffsets:
        outString = decompress(romFile, i)
        sys.stdout.write("{0:s}".format(outString))
        sys.stdout.write("------------------------------------------------------------------------\n")

    # Exit.
    sys.exit(0)

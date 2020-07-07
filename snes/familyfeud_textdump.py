#!/usr/bin/env python3
#
# Family Feud (SNES) Text Dumper
# Osteoclave
# 2012-09-15
#
# Produces a nicely-formatted dump of the game's questions and answers.
#
# This code uses python-bitstring:
# https://pypi.org/project/bitstring/

import sys
import bitstring



# Define the dictionary.
dictHuffman = {
    "000"      : "E",
    "001"      : " ",
    "010"      : "%", # This key translates to "%" (0x25) in-game, but it's
                      # not used to print a literal "%". Instead, it's used
                      # as a delimiter.
                      # In a question/answer set, this key separates the
                      # question string from the first answer, the first
                      # answer from the second, and so on.
    "0110"     : "@", # This key translates to "@" (0x40) in-game, but it's
                      # not used to print a literal "@". Instead, it's used
                      # as a delimiter.
                      # In an answer string, this key separates the answer
                      # popularity (1-2 character string with all characters
                      # numeric) from the answer text.
    "0111"     : "A",
    "10000"    : "S",
    "10001"    : "T",
    "10010"    : "O",
    "10011"    : "R",
    "101000"   : "I",
    "101001"   : "L",
    "101010"   : "C",
    "101011"   : "H",
    "101100"   : "_", # This key does not translate to a string in-game.
                      # In answer text, this key toggles between mandatory
                      # and optional characters (e.g. "_RED_ MEAT" can be
                      # answered with "RED MEAT" or "MEAT").
                      # It's represented here with "_" so as to be visible
                      # but unobtrusive in the output.
    "101101"   : "D",
    "101110"   : "M",
    "101111"   : "U",
    "1100000"  : "P",
    "1100001"  : "N",
    "1100010"  : "B",
    "1100011"  : "Y",
    "1100100"  : "2",
    "1100101"  : "1",
    "1100110"  : "W",
    "1100111"  : "3",
    "1101000"  : "G",
    "1101001"  : "/", # This key translates to "\" (0x5C) in-game, but it's
                      # not used to print a literal "\". Instead, it's used
                      # as a delimiter.
                      # In answer text, this key separates distinct correct
                      # answers (e.g. "KENNEDY\JFK" can be answered with
                      # "KENNEDY" or "JFK").
                      # It's represented here with "/" to make the output
                      # look better.
    "1101010"  : "F",
    "1101011"  : "K",
    "1101100"  : "4",
    "1101101"  : "AN",
    "1101110"  : "\0", # This key translates to a null byte (0x00) in-game.
                       # Unsurprisingly, it's used to indicate the end of a
                       # question/answer set.
    "1101111"  : "5",
    "11100000" : "AR",
    "11100001" : "ON",
    "11100010" : "^",  # This key does not translate to a string in-game.
                       # In answer text, this key indicates that the
                       # following character is optional (e.g. "SPAG^HETTI"
                       # can be answered with "SPAGHETTI" or "SPAGETTI").
                       # It's represented here with "^" so as to be visible
                       # but unobtrusive in the output.
    "11100011" : "OR",
    "11100100" : "IN",
    "11100101" : "6",
    "11100110" : "V",
    "11100111" : "7",
    "11101000" : "ING",
    "11101001" : "8",
    "11101010" : "NAME SOMETHING",
    "11101011" : "0",
    "11101100" : "THE",
    "11101101" : "9",
    "11101110" : "OF",
    "11101111" : "THAT",
    "11110000" : "J",
    "11110001" : "\'",
    "11110010" : "X",
    "11110011" : "Z",
    "11110100" : "\"",
    "11110101" : ",",
    "11110110" : "?",
    "11110111" : "Q",
    "11111000" : "&",
    "11111001" : ".",
    "11111010" : "-",
    "11111011" : "!",
    "11111100" : "$",
    "11111101" : "$",
    "11111110" : "$",
    "11111111" : "$",
}



def dumpText(inBits, numberOfLines):

    # Main decompression loop.
    for i in range(numberOfLines):

        # Read the next line.
        nextLine = ""
        while True:
            # Read the next key.
            nextKey = ""
            while nextKey not in dictHuffman:
                nextKey += str(inBits.read("uint:1"))
            nextValue = dictHuffman[nextKey]

            # If the associated value ends the line, break the loop.
            if nextValue == "\0":
                break
            else:
                nextLine += nextValue

        # Discard any remaining bits.
        # (New lines always start at byte boundaries.)
        inBits.bytealign()

        # Parse the current line.
        question, _, answers = nextLine.partition("%")
        answerLines = answers.split("%")

        # Print the current line.
        print("{0:s}".format(question))
        for answerLine in answerLines:
            answerPopularity, answerText = answerLine.split("@")
            print("  {0:>2s}% = {1:s}".format(answerPopularity, answerText))
        print()



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
    inBytes += romBytes[0x40000:0x5D78B]
    inBytes += romBytes[0x28000:0x30609]

    # Make a bitstream from the byte array.
    inBits = bitstring.ConstBitStream(inBytes)

    # Dump the text.
    dumpText(inBits, 2048)

    # Exit.
    sys.exit(0)

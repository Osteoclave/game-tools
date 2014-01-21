# Family Feud Text Dumper
# Written by Alchemic
# 2012 Sep 15
# 
# 
# 
# Produces a nicely-formatted dump of the game's questions and answers.
# 
# 
# 
# This code uses python-bitstring:
# http://code.google.com/p/python-bitstring/

import sys
import bitstring





# Define the dictionary.
dictHuffman = {
  "000"      : "E",
  "001"      : " ",
  "010"      : "%",
  "0110"     : "@",
  "0111"     : "A",
  "10000"    : "S",
  "10001"    : "T",
  "10010"    : "O",
  "10011"    : "R",
  "101000"   : "I",
  "101001"   : "L",
  "101010"   : "C",
  "101011"   : "H",
  "101100"   : "_",     # Optional parts of answers are indicated with this symbol.
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
  "1101001"  : "\\",
  "1101010"  : "F",
  "1101011"  : "K",
  "1101100"  : "4",
  "1101101"  : "AN",
  "1101110"  : "<END>",
  "1101111"  : "5",
  "11100000" : "AR",
  "11100001" : "ON",
  "11100010" : "^",     # This symbol indicates an alternate end to a given answer.
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
  "11111111" : "$"
}





def dumpText(inBits, numberOfLines):

    # Main decompression loop.
    for i in xrange(numberOfLines):

        # Read the next line.
        nextLine = ""
        while True:
            # Read the next key.
            nextKey = ""
            while nextKey not in dictHuffman:
                nextKey += str(inBits.read('uint:1'))
            nextValue = dictHuffman[nextKey]

            # If the associated value ends the line, break the loop.
            if nextValue == "<END>":
                break
            else:
                nextLine += nextValue

        # Discard any remaining bits.
        # (New lines always start at byte boundaries.)
        inBits.bytealign()

        # Parse the current line.
        question, _, rawPairs = nextLine.partition("%")
        rawPairList = rawPairs.split("%")
        pairList = []
        for rawPair in rawPairList:
            percentage, answer = rawPair.split("@")
            pairList.append((percentage, answer))

        # Print the current line.
        sys.stdout.write("{0:s}\n".format(question))
        for eachPair in pairList:
            sys.stdout.write("  {0:>2s}% = {1:s}\n".format(eachPair[0], eachPair[1]))
        sys.stdout.write("\n")





if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc != 2:
        sys.stdout.write("Usage: ")
        sys.stdout.write("{0:s} ".format(sys.argv[0]))
        sys.stdout.write("<romFile>\n")
        sys.exit(1)

    # Copy the argument.
    romFile = sys.argv[1]

    # Open, read and close the input file.
    romStream = open(romFile, "rb")
    romBytes = romStream.read()
    romStream.close()

    # Create a byte array containing the game's text.
    inBytes = bytearray()
    inBytes += romBytes[0x40000:0x5D800]

    # Make a bitstream from the byte array.
    inBits = bitstring.ConstBitStream(inBytes)

    # Dump the text.
    dumpText(inBits, 1536)

    # Exit.
    sys.exit(0)

# Shadowrun Text Dumper
# Written by Alchemic
# 2013 Jul 13 (rewrite of 2011 Aug 26 code)
# 
# This code uses python-bitstring version 2.2.0:
# http://code.google.com/p/python-bitstring/

from __future__ import print_function

import sys
import bitstring





def buildSymbolDict(romStream, index, prefix, symbolDict = {}):
    # Examine the current node of the symbol tree.
    romStream.bytepos = 0xE8000 + index
    leftData = romStream.read('uintle:16')
    rightData = romStream.read('uintle:16')

    # Examine the left child.
    if leftData >= 0x8000:

        # The left child is a leaf node.
        leafString = ""

        # Read the first character.
        firstChar = (leftData & 0x7F00) >> 8
        if firstChar == 0x00:
            pass
        elif (firstChar < 0x20) or (firstChar > 0x7E):
            leafString += "[{0:02X}]".format(firstChar)
        else:
            leafString += "{0:c}".format(firstChar)

        # Read the second character.
        secondChar = (leftData & 0x007F)
        if secondChar == 0x00:
            pass
        elif (secondChar < 0x20) or (secondChar > 0x7E):
            leafString += "[{0:02X}]".format(secondChar)
        else:
            leafString += "{0:c}".format(secondChar)

        # Add the leaf to the dictionary.
        symbolDict[prefix + "0"] = leafString

    else:

        # The left child is an internal node.
        buildSymbolDict(romStream, leftData, prefix + "0")

    # Examine the right child.
    if rightData >= 0x8000:

        # The right child is a leaf node.
        leafString = ""

        # Read the first character.
        firstChar = (rightData & 0x7F00) >> 8
        if firstChar == 0x00:
            pass
        elif (firstChar < 0x20) or (firstChar > 0x7E):
            leafString += "[{0:02X}]".format(firstChar)
        else:
            leafString += "{0:c}".format(firstChar)

        # Read the second character.
        secondChar = (rightData & 0x007F)
        if secondChar == 0x00:
            pass
        elif (secondChar < 0x20) or (secondChar > 0x7E):
            leafString += "[{0:02X}]".format(secondChar)
        else:
            leafString += "{0:c}".format(secondChar)

        # Add the leaf to the dictionary.
        symbolDict[prefix + "1"] = leafString

    else:

        # The right child is an internal node.
        buildSymbolDict(romStream, rightData, prefix + "1")

    # Return the completed symbol dictionary.
    return symbolDict





def readLine(romStream, startPos, symbolDict):
    romStream.bytepos = startPos
    lineTerminator = "[0A]"
    currentLine = ""

    while True:
        # Read the next symbol.
        currentKey = ""
        while currentKey not in symbolDict:
            nextBit = romStream.read('bool')
            if nextBit == False:
                currentKey += "0"
            else:
                currentKey += "1"
        currentSymbol = symbolDict[currentKey]

        # Detect line termination.
        if lineTerminator in currentSymbol:
            # The (optional) replace call hides the line terminator.
            currentLine += currentSymbol.replace(lineTerminator, "")
            break
        else:
            currentLine += currentSymbol

    romStream.bytealign()
    return currentLine





if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc != 2:
        sys.stdout.write("Usage: ")
        sys.stdout.write("{0:s} ".format(sys.argv[0]))
        sys.stdout.write("<romFile>\n")
        sys.exit(1)

    # Process the argument.
    romFile = sys.argv[1]
    romStream = bitstring.ConstBitStream(filename=romFile)

    # Build the dictionary of symbols.
    symbolDict = buildSymbolDict(romStream, 0, "")

    # romStream's reading position (bytepos) is now right after the 
    # end of the symbol tree, which is where the text begins.

    keywordDict = {}
    lineDict = {}

    # Read the lines of text.
    # Shadowrun has somewhere around 1600 lines of text, but the 
    # exact number varies among the various versions of the ROM. 
    # Hence the 1608 (which grabs all the lines and then some).
    for i in xrange(1608):
        # Read the current line.
        startPos = romStream.bytepos
        currentLine = readLine(romStream, startPos, symbolDict)

        # Handle crossing the bank boundary.
        if (startPos < 0xF0000) and (romStream.bytepos >= 0xF0000):
            startPos = 0xF0000
            currentLine = readLine(romStream, startPos, symbolDict)

        # If it's one of the first 64 lines, it's a keyword.
        if i < 64:
            keywordDict[i] = currentLine

        # Add the current line to the line dictionary.
        lineDict[startPos] = currentLine

    # Output the lines of text.
    print("------------------------------------------------------------------------")
    print("Shadowrun Text Dump")
    print("- Dumped from: {0:s}".format(romFile))
    print("------------------------------------------------------------------------")
    print("")
    lineIter = sorted(lineDict.items())
    for i, (k, v) in enumerate(lineIter):
        print("{0:4d}    {1:5X}    {2:s}".format(i, k, v))
    print("")
    print("------------------------------------------------------------------------")
    print("")

    # Read and dump the conversation data.
    # There's a pointer table for this data at 0x147A, but I'm not 
    # using it (just reading the entries in ROM order).

    converseMusicDict = {
      0x00 : "00 (no change)",
      0x01 : "01 (Funky Conversation)",
      0x02 : "02 (Shady Conversation)"
    }

    keywordDict[0xFF] = "Introduction"
    keywordDict[0xFE] = "Talk To"
    keywordDict[0xFD] = "Default"

    # There are 139 conversation data entries.
    # This is consistent among the various versions of the ROM.
    romStream.bytepos = 0x680C0
    for i in xrange(139):

        startPos = romStream.bytepos
        imagePointer = romStream.read('uintle:24')
        imageFlipped = romStream.read('bool')
        converseMusic = romStream.read('uint:7')

        print("{0:5X}".format(startPos))
        print("")
        print("   Image = {0:6X}".format(imagePointer), end="")
        if imageFlipped:
            print(" (flipped horizontally)", end="")
        print("")
        print("   Music = {0:s}".format(converseMusicDict[converseMusic]))
        print("")
        nextKeyword = romStream.read('uint:8')

        while nextKeyword != 0xF8:
            print("   {0:s}".format(keywordDict[nextKeyword]))
            skipAhead = romStream.read('uint:8')
            mysteryBit = romStream.read('bool')
            keywordChanges = romStream.read('uint:7')

            while keywordChanges > 0:
                whichKeyword = romStream.read('uint:8')
                print('   - Learn "{0:s}"'.format(keywordDict[whichKeyword]))
                keywordChanges -= 1

            if mysteryBit:
                mysteryWord = romStream.read('uintle:16')
                print("   - Mystery word (0x{0:04X})".format(mysteryWord))

            textPointer = romStream.read('uintle:16')
            textPointer += 0xE8000
            if lineDict[textPointer]:
                print("   {0:5X} --> {1:s}".format(textPointer, lineDict[textPointer]))
            else:
                print("   {0:5X} --> (?)".format(textPointer))
            print("")

            nextKeyword = romStream.read('uint:8')

        print("------------------------------------------------------------------------")
        print("")

    # Exit.
    sys.exit(0)

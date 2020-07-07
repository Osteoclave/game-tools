#!/usr/bin/env python3
#
# EarthBound Compressor
# Osteoclave
# 2012-04-25
#
# The compression format is described in the decompressor.

import os
import sys



# Reverse the bits of a byte (e.g. 0x80 <---> 0x01).
def reverseByte(currentByte):
    currentByte = ((currentByte >> 4) & 0x0F) | ((currentByte << 4) & 0xF0)
    currentByte = ((currentByte >> 2) & 0x33) | ((currentByte << 2) & 0xCC)
    currentByte = ((currentByte >> 1) & 0x55) | ((currentByte << 1) & 0xAA)
    return currentByte



# Command 1: Run of a constant byte
def lookForConstantByte(inBuffer, currentIndex):
    # Don't look past the end of the buffer.
    compareLimit = len(inBuffer) - currentIndex

    # Don't look too far ahead.
    if compareLimit > 1024:
        compareLimit = 1024

    nextByte = inBuffer[currentIndex]
    matchLength = 0

    for i in range(compareLimit):
        if inBuffer[currentIndex + i] == nextByte:
            matchLength += 1
        else:
            break

    return matchLength, nextByte



# Command 2: Run of a constant word
def lookForConstantWord(inBuffer, currentIndex):
    # Don't look past the end of the buffer.
    compareLimit = len(inBuffer) - currentIndex
    if (compareLimit % 2) == 1:
        compareLimit -= 1

    # Don't look too far ahead.
    if compareLimit > 2048:
        compareLimit = 2048

    # We need at least one word remaining to continue.
    if compareLimit < 2:
        return 0, None

    nextWord = inBuffer[currentIndex+0]
    nextWord += (inBuffer[currentIndex+1] << 8)
    matchLength = 0

    for i in range(0, compareLimit, 2):
        currentWord = inBuffer[currentIndex + i + 0]
        currentWord += (inBuffer[currentIndex + i + 1] << 8)
        if currentWord == nextWord:
            matchLength += 2
        else:
            break

    return matchLength, nextWord



# Command 3: Run of incrementing bytes
def lookForIncrementingByte(inBuffer, currentIndex):
    # Don't look past the end of the buffer.
    compareLimit = len(inBuffer) - currentIndex

    # Don't look too far ahead.
    if compareLimit > 1024:
        compareLimit = 1024

    nextByte = inBuffer[currentIndex]
    matchLength = 0

    for i in range(compareLimit):
        if inBuffer[currentIndex + i] == ((nextByte + i) & 0xFF):
            matchLength += 1
        else:
            break

    return matchLength, nextByte



# Command 4: Copy past bytes
def lookForPastBytesForward(inBuffer, currentIndex):
    bestIndex = 0
    bestLength = 0

    # Don't look past the end of the buffer.
    compareLimit = len(inBuffer) - currentIndex

    # Don't look too far ahead.
    if compareLimit > 1024:
        compareLimit = 1024

    for i in range(currentIndex):
        # Count how many sequential bytes match (possibly zero).
        currentLength = 0
        for j in range(compareLimit):
            if inBuffer[i + j] == inBuffer[currentIndex + j]:
                currentLength += 1
            else:
                break

        # Keep track of the largest match we've seen.
        if currentLength > bestLength:
            bestIndex = i
            bestLength = currentLength

    return bestLength, bestIndex



# Command 5: Copy past bytes (with bits in reverse order)
def lookForPastBytesBitReversed(inBuffer, inBufferBitReversed, currentIndex):
    bestIndex = 0
    bestLength = 0

    # Don't look past the end of the buffer.
    compareLimit = len(inBufferBitReversed) - currentIndex

    # Don't look too far ahead.
    if compareLimit > 1024:
        compareLimit = 1024

    for i in range(currentIndex):
        # Count how many sequential bytes match (possibly zero).
        currentLength = 0
        for j in range(compareLimit):
            if inBufferBitReversed[i + j] == inBuffer[currentIndex + j]:
                currentLength += 1
            else:
                break

        # Keep track of the largest match we've seen.
        if currentLength > bestLength:
            bestIndex = i
            bestLength = currentLength

    return bestLength, bestIndex



# Command 6: Copy past bytes (backward)
def lookForPastBytesBackward(inBuffer, currentIndex):
    bestIndex = 0
    bestLength = 0

    # Don't look past the end of the buffer.
    initialCompareLimit = len(inBuffer) - currentIndex

    # Don't look too far ahead.
    if initialCompareLimit > 1024:
        initialCompareLimit = 1024

    for i in range(currentIndex):
        # Don't look too far back.
        compareLimit = initialCompareLimit
        if compareLimit > i:
            compareLimit = i

        # Count how many sequential bytes match (possibly zero).
        currentLength = 0
        for j in range(compareLimit):
            if inBuffer[i - j] == inBuffer[currentIndex + j]:
                currentLength += 1
            else:
                break

        # Keep track of the largest match we've seen.
        if currentLength > bestLength:
            bestIndex = i
            bestLength = currentLength

    return bestLength, bestIndex



# Turn a command number, count and argument into compressed data.
def encodeCommand(command, count, argument):
    encodedResult = bytearray()

    # Command 2 (run of a constant word) uses a count of words
    # instead of a count of bytes.
    if command == 2:
        count //= 2

    count -= 1
    if count < 32:
        encodedResult.append((command << 5) + count)
    else:
        encodedResult.append((7 << 5) + (command << 2) + (count >> 8))
        encodedResult.append(count & 0xFF)

    if command == 0:
        # Use extend() instead of append().
        encodedResult.extend(argument)
    elif command == 1:
        encodedResult.append(argument & 0xFF)
    elif command == 2:
        encodedResult.append(argument & 0xFF)
        encodedResult.append((argument & 0xFF00) >> 8)
    elif command == 3:
        encodedResult.append(argument & 0xFF)
    else:
        encodedResult.append((argument & 0xFF00) >> 8)
        encodedResult.append(argument & 0xFF)

    return encodedResult



def compress(inBytes):
    # Prepare for compression.
    inBuffer = bytearray(inBytes)
    output = bytearray()
    currentIndex = 0
    queuedLiterals = bytearray()

    # Create a copy of the buffer where the bits of every byte are
    # reversed (e.g. 0x80 <---> 0x01).
    inBufferBitReversed = bytearray([reverseByte(x) for x in inBuffer])

    # Main compression loop.
    while currentIndex < len(inBuffer):
        bestCommand = 0
        bestLength = 0
        bestArgument = 0
        bestRatio = 1.0

        candidateLength = 0
        candidateArgument = 0
        candidateRatio = 0.0

        # Find the command that will compress the most upcoming bytes.
        # Command 1: Run of a constant byte
        candidateLength, candidateArgument = lookForConstantByte(inBuffer, currentIndex)
        if candidateLength >= 32:
            candidateRatio = candidateLength / 3
        else:
            candidateRatio = candidateLength / 2
        if candidateRatio > bestRatio:
            bestCommand = 1
            bestLength = candidateLength
            bestArgument = candidateArgument
            bestRatio = candidateRatio

        # Command 2: Run of a constant word
        candidateLength, candidateArgument = lookForConstantWord(inBuffer, currentIndex)
        if candidateLength >= 64:
            candidateRatio = candidateLength / 4
        else:
            candidateRatio = candidateLength / 3
        if candidateRatio > bestRatio:
            bestCommand = 2
            bestLength = candidateLength
            bestArgument = candidateArgument
            bestRatio = candidateRatio

        # Command 3: Run of incrementing bytes
        candidateLength, candidateArgument = lookForIncrementingByte(inBuffer, currentIndex)
        if candidateLength >= 32:
            candidateRatio = candidateLength / 3
        else:
            candidateRatio = candidateLength / 2
        if candidateRatio > bestRatio:
            bestCommand = 3
            bestLength = candidateLength
            bestArgument = candidateArgument
            bestRatio = candidateRatio

        # Command 4: Copy past bytes
        candidateLength, candidateArgument = lookForPastBytesForward(inBuffer, currentIndex)
        if candidateLength >= 32:
            candidateRatio = candidateLength / 4
        else:
            candidateRatio = candidateLength / 3
        if candidateRatio > bestRatio:
            bestCommand = 4
            bestLength = candidateLength
            bestArgument = candidateArgument
            bestRatio = candidateRatio

        # Command 5: Copy past bytes (with bits in reverse order)
        candidateLength, candidateArgument = lookForPastBytesBitReversed(inBuffer, inBufferBitReversed, currentIndex)
        if candidateLength >= 32:
            candidateRatio = candidateLength / 4
        else:
            candidateRatio = candidateLength / 3
        if candidateRatio > bestRatio:
            bestCommand = 5
            bestLength = candidateLength
            bestArgument = candidateArgument
            bestRatio = candidateRatio

        # Command 6: Copy past bytes (backward)
        candidateLength, candidateArgument = lookForPastBytesBackward(inBuffer, currentIndex)
        if candidateLength >= 32:
            candidateRatio = candidateLength / 4
        else:
            candidateRatio = candidateLength / 3
        if candidateRatio > bestRatio:
            bestCommand = 6
            bestLength = candidateLength
            bestArgument = candidateArgument
            bestRatio = candidateRatio

        # If none of the commands find a match large enough to be worth
        # using, the next byte will be encoded as a literal. Don't output
        # it right away. (If we did, multiple literals in a row would be
        # encoded as several one-byte commands instead of a single
        # multi-byte command.)
        if bestCommand == 0:
            queuedLiterals.append(inBuffer[currentIndex])
            currentIndex += 1
            # If we have 1024 literals queued up, output them.
            # (That's the most we can write with one command.)
            if len(queuedLiterals) == 1024:
                output += encodeCommand(0, len(queuedLiterals), queuedLiterals)
                queuedLiterals = bytearray()
            continue

        # If we've reached this point, we have a non-literal command
        # to output. If we have any literals queued, output them now.
        if len(queuedLiterals) > 0:
            output += encodeCommand(0, len(queuedLiterals), queuedLiterals)
            queuedLiterals = bytearray()

        # Output the non-literal command.
        output += encodeCommand(bestCommand, bestLength, bestArgument)

        # Advance the current position in the buffer.
        currentIndex += bestLength

    # Output any leftover queued literals.
    if len(queuedLiterals) > 0:
        output += encodeCommand(0, len(queuedLiterals), queuedLiterals)

    # Append the 0xFF terminator.
    output.append(0xFF)

    # Return the compressed data.
    return output



# Open a file for reading and writing. If the file doesn't exist, create it.
# (Vanilla open() with mode "r+" raises an error if the file doesn't exist.)
def touchopen(filename, *args, **kwargs):
    fd = os.open(filename, os.O_RDWR | os.O_CREAT)
    return os.fdopen(fd, *args, **kwargs)



if __name__ == "__main__":

    # Check for incorrect usage.
    argc = len(sys.argv)
    if argc < 2 or argc > 4:
        print("Usage: {0:s} <inFile> [outFile] [outOffset]".format(
            sys.argv[0]
        ))
        sys.exit(1)

    # Copy the arguments.
    inFile = sys.argv[1]
    outFile = None
    if argc == 3 or argc == 4:
        outFile = sys.argv[2]
    outOffset = 0
    if argc == 4:
        outOffset = int(sys.argv[3], 16)

    # Read the input file.
    with open(inFile, "rb") as inStream:
        inBytes = bytearray(inStream.read())

    # Compress the data.
    outBytes = compress(inBytes)

    # Write the compressed output, if appropriate.
    if outFile is not None:
        with touchopen(outFile, "r+b") as outStream:
            outStream.seek(outOffset)
            outStream.write(outBytes)
            lastOffset = outStream.tell()
            print("Last offset written, inclusive: {0:X}".format(
                lastOffset - 1
            ))

    # Report statistics on the data.
    print("Uncompressed size: 0x{0:X} ({0:d}) bytes".format(len(inBytes)))
    print("Compressed size: 0x{0:X} ({0:d}) bytes".format(len(outBytes)))
    print("Ratio: {0:f}".format(len(outBytes) / len(inBytes)))

    # Exit.
    sys.exit(0)

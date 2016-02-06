# Quintet Arrangement Viewer
# Written by Alchemic
# 2011 Nov 15
# 
# 
# 
# This code uses the Python Imaging Library (PIL):
# http://www.pythonware.com/products/pil/

from __future__ import print_function

import sys
import quintet_decomp

from PIL import Image





# Check for incorrect usage.
argc = len(sys.argv)
if argc < 3 or argc > 4:
    print("Usage: {0:s} <inFile> <startOffset> [outFile]".format(sys.argv[0]))
    sys.exit(1)

# Copy the arguments.
inFile = sys.argv[1]
startOffset = int(sys.argv[2], 16)
outFile = "{0:s}_{1:06X}.png".format(inFile, startOffset)
if argc == 4:
    outFile = sys.argv[3]

# Open, read and close the input file.
inStream = open(inFile, "rb")
inBytes = inStream.read()
inStream.close()

# Read the size bytes.
xSize = 0x10 * ord(inBytes[startOffset + 0])
ySize = 0x10 * ord(inBytes[startOffset + 1])

# Decompress the arrangement data.
outBytes, endOffset = quintet_decomp.decompress(inBytes, startOffset + 2)

# Create the arrangement bitmap.
canvas = Image.new("RGB", (xSize, ySize))

for y in range(ySize):
    for x in range(xSize):

        currentIndex = 0
        currentIndex += (0x10 * xSize * (y / 0x10))
        currentIndex += (0x100 * (x / 0x10))
        currentIndex += (0x10 * (y % 0x10))
        currentIndex += (0x1 * (x % 0x10))

        currentTile = outBytes[currentIndex]

        # This produces a nice orange-and-blue scheme.
        canvas.putpixel(
          (x, y), 
          (
            0xFF - abs(currentTile - 0x40), 
            0xD0 - abs(currentTile - 0x80), 
            0xFF - abs(currentTile - 0xC0)
          )
        )

# Output a scaled-up version of the image, and exit.
canvas.resize((xSize * 4, ySize * 4), Image.NEAREST).save(outFile, "PNG")
sys.exit(0)

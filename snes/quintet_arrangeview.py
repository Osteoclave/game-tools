# Quintet Arrangement Viewer
# Written by Alchemic
# 2011 Nov 15
# 
# 
# 
# This code uses PIL (Python Imaging Library) version 1.1.7:
# http://www.pythonware.com/products/pil/

import sys
import struct
import quintet_decomp

from PIL import Image



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
outFile = "{0:s}_{1:06X}.png".format(romFile, startOffset)
if argc == 4:
    outFile = sys.argv[3]

# Read the size bytes.
romStream = open(romFile, "rb")
romStream.seek(startOffset)
xSize = 0x10 * struct.unpack("<B", romStream.read(1))[0]
ySize = 0x10 * struct.unpack("<B", romStream.read(1))[0]
romStream.close()

# Decompress the arrangement data.
decompData, endOffset = quintet_decomp.decompress(romFile, startOffset + 2)

# Create the arrangement bitmap.
canvas = Image.new("RGB", (xSize, ySize))

for y in range(ySize):
    for x in range(xSize):

        currentIndex = 0
        currentIndex += (0x10 * xSize * (y / 0x10))
        currentIndex += (0x100 * (x / 0x10))
        currentIndex += (0x10 * (y % 0x10))
        currentIndex += (0x1 * (x % 0x10))

        currentTile = decompData[currentIndex]

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

-- Wheel of Fortune Puzzle Injector
-- Osteoclave
-- 2025-11-01
--
-- This is a Lua script for use with FCEUX.

puzzles = {}
currentPuzzle = nil
remainingIndex = 1



function trim(s)
  return s:match("^ *(.-) *$")
end



function parsePuzzleString(puzzleString)
  -- Split the puzzle string into category and raw answer data
  local puzzleString = puzzleString:upper()
  local category, answerRaw = puzzleString:match("^([^:]+):([^:]+)$")
  if category == nil or answerRaw == nil then return end

  -- Validate the category
  category = trim(category)
  category = category:match("^[ %$'%-%?0-9A-Z]+$")
  if category == nil then return end
  if category:len() > 8 then return end

  -- Validate the raw answer data
  local answerLines = {}
  local lineStartIndex = 1
  repeat
    local lineEndIndex = answerRaw:len()
    local nextDelimIndex = answerRaw:find("/", lineStartIndex)
    if nextDelimIndex ~= nil then
      lineEndIndex = nextDelimIndex - 1
    end
    local answerLine = answerRaw:sub(lineStartIndex, lineEndIndex)
    answerLine = trim(answerLine)
    answerLine = select(2, answerLine:match("^(\"?)([ '%-A-Z_]*)%1$"))
    if answerLine == nil then
      answerLines = nil
      break
    end
    table.insert(answerLines, answerLine)
    if #answerLines > 4 then
      answerLines = nil
      break
    end
    lineStartIndex = lineEndIndex + 2
  until nextDelimIndex == nil

  if answerLines == nil then return end

  -- If the answer contains no consonants, return.
  -- ("Y" is always treated as a consonant in Wheel of Fortune.)
  if table.concat(answerLines):match("[BCDFGHJKLMNPQRSTVWXYZ]+") == nil then
    return
  end

  -- If the answer lines are too long for the game board, return
  if #answerLines == 1 then
    if answerLines[1]:len() > 13 then return end
  elseif #answerLines == 2 then
    if answerLines[1]:len() > 13 then return end
    if answerLines[2]:len() > 13 then return end
  elseif #answerLines == 3 then
    if answerLines[1]:len() > 11 then return end
    if answerLines[2]:len() > 13 then return end
    if answerLines[3]:len() > 13 then return end
  elseif #answerLines == 4 then
    if answerLines[1]:len() > 11 then return end
    if answerLines[2]:len() > 13 then return end
    if answerLines[3]:len() > 13 then return end
    if answerLines[4]:len() > 11 then return end
  else
    return
  end

  local newPuzzle = {
    ["category"] = category,
    ["answerLines"] = answerLines,
  }
  return newPuzzle
end



function loadPuzzles(puzzleFileName)
  emu.print(string.format(
    "[loadPuzzles] Loading puzzles from %s", puzzleFileName
  ))

  local lineNumber = 0
  local puzzlesLoaded = 0
  local puzzlesSkipped = 0

  for puzzleString in io.lines(puzzleFileName) do
    -- Keep track of the current line number
    lineNumber = lineNumber + 1
    -- Trim comments
    puzzleString = puzzleString:match("^([^#]*)#?.*$")
    -- Trim trailing spaces
    puzzleString = puzzleString:match("^(.-) *$")
    -- If there's anything left after trimming, parse it
    if puzzleString ~= "" then
      local newPuzzle = parsePuzzleString(puzzleString)
      if newPuzzle ~= nil then
        table.insert(puzzles, newPuzzle)
        puzzlesLoaded = puzzlesLoaded + 1
      else
        emu.print(string.format(
          "[loadPuzzles] %s:%d: could not parse puzzle, skipping",
          puzzleFileName, lineNumber
        ))
        puzzlesSkipped = puzzlesSkipped + 1
      end
    end
  end

  emu.print(string.format("[loadPuzzles] %d lines read", lineNumber))
  emu.print(string.format("[loadPuzzles] %d puzzles loaded", puzzlesLoaded))
  emu.print(string.format("[loadPuzzles] %d puzzles skipped", puzzlesSkipped))
end



vIndent = {0x10, 0x10, 0x00, 0x00}
hIndent = {6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0, 0}

function injectPuzzle()
  -- Check if we're in the correct bank ($81B9 --> 0x101C9 in the ROM)
  local bankCheck = memory.readbyte(0x81B9)
  if bankCheck ~= 0x9D then return end

  -- Check if any puzzles have been loaded
  if #puzzles == 0 then
    currentPuzzle = nil
    return
  end

  -- Select a puzzle
  -- With each puzzle selection, do one element-swap of a Fisher-Yates
  -- shuffle. This prevents puzzles from repeating until the entire
  -- puzzle list has been exhausted.
  local swapIndex = math.random(remainingIndex, #puzzles)
  puzzles[remainingIndex], puzzles[swapIndex] = puzzles[swapIndex], puzzles[remainingIndex]
  currentPuzzle = puzzles[remainingIndex]
  remainingIndex = remainingIndex + 1
  if remainingIndex > #puzzles then
    remainingIndex = 1
  end

  -- Clear the game board
  for clearDest=0x0341, 0x0380, 1 do
    memory.writebyte(clearDest, 0x00)
  end

  -- Write the puzzle to the game board
  local boardStartOfLine = 0x0341 + vIndent[#currentPuzzle.answerLines]
  for i, answerLine in ipairs(currentPuzzle.answerLines) do
    local boardDest = boardStartOfLine
    if answerLine:len() > 0 then
      boardDest = boardDest + hIndent[answerLine:len()]
    end

    for j=1, answerLine:len(), 1 do
      local letter = answerLine:byte(j)
      if letter == 0x20 or letter == 0x5F then
        -- Space or underscore: Replace with 0x00
        letter = 0x00
      elseif letter == 0x27 or letter == 0x2D then
        -- Apostrophe or dash: No change
      elseif letter >= 0x41 and letter <= 0x5A then
        -- Capital letter: Hide by setting the 0x80 bit
        -- FCEUX's Lua environment uses Lua 5.1, which doesn't have
        -- bitwise operators. Hence, the FCEUX-provided OR(a,b).
        letter = OR(letter, 0x80)
      else
        -- Anything else: Invalid character, replace with 0x00
        -- (This should never happen, but just in case...)
        letter = 0x00
      end
      memory.writebyte(boardDest, letter)
      boardDest = boardDest + 1
    end

    boardStartOfLine = boardStartOfLine + 0x10
  end

end



categoryTiles = {
  [" "] = 0xD4,
  ["'"] = 0xD5,
  ["$"] = 0xD6,
  ["-"] = 0xD7,
  ["?"] = 0xDA,
  ["0"] = 0xDB,
  ["1"] = 0xDC,
  ["2"] = 0xDD,
  ["3"] = 0xDE,
  ["4"] = 0xDF,
  ["5"] = 0xE0,
  ["6"] = 0xE1,
  ["7"] = 0xE2,
  ["8"] = 0xE3,
  ["9"] = 0xE4,
  ["A"] = 0xE5,
  ["B"] = 0xE6,
  ["C"] = 0xE7,
  ["D"] = 0xE8,
  ["E"] = 0xE9,
  ["F"] = 0xEA,
  ["G"] = 0xEB,
  ["H"] = 0xEC,
  ["I"] = 0xED,
  ["J"] = 0xEE,
  ["K"] = 0xEF,
  ["L"] = 0xF0,
  ["M"] = 0xF1,
  ["N"] = 0xF2,
  ["O"] = 0xF3,
  ["P"] = 0xF4,
  ["Q"] = 0xF5,
  ["R"] = 0xF6,
  ["S"] = 0xF7,
  ["T"] = 0xF8,
  ["U"] = 0xF9,
  ["V"] = 0xFA,
  ["W"] = 0xFB,
  ["X"] = 0xFC,
  ["Y"] = 0xFD,
  ["Z"] = 0xFE,
}

function injectCategory()
  -- Check if we're in the correct bank ($9332 --> 0x1342 in the ROM)
  local bankCheck = memory.readbyte(0x9332)
  if bankCheck ~= 0xA5 then return end

  -- Check if we have a current puzzle
  if currentPuzzle == nil then return end

  -- Inject sprites to display the category string
  local xPosition = 0x81 - 4*currentPuzzle.category:len()
  for i=1, currentPuzzle.category:len(), 1 do
    -- Y coordinate
    memory.writebyte(0x0204 + 4*(i-1), 0x18)
    -- Tile index
    local tileIndex = categoryTiles[currentPuzzle.category:sub(i, i)]
    if tileIndex == nil then tileIndex = 0x00 end
    memory.writebyte(0x0205 + 4*(i-1), tileIndex)
    -- Sprite attributes
    memory.writebyte(0x0206 + 4*(i-1), 0x03)
    -- X coordinate
    memory.writebyte(0x0207 + 4*(i-1), xPosition)
    xPosition = xPosition + 8
  end
end



xPositionToCategoryLength = {
  [0x7D] = 1,
  [0x79] = 2,
  [0x75] = 3,
  [0x71] = 4,
  [0x6D] = 5,
  [0x69] = 6,
  [0x65] = 7,
  [0x61] = 8,
}

function injectNextUnusedSpriteIndex()
  -- Check if we're in the correct bank ($9332 --> 0x1342 in the ROM)
  local bankCheck = memory.readbyte(0x9332)
  if bankCheck ~= 0xA5 then return end

  -- Check if we have a current puzzle
  if currentPuzzle == nil then return end

  -- Check the Y position of the sprite in the 0x0204-7 slot. If the
  -- Y position is 0x18, then this sprite is most likely being used
  -- to display the first character of the category string.
  -- (Not a very precise check, but it works.)
  local yPosition = memory.readbyte(0x0204)
  if yPosition ~= 0x18 then return end

  -- Use the X position of the first character of the category string
  -- to determine the length of the category string.
  local xPosition = memory.readbyte(0x0207)
  local categoryLength = xPositionToCategoryLength[xPosition]
  if categoryLength == nil then return end

  -- From the length, determine the index of the next unused sprite.
  local nextUnusedSpriteIndex = 4 + 4*categoryLength
  memory.setregister("x", nextUnusedSpriteIndex)
end



emu.print("[main] Script started")
math.randomseed(os.time())
loadPuzzles("WheelOfFortune_PuzzleInjector_puzzles.txt")
memory.registerexecute(0x81BC, injectPuzzle)
memory.registerexecute(0x9379, injectCategory)
memory.registerexecute(0x9FAD, injectNextUnusedSpriteIndex)
emu.print("[main] Ready")

from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import time
import random

##########################################################################################################################
# CLASSES:
# configurable things
class Config(object):
    def __init__(self):
        # block size
        self.size = 4
        # width is the play area's width, so it's the display's y value
        # height is the play area's height, so it's the display's x value
        self.height = 22
        self.width = 10
        # fallDistance is the difference in coordinates between two adjacent grid spaces
        self.fallDistance = 6
        # displayWidth and displayHeight are relative to the proper orientation of the display
        self.displayWidth = 128
        self.displayHeight = 64
        # wallWidth is the amount of space given to each of the game's walls
        self.wallWidth = 2
        # gameWidth and gameHeight are relative to the game's interpretation of the display's orientation (on its side)
        self.gameWidth = self.displayHeight - (self.wallWidth * 2)
        self.gameHeight = self.displayWidth
        # speed is the length of time.sleep() in the game's loop
        self.speed = 0.025
        # there is a variable tick that increments by 1 every loop until tick % tickrate == 0, at which point the game updates
        self.tickrate = 2
        # holdDelay is the amount of ticks between when you begin to hold a button and when it begins to repeat itsself
        self.holdDelay = 5
        # pieceTypes are the types of pieces possible
        self.pieceTypes = ['J', 'L', 'S', 'Z', 'I', 'O', 'T']
        
# play area is an object of this type:
# x and y are backwards here so that entire rows at a time may be accessed, for line clearing purposes (it's a list of rows rather than a list of columns)
# 1 is the highest visible spot, 20 is the lowest visible spot, 21 (the maximum) is filled with Trues
class Area(object):
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.array = [[False for j in range(width)] for i in range(height)]
        for i in range(width):
            self.array[height - 1][i] = True # row of Trues at the bottom
    def update(self, block):
        self.array[block.y][block.x] = True
    def draw(self, oled, config):
        for i in range(self.height - 1):
            for j in range(self.width):
                if(self.array[i][j] == True):
                    x, y = playAreaToPixel(i, j)
                    oled.fill_rect(x - 6, config.gameWidth - y, config.size, config.size, 1)

# the x and y values held by Block are the coordinates on the screen, not the location in the array
# tetriminos will be made of these:
class Block(object):
    def __init__(self, x = 4, y = 1):
        self.active = True
        self.x = x
        self.y = y
    def draw(self, oled, config):
        # x and y are backwards here because the display is sideways
        x, y = playAreaToPixel(self.x, self.y)
        oled.fill_rect(y - 6, config.gameWidth - x, config.size, config.size, 1)
    def update(self, x, y):
        self.x = x
        self.y = y

class Tetrimino(object):
    def __init__(self, pieceType, oled, config):
        self.root = Block(4, 1)
        self.b1 = Block()
        self.b2 = Block()
        self.b3 = Block()
        self.blocks = [self.root, self.b1, self.b2, self.b3]
        self.active = True
        self.rotationState = 0
        self.pieceType = pieceType
        self._update(oled, config)
    def _update(self, oled, config):
        if self.rotationState == 0:
            if self.pieceType == 'I':
                if self.b1.y == self.root.y + 1:
                    self.root.update(self.root.x, self.root.y - 1)
                else:
                    self.root.update(self.root.x - 1, self.root.y)
                self.b1.update(self.root.x - 1, self.root.y)
                self.b2.update(self.root.x + 1, self.root.y)
                self.b3.update(self.root.x + 2, self.root.y)
            elif self.pieceType == 'J':
                self.b1.update(self.root.x - 1, self.root.y - 1)
                self.b2.update(self.root.x - 1, self.root.y)
                self.b3.update(self.root.x + 1, self.root.y)
            elif self.pieceType == 'L':
                self.b1.update(self.root.x - 1, self.root.y)
                self.b2.update(self.root.x + 1, self.root.y)
                self.b3.update(self.root.x + 1, self.root.y - 1)
            elif self.pieceType == 'O':
                self.b1.update(self.root.x, self.root.y - 1)
                self.b2.update(self.root.x + 1, self.root.y)
                self.b3.update(self.root.x + 1, self.root.y - 1)
            elif self.pieceType == 'S':
                self.b1.update(self.root.x - 1, self.root.y)
                self.b2.update(self.root.x, self.root.y - 1)
                self.b3.update(self.root.x + 1, self.root.y - 1)
            elif self.pieceType == 'T':
                self.b1.update(self.root.x - 1, self.root.y)
                self.b2.update(self.root.x, self.root.y - 1)
                self.b3.update(self.root.x + 1, self.root.y)
            elif self.pieceType == 'Z':
                self.b1.update(self.root.x - 1, self.root.y - 1)
                self.b2.update(self.root.x, self.root.y - 1)
                self.b3.update(self.root.x + 1, self.root.y)
        elif self.rotationState == 1:
            if self.pieceType == 'I':
                if self.b1.x == self.root.x - 1:
                    self.root.update(self.root.x + 1, self.root.y)
                else:
                    self.root.update(self.root.x, self.root.y - 1)
                self.b1.update(self.root.x, self.root.y - 1)
                self.b2.update(self.root.x, self.root.y + 1)
                self.b3.update(self.root.x, self.root.y - 2)
            elif self.pieceType == 'J':
                self.b1.update(self.root.x + 1, self.root.y - 1)
                self.b2.update(self.root.x, self.root.y - 1)
                self.b3.update(self.root.x, self.root.y + 1)
            elif self.pieceType == 'L':
                self.b1.update(self.root.x, self.root.y - 1)
                self.b2.update(self.root.x, self.root.y + 1)
                self.b3.update(self.root.x + 1, self.root.y + 1)
            elif self.pieceType == 'O':
                print("lol")
            elif self.pieceType == 'S':
                self.b1.update(self.root.x, self.root.y - 1)
                self.b2.update(self.root.x + 1, self.root.y)
                self.b3.update(self.root.x + 1, self.root.y + 1)
            elif self.pieceType == 'T':
                self.b1.update(self.root.x, self.root.y - 1)
                self.b2.update(self.root.x + 1, self.root.y)
                self.b3.update(self.root.x, self.root.y + 1)
            elif self.pieceType == 'Z':
                self.b1.update(self.root.x + 1, self.root.y - 1)
                self.b2.update(self.root.x + 1, self.root.y)
                self.b3.update(self.root.x, self.root.y + 1)
        elif self.rotationState == 2:
            if self.pieceType == 'I':
                if self.b1.y == self.root.y - 1:
                    self.root.update(self.root.x, self.root.y + 1)
                else:
                    self.root.update(self.root.x + 1, self.root.y)
                self.b1.update(self.root.x + 1, self.root.y)
                self.b2.update(self.root.x - 1, self.root.y)
                self.b3.update(self.root.x - 2, self.root.y)
            elif self.pieceType == 'J':
                self.b1.update(self.root.x + 1, self.root.y + 1)
                self.b2.update(self.root.x + 1, self.root.y)
                self.b3.update(self.root.x - 1, self.root.y)
            elif self.pieceType == 'L':
                self.b1.update(self.root.x + 1, self.root.y)
                self.b2.update(self.root.x - 1, self.root.y)
                self.b3.update(self.root.x - 1, self.root.y + 1)
            elif self.pieceType == 'O':
                print("lol")
            elif self.pieceType == 'S':
                self.b1.update(self.root.x + 1, self.root.y)
                self.b2.update(self.root.x, self.root.y + 1)
                self.b3.update(self.root.x - 1, self.root.y + 1)
            elif self.pieceType == 'T':
                self.b1.update(self.root.x + 1, self.root.y)
                self.b2.update(self.root.x, self.root.y + 1)
                self.b3.update(self.root.x - 1, self.root.y)
            elif self.pieceType == 'Z':
                self.b1.update(self.root.x + 1, self.root.y + 1)
                self.b2.update(self.root.x, self.root.y + 1)
                self.b3.update(self.root.x - 1, self.root.y)
        elif self.rotationState == 3:
            if self.pieceType == 'I':
                if self.b1.x == self.root.x + 1:
                    self.root.update(self.root.x - 1, self.root.y)
                else:
                    self.root.update(self.root.x, self.root.y + 1)
                self.b1.update(self.root.x, self.root.y + 1)
                self.b2.update(self.root.x, self.root.y - 1)
                self.b3.update(self.root.x, self.root.y - 2)
            elif self.pieceType == 'J':
                self.b1.update(self.root.x - 1, self.root.y + 1)
                self.b2.update(self.root.x, self.root.y + 1)
                self.b3.update(self.root.x, self.root.y - 1)
            elif self.pieceType == 'L':
                self.b1.update(self.root.x, self.root.y + 1)
                self.b2.update(self.root.x, self.root.y - 1)
                self.b3.update(self.root.x - 1, self.root.y - 1)
            elif self.pieceType == 'O':
                print("lol")
            elif self.pieceType == 'S':
                self.b1.update(self.root.x, self.root.y + 1)
                self.b2.update(self.root.x - 1, self.root.y)
                self.b3.update(self.root.x - 1, self.root.y - 1)
            elif self.pieceType == 'T':
                self.b1.update(self.root.x, self.root.y + 1)
                self.b2.update(self.root.x - 1, self.root.y)
                self.b3.update(self.root.x, self.root.y - 1)
            elif self.pieceType == 'Z':
                self.b1.update(self.root.x - 1, self.root.y + 1)
                self.b2.update(self.root.x - 1, self.root.y)
                self.b3.update(self.root.x, self.root.y - 1)
        self._draw(oled, config)
    def _draw(self, oled, config):
        oled.fill(0)
        drawBorders(oled)
        for block in self.blocks:
            block.draw(oled, config)
    def _place(self, oled, playArea):
        oled.fill(0)
        drawBorders(oled)
        for block in self.blocks:
            playArea.update(block)
        self.active = False
    def fall(self, oled, config, playArea):
        if ((not playArea.array[self.root.y + 1][self.root.x]) and (not playArea.array[self.b1.y + 1][self.b1.x]) and (not playArea.array[self.b2.y + 1][self.b2.x]) and (not playArea.array[self.b3.y + 1][self.b3.x])):
            for block in self.blocks:
                block.y += 1
            self._draw(oled, config)
        else:
            self._place(oled, playArea)
    def moveLeft(self, playArea):
        blockX = [block.x for block in self.blocks]
        minBlock = self.blocks[blockX.index(min(blockX))]
        if minBlock.x > 0 and not playArea.array[minBlock.y][minBlock.x - 1]:
            for block in self.blocks:
                block.x -= 1
    def moveRight(self, config, playArea):
        blockX = [block.x for block in self.blocks]
        maxBlock = self.blocks[blockX.index(max(blockX))]
        if maxBlock.x < config.width - 1 and not playArea.array[maxBlock.y][maxBlock.x + 1]:
            for block in self.blocks:
                block.x += 1
    def rotateRight(self, oled, config, playArea):
        self.rotationState = (self.rotationState + 1) % 4
        self._update(oled, config)
    def rotateLeft(self, oled, config, playArea):
        if self.rotationState == 0:
            self.rotationState = 3
        else:
            self.rotationState -= 1
        self._update(oled, config)
        
##########################################################################################################################
# FUNCTIONS:
# order of passing: oled, config, playArea, block, any additional info
def readyDisplay(config):
    displayWidth = config.displayWidth
    displayHeight = config.displayHeight

    #buffer = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7f\x80\x0f\xc0\xc0`\xc8\x13\x1b\x80\x01\xc4\x01\x02\x00\x00\xaa\xfb\x1c\xfb\xf0\xaf\xfe7\xed\xe7\x01\xa2\xda\xce\x00\x00\xff\xff\x9f\xff\xfb\xff\xfe?\xdb\xea\x03\xcf\xff\xc5\x00\x01\xff\xff\x1f\xff\xd3\xff\xff\x7f\xff\xe7\x03\x8f\xff\xca\x00\x01\x80\x7f\xbf\xcf\xfb\x1d\xf77\xdd\xd7\x03\xcf\xfe\xe7\x00\x03\xd5\x00\x19\x00s\xc2\x01p\x00\xe7\x87\x00%\xe5\x00\x03\x80\x000\x00?\x00\x03h\x00g\x0f\x80\x00a\x00\x03\x00\x00\x18\x00;\x00\x03p\x00\'\x0e\x00\x00\xec\x80\x03\x80\x000\x00\x12\x00\x03p\x00g:\x00\x00g\x00\x03\x80\x10\x18\n9\x00\x032\xa4\xf7|\x00\x00o\x00\x03\x0f\xee?\xff\xf3\xe6w\xffwg<\x05\xfe\xf5\x00\x03\x8f\xdf\x9f\xbf\xd3\xff\xff?\xef\xe7\xe8\x03\xb7\xa7\x00\x03\x8b\x7f?\x7f\xfb\xff\xff\xff\xff\xe7P\x07\xff\xcf\x80\x03\x80[\xb0\x84c\xef\x00s\xe0\x06p\r\x81\x8f\x00\x03\x80\x01\x98\x00\x07\x00\x000\x04\x07|\x0e \x07\x00\x03\x00\x03(\x00#\x80\x03(\x00\x07\x1a\x0e\x00\x0f\x00\x03\x80\x01\x98\x00;\x00\x07`\x00g\xbe\x0e\x00\x05\x00\x02\x80\x03\xbc\x007\x00\x030\x00\'\x17\x0e\x00\x0b\x00\x03\xe0\x07\x98\x00{\x80\x07h\x00g\x0f\x8a\x00\x07\x00\x01\xd3\xff_\xfd\xfb\xfa\xff}_\xe3\x07\xce\x00\x0f\x00\x03\xbf\xde\x9e\xf7\xd3\xef\xef?\xfe\xc7\x05\x8e\x00\x07\x00\x01\xff\xff7\xff\xfb\xff\xff\x7f\xff\xeb\x03\xee\x00\r\x00\x00C]\x1b\xef\xd1\xff\xfe\x08\x1e\xa4\x00L\x00\x07\x00\x00\x10\xa2\x04\x10!\x04\x00\x07\x81B\x00"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

    #fb = framebuf.FrameBuffer(buffer, 128, 64, framebuf.MONO_HLSB)
    
    conversion_factor = 3.3 / (65535) # Conversion from Pin read to proper voltage

    i2c = I2C(0, scl=Pin(13), sda=Pin(12),freq=200000)

    oled = SSD1306_I2C(displayWidth, displayHeight, i2c)
    
    # clear screen
    oled.fill(0)
    
    return(conversion_factor, i2c, oled)

# convert array values to location values
def playAreaToPixel(x, y):
    return (int(x * 6) + 3), int(((y + 1) * 6) - 3)

# convert location values to array values
def pixelToPlayArea(x, y):
    return (int(x / 6), int(((y - 3) / 6)))

# draw border walls and floor
def drawBorders(oled):
    oled.fill_rect(0, 0, 128, 1, 1)
    oled.fill_rect(0, 63, 128, 1, 1)
    oled.fill_rect(123, 0, 5, 64, 1)

# 'L' is left, 'R' is right, 'O' is off, 0 is none 
def checkButtons(offButton, leftButton, rightButton, rotateButton):
    buttonPressed = 0
    if offButton.value() != 1:
        buttonPressed = 'O'
    elif leftButton.value() != 1:
        buttonPressed = 'L'
    elif rightButton.value() != 1:
        buttonPressed = 'R'
    elif rotateButton.value() != 1:
        buttonPressed = 'T'
    return buttonPressed

# determines if the button is pressed and performs the relevant actions if so
def evaluateButton(oled, config, playArea, t1, buttonPressed, tick, holdTick, holdingButton):
    if buttonPressed:
        if not holdTick:
            holdTick = tick
            moveBlock(oled, config, playArea, t1, buttonPressed)
        elif ((tick - holdTick) % config.holdDelay == 0) or (holdingButton == True):
            holdingButton = True
            moveBlock(oled, config, playArea, t1, buttonPressed)
    else:
        holdTick = 0
        holdingButton = False
    return(holdTick, holdingButton)

# moves the block either left or right
def moveBlock(oled, config, playArea, t1, buttonPressed):
    if buttonPressed == 'L':
        t1.moveLeft(playArea)
    elif buttonPressed == 'R':
        t1.moveRight(config, playArea)
    elif buttonPressed == 'T':
        t1.rotateRight(oled, config, playArea)

# determine if the game has been lost (called at the creation of every new tetrimino)
def checkIfLost(config, playArea, block):
    return playArea.array[1][block.x]

# check for clearable lines
def checkClear(playArea):
    linesCleared = 0
    for i in range(playArea.height - 1):
        if all(playArea.array[i]):
            clearLine(playArea, i)
            print("line cleared")
            linesCleared = linesCleared + 1
    return linesCleared

# clear lines
def clearLine(playArea, y):
    for i in range(playArea.width):
        playArea.array[y][i] = False 
    for i in reversed(range(y)):
        for j in range(playArea.width):
            playArea.array[i + 1][j] = playArea.array[i][j]

# convert pieceTypes to numbers
def pieceTypeToNumber(pieceType):
    if pieceType == 'I':
        number = 0
    elif pieceType == 'J':
        number = 1
    elif pieceType == 'L':
        number = 2
    elif pieceType == 'O':
        number = 3
    elif pieceType == 'S':
        number = 4
    elif pieceType == 'T':
        number = 5
    else:
        number = 6
    return number

# randomize
def randomizer(sevenBagger, config):
    pieceType = random.choice(config.pieceTypes)
    index = pieceTypeToNumber(pieceType)
    valid = False
    if all(sevenBagger):
        sevenBagger = [False for i in range(len(config.pieceTypes))]
    while not valid:
        if sevenBagger[index] == True:
            pieceType = random.choice(config.pieceTypes)
            index = pieceTypeToNumber(pieceType)
        else:
            sevenBagger[index] = True
            valid = True
    return sevenBagger, pieceType
    
##########################################################################################################################
# MAIN:
def main():
    # DEFINITIONS:
    potentiometer = ADC(26)
    screenOff = False
    offButton = Pin(0, Pin.IN, Pin.PULL_UP)
    leftButton = Pin(1, Pin.IN, Pin.PULL_UP)
    rightButton = Pin(2, Pin.IN, Pin.PULL_UP)
    rotateButton = Pin(3, Pin.IN, Pin.PULL_UP)
    config = Config()
    conversion_factor, i2c, oled = readyDisplay(config)
    playArea = Area(config.height, config.width)
    b1 = Block(4, 0)
    tick = 0
    holdTick = 0
    holdingButton = False
    canFall = True
    hasLost = False
    buttonPressed = 0
    sevenBagger = [False for i in range(len(config.pieceTypes))]
    sevenBagger, pieceType = randomizer(sevenBagger, config)
    t1 = Tetrimino(pieceType, oled, config)
    # NOT DEFINITIONS:
    
    # the game's 20 tall, 10 wide
    # blocks are drawn within the bounds y = 3 to y = 57, x = 0 to x = 118
    
    while buttonPressed != 'O':
        # draw borders
        drawBorders(oled)
        
        # poll buttons
        buttonPressed = checkButtons(offButton, leftButton, rightButton, rotateButton)

        # falling tetrimino
        if t1.active == True:
            holdTick, holdingButton = evaluateButton(oled, config, playArea, t1, buttonPressed, tick, holdTick, holdingButton)
            if tick % config.tickrate == 0:
                t1.fall(oled, config, playArea)
                playArea.draw(oled, config)
        else:
            sevenBagger, pieceType = randomizer(sevenBagger, config)
            t1 = Tetrimino(pieceType, oled, config)
            hasLost = checkIfLost(config, playArea, t1.root)
            b1.active = not hasLost
            checkClear(playArea)
        
        if hasLost:
            print("you lose")
            buttonPressed = 'O'
            
        # game tickrate
        tick = tick + 1
        
        # display
        oled.show()
        
        # polling/refresh rate
        time.sleep(config.speed)

    # off button was pressed, while loop was ended:
    oled.poweroff()

##########################################################################################################################
# call main:
main()

"""
next: rotation! (oh jeez)
"""
  



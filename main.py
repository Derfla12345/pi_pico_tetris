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
        self.speed = 0.001
        # there is a variable tick that increments by 1 every loop until tick % tickrate == 0, at which point the game updates, TICKRATE is const while tickrate is modified
        self.TICKRATE = 10
        self.tickrate = self.TICKRATE
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
    def __init__(self, pieceType, oled, config, playArea):
        self.root = Block(4, 1)
        self.b1 = Block()
        self.b2 = Block()
        self.b3 = Block()
        self.blocks = [self.root, self.b1, self.b2, self.b3]
        self.active = True
        self.rotationState = 0
        self.pieceType = pieceType
        self._update(oled, config, playArea)
    def _update(self, oled, config, playArea):
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
        self.draw(oled, config, playArea)
    def draw(self, oled, config, playArea):
        oled.fill(0)
        drawBorders(oled)
        playArea.draw(oled, config)
        for block in self.blocks:
            block.draw(oled, config)
    def _place(self, oled, playArea):
        oled.fill(0)
        drawBorders(oled)
        for block in self.blocks:
            playArea.update(block)
        self.active = False
    def rotationCheck(self, config):
        self._rotationCheckLeft(config)
        self._rotationCheckRight(config)
        self._rotationCheckDown(config)
    def _rotationCheckRight(self, config):
        offset = 0
        for block in self.blocks:
            offset = min(offset, config.width - 1 - block.x)
        for block in self.blocks:
            block.x += offset
    def _rotationCheckLeft(self, config):
        offset = 0
        for block in self.blocks:
            offset = max(offset, -block.x)
        for block in self.blocks:
            block.x += offset
    def _rotationCheckDown(self, config):
        offset = 0
        for block in self.blocks:
            offset = min(offset, config.height - 2 - block.y)
        for block in self.blocks:
            block.y += offset
    def fall(self, oled, config, playArea):
        if ((not playArea.array[self.root.y + 1][self.root.x]) and (not playArea.array[self.b1.y + 1][self.b1.x]) and (not playArea.array[self.b2.y + 1][self.b2.x]) and (not playArea.array[self.b3.y + 1][self.b3.x])):
            for block in self.blocks:
                block.y += 1
            self.draw(oled, config, playArea)
        else:
            self._place(oled, playArea)
    def moveLeft(self, playArea):
        collision = False
        blockX = [block.x for block in self.blocks]
        minBlock = self.blocks[blockX.index(min(blockX))]
        if minBlock.x > 0:
            for block in self.blocks:
                if playArea.array[block.y][block.x - 1]:
                    collision = True
            if not collision:
                for block in self.blocks:
                    block.x -= 1
    def moveRight(self, config, playArea):
        collision = False
        blockX = [block.x for block in self.blocks]
        maxBlock = self.blocks[blockX.index(max(blockX))]
        if maxBlock.x < config.width - 1:
            for block in self.blocks:
                if playArea.array[block.y][block.x + 1]:
                    collision = True
            if not collision:
                for block in self.blocks:
                    block.x += 1
    def _checkUndo(self, playArea, undoBlocks):
        collision = False
        for block in self.blocks:
            if playArea.array[block.y][block.x]:
                print("whoops!")
                collision = True
        if collision:
            for i in range(len(self.blocks)):
                self.blocks[i].x = undoBlocks[i].x
                self.blocks[i].y = undoBlocks[i].y
    def rotateRight(self, oled, config, playArea):
        undoBlocks = [Block(self.root.x, self.root.y), Block(self.b1.x, self.b1.y), Block(self.b2.x, self.b2.y), Block(self.b3.x, self.b3.y)]
        self.rotationState = (self.rotationState + 1) % 4
        self._update(oled, config, playArea)
        self.rotationCheck(config)
        self._checkUndo(playArea, undoBlocks)
    def rotateLeft(self, oled, config, playArea):
        if self.rotationState == 0:
            self.rotationState = 3
        else:
            self.rotationState -= 1
        self._update(oled, config, playArea)
        self.rotationCheck(config)
    def hardDrop(self, oled, config, playArea):
        while ((not playArea.array[self.root.y + 1][self.root.x]) and (not playArea.array[self.b1.y + 1][self.b1.x]) and (not playArea.array[self.b2.y + 1][self.b2.x]) and (not playArea.array[self.b3.y + 1][self.b3.x])):
            for block in self.blocks:
                block.y += 1
        self._place(oled, playArea)
        self.draw(oled, config, playArea)
        
##########################################################################################################################
# FUNCTIONS:
# order of passing: oled, config, playArea, block, any additional info
def readyDisplay(config):
    displayWidth = config.displayWidth
    displayHeight = config.displayHeight

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

# 'L' is left, 'R' is right, 'D' is (soft) drop, 'M' is modifier (ML is rotate left, MR is rotate right, MD is hard drop)
def checkButtons(dropButton, leftButton, rightButton, modifyButton):
    buttonPressed = 0
    if modifyButton.value() != 1 or dropButton.value() != 1 or leftButton.value() != 1 or rightButton.value() != 1:
        buttonPressed = ''
        if modifyButton.value() != 1:
            buttonPressed += 'M'
        if dropButton.value() != 1:
            buttonPressed += 'D'
        if leftButton.value() != 1:
            buttonPressed += 'L'
        if rightButton.value() != 1:
            buttonPressed += 'R'
    return buttonPressed

# determines if the button is pressed and performs the relevant actions if so
def evaluateButton(oled, config, playArea, t1, buttonPressed, tick, holdTick, holdingButton):
    if buttonPressed and buttonPressed != 'M':
        holdTick, holdingButton = holdCheck(oled, config, playArea, t1, buttonPressed, tick, holdTick, holdingButton)
    else:
        normalDrop(config)
        holdTick = 0
        holdingButton = False
    return(holdTick, holdingButton)

# checks if buttons are held and sends inputs
def holdCheck(oled, config, playArea, t1, buttonPressed, tick, holdTick, holdingButton):
    if not holdTick:
        holdTick = 1
        moveBlock(oled, config, playArea, t1, buttonPressed)
    elif holdTick < config.holdDelay:
        holdTick += 1
    elif (holdTick >= config.holdDelay) or (holdingButton == True):
        holdingButton = True
        if buttonPressed != 'ML' and buttonPressed != 'MR':
            moveBlock(oled, config, playArea, t1, buttonPressed)
    return(holdTick, holdingButton)

# moves the block either left or right, or rotates it
def moveBlock(oled, config, playArea, t1, buttonPressed):
    if buttonPressed == 'L':
        t1.moveLeft(playArea)
    elif buttonPressed == 'R':
        t1.moveRight(config, playArea)
    elif buttonPressed == 'ML':
        t1.rotateLeft(oled, config, playArea)
    elif buttonPressed == 'MR':
        t1.rotateRight(oled, config, playArea)
    elif buttonPressed == 'D':
        softDrop(config)
    elif buttonPressed == 'MD':
        hardDrop(oled, config, playArea, t1)

# speeds up the rate at which tetriminos fall
def softDrop(config):
    config.tickrate = 2

# instantly drops a tetrimino
def hardDrop(oled, config, playArea, t1):
    t1.hardDrop(oled, config, playArea)

# returns tetrimino fall rate to normal
def normalDrop(config):
    config.tickrate = config.TICKRATE

# determine if the game has been lost (called at the creation of every new tetrimino)
def checkIfLost(config, playArea, t1):
    lost = False
    for block in t1.blocks:
        if playArea.array[1][block.x]:
            lost = True
    return lost

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
    dropButton = Pin(0, Pin.IN, Pin.PULL_UP) # k2
    leftButton = Pin(1, Pin.IN, Pin.PULL_UP) # k0
    rightButton = Pin(2, Pin.IN, Pin.PULL_UP) # k1
    modifyButton = Pin(3, Pin.IN, Pin.PULL_UP) # k3
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
    linesCleared = 0
    sevenBagger = [False for i in range(len(config.pieceTypes))]
    sevenBagger, pieceType = randomizer(sevenBagger, config)
    t1 = Tetrimino(pieceType, oled, config, playArea)
    # NOT DEFINITIONS:
    # the game's 20 tall, 10 wide (indices are different and weird)
    # blocks are drawn within the bounds y = 3 to y = 57, x = 0 to x = 118
    
    while buttonPressed != 'MDLR':
        # draw borders
        drawBorders(oled)
        
        # poll buttons
        buttonPressed = checkButtons(dropButton, leftButton, rightButton, modifyButton) #stopped here

        # falling tetrimino
        if t1.active == True:
            holdTick, holdingButton = evaluateButton(oled, config, playArea, t1, buttonPressed, tick, holdTick, holdingButton)
            if tick >= config.tickrate:
                t1.fall(oled, config, playArea)
                playArea.draw(oled, config)
                tick = 0
        else:
            sevenBagger, pieceType = randomizer(sevenBagger, config)
            t1 = Tetrimino(pieceType, oled, config, playArea)
            hasLost = checkIfLost(config, playArea, t1)
            b1.active = not hasLost
            linesCleared += checkClear(playArea)
        
        if hasLost:
            print("you lose")
            buttonPressed = 'O'
            
        # game tickrate
        tick = tick + 1
        
        # display
        t1.draw(oled, config, playArea)
        oled.show()
        
        # polling/refresh rate
        time.sleep(config.speed)

    # off button was pressed, while loop was ended:
    oled.poweroff()
    print(linesCleared)

##########################################################################################################################
# call main:
main()

"""
add score, next, or ramping up speed
"""
  



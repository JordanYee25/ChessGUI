import pygame, sys
from pygame.locals import *
pygame.init()

BOARDSIZE = 800
SQUARESIZE = BOARDSIZE/8
FPS = 60

DISPLAYSURF = pygame.display.set_mode((BOARDSIZE, BOARDSIZE), 0, 32)

pygame.display.set_caption('Chess!')
DISPLAYSURF.fill((255,255,255))
fps = pygame.time.Clock()

#Gameboard is created by two for loop that alternate color of square for all 64 squares
#If row and column is odd, set as dark square
def drawBoard(Display):
    for row in range(8):
        for col in range(8):
            if (row + col) % 2 == 1:  #dark squares
                rect = pygame.Rect(col * SQUARESIZE,row * SQUARESIZE, SQUARESIZE, SQUARESIZE)
                pygame.draw.rect(Display, (105, 146, 62), rect)
            else:
                rect = pygame.Rect(col * SQUARESIZE,row * SQUARESIZE, SQUARESIZE, SQUARESIZE)
                pygame.draw.rect(Display, (255,255,255), rect)

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()        

    drawBoard(DISPLAYSURF)
    pygame.display.update()
    fps.tick(FPS)


import pygame, sys, random, chess, platform
from board import boardState
from pygame.locals import *

WHITE = "w"
BLACK = "b"

UNICODE_PIECES = {
    "K": "♔",
    "Q": "♕",
    "R": "♖",
    "B": "♗",
    "N": "♘",
    "P": "♙",
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
}

BOARDSIZE = 800
FPS = 60


##############
#DO NOT TOUCH
##############

SQUARESIZE = BOARDSIZE/8 

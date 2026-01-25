import pygame, sys, random, chess, platform
from board import boardState
from pygame.locals import *
import config , game

newGame = game.game()

while True:

    gamestep = newGame.step()

    #PGN updated/prints per move
    if gamestep == "move":
        #If you want to access PGN once per turn
        PGN = newGame.PGN
        print("Game PGN: ", PGN)
    elif gamestep == "gameover": 
        break

    #Otherwise if you want PGN at every frame, for some reason:
    # PGN = newGame.PGN
    # print("Game PGN: ", PGN)

    # if gamestep == "gameover": 
    #     break


print("Game Over")

#Final PGN
FinalPGN = newGame.PGN
print("Game PGN: ", FinalPGN)
import pygame, sys, random, chess, platform
from board import boardState
from pygame.locals import *
import config 


class game:

    def __init__(self):
    
        self.board = boardState()

        pygame.init()
        self.DISPLAYSURF = pygame.display.set_mode((config.BOARDSIZE, config.BOARDSIZE), 0, 32)
        pygame.display.set_caption('Chess!')
        self.DISPLAYSURF.fill((255,255,255))
        
        self.fps = pygame.time.Clock()
        # Gets the font per system, optherwise pieces appear as empty rectangle
        self.PIECE_FONT = pygame.font.SysFont('arial', int(config.SQUARESIZE * 0.8))
        if platform.system() == "Windows":
            self.PIECE_FONT = pygame.font.SysFont('segoeuisymbol', int(config.SQUARESIZE * 0.8))  # Windows
        elif platform.system() == "Darwin":
            self.PIECE_FONT = pygame.font.SysFont('applesymbols', int(config.SQUARESIZE * 0.8))  # Mac

        self.drawBoard(self.DISPLAYSURF)
        self.drawPieces(self.DISPLAYSURF, self.board)  # Draw pieces on top of board



    #Gameboard is created by two for loop that alternate color of square for all 64 squares
    #If row and column is odd, set as dark square
    def drawBoard(self, Display):
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 1:  #dark squares
                    rect = pygame.Rect(col * config.SQUARESIZE,row * config.SQUARESIZE, config.SQUARESIZE, config.SQUARESIZE)
                    pygame.draw.rect(Display, (118, 150, 86), rect)
                else:
                    rect = pygame.Rect(col * config.SQUARESIZE,row * config.SQUARESIZE, config.SQUARESIZE, config.SQUARESIZE)
                    pygame.draw.rect(Display, (255,255,255), rect)


    def drawPieces(self, Display, board_state):
        # Iterate through all squares on the chess board
        for row in range(8):
            for col in range(8):
                # python-chess uses rank 0-7 (bottom to top) and file 0-7 (left to right)
                # We need to flip the row since pygame draws top to bottom
                chess_square = chess.square(col, 7 - row)
                piece = board_state.board.piece_at(chess_square)
                
                if piece:
                    # Get the unicode character for this piece
                    piece_symbol = piece.symbol()  # Returns 'K', 'q', 'P', etc.
                    unicode_piece = config.UNICODE_PIECES[piece_symbol]
                    
                    # Render the piece
                    piece_surface = self.PIECE_FONT.render(unicode_piece, True, (0, 0, 0))
                    
                    # Center the piece in the square
                    piece_rect = piece_surface.get_rect()
                    piece_rect.center = (col * config.SQUARESIZE + config.SQUARESIZE // 2,
                                        row * config.SQUARESIZE + config.SQUARESIZE // 2)
                    
                    Display.blit(piece_surface, piece_rect)

    def start(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()        

            pygame.display.update()
            self.fps.tick(config.FPS)




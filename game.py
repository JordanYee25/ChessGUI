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

        self.selectedPiece = None
        self.selectedPieceSquare = None

        self.drawBoard(self.DISPLAYSURF)
        self.drawPieces(self.DISPLAYSURF, self.board)  


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
                #flip the row since pygame draws top to bottom
                chess_square = chess.square(col, 7 - row)
                piece = board_state.board.piece_at(chess_square)
                
                if piece:
                    piece_symbol = piece.symbol()  # Returns 'K', 'q', 'P', etc.
                    unicode_piece = config.UNICODE_PIECES[piece_symbol]
                    piece_surface = self.PIECE_FONT.render(unicode_piece, True, (0, 0, 0))
                    
                    #Center
                    piece_rect = piece_surface.get_rect()
                    piece_rect.center = (col * config.SQUARESIZE + config.SQUARESIZE // 2,
                                        row * config.SQUARESIZE + config.SQUARESIZE // 2)
                    
                    Display.blit(piece_surface, piece_rect)


    #Given a square, if there exists a piece return the squares that it can move to
    def drawMoves(self, square):
        legalPieceMoves = []
        for move in self.legalPieceMoves(square):
            legalPieceMoves.append(move.to_square)

        self.drawMoveIndicators(self.DISPLAYSURF, legalPieceMoves)

    #Whenver the user clicks on a piece circles should pop up that show where the piece can move
    def drawMoveIndicators(self, Display, moveSquare):
        #Clear dots by redrawing the game board and pieces from the pychess board
        self.drawBoard(self.DISPLAYSURF)
        self.drawPieces(self.DISPLAYSURF, self.board)

        for square in moveSquare:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            
            center_x = int(col * config.SQUARESIZE + config.SQUARESIZE // 2)
            center_y = int(row * config.SQUARESIZE + config.SQUARESIZE // 2)
            radius = int(config.SQUARESIZE // 6)
            
            #TODO Change to semi transparent circle
            pygame.draw.circle(Display, (200, 200, 200, 128), (center_x, center_y), radius)
            

    def legalPieceMoves(self, square):
        piece = self.board.board.piece_at(square)
        if not piece: return []
        
        legalMoves = self.board.board.legal_moves
        legalPieceMoves = []

        for move in legalMoves:
            if move.from_square == square:
                legalPieceMoves.append(move)
    
        return legalPieceMoves
    

    def DisplaytoSquare(self, x, y):
        boardFile = int(x / config.SQUARESIZE)
        boardRank = int(8 - y / config.SQUARESIZE) #Coords are flipped for Y so flip it back
        return chess.square(boardFile, boardRank)
    

    def start(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()   
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    #Convert Display X Y to board X Y square
                    clickedSquare = self.DisplaytoSquare(x, y)

                    clickedPiece = self.board.board.piece_at(clickedSquare)
                    if clickedPiece  and clickedPiece.color == self.board.board.turn:
                        self.selectedPiece = clickedPiece
                        self.selectedPieceSquare = clickedSquare
                        self.drawMoves(clickedSquare)
                    
                    selectedPieceMoves = self.legalPieceMoves(self.selectedPieceSquare)
                    for move in selectedPieceMoves:
                        if move.to_square == clickedSquare:
                            selectedMove = move
                            #Move selected piece to move/make move in pychess and redraw
                            if move.promotion:
                                selectedMove = chess.Move(self.selectedPieceSquare, clickedSquare, chess.QUEEN)
                            self.board.board.push(selectedMove)
                            self.drawBoard(self.DISPLAYSURF)
                            self.drawPieces(self.DISPLAYSURF, self.board)
                            break
            
            if self.board.isGameOver():
                print("Game Over")
                break

            pygame.display.update()
            self.fps.tick(config.FPS)



##Add function for semi transparent move indicators

#Convert notation to Henry's requested format:
#  [Piece][Square][Modifier]

# 1. e4 e5 2. Nf3 Nc6 3. Bb5 Nd4 4. Nxd4 exd4 5. O-O Bc5 6. Bc4 d6 7. b3 Nf6 8.
# Re1 O-O 9. Bb2 Re8 10. d3 Bb6 11. Nd2 Be6 12. Bxe6 Rxe6 13. Nf3 c5 14. c3 Ng4
# 15. cxd4 cxd4 16. Nxd4 Rh6 17. Qxg4 Rg6 18. Qe2 Qg5 19. g3 Rf6 20. Nf3 Rxf3 21.
# Qxf3 Qd2 22. Re2 Qh6 23. d4 Re8 24. e5 dxe5 25. Rxe5 Rxe5 26. dxe5 Qd2 27. Bc3
# Bxf2+ 28. Qxf2 Qxc3 29. Rf1 Qc7 30. e6 f6 31. Qxa7 h6 32. Re1 Qe7 33. Qd4 Kh8
# 34. Qe4 Kg8 35. Rc1 Qd8 36. e7 Qb6+ 37. Kg2 g5 38. e8=Q+ Kg7 39. Q4g6# 1-0

# [['Pe4', 'Pe5'], ['Nf3', 'Nc6'], ['Bb5', 'Nd4'], ['Nd4x', 'Pd4ex'], ['O-O', 'Bc5'], ['Bc4', 'Pd6'], ['Pb3', 'Nf6'], ['Re1', 'O-O'], ['Bb2', 'Re8'], ['Pd3', 'Bb6'], ['Nd2', 'Be6'], ['Be6x', 'Re6x'], ['Nf3', 'Pc5'], ['Pc3', 'Ng4'], ['Pd4cx', 'Pd4cx'], ['Nd4x', 'Rh6'], ['Qg4x', 'Rg6'], ['Qe2', 'Qg5'], ['Pg3', 'Rf6'], ['Nf3', 'Rf3x'], ['Qf3x', 'Qd2'], ['Re2', 'Qh6'], ['Pd4', 'Re8'], ['Pe5', 'Pe5dx'], ['Re5x', 'Re5x'], ['Pe5dx', 'Qd2'], ['Bc3', 'Bf2x+'], ['Qf2x', 'Qc3x'], ['Rf1', 'Qc7'], ['Pe6', 'Pf6'], ['Qa7x', 'Ph6'], ['Re1', 'Qe7'], ['Qd4', 'Kh8'], ['Qe4', 'Kg8'], ['Rc1', 'Qd8'], ['Pe7', 'Qb6+'], ['Kg2', 'Pg5'], ['Pe8=Q+', 'Kg7'], ['Qg64#', '1-0']]
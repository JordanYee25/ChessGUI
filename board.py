
import chess

#File for running game operations. This will handle things like the board state and interacting with the chessAPI
class boardState:

    #board is a state of the board currently
    #move is the last move that resulted in this new board
    #boardState has a param for board as it doesnt assume all board begin from the zero move state
    #This allows any variation of chess board to be input
    def __init__(self, board : chess.Board = chess.Board()):
        self.board = board.copy() 
        self.turn = self.board.turn

        #Bad code, needs to be child of board
        self.winner = None # 'white' or 'black'
        self.draw = False

        # Integer value of points, white_pts being a value of 5 (for example) means that 
        # white has captured exactly enough of blacks pieces to get 5 points
        # Pawn = 1      Knight = 3
        # Bishop = 3    Rook = 5
        # Queen = 9     King = Win condt
        # self.white_pts = 0 
        # self.black_pts = 0  

    def generate_successor(self, state, move : chess.Move):
        successor = state.board.copy()
        successor.push(move)
        return boardState(successor, move)
    
    # Ret True or False (game not over)
    def isGameOver(self):
        if len(list(self.board.legal_moves)) == 0:
            return True
        return False
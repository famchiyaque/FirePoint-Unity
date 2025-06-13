from model.model import GameBoard

class GameModel:
    def __init__(self, mode, init_data):
        self.board = GameBoard(mode, init_data)

    def step(self):
        self.board.step()
        return self.board.get_state() 
    
    # def 
    
    @property
    def state(self):
        # obj = self.board.get_state()
        # print("in wrapper, returning: ")
        # print(obj)
        # return obj
        return self.board.get_state()

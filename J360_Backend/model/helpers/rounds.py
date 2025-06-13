def advance_fire(model):
    print('')

def move_bombero(model):
    # for random model, next spot is chosen at random


    # for smart model, will implement better logic later

    print('')

def begin_round(model):
    for fireSpot in model.fireSpots:
        advance_fire(model, fireSpot)
    for bombero in model.bomberos:
        move_bombero(model, bombero)
    return


def getBestStepToVic():
    # logic to get best steps for firefighter, in order, like heap
    return [0, 0]


def getBestStepOut():
    # logic to find quickest way out
    return [0, 0]

# def findVictim(self):
    #     best_step = getBestStepToVic() 

    #     if self.model.grid.cells[best_step[0], best_step[1]] == 2:
    #         self.ap -= 2
    #     else:
    #         self.ap -= 1

    #     self.model.grid.move_agent(self, best_step)

    # def saveVictim(self):
    #     best_step = getBestStepOut()

    #     self.ap -= 2
    #     self.model.grid.move_agent(self, best_step)
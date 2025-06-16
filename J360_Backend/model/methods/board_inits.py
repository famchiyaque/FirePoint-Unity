from model.config import SIZE_X, SIZE_Y, NUM_FIRE_START, NUM_SMOKE_START, NUM_POI_START, NUM_BOMBEROS
from model.classes.bombero import Bombero
from model.classes.smart_bombero import SmartBombero
from model.classes.barrier import Barrier

def _setup_barriers(self):
        """Set up walls and doors"""
        barriers_data = []

        entrances = [
            [(0, 3), (1, 3)], [(6, 0), (6, 1)], [(8, 4), (9, 4)], [(3, 6), (3, 7)] 
        ]

        entrance_set = {tuple(sorted((tuple(pos1), tuple(pos2)))) for pos1, pos2 in entrances}

        doors = [
            [(3, 1), (4, 1)], [(5, 2), (6, 2)], [(2, 3), (3, 3)], [(4, 4), (4, 5)], 
            [(6, 4), (7, 4)], [(8, 2), (8, 3)], [(5, 6), (6, 6)], [(7, 6), (8, 6)]
        ]

        other_walls = [
            [(3, 2), (4, 2)], [(3, 2), (3, 3)], [(4, 2), (4, 3)], [(5, 2), (5, 3)], 
            [(2, 4), (3, 4)], [(2, 4), (2, 5)], [(1, 4), (1, 5)], [(3, 4), (3, 5)],
            [(5, 4), (5, 5)], [(5, 1), (6, 1)], [(6, 2), (6, 3)], [(7, 2), (7, 3)],
            [(6, 3), (7, 3)], [(6, 4), (6, 5)], [(5, 5), (5, 6)], [(7, 4), (7, 5)],
            [(8, 4), (8, 5)], [(7, 5), (8, 5)]   
        ]

        for entrance in entrances:
             barriers_data.append([entrance[0], entrance[1], False, True, True])

        for door in doors:
            barriers_data.append([door[0], door[1], False, True, False])

        for other_wall in other_walls:
            barriers_data.append([other_wall[0], other_wall[1], True, False, False])
        
        for i in range(1, SIZE_X - 1):
            wall_segment = tuple(sorted([(i, 0), (i, 1)]))
            if wall_segment not in entrance_set:
                barriers_data.append([(i, 0), (i, 1), True, False, False])
            
            wall_segment = tuple(sorted([(i, 6), (i, 7)]))
            if wall_segment not in entrance_set:
                barriers_data.append([(i, 6), (i, 7), True, False, False])
        
        for i in range(1, SIZE_Y - 1):
            wall_segment = tuple(sorted([(0, i), (1, i)]))
            if wall_segment not in entrance_set:
                barriers_data.append([(0, i), (1, i), True, False, False])
            
            wall_segment = tuple(sorted([(8, i), (9, i)]))
            if wall_segment not in entrance_set:
                barriers_data.append([(8, i), (9, i), True, False, False])
        
        for pos1, pos2, is_wall, is_door, is_open in barriers_data:
            key = tuple(sorted([tuple(pos1), tuple(pos2)]))
            self.barriers[key] = Barrier(pos1, pos2, is_wall, is_door, is_open)

def _place_initial_tokens(self):
    """Randomly place initial fire, smoke, and POI tokens without overlap"""

    occupied = set()

    def get_random_position():
        while True:
            x = self.random.randint(1, SIZE_X - 2)
            y = self.random.randint(1, SIZE_Y - 2)
            if (x, y) not in occupied:
                occupied.add((x, y))
                return x, y

    # Place fire
    for _ in range(NUM_FIRE_START):
        x, y = get_random_position()
        tile = self.get_tile(x, y)
        tile.fire = True
        self.fire_spots.append(tile)

    # Place smoke
    for _ in range(NUM_SMOKE_START):
        while True:
            x, y = get_random_position()
            tile = self.get_tile(x, y)
            if not tile.fire:
                tile.smoke = True
                self.smoke_spots.append(tile)
                break

    # Place POIs
    for _ in range(NUM_POI_START):
        while True:
            x, y = get_random_position()
            tile = self.get_tile(x, y)
            if not tile.fire and not tile.smoke:
                tile.poi = True
                tile.victim = self.random.choice([True, False])
                self.poi_spots.append(tile)
                break

def _place_firefighters(self):
        """Place initial firefighters"""
        # Place at entrance
        entrance_positions = [(2, 0), (0, 3), (3, 7), (6, 0), (9, 4), (7, 7)]
        agent_id = SIZE_X * SIZE_Y  # Start after tile IDs
        # print("mode to determine which bomberos to create: ", self.mode)
        
        for i in range(NUM_BOMBEROS):
            x, y = entrance_positions[i]
            if self.mode == 'smart':
                # print("mode was smart, so placing SmartBombero")
                # bombero = SmartBombero(agent_id, self, x, y)
                bombero = SmartBombero(self, agent_id)
            else:
                # print("mode was not smart in bomber init")
                bombero = Bombero(self, agent_id)
                
            bombero.x = x
            bombero.y = y
            
            tile = self.get_tile(x, y)
            tile.bombero = bombero
            tile.has_bombero = True
            self.bomberos.append(bombero)
            self.schedule.add(bombero)
            agent_id += 1
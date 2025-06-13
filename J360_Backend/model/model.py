from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np
import random

NUM_BOMBEROS = 6
SIZE_X = 10  # 10 + 1
SIZE_Y = 8   # 8 + 1
LIMIT_RESCUED = 7
LIMIT_LOST = 4
LIMIT_BUILDING = 24
NUM_FIRE_START = 3
NUM_SMOKE_START = 3
NUM_POI_START = 3

# class Tile(Agent):
class Tile:
    """Tile agent that can hold fire, smoke, victims, etc."""
    def __init__(self, unique_id, model, x, y):
        # super().__init__(unique_id, model)
        self.unique_id = unique_id
        self.model = model
        self.x = x
        self.y = y
        self.fire = False
        self.smoke = False
        self.victim = False
        self.poi = False
        self.hot_spot = False
        self.has_bombero = False
        self.bombero = None
        # self.firefighter = None
        self.is_outside = (x == 0 or x == SIZE_X-1 or y == 0 or y == SIZE_Y-1)
    
    # def step(self):
    #     """Tile behavior during each step - currently just exists"""
    #     pass

class Barrier:
    def __init__(self, pos1, pos2, is_wall, is_door, is_open):
        self.pos1 = tuple(pos1)
        self.pos2 = tuple(pos2)
        self.damage_counters = 0
        self.is_wall = is_wall
        self.is_door = is_door
        self.is_open = is_open
        self.is_destroyed = False
    
    def add_damage(self):
        """Add damage to barrier"""
        if self.is_wall:
            self.damage_counters += 1
            if self.damage_counters >= 2:
                self.is_destroyed = True
        elif self.is_door:
            self.is_destroyed = True
    
    def can_pass_through(self):
        """Check if agents can pass through this barrier"""
        if self.is_destroyed:
            return True
        if self.is_door and self.is_open:
            return True
        return False
        
    
class SmartBombero(Agent):
    def __init__(self, model, unique_id):
        # super().__init__(unique_id, model)
        try:
            super().__init__(model)
        except Exception as e:
            print("ERROR during Agent init:", e)
            import traceback
            traceback.print_exc()
            raise e  # Optional: to keep the 500 behavior
        # self.x = x
        # self.y = y
        self.unique_id = unique_id
        self.ap = 4
        self.has_victim = False
        self.knocked_down = False
        self.path = []  # stores planned path for current goal

    def step(self):
        if self.knocked_down:
            return
        
        self.ap = 4  # Reset AP each turn
        while self.ap > 0:
            self.smart_action()

    def smart_action(self):
        current_tile = self.model.get_tile(self.x, self.y)

        # Priority 1: Extinguish fire on current tile
        if current_tile.fire and self.ap >= 2:
            current_tile.fire = False
            self.ap -= 2
            print(f"SmartBombero extinguished fire at ({self.x},{self.y})")
            return

        # Priority 2: Extinguish smoke on current tile
        if current_tile.smoke and self.ap >= 1:
            current_tile.smoke = False
            self.ap -= 1
            print(f"SmartBombero extinguished smoke at ({self.x},{self.y})")
            return

        # Priority 3: If on POI and not carrying victim, check it
        if current_tile.poi and not self.has_victim and self.ap >= 2:
            if current_tile.victim:
                self.has_victim = True
                current_tile.poi = False
                current_tile.victim = False
                if current_tile in self.model.poi_spots:
                    self.model.poi_spots.remove(current_tile)
                self.ap -= 2
                print(f"SmartBombero rescued a victim at ({self.x},{self.y})")
            else:
                current_tile.poi = False
                if current_tile in self.model.poi_spots:
                    self.model.poi_spots.remove(current_tile)
                self.ap -= 1
                print(f"SmartBombero checked POI - false alarm at ({self.x},{self.y})")
            return

        # If carrying victim, move to exit
        if self.has_victim:
            target = self.find_nearest_exit()
        else:
            # Otherwise, find nearest POI
            target = self.find_nearest_poi()

        # Move toward the target
        if target:
            if not self.path or self.path[-1] != target:
                self.path = self.find_path_to(*target)

            if self.path and len(self.path) > 1:  # ✅ Added self.path check
                next_x, next_y = self.path[1]
                cost = self.get_move_cost(next_x, next_y)
                if cost <= self.ap:
                    self.move_to(next_x, next_y)
                    self.ap -= cost
                    self.path.pop(0)
                    return


        # Nothing to do, end AP
        self.ap = 0

    def find_nearest_poi(self):
        min_dist = float('inf')
        closest = None
        for tile in self.model.poi_spots:
            dist = abs(tile.x - self.x) + abs(tile.y - self.y)
            if dist < min_dist:
                min_dist = dist
                closest = (tile.x, tile.y)
        return closest

    def find_nearest_exit(self):
        # Assume exit is any border tile
        exits = []
        for x in range(SIZE_X):
            exits.append((x, 0))
            exits.append((x, SIZE_Y - 1))
        for y in range(SIZE_Y):
            exits.append((0, y))
            exits.append((SIZE_X - 1, y))

        min_dist = float('inf')
        best = None
        for (ex, ey) in exits:
            dist = abs(self.x - ex) + abs(self.y - ey)
            if dist < min_dist:
                min_dist = dist
                best = (ex, ey)
        return best

    def find_path_to(self, target_x, target_y):
        """Breadth-First Search avoiding fire if possible"""
        from collections import deque

        visited = set()
        queue = deque()
        queue.append(((self.x, self.y), [(self.x, self.y)]))

        while queue:
            (cx, cy), path = queue.popleft()

            if (cx, cy) == (target_x, target_y):
                return path

            for nx, ny in self.model.get_neighbors(cx, cy):
                if (nx, ny) in visited:
                    continue
                tile = self.model.get_tile(nx, ny)
                if tile.fire:
                    continue  # Avoid stepping on fire if possible

                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
        return None

    def get_move_cost(self, x, y):
        tile = self.model.get_tile(x, y)
        return 2 if tile.fire else 1

    def move_to(self, x, y):
        old_tile = self.model.get_tile(self.x, self.y)
        old_tile.bombero = None
        old_tile.has_bombero = False

        self.x = x
        self.y = y
        new_tile = self.model.get_tile(x, y)
        new_tile.bombero = self
        new_tile.has_bombero = True

        print(f"SmartBombero moved to ({x},{y})")



class Bombero(Agent):
    """Firefighter agent"""
    def __init__(self, model, unique_id):
        # print(f"Initializing Bombero: at ({x}, {y})")
        try:
            super().__init__(model)
        except Exception as e:
            print("ERROR during Agent init:", e)
            import traceback
            traceback.print_exc()
            raise e  # Optional: to keep the 500 behavior
        # super().__init__(unique_id, model)
        # self.x = 0
        # self.y = 3
        # self.model = model
        self.ap = 4
        self.has_victim = False
        self.knocked_down = False
        self.unique_id = unique_id
        # print("basic configs setup well")
    
    def step(self):
        """Firefighter AI behavior - spend all AP each turn"""
        print(f"Bombero {self.unique_id} at ({self.x},{self.y}) taking a step with {self.ap} AP")
        
        if self.knocked_down:
            return
            
        # Spend all AP each turn
        while self.ap > 0:
            self.take_action()

    def take_action(self):
        """Take a single action based on current situation"""
        if self.ap <= 0:
            return
            
        current_tile = self.model.get_tile(self.x, self.y)
        
        # Check current tile for immediate actions
        if current_tile.fire and self.ap >= 2:
            # Random choice: extinguish fire or move through it
            if self.model.random.choice([True, False]):
                self.extinguish_fire(current_tile)
                return
        
        if current_tile.smoke and self.ap >= 1:
            self.extinguish_smoke(current_tile)
            return
            
        if current_tile.poi and not self.has_victim and self.ap >= 2:
            self.check_poi(current_tile)
            return
        
        # Try to move randomly
        self.random_move()

    def random_move(self):
        """Move randomly to an adjacent space"""
        if self.ap < 1:
            return
        
        # Get all adjacent positions (including blocked ones)
        adjacent_positions = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < SIZE_X and 0 <= ny < SIZE_Y:
                adjacent_positions.append((nx, ny))
        
        if not adjacent_positions:
            self.ap = 0  # No moves possible, end turn
            return
        
        # Pick random adjacent position
        target_x, target_y = self.model.random.choice(adjacent_positions)
        
        # Check if movement is blocked by barriers
        barrier = self.get_barrier_between((self.x, self.y), (target_x, target_y))
        
        if barrier and not barrier.can_pass_through():
            self.handle_barrier(barrier)
            return
        
        # Check target tile
        target_tile = self.model.get_tile(target_x, target_y)
        
        if target_tile.fire:
            # Random choice: extinguish or walk through
            if self.model.random.choice([True, False]) and self.ap >= 4:
                # Move and extinguish (2 AP to move through fire + 2 AP to extinguish)
                self.move_to(target_x, target_y, fire_cost=True)
                if self.ap >= 2:
                    self.extinguish_fire(target_tile)
            elif self.ap >= 2:
                # Just move through fire
                self.move_to(target_x, target_y, fire_cost=True)
            else:
                # Not enough AP, end turn
                self.ap = 0
        else:
            # Normal movement (1 AP)
            self.move_to(target_x, target_y)

    def get_barrier_between(self, pos1, pos2):
        """Get barrier between two positions"""
        key1 = tuple(sorted([pos1, pos2]))
        key2 = tuple(sorted([pos2, pos1]))
        return self.model.barriers.get(key1) or self.model.barriers.get(key2)
    
    def handle_barrier(self, barrier):
        """Handle interaction with walls/doors"""
        if barrier.is_door and not barrier.is_open and self.ap >= 1:
            # Open door (1 AP)
            barrier.is_open = True
            self.ap -= 1
            print(f"Bombero {self.unique_id} opened a door")
        elif barrier.is_wall and self.ap >= 2:
            # Hack wall (2 AP per hit)
            barrier.add_damage()
            self.model.total_damage_counters += 1
            self.ap -= 2
            print(f"Bombero {self.unique_id} hit a wall (damage: {barrier.damage_counters})")
        else:
            # Not enough AP or can't interact, end turn
            self.ap = 0

    def move_to(self, x, y, fire_cost=False):
        """Move to new position"""
        if self.ap < (2 if fire_cost else 1):
            return
            
        # Remove from old position
        old_tile = self.model.get_tile(self.x, self.y)
        old_tile.bombero = None
        old_tile.has_bombero = False
        
        # Move to new position
        self.x = x
        self.y = y
        new_tile = self.model.get_tile(x, y)
        new_tile.bombero = self
        new_tile.has_bombero = True
        
        # Deduct AP
        self.ap -= 2 if fire_cost else 1
        
        print(f"Bombero {self.unique_id} moved to ({x}, {y}), AP remaining: {self.ap}")

    def extinguish_fire(self, tile):
        """Extinguish fire (2 AP)"""
        if self.ap >= 2 and tile.fire:
            tile.fire = False
            self.ap -= 2
            # Remove from fire_spots list
            if tile in self.model.fire_spots:
                self.model.fire_spots.remove(tile)
            print(f"Bombero {self.unique_id} extinguished fire at ({tile.x}, {tile.y})")

    def extinguish_smoke(self, tile):
        """Extinguish smoke (1 AP)"""
        if self.ap >= 1 and tile.smoke:
            tile.smoke = False
            self.ap -= 1
            # Remove from smoke_spots list
            if tile in self.model.smoke_spots:
                self.model.smoke_spots.remove(tile)
            print(f"Bombero {self.unique_id} extinguished smoke at ({tile.x}, {tile.y})")

    def check_poi(self, tile):
        """Check POI and potentially rescue victim (2 AP to start carrying)"""
        if self.ap >= 2 and tile.poi and not self.has_victim:
            if tile.victim:
                # Start carrying victim
                self.has_victim = True
                tile.victim = False
                tile.poi = False
                self.ap -= 2
                print(f"Bombero {self.unique_id} rescued a victim!")
            else:
                # False alarm
                tile.poi = False
                self.ap -= 1  # Still takes some time to check
                print(f"Bombero {self.unique_id} checked POI - false alarm")

            if tile in self.model.poi_spots:
                self.model.poi_spots.remove(tile)
    
    # def random_action(self):
    #     """Perform a random action"""
    #     possible_actions = ['move', 'extinguish', 'stay']
    #     action = self.model.random.choice(possible_actions)
        
    #     if action == 'move':
    #         self.random_move()
    #     elif action == 'extinguish':
    #         self.random_extinguish()
    #     # 'stay' does nothing
    
    # def random_move(self):
    #     """Move randomly to adjacent space"""
    #     if self.ap < 1:
    #         return
        
    #     neighbors = self.model.get_neighbors(self.x, self.y)
    #     if neighbors:
    #         target_x, target_y = self.model.random.choice(neighbors)
    #         cost = self.get_move_cost(target_x, target_y)
    #         if cost <= self.ap:
    #             self.move_to(target_x, target_y)
    #             self.ap -= cost
    
    # def get_move_cost(self, x, y):
    #     """Get AP cost to move to position"""
    #     tile = self.model.get_tile(x, y)
    #     if tile.fire:
    #         return 2
    #     return 1
    
    # def move_to(self, x, y):
    #     """Move to new position"""
    #     # Remove from old position
    #     old_tile = self.model.get_tile(self.x, self.y)
    #     old_tile.bombero = None
    #     # old_tile.firefighter = None
        
    #     # Move to new position
    #     self.x = x
    #     self.y = y
    #     new_tile = self.model.get_tile(x, y)
    #     new_tile.bombero = self
    #     # new_tile.firefighter = self
    
    # def random_extinguish(self):
    #     """Randomly extinguish fire/smoke nearby"""
    #     if self.ap < 1:
    #         return
        
    #     # Try current position first
    #     current_tile = self.model.get_tile(self.x, self.y)
    #     if current_tile.fire and self.ap >= 2:
    #         current_tile.fire = False
    #         self.ap -= 2
    #         return
    #     elif current_tile.smoke and self.ap >= 1:
    #         current_tile.smoke = False
    #         self.ap -= 1
    #         return
        
    #     # Try adjacent positions
    #     neighbors = self.model.get_neighbors(self.x, self.y)
    #     for nx, ny in neighbors:
    #         tile = self.model.get_tile(nx, ny)
    #         if tile.fire and self.ap >= 2:
    #             tile.fire = False
    #             self.ap -= 2
    #             return
    #         elif tile.smoke and self.ap >= 1:
    #             tile.smoke = False
    #             self.ap -= 1
    #             return

def get_grid(model):
    """Get grid state for visualization"""
    return np.array([[
        4 if tile.bombero else
        3 if tile.victim else
        2 if tile.fire else
        1 if tile.smoke else
        0
        for tile in row
    ] for row in model.grid])

class GameBoard(Model):
    def __init__(self, mode='dumb', init_data=None):
        # super().__init__(seed=None)
        super().__init__()

        self.mode = mode
        
        self.schedule = RandomActivation(self)
        self.barriers = {}
        self.saved_victims = 0
        self.lost_victims = 0
        self.total_damage_counters = 0
        self.bomberos = []
        self.fire_spots = []
        self.smoke_spots = []
        self.poi_spots = []
        
        # Initialize grid with Tile agents
        self.grid = []
        agent_id = 0
        for x in range(SIZE_X):
            row = []
            for y in range(SIZE_Y):
                tile = Tile(agent_id, self, x, y)
                row.append(tile)
                # self.schedule.add(tile)
                agent_id += 1
            self.grid.append(row)
        
        self.datacollector = DataCollector(model_reporters={"Grid": get_grid})

        print("mode passed: ", mode)
        print("init_data passed: ", init_data)

        # Check if we have actual grid data to load
        if init_data and "grid" in init_data and len(init_data["grid"]) > 0:
            print("there was init data")
            # Load existing game state (this would be for /step calls)
            self.load_state(init_data)
        else:
            print("no init data, starting board")
             # Initialize board
            self._setup_barriers()
            # Create new game from scratch (this is for /init calls)
            self._place_initial_tokens()
            self._place_firefighters()
            # print("back here, about to get grid state")
            # grid_state = self.get_state()
            # print("returning grid state: ")
            # print(grid_state)
            # return grid_state
    
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

        # print("barriers setup finisehd")
        # print("current self.barriers: ", self.barriers)
    
    import random  # Ensure you import this at the top if not already

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

        # Place smoke (not on fire)
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
    
    def get_tile(self, x, y):
        """Get tile at position"""
        if 0 <= x < SIZE_X and 0 <= y < SIZE_Y:
            return self.grid[x][y]
        return None
    
    def get_neighbors(self, x, y):
        """Get valid neighboring positions"""
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < SIZE_X and 0 <= ny < SIZE_Y:
                # Check if movement is blocked by barriers
                if self._can_move_between((x, y), (nx, ny)):
                    neighbors.append((nx, ny))
        return neighbors
    
    def _can_move_between(self, pos1, pos2):
        """Check if movement between positions is allowed"""
        key1 = tuple(sorted([pos1, pos2]))
        key2 = tuple(sorted([pos2, pos1]))
        
        barrier = self.barriers.get(key1) or self.barriers.get(key2)
        if barrier:
            return barrier.can_pass_through()
        return True
    
    def advance_fire(self):
        """Advance fire according to game rules"""
        # Roll dice to determine target space
        target_x = self.random.randint(1, SIZE_X - 2)
        target_y = self.random.randint(1, SIZE_Y - 2)
        
        target_tile = self.get_tile(target_x, target_y)
        
        if target_tile.fire:
            # Explosion!
            self._handle_explosion(target_x, target_y)
        elif target_tile.smoke:
            # Smoke + Smoke = Fire
            target_tile.smoke = False
            target_tile.fire = True
            if target_tile in self.smoke_spots:
                self.smoke_spots.remove(target_tile)
            self.fire_spots.append(target_tile)
        else:
            # Place smoke
            target_tile.smoke = True
            self.smoke_spots.append(target_tile)
            
            # Check if smoke is adjacent to fire
            self._check_smoke_adjacent_to_fire(target_x, target_y)
    
    def _handle_explosion(self, x, y):
        """Handle explosion at position"""
        print(f"Explosion at ({x}, {y})!")
        
        # Spread fire in all directions
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            self._handle_explosion_direction(x, y, dx, dy)
    
    def _handle_explosion_direction(self, start_x, start_y, dx, dy):
        """Handle explosion in one direction"""
        current_x, current_y = start_x + dx, start_y + dy
        
        # Check bounds
        if not (0 <= current_x < SIZE_X and 0 <= current_y < SIZE_Y):
            return
        
        tile = self.get_tile(current_x, current_y)
        
        if tile.fire:
            # Shockwave continues
            self._handle_shockwave(current_x, current_y, dx, dy)
        elif tile.smoke:
            # Flip smoke to fire
            tile.smoke = False
            tile.fire = True
            if tile in self.smoke_spots:
                self.smoke_spots.remove(tile)
            self.fire_spots.append(tile)
        else:
            # Place fire in open space
            tile.fire = True
            self.fire_spots.append(tile)
        
        # Damage walls/doors adjacent to explosion center
        self._damage_barriers_around(start_x, start_y)
    
    def _handle_shockwave(self, x, y, dx, dy):
        """Handle shockwave traveling through fire"""
        current_x, current_y = x, y
        
        while True:
            current_x += dx
            current_y += dy
            
            # Check bounds
            if not (0 <= current_x < SIZE_X and 0 <= current_y < SIZE_Y):
                break
            
            tile = self.get_tile(current_x, current_y)
            
            if tile.fire:
                # Continue shockwave
                continue
            elif tile.smoke:
                # Flip smoke to fire and stop
                tile.smoke = False
                tile.fire = True
                if tile in self.smoke_spots:
                    self.smoke_spots.remove(tile)
                self.fire_spots.append(tile)
                break
            else:
                # Open space - place fire and stop
                tile.fire = True
                self.fire_spots.append(tile)
                break
    
    def _damage_barriers_around(self, x, y):
        """Damage barriers around a position"""
        neighbors = [(x, y+1), (x, y-1), (x+1, y), (x-1, y)]
        
        for nx, ny in neighbors:
            key1 = tuple(sorted([(x, y), (nx, ny)]))
            key2 = tuple(sorted([(nx, ny), (x, y)]))
            
            barrier = self.barriers.get(key1) or self.barriers.get(key2)
            if barrier:
                barrier.add_damage()
                self.total_damage_counters += 1
    
    def _check_smoke_adjacent_to_fire(self, x, y):
        """Check if smoke is adjacent to fire and convert if so"""
        tile = self.get_tile(x, y)
        if not tile.smoke:
            return
        
        # Check all adjacent positions for fire
        for nx, ny in self.get_neighbors(x, y):
            neighbor = self.get_tile(nx, ny)
            if neighbor.fire:
                # Convert smoke to fire
                tile.smoke = False
                tile.fire = True
                if tile in self.smoke_spots:
                    self.smoke_spots.remove(tile)
                self.fire_spots.append(tile)
                break
    
    def apply_secondary_effects(self):
        """Apply flashover and other secondary effects"""
        # Flashover - convert all smoke adjacent to fire
        changed = True
        while changed:
            changed = False
            for tile in self.smoke_spots[:]:  # Copy list since we modify it
                for nx, ny in self.get_neighbors(tile.x, tile.y):
                    neighbor = self.get_tile(nx, ny)
                    if neighbor.fire:
                        tile.smoke = False
                        tile.fire = True
                        self.smoke_spots.remove(tile)
                        self.fire_spots.append(tile)
                        changed = True
                        break
        
        # Check for victims/POI lost to fire
        for row in self.grid:
            for tile in row:
                if tile.fire and (tile.victim or tile.poi):
                    if tile.victim:
                        self.lost_victims += 1
                    tile.victim = False
                    tile.poi = False
        
        # Remove fire markers outside building
        for row in self.grid:
            for tile in row:
                if tile.is_outside and tile.fire:
                    tile.fire = False
                    if tile in self.fire_spots:
                        self.fire_spots.remove(tile)
    
    def reset_firefighter_ap(self):
        """Reset action points for all firefighters"""
        for bombero in self.bomberos:
            bombero.ap = 4

    def reset_pois(self):
        while len(self.poi_spots) < NUM_POI_START:
            x = self.random.randint(1, SIZE_X - 2)
            y = self.random.randint(1, SIZE_Y - 2)
            tile = self.get_tile(x, y)
            if not tile.fire and not tile.smoke and not tile.poi:
                tile.poi = True
                tile.victim = self.random.choice([True, False])
                self.poi_spots.append(tile)

    
    def load_state(self, init_data):
        """Load state from Unity data format"""
        try:
            if "grid" in init_data:
                for row_data in init_data["grid"]:
                    for tile_data in row_data:
                        x, y = tile_data["x"], tile_data["y"]
                        if 0 <= x < SIZE_X and 0 <= y < SIZE_Y:
                            tile = self.get_tile(x, y)
                            tile.fire = tile_data.get("fire", False)
                            tile.smoke = tile_data.get("smoke", False)
                            tile.victim = tile_data.get("victim", False)
                            tile.poi = tile_data.get("poi", False)
                            tile.hot_spot = tile_data.get("hot_spot", False)
                            firefighter_data = tile_data.get("firefighter", None)
                            if firefighter_data:
                                # Create firefighter at this position
                                bombero = Bombero(len(self.bomberos) + SIZE_X * SIZE_Y, self, x, y)
                                tile.bombero = bombero
                                # tile.firefighter = bombero
                                self.bomberos.append(bombero)
                                self.schedule.add(bombero)
        except Exception as e:
            print(f"Error loading state: {e}")
    
    def get_state(self):
        """Return state in Unity format"""
        state = []
        for row in self.grid:
            row_data = []
            for tile in row:
                bombero = None
                if tile.bombero:
                    bombero = {
                        "id": tile.bombero.unique_id,
                        "ap": tile.bombero.ap,
                        "has_victim": tile.bombero.has_victim
                    }
                
                row_data.append({
                    "x": tile.x,
                    "y": tile.y,
                    "fire": tile.fire,
                    "smoke": tile.smoke,
                    "victim": tile.victim,
                    "poi": tile.poi,
                    "hot_spot": tile.hot_spot,
                    "bombero": bombero,
                    "is_outside": tile.is_outside
                })
            state.append(row_data)

        return ({
            "grid": state,
            "barriers": self.get_barriers(),
            "total_damage": self.total_damage_counters,
            "saved_victims": self.saved_victims,
            "lost_victims": self.lost_victims
        })
    
    def get_barriers(self):
        """Convert barriers to JSON-serializable format"""
        barriers_state = []

        for key, barrier in self.barriers.items():
            pos1, pos2 = key
            barriers_state.append({
                "from": {"x": pos1[0], "y": pos1[1]},
                "to": {"x": pos2[0], "y": pos2[1]},
                "is_wall": barrier.is_wall,
                "is_door": barrier.is_door,
                "is_open": barrier.is_open,
                "is_destroyed": barrier.is_destroyed,
                "damage_counters": barrier.damage_counters
            })

        return barriers_state

    
    def game_over(self):
        """Check if game is over"""
        return (
            self.saved_victims >= LIMIT_RESCUED or 
            self.lost_victims >= LIMIT_LOST or 
            self.total_damage_counters >= LIMIT_BUILDING
        )
    
    def step(self):
        """Execute one game turn"""
        if self.game_over():
            return {"grid": self.get_state()["grid"], "status": "game_over"}
        
        try:
            # Reset firefighter action points
            self.reset_firefighter_ap()
            print("got past bomberos movements alright")

            # reset pois if any have been found
            self.reset_pois()
            print("got past the poi checker alright")
            
            # Firefighters take actions
            self.schedule.step()
            print("got past the step call")
            
            # Advance fire
            self.advance_fire()
            print("past the advance dire dall")
            
            # Apply secondary effects
            self.apply_secondary_effects()
            
            # Collect data
            self.datacollector.collect(self)
            
        except Exception as e:
            print(f"Error in step: {e}")
        
        return self.get_state()
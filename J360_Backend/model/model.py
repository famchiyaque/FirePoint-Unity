from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np

# from bombero import Bombero
# from smart_bombero import SmartBombero

from model.config import (
    NUM_BOMBEROS, SIZE_X, SIZE_Y, LIMIT_RESCUED, LIMIT_LOST,
    LIMIT_BUILDING, NUM_FIRE_START, NUM_SMOKE_START, NUM_POI_START
)

from model.methods.board_inits import (
    _setup_barriers, _place_initial_tokens, _place_firefighters
)

from model.methods.hazards import (
    advance_fire, apply_secondary_effects
)

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
        self.is_being_hunted = False
        # self.firefighter = None
        self.is_outside = (x == 0 or x == SIZE_X-1 or y == 0 or y == SIZE_Y-1)
    
    # def step(self):
    #     """Tile behavior during each step - currently just exists"""
    #     pass


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
            print("################this was actually called tf")
            # Load existing game state (this would be for /step calls)
            self.load_state(init_data)
        else:
            print("no init data, starting board")
             # Initialize board
            # self._setup_barriers()
            _setup_barriers(self)
            # Create new game from scratch (this is for /init calls)
            # self._place_initial_tokens()
            _place_initial_tokens(self)
            # self._place_firefighters()
            _place_firefighters(self)
            # print("back here, about to get grid state")
            # grid_state = self.get_state()
            # print("returning grid state: ")
            # print(grid_state)
            # return grid_state
    
    # import random  # Ensure you import this at the top if not already

    
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
    
    def reset_firefighter_ap(self):
        """Reset action points for all firefighters"""
        print("resetting bombers ap")
        for bombero in self.bomberos:
            bombero.ap = 4

    def reset_pois(self):
        print("pois length: ", len(self.poi_spots))
        while len(self.poi_spots) < NUM_POI_START:
            x = self.random.randint(1, SIZE_X - 2)
            y = self.random.randint(1, SIZE_Y - 2)
            tile = self.get_tile(x, y)
            if not tile.fire and not tile.smoke and not tile.poi:
                tile.poi = True
                tile.victim = self.random.choice([True, False])
                self.poi_spots.append(tile)

    
    # def load_state(self, init_data):
    #     print("load state was called")
    #     """Load state from Unity data format"""
    #     try:
    #         if "grid" in init_data:
    #             for row_data in init_data["grid"]:
    #                 for tile_data in row_data:
    #                     x, y = tile_data["x"], tile_data["y"]
    #                     if 0 <= x < SIZE_X and 0 <= y < SIZE_Y:
    #                         tile = self.get_tile(x, y)
    #                         tile.fire = tile_data.get("fire", False)
    #                         tile.smoke = tile_data.get("smoke", False)
    #                         tile.victim = tile_data.get("victim", False)
    #                         tile.poi = tile_data.get("poi", False)
    #                         tile.hot_spot = tile_data.get("hot_spot", False)
    #                         firefighter_data = tile_data.get("firefighter", None)
    #                         if firefighter_data:
    #                             # Create firefighter at this position
    #                             bombero = Bombero(len(self.bomberos) + SIZE_X * SIZE_Y, self, x, y)
    #                             tile.bombero = bombero
    #                             # tile.firefighter = bombero
    #                             self.bomberos.append(bombero)
    #                             self.schedule.add(bombero)
    #     except Exception as e:
    #         print(f"Error loading state: {e}")
    
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
    
    def print_spots(self, name):
        if name == 'pois':
            for poi in self.poi_spots:
                print("1: ", poi.x, " ", poi.y)
        if name == 'fire':
            for fire in self.fire_spots:
                print("1: ", fire.x, " ", fire.y)
        if name == 'smoke':
            for smoke in self.smoke_spots:
                print("1: ", smoke.x, " ", smoke.y)
    
    def step(self):
        print("in step function")
        print("current poi spots: ")
        self.print_spots('pois')
        print("current fire spots: ")
        self.print_spots('fire')
        print("current smoke spots: ")
        self.print_spots('smoke')
        # print("current fire spots: ", self.fire_spots)

        """Execute one game turn"""
        if self.game_over():
            return {"grid": self.get_state()["grid"], "status": "game_over"}
        
        try:
            # Reset firefighter action points
            self.reset_firefighter_ap()
            print("got past bomberos reset ap alright")
            
            # Firefighters take actions
            self.schedule.step()
            print("got past the schedule step call")
            
            # Advance fire
            # self.advance_fire()
            advance_fire(self)
            print("past the advance dire dall")
            
            # Apply secondary effects
            # self.apply_secondary_effects()
            apply_secondary_effects(self)

            # reset pois if any have been found
            self.reset_pois()
            print("got past the poi checker alright")
            print("pois length after: ", len(self.poi_spots))
            
            # Collect data
            self.datacollector.collect(self)
            
        except Exception as e:
            print(f"Error in step: {e}")
        
        return self.get_state()
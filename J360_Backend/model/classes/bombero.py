from mesa import Agent

from model.config import SIZE_X, SIZE_Y

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
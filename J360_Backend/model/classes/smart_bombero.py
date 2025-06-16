from mesa import Agent
import heapq

from model.config import SIZE_X, SIZE_Y, NUM_POI_START

class SmartBombero(Agent):
    def __init__(self, model, unique_id):
        try:
            super().__init__(model)
        except Exception as e:
            print("ERROR during Agent init:", e)
            import traceback
            traceback.print_exc()
            raise e

        self.unique_id = unique_id
        self.ap = 4
        self.has_victim = False
        self.knocked_down = False
        self.path = []  # stores planned path for current goal

    def step(self):
        current_tile = self.model.get_tile(self.x, self.y)
        print("in step for bombero: ", self.unique_id, "with ", self.ap, " ap at: ", current_tile.x, ", ", current_tile.y)
        
        if self.knocked_down:
            print("knocked down was true")
            return        
        
        # Add safety mechanism to prevent infinite loops
        max_iterations = 10
        iteration_count = 0
        
        while self.ap > 0 and iteration_count < max_iterations:
            old_ap = self.ap
            
            if len(self.model.poi_spots) < NUM_POI_START:
                self.model.reset_pois()
            
            self.smart_action()
            iteration_count += 1
            
            # Safety check to prevent infinite loops
            if self.ap == old_ap:
                print(f"SmartBombero {self.unique_id} couldn't find valid action, ending turn")
                self.ap = 0  # Force end turn if no AP was consumed
                break
        
        if iteration_count >= max_iterations:
            print(f"SmartBombero {self.unique_id} hit max iterations, forcing end turn")
            self.ap = 0

    def smart_action(self):
        current_tile = self.model.get_tile(self.x, self.y)
        print("Current tile:", current_tile.x, current_tile.y)

        # Priority 1: Extinguish fire on current tile
        if current_tile.fire and self.ap >= 2:
            current_tile.fire = False
            if current_tile in self.model.fire_spots:
                self.model.fire_spots.remove(current_tile)
            self.ap -= 2
            print(f"SmartBombero extinguished fire at ({self.x},{self.y})")
            return

        # Priority 2: Extinguish smoke on current tile
        if current_tile.smoke and self.ap >= 1:
            current_tile.smoke = False
            if current_tile in self.model.smoke_spots:
                self.model.smoke_spots.remove(current_tile)
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
                print(f"SmartBombero rescued a victim at ({self.x},{self.y})")
            else:
                current_tile.poi = False
                if current_tile in self.model.poi_spots:
                    self.model.poi_spots.remove(current_tile)
                print(f"SmartBombero checked POI - false alarm at ({self.x},{self.y})")
            
            # FIX: Always consume AP for checking POI
            # self.ap -= 2
            return

        # Priority 4: Drop off victim if at exit
        if self.has_victim and current_tile.is_outside and self.ap >= 1:
            self.has_victim = False
            self.model.saved_victims += 1
            self.ap -= 1
            print(f"SmartBombero dropped off victim at exit ({self.x},{self.y})")
            return

        # Priority 5: Extinguish nearby fire or smoke
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < SIZE_X and 0 <= ny < SIZE_Y:
                tile = self.model.get_tile(nx, ny)
                if tile.fire and self.ap >= 2:
                    tile.fire = False
                    # FIX: Remove the correct tile from fire_spots
                    if tile in self.model.fire_spots:
                        self.model.fire_spots.remove(tile)
                    self.ap -= 2
                    print(f"Bombero {self.unique_id} extinguished fire at ({nx},{ny})")
                    return
                elif tile.smoke and self.ap >= 1:
                    tile.smoke = False
                    # FIX: Remove the correct tile from smoke_spots
                    if tile in self.model.smoke_spots:
                        self.model.smoke_spots.remove(tile)
                    self.ap -= 1
                    print(f"Bombero {self.unique_id} cleared smoke at ({nx},{ny})")
                    return

        # Determine target (POI or Exit)
        target = self.find_nearest_exit() if self.has_victim else self.find_nearest_poi()
        print("New target is:", target)

        # Movement logic using Dijkstra and try_follow_path
        if target:
            if not self.path or self.path[-1] != target:
                self.path = self.find_path_to_dijkstra(*target)
                print(f"Calculated new path: {self.path}")

            if self.path and len(self.path) > 1:
                # Store current position to detect if movement succeeded
                old_pos = (self.x, self.y)
                old_ap = self.ap
                
                self.try_follow_path(self.path)
                
                # If we didn't move and didn't use AP, we're stuck
                if (self.x, self.y) == old_pos and self.ap == old_ap:
                    print(f"SmartBombero {self.unique_id} is stuck, ending turn")
                    self.ap = 0
            else:
                print(f"SmartBombero {self.unique_id} no valid path, ending turn")
                self.ap = 0
        else:
            print(f"SmartBombero {self.unique_id} no target found, ending turn")
            self.ap = 0

    def find_nearest_poi(self):
        if not self.model.poi_spots:
            return None
        
        min_dist = float('inf')
        closest = None
        # Create a copy to avoid modification during iteration
        poi_list = list(self.model.poi_spots)
        for tile in poi_list:
            dist = abs(tile.x - self.x) + abs(tile.y - self.y)
            if dist < min_dist:
                min_dist = dist
                closest = (tile.x, tile.y)
        return closest

    def find_nearest_exit(self):
        # Find all border tiles (exits)
        exits = []
        for x in range(SIZE_X):
            if x == 0 or x == SIZE_X - 1:
                for y in range(SIZE_Y):
                    exits.append((x, y))
        for y in range(SIZE_Y):
            if y == 0 or y == SIZE_Y - 1:
                for x in range(SIZE_X):
                    if (x, y) not in exits:  # Avoid duplicates at corners
                        exits.append((x, y))

        min_dist = float('inf')
        best = None
        for (ex, ey) in exits:
            dist = abs(self.x - ex) + abs(self.y - ey)
            if dist < min_dist:
                min_dist = dist
                best = (ex, ey)
        return best
    
    def try_follow_path(self, path):
        while self.ap > 0 and len(path) > 1:
            next_x, next_y = path[1]
            barrier = self.get_barrier_between((self.x, self.y), (next_x, next_y))
            
            if barrier and not barrier.can_pass_through():
                # Try to damage it
                if self.ap >= 2:
                    barrier.add_damage()
                    self.ap -= 2
                    print(f"Bombero {self.unique_id} hit barrier at {barrier.pos1}, {barrier.pos2}")
                    if barrier.can_pass_through():
                        print("Barrier now open.")
                    return  # Used AP to interact
                else:
                    print(f"Bombero {self.unique_id} can't afford to hit barrier")
                    return  # Not enough AP to interact

            cost = self.get_move_cost(next_x, next_y)
            if cost > self.ap:
                print(f"Bombero {self.unique_id} can't afford move cost {cost}")
                return  # Can't afford this move

            self.move_to(next_x, next_y)  # ✅ THIS is where movement happens
            self.ap -= cost
            path.pop(0)
            print(f"Bombero {self.unique_id} moved to ({next_x}, {next_y}), AP remaining: {self.ap}")

    def find_path_to(self, target_x, target_y):
        """Breadth-First Search with barrier awareness"""
        from collections import deque

        visited = set()
        queue = deque()
        queue.append(((self.x, self.y), [(self.x, self.y)]))
        visited.add((self.x, self.y))

        while queue:
            (cx, cy), path = queue.popleft()

            if (cx, cy) == (target_x, target_y):
                return path

            # Check all neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                
                # Check bounds
                if not (0 <= nx < SIZE_X and 0 <= ny < SIZE_Y):
                    continue
                    
                if (nx, ny) in visited:
                    continue

                # Check for barriers
                barrier = self.get_barrier_between((cx, cy), (nx, ny))
                if barrier and not barrier.can_pass_through():
                    continue

                # Avoid fire tiles if possible (but don't completely block path)
                tile = self.model.get_tile(nx, ny)
                
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
        
        return None  # No path found

    def find_path_to_dijkstra(self, target_x, target_y):
        """Dijkstra's pathfinding with tile weights and barrier costs"""
        import heapq
        
        heap = []
        heapq.heappush(heap, (0, [(self.x, self.y)]))  # (cost, path)

        visited = {}

        while heap:
            cost, path = heapq.heappop(heap)
            x, y = path[-1]

            if (x, y) == (target_x, target_y):
                return path

            if (x, y) in visited and visited[(x, y)] <= cost:
                continue
            visited[(x, y)] = cost

            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < SIZE_X and 0 <= ny < SIZE_Y):
                    continue

                barrier = self.get_barrier_between((x, y), (nx, ny))
                tile = self.model.get_tile(nx, ny)

                step_cost = 1
                # Adjust cost for fire
                if tile.fire:
                    step_cost = 2

                # Carrying victim increases movement cost
                if self.has_victim:
                    step_cost += 1

                # Add barrier cost
                if barrier:
                    if barrier.is_door:
                        if not barrier.is_open:
                            step_cost += 1  # opening the door
                    elif barrier.is_wall:
                        if barrier.damage_counters < 2:
                            remaining_hits = 2 - barrier.damage_counters
                            step_cost += remaining_hits * 2  # 2 AP per hit

                heapq.heappush(heap, (cost + step_cost, path + [(nx, ny)]))

        return None  # no path found

    def get_barrier_between(self, pos1, pos2):
        """Get barrier between two positions"""
        key1 = tuple(sorted([pos1, pos2]))
        return self.model.barriers.get(key1)

    def handle_barrier(self, barrier):
        """Handle interaction with walls/doors, returns True if AP was consumed"""
        if barrier.is_door and not barrier.is_open and self.ap >= 1:
            # Open door (1 AP)
            barrier.is_open = True
            self.ap -= 1
            print(f"SmartBombero {self.unique_id} opened a door")
            return True
        elif barrier.is_wall and self.ap >= 2:
            # Hack wall (2 AP per hit)
            barrier.add_damage()
            self.model.total_damage_counters += 1
            self.ap -= 2
            print(f"SmartBombero {self.unique_id} hit a wall (damage: {barrier.damage_counters})")
            return True
        else:
            # Not enough AP or can't interact
            return False

    def get_move_cost(self, x, y):
        tile = self.model.get_tile(x, y)
        return 2 if tile.fire or self.has_victim else 1

    def move_to(self, x, y):
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

        print(f"SmartBombero moved to ({x},{y})")
from model.config import SIZE_X, SIZE_Y, NUM_FIRE_START, NUM_SMOKE_START, NUM_POI_START, NUM_BOMBEROS

def advance_fire(self):
        """Advance fire according to game rules"""
        # Roll dice to determine target space
        target_x = self.random.randint(1, SIZE_X - 2)
        target_y = self.random.randint(1, SIZE_Y - 2)
        
        target_tile = self.get_tile(target_x, target_y)
        
        if target_tile.fire:
            # Explosion!
            _handle_explosion(self, target_x, target_y)
            # self._handle_explosion(target_x, target_y)
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
            # self._check_smoke_adjacent_to_fire(target_x, target_y)
            _check_smoke_adjacent_to_fire(self, target_x, target_y)

def _handle_explosion(self, x, y):
        """Handle explosion at position"""
        print(f"Explosion at ({x}, {y})!")
        
        # Spread fire in all directions
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            _handle_explosion_direction(self, x, y, dx, dy)
            # self._handle_explosion_direction(x, y, dx, dy)

def _handle_explosion_direction(self, start_x, start_y, dx, dy):
        """Handle explosion in one direction"""
        current_x, current_y = start_x + dx, start_y + dy
        
        # Check bounds
        if not (0 <= current_x < SIZE_X and 0 <= current_y < SIZE_Y):
            return
        
        tile = self.get_tile(current_x, current_y)
        
        if tile.fire:
            # Shockwave continues
            # self._handle_shockwave(current_x, current_y, dx, dy)
            _handle_shockwave(self, current_x, current_y, dx, dy)
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
        # self._damage_barriers_around(start_x, start_y)
        _damage_barriers_around(self, start_x, start_y)

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
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
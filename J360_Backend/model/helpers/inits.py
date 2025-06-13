def barrier_key(a, b):
    return tuple(sorted([a, b]))  # Fixed: was missing brackets around [a, b]


def set_map_barriers(model):
    from ..azar import Barrier  # Import only what's needed
    
    barriers_data = [
        # doors
        [(0, 3), (1, 3), False, True, True],
        [(3, 1), (4, 1), False, True, False],
        [(6, 0), (6, 1), False, True, True],
        [(5, 2), (6, 2), False, True, False],
        [(2, 3), (3, 3), False, True, False],
        [(4, 4), (4, 5), False, True, False],
        [(6, 4), (7, 4), False, True, False],
        [(8, 2), (8, 3), False, True, False],
        [(8, 4), (9, 4), False, True, True],
        [(3, 6), (3, 7), False, True, True],
        [(5, 6), (5, 7), False, True, False],
        [(7, 7), (7, 8), False, True, False],
    ]

    # Add walls
    SIZE_X = 11  # 10 + 1
    SIZE_Y = 9   # 8 + 1
    
    for i in range(1, SIZE_X):
        barriers_data.append([(i, 0), (i, 1), True, False, False])  # top wall
        barriers_data.append([(i, 6), (i, 7), True, False, False])  # bottom wall
    for i in range(1, SIZE_Y):
        barriers_data.append([(0, i), (1, i), True, False, False])  # left wall
        barriers_data.append([(8, i), (9, i), True, False, False])  # right wall

    for (a, b, is_wall, is_door, is_open) in barriers_data:
        key = barrier_key(a, b)
        model.barriers[key] = Barrier(a, b, is_wall, is_door, is_open)


def setRandomTokens(model):
    """Set random tokens on the board - SIMPLIFIED VERSION"""
    from ..azar import Tile
    import random
    
    SIZE_X = 11
    SIZE_Y = 9
    NUM_FIRE_START = 3
    NUM_SMOKE_START = 3
    NUM_POI_START = 3
    
    # Initialize random seed if model doesn't have random
    if not hasattr(model, 'random'):
        model.random = random.Random()
    
    # Place fire tokens
    fire_placed = 0
    attempts = 0
    while fire_placed < NUM_FIRE_START and attempts < 100:
        x = model.random.randrange(1, SIZE_X - 1)
        y = model.random.randrange(1, SIZE_Y - 1)
        if not model.grid[x][y].fire and not model.grid[x][y].smoke:
            model.grid[x][y].fire = True
            model.fire_spots.append(model.grid[x][y])
            fire_placed += 1
        attempts += 1
    
    # Place smoke tokens
    smoke_placed = 0
    attempts = 0
    while smoke_placed < NUM_SMOKE_START and attempts < 100:
        x = model.random.randrange(1, SIZE_X - 1)
        y = model.random.randrange(1, SIZE_Y - 1)
        if not model.grid[x][y].fire and not model.grid[x][y].smoke:
            model.grid[x][y].smoke = True
            model.smoke_spots.append(model.grid[x][y])
            smoke_placed += 1
        attempts += 1
    
    # Place POI tokens
    poi_placed = 0
    attempts = 0
    while poi_placed < NUM_POI_START and attempts < 100:
        x = model.random.randrange(1, SIZE_X - 1)
        y = model.random.randrange(1, SIZE_Y - 1)
        if not model.grid[x][y].fire and not model.grid[x][y].smoke and not model.grid[x][y].poi:
            model.grid[x][y].poi = True
            model.poi_spots.append(model.grid[x][y])
            poi_placed += 1
        attempts += 1


def setBomberos(model):
    """Set bomberos/firefighters on the board"""
    from ..azar import Bombero
    
    NUM_BOMBEROS = 6
    SIZE_X = 11
    SIZE_Y = 9
    
    # Place firefighters at entrance (0, 3) or nearby positions
    entrance_positions = [(0, 3), (0, 2), (0, 4), (1, 3), (1, 2), (1, 4)]
    
    bomberos_placed = 0
    for pos in entrance_positions:
        if bomberos_placed >= NUM_BOMBEROS:
            break
        x, y = pos
        if 0 <= x < SIZE_X and 0 <= y < SIZE_Y:
            if not model.grid[x][y].bombero and not model.grid[x][y].firefighter:
                bombero = Bombero(len(model.bomberos), model)
                model.grid[x][y].bombero = bombero
                model.grid[x][y].firefighter = bombero  # For compatibility
                model.bomberos.append(bombero)
                model.schedule.add(bombero)
                bomberos_placed += 1
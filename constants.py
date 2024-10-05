# constants.py

import pygame

# Window settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 70, 140)
LIGHT_BLUE = (173, 216, 230)
GRAY = (200, 200, 200)
LIGHT_GRAY = (220, 220, 220)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Grid settings
GRID_SIZE = 10
CELL_SIZE = 40
GRID_ORIGIN = (WINDOW_WIDTH - CELL_SIZE * GRID_SIZE - 50, 50)

# Ship data
SHIP_SIZES = {
    'Carrier': 5,
    'Battleship': 4,
    'Cruiser': 3,
    'Submarine': 3,
    'Destroyer': 2
}

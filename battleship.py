import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up the display
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Battleship')

# Set up fonts
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 24)

# Define colors 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 70, 140)
LIGHT_BLUE = (173, 216, 230)
GRAY = (200, 200, 200)
LIGHT_GRAY = (220, 220, 220)
RED = (255, 0, 0)

# Grid settings
GRID_SIZE = 10
CELL_SIZE = 40
GRID_ORIGIN = (WINDOW_WIDTH - CELL_SIZE * GRID_SIZE - 50, 50)  # Position the grid on the right

# Ship data
SHIP_SIZES = {
    'Carrier': 5,
    'Battleship': 4,
    'Cruiser': 3,
    'Submarine': 3,
    'Destroyer': 2
}

# Button class
class Button:
    def __init__(self, text, pos, callback):
        self.text = text
        self.pos = pos
        self.callback = callback
        self.rect = pygame.Rect(pos[0], pos[1], 200, 60)
        self.color = BLUE

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()

# Game class
class Game:
    def __init__(self):
        self.running = True
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_ship = None
        self.ship_orientation = 'horizontal'  # Default orientation
        self.placed_ships = {}
        self.available_ships = list(SHIP_SIZES.keys())
        self.mouse_pos = (0, 0)

    def draw_grid(self, surface):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                rect = pygame.Rect(
                    GRID_ORIGIN[0] + col * CELL_SIZE,
                    GRID_ORIGIN[1] + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                pygame.draw.rect(surface, BLACK, rect, 1)
                # Optionally fill the cell if a ship is placed
                if self.grid[row][col] == 1:
                    pygame.draw.rect(surface, LIGHT_BLUE, rect)

    def draw_ships(self, surface):
        # Display the list of available ships on the left
        y_offset = 50
        for ship in self.available_ships:
            text_surface = small_font.render(ship, True, BLACK)
            text_rect = text_surface.get_rect(topleft=(50, y_offset))
            ship_rect = text_surface.get_rect()
            ship_rect.topleft = (50, y_offset)
            surface.blit(text_surface, text_rect)
            y_offset += 40

        # Highlight the selected ship
        if self.selected_ship:
            index = self.available_ships.index(self.selected_ship)
            highlight_rect = pygame.Rect(45, 50 + index * 40, 110, 30)
            pygame.draw.rect(surface, RED, highlight_rect, 2)

    def run(self):
        while self.running:
            window.fill(LIGHT_GRAY)
            self.mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # Handle mouse wheel for rotation
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # Mouse wheel up
                        self.rotate_ship()
                    elif event.button == 5:  # Mouse wheel down
                        self.rotate_ship()
                    elif event.button == 1:  # Left mouse button
                        self.handle_click(event.pos)

            self.draw_grid(window)
            self.draw_ships(window)
            pygame.display.flip()

    def rotate_ship(self):
        # Rotate the ship orientation
        if self.ship_orientation == 'horizontal':
            self.ship_orientation = 'vertical'
        else:
            self.ship_orientation = 'horizontal'
        print(f"Ship orientation: {self.ship_orientation}")

    def handle_click(self, pos):
        x, y = pos
        if x < GRID_ORIGIN[0]:
            # Clicked on the left side (ship selection area)
            y_offset = 50
            for ship in self.available_ships:
                ship_rect = pygame.Rect(50, y_offset, 100, 30)
                if ship_rect.collidepoint(pos):
                    self.selected_ship = ship
                    print(f"Selected ship: {self.selected_ship}")
                    break
                y_offset += 40
        else:
            # Clicked on the grid area
            if self.selected_ship:
                grid_x = (x - GRID_ORIGIN[0]) // CELL_SIZE
                grid_y = (y - GRID_ORIGIN[1]) // CELL_SIZE
                if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                    # Attempt to place the ship
                    if self.can_place_ship(grid_x, grid_y):
                        self.place_ship(grid_x, grid_y)
                        print(f"Placed {self.selected_ship} at ({grid_x}, {grid_y})")
                        self.available_ships.remove(self.selected_ship)
                        self.selected_ship = None
                    else:
                        print("Cannot place ship here.")
                else:
                    print("Click within the grid area.")
            else:
                print("No ship selected.")

    def can_place_ship(self, grid_x, grid_y):
        ship_length = SHIP_SIZES[self.selected_ship]
        if self.ship_orientation == 'horizontal':
            if grid_x + ship_length > GRID_SIZE:
                return False
            for i in range(ship_length):
                if self.grid[grid_y][grid_x + i] != 0:
                    return False
        else:
            if grid_y + ship_length > GRID_SIZE:
                return False
            for i in range(ship_length):
                if self.grid[grid_y + i][grid_x] != 0:
                    return False
        return True

    def place_ship(self, grid_x, grid_y):
        ship_length = SHIP_SIZES[self.selected_ship]
        if self.ship_orientation == 'horizontal':
            for i in range(ship_length):
                self.grid[grid_y][grid_x + i] = 1
        else:
            for i in range(ship_length):
                self.grid[grid_y + i][grid_x] = 1
        # Store the ship's position and orientation
        self.placed_ships[self.selected_ship] = {
            'x': grid_x,
            'y': grid_y,
            'orientation': self.ship_orientation
        }

# Callback functions
def create_room():
    print("Create Room clicked")
    game = Game()
    game.run()

def select_room():
    print("Select Room clicked")
    # TODO: Implement select room functionality

# Create buttons
create_room_button = Button('Create Room', (WINDOW_WIDTH//2 - 100, 200), create_room)
select_room_button = Button('Select Room', (WINDOW_WIDTH//2 - 100, 300), select_room)

# Main loop
def main_menu():
    while True:
        window.fill(GRAY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                create_room_button.check_click(pos)
                select_room_button.check_click(pos)

        create_room_button.draw(window)
        select_room_button.draw(window)

        pygame.display.flip()

if __name__ == "__main__":
    main_menu()

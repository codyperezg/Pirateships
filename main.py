import pygame
import sys
import socket
import threading

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
GREEN = (0, 255, 0)

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

# Networking settings
SERVER_HOST = '127.0.0.1'  # Replace with your server's IP address
SERVER_PORT = 5555

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

# Networking client class
class NetworkClient:
    def __init__(self):
        self.server_host = SERVER_HOST
        self.server_port = SERVER_PORT
        self.sock = None

    def connect_to_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.server_host, self.server_port))
            print("Connected to server.")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.sock = None

    def send_command(self, command):
        if self.sock:
            try:
                self.sock.sendall(command.encode())
                response = self.sock.recv(1024).decode()
                return response
            except Exception as e:
                print(f"Communication error: {e}")
                return None
        else:
            print("Not connected to server.")
            return None

    def close_connection(self):
        if self.sock:
            self.sock.close()
            self.sock = None

# MessageLog class
class MessageLog:
    def __init__(self, x, y, width, height, font, max_messages=5):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.messages = []
        self.max_messages = max_messages

    def add_message(self, message):
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def draw(self, surface):
        # Draw background
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        # Draw messages
        y_offset = self.rect.y + 5
        for message in self.messages:
            text_surface = self.font.render(message, True, BLACK)
            surface.blit(text_surface, (self.rect.x + 5, y_offset))
            y_offset += text_surface.get_height() + 2



# RoomSelectionMenu class
class RoomSelectionMenu:
    def __init__(self):
        self.running = True
        self.rooms = []
        self.selected_room = None
        self.fetch_rooms()

    def fetch_rooms(self):
        network_client.connect_to_server()
        response = network_client.send_command("LIST_ROOMS")
        if response and response.startswith("ROOM_LIST"):
            room_list_str = response[len("ROOM_LIST "):]
            self.rooms = room_list_str.split(',') if room_list_str else []
        else:
            print("Failed to retrieve room list.")
            self.rooms = []
        network_client.close_connection()

    def run(self):
        while self.running:
            window.fill(GRAY)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self.handle_click(pos)

            self.draw(window)
            pygame.display.flip()

        return self.selected_room

    def draw(self, surface):
        # Draw the title
        title_text = font.render("Select a Room", True, BLACK)
        surface.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, 50))

        # Draw the list of rooms
        y_offset = 150
        for idx, room_name in enumerate(self.rooms):
            room_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, y_offset, 300, 40)
            pygame.draw.rect(surface, LIGHT_BLUE, room_rect)
            pygame.draw.rect(surface, BLACK, room_rect, 2)
            room_text = small_font.render(room_name, True, BLACK)
            text_rect = room_text.get_rect(center=room_rect.center)
            surface.blit(room_text, text_rect)
            y_offset += 60

        # Draw 'No rooms available' message if list is empty
        if not self.rooms:
            no_rooms_text = small_font.render("No rooms available.", True, BLACK)
            surface.blit(no_rooms_text, (WINDOW_WIDTH // 2 - no_rooms_text.get_width() // 2, y_offset))

    def handle_click(self, pos):
        y_offset = 150
        for idx, room_name in enumerate(self.rooms):
            room_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, y_offset, 300, 40)
            if room_rect.collidepoint(pos):
                self.selected_room = room_name
                self.running = False
                break
            y_offset += 60

# Game class
class Game:
    def __init__(self, is_host=False, peer_ip=None, peer_port=None):
        # ... [Existing initialization code] ...
        self.running = True
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_ship = None
        self.ship_orientation = 'horizontal'  # Default orientation
        self.placed_ships = {}
        self.available_ships = list(SHIP_SIZES.keys())
        self.mouse_pos = (0, 0)
        self.is_host = is_host
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.conn = None  # Socket connection to peer
        self.peer_thread = None
        self.hovered_cells = []      # Cells currently being hovered over
        self.valid_placement = False # Indicates if the current placement is valid
        self.enemy_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.my_turn = False
        self.game_over = False
        self.winner = None
        self.message_log = MessageLog(50, WINDOW_HEIGHT - 150, WINDOW_WIDTH - 100, 100, small_font)

        if self.is_host:
            self.my_turn = True  # Host starts the game
            self.start_host()
        elif self.peer_ip and self.peer_port:
            self.connect_to_host()

    def start_host(self):
        threading.Thread(target=self.host_listener, daemon=True).start()

    def host_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))  # Bind to any free port
            s.listen()
            host_ip = socket.gethostbyname(socket.gethostname())
            host_port = s.getsockname()[1]
            print(f"Hosting game on {host_ip}:{host_port}")
            # Update the server with the correct port
            network_client.connect_to_server()
            network_client.send_command(f"UPDATE_ROOM_PORT {host_port}")
            network_client.close_connection()
            # Accept a connection from the peer
            self.conn, addr = s.accept()
            print(f"Player connected from {addr}")
            self.peer_thread = threading.Thread(target=self.handle_peer_messages, daemon=True)
            self.peer_thread.start()

    def connect_to_host(self):
        print(f"Connecting to host at {self.peer_ip}:{self.peer_port}")
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.peer_ip, int(self.peer_port)))
        self.peer_thread = threading.Thread(target=self.handle_peer_messages, daemon=True)
        self.peer_thread.start()


    def draw(self, surface):
        # Draw the grid, ships, enemy grid, etc.
        self.draw_grid(surface)
        self.draw_ships(surface)
        self.draw_enemy_grid(surface)
        self.draw_status(surface)
        self.message_log.draw(surface)

    def handle_peer_messages(self):
        try:
            while True:
                data = self.conn.recv(1024).decode()
                if data:
                    print(f"Received from peer: {data}")
                    # Parse the message and handle accordingly
                    self.parse_message(data)
                else:
                    break
        except ConnectionResetError:
            print("Peer disconnected.")
        finally:
            self.conn.close()

    def parse_message(self, data):
        parts = data.strip().split(' ')
        command = parts[0]

        if command == 'ATTACK':
            grid_x, grid_y = int(parts[1]), int(parts[2])
            self.handle_attack(grid_x, grid_y)
        elif command == 'RESULT':
            grid_x, grid_y = int(parts[1]), int(parts[2])
            hit_or_miss = parts[3]
            ship_sunk = parts[4] if len(parts) > 4 else None
            self.handle_result(grid_x, grid_y, hit_or_miss, ship_sunk)
        elif command == 'GAME_OVER':
            winner = parts[1]
            self.game_over = True
            self.winner = winner
            print(f"Game over! Winner: {winner}")
        else:
            print(f"Unknown command received: {command}")

    def handle_attack(self, grid_x, grid_y):
        # Check if any ship occupies this cell
        hit = False
        sunk_ship = None
        for ship, info in self.placed_ships.items():
            if (grid_x, grid_y) in info['cells']:
                hit = True
                info['cells'].remove((grid_x, grid_y))
                if not info['cells']:
                    sunk_ship = ship
                    self.message_log.add_message(f"Your {sunk_ship} has been sunk!")
                else:
                    self.message_log.add_message(f"Your {ship} has been hit!")
                break

        # Update own grid to reflect hit or miss
        self.grid[grid_y][grid_x] = 2 if hit else 3  # 2: Hit, 3: Miss

        # Send result back to attacker
        result_message = f"RESULT {grid_x} {grid_y} {'HIT' if hit else 'MISS'}"
        if sunk_ship:
            result_message += f" {sunk_ship}"
        self.send_to_peer(result_message)

        # Check if all ships are sunk
        if self.check_game_over():
            self.game_over = True
            self.winner = 'Opponent'
            self.send_to_peer("GAME_OVER Opponent")
            self.message_log.add_message("All your ships have been sunk! You lose.")

        # Switch turns
        self.my_turn = True

    def check_game_over(self):
        # If all ships have no remaining cells, game over
        return all(not info['cells'] for info in self.placed_ships.values())


    def send_attack(self, grid_x, grid_y):
        self.send_to_peer(f"ATTACK {grid_x} {grid_y}")


    def check_opponent_game_over(self):
        # This is a placeholder
        # In a real implementation, we'd need to track hits on opponent's ships
        return False  # Needs proper implementation


    def handle_result(self, grid_x, grid_y, hit_or_miss, ship_sunk):
        # Update enemy grid
        self.enemy_grid[grid_y][grid_x] = 2 if hit_or_miss == 'HIT' else 3  # 2: Hit, 3: Miss
        if ship_sunk:
            self.message_log.add_message(f"You sunk the opponent's {ship_sunk}!")
        elif hit_or_miss == 'HIT':
            self.message_log.add_message(f"Hit at ({grid_x}, {grid_y})!")
        else:
            self.message_log.add_message(f"Miss at ({grid_x}, {grid_y}).")

        # Check if opponent has lost
        if hit_or_miss == 'HIT' and ship_sunk:
            # Since we don't have opponent's ship data, we rely on GAME_OVER message
            pass

        # Switch turns
        self.my_turn = False

    def send_to_peer(self, message):
        if self.conn:
            try:
                self.conn.sendall(message.encode())
            except Exception as e:
                print(f"Failed to send message: {e}")

    def draw_grid(self, surface):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                rect = pygame.Rect(
                    GRID_ORIGIN[0] + col * CELL_SIZE,
                    GRID_ORIGIN[1] + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                # Check if this cell is in hovered_cells
                if (col, row) in self.hovered_cells:
                    if self.valid_placement:
                        color = (0, 255, 0, 100)  # Semi-transparent green
                    else:
                        color = (255, 0, 0, 100)  # Semi-transparent red
                    # Create a semi-transparent surface
                    highlight_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    highlight_surface.fill(color)
                    surface.blit(highlight_surface, rect.topleft)
                elif self.grid[row][col] == 1:
                    pygame.draw.rect(surface, LIGHT_BLUE, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)  # Draw grid lines

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

    def rotate_ship(self):
        # Rotate the ship orientation
        if self.ship_orientation == 'horizontal':
            self.ship_orientation = 'vertical'
        else:
            self.ship_orientation = 'horizontal'
        print(f"Ship orientation: {self.ship_orientation}")

    def update_hovered_cells(self):
        # Reset the hovered cells and valid placement flag
        self.hovered_cells = []
        self.valid_placement = False

        if not self.selected_ship:
            return  # No ship selected, nothing to update

        x, y = self.mouse_pos
        grid_x = (x - GRID_ORIGIN[0]) // CELL_SIZE
        grid_y = (y - GRID_ORIGIN[1]) // CELL_SIZE

        ship_length = SHIP_SIZES[self.selected_ship]
        cells = []

        if self.ship_orientation == 'horizontal':
            if grid_x < 0 or grid_x + ship_length > GRID_SIZE or grid_y < 0 or grid_y >= GRID_SIZE:
                return  # Out of bounds
            for i in range(ship_length):
                cells.append((grid_x + i, grid_y))
        else:  # Vertical orientation
            if grid_y < 0 or grid_y + ship_length > GRID_SIZE or grid_x < 0 or grid_x >= GRID_SIZE:
                return  # Out of bounds
            for i in range(ship_length):
                cells.append((grid_x, grid_y + i))

        # Check for overlaps
        for col, row in cells:
            if self.grid[row][col] != 0:
                return  # Overlaps with existing ship

        # If we reach here, placement is valid
        self.hovered_cells = cells
        self.valid_placement = True

    def handle_mouse_motion(self, pos):
        self.mouse_pos = pos
        self.update_hovered_cells()

    def handle_click(self, pos):
        x, y = pos

        if self.game_over:
            self.message_log.add_message("Game over.")
            return

        if x < GRID_ORIGIN[0]:
            # Clicked on the left side (ship selection area)
            y_offset = 50
            for ship in self.available_ships:
                ship_rect = pygame.Rect(50, y_offset, 100, 30)
                if ship_rect.collidepoint(pos):
                    self.selected_ship = ship
                    self.message_log.add_message(f"Selected ship: {self.selected_ship}")
                    self.update_hovered_cells()
                    break
                y_offset += 40
        else:
            # Clicked on the grid area
            grid_x = (x - GRID_ORIGIN[0]) // CELL_SIZE
            grid_y = (y - GRID_ORIGIN[1]) // CELL_SIZE

            if self.all_ships_placed():
                # Attack phase
                if not self.my_turn:
                    self.message_log.add_message("It's not your turn.")
                    return
                if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                    if self.enemy_grid[grid_y][grid_x] == 0:
                        self.send_attack(grid_x, grid_y)
                        self.my_turn = False
                        self.message_log.add_message(f"Attacked position ({grid_x}, {grid_y})")
                    else:
                        self.message_log.add_message("You have already attacked this cell.")
                else:
                    self.message_log.add_message("Click within the grid area.")
            else:
                # Ship placement phase
                if self.selected_ship:
                    if self.valid_placement:
                        # Place the ship
                        self.place_ship()
                        self.message_log.add_message(f"Placed {self.selected_ship}")
                        self.available_ships.remove(self.selected_ship)
                        self.selected_ship = None
                        self.hovered_cells = []
                        self.valid_placement = False
                        # Notify peer when all ships are placed
                        if self.all_ships_placed():
                            self.send_to_peer("ALL_SHIPS_PLACED")
                            self.message_log.add_message("All ships placed. Waiting for opponent.")
                    else:
                        self.message_log.add_message("Cannot place ship here.")
                else:
                    self.message_log.add_message("No ship selected.")

    def all_ships_placed(self):
        return len(self.placed_ships) == len(SHIP_SIZES)



    def can_place_ship(self, grid_x, grid_y):
        # This method is now redundant due to update_hovered_cells handling placement validation
        return self.valid_placement

    def place_ship(self):
        # Place the ship in the grid
        for col, row in self.hovered_cells:
            self.grid[row][col] = 1
        # Store the ship's position and orientation
        self.placed_ships[self.selected_ship] = {
            'cells': self.hovered_cells.copy(),
            'orientation': self.ship_orientation
        }

    def draw_enemy_grid(self, surface):
        # Draw a second grid for the enemy, perhaps on the left side
        # For simplicity, overlay on the existing grid for now
        pass  # Implementation of drawing the enemy grid

    def draw_status(self, surface):
        # Display whose turn it is and game status
        status_text = "Your turn" if self.my_turn else "Opponent's turn"
        if self.game_over:
            status_text = f"Game Over! Winner: {self.winner}"
        text_surface = small_font.render(status_text, True, BLACK)
        surface.blit(text_surface, (WINDOW_WIDTH // 2 - text_surface.get_width() // 2, 10))


    def run(self):
        while self.running:
            window.fill(LIGHT_GRAY)
            self.mouse_pos = pygame.mouse.get_pos()
            self.update_hovered_cells()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    if self.conn:
                        self.conn.close()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4 or event.button == 5:  # Mouse wheel
                        self.rotate_ship()
                        self.update_hovered_cells()
                    elif event.button == 1:  # Left click
                        self.handle_click(event.pos)

            self.draw_grid(window)
            self.draw_ships(window)
            # self.draw_enemy_grid(window)  # Implement this method as needed
            self.draw_status(window)
            pygame.display.flip()

# Callback functions 
def create_room():
    print("Create Room clicked")
    room_name = "Room_" + socket.gethostname()
    network_client.connect_to_server()
    response = network_client.send_command(f"CREATE_ROOM {room_name}")
    if response and response.startswith("ROOM_CREATED"):
        print(f"Room '{room_name}' created.")
        # Start the game as host
        game = Game(is_host=True)
        game.run()
    else:
        print("Failed to create room.")
        network_client.close_connection()


# Modify select_room function
def select_room():
    print("Select Room clicked")
    room_menu = RoomSelectionMenu()
    selected_room = room_menu.run()
    if selected_room:
        join_room(selected_room)
    else:
        print("No room selected.")

def room_selection_menu(room_list):
    # Simple text-based selection for demonstration purposes
    if not room_list:
        print("No rooms available.")
        return None
    print("Available rooms:")
    for idx, room_name in enumerate(room_list):
        print(f"{idx + 1}. {room_name}")
    while True:
        choice = input("Enter the number of the room to join: ")
        if choice.isdigit() and 1 <= int(choice) <= len(room_list):
            return room_list[int(choice) - 1]
        else:
            print("Invalid selection.")

def join_room(room_name):
    network_client.connect_to_server()  # Connect to the server
    response = network_client.send_command(f"GET_ROOM {room_name}")
    if response and response.startswith("ROOM_INFO"):
        _, host_ip, host_port = response.split()
        print(f"Connecting to room '{room_name}' at {host_ip}:{host_port}")
        # Start the game as client, connecting to the host
        game = Game(is_host=False, peer_ip=host_ip, peer_port=host_port)
        game.run()
    else:
        print("Failed to join room.")
    network_client.close_connection()

# Create buttons
create_room_button = Button('Create Room', (WINDOW_WIDTH//2 - 100, 200), create_room)
select_room_button = Button('Select Room', (WINDOW_WIDTH//2 - 100, 300), select_room)

# Global network client instance
network_client = NetworkClient()



# Main loop
def main_menu():
    while True:
        window.fill(GRAY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                network_client.close_connection()
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

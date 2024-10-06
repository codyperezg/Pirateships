# game.py

import pygame
from constants import *
import threading
import socket
import sys
from message_log import MessageLog
# Any other necessary imports


#REMEMbER for safety hit a .set_alpha() before using an img because it gets changed throughout the code
#255 max is fully opaque image
tileimg = pygame.image.load("oceanTile.png")
tileimg = pygame.transform.scale(tileimg, (CELL_SIZE - 1,CELL_SIZE - 1))
darktileimg = pygame.image.load("darkOceanTile.png")
darktileimg = pygame.transform.scale(darktileimg, (CELL_SIZE - 1,CELL_SIZE - 1))

boatbutt = pygame.image.load("boatend.png")
boatmid = pygame.image.load("boatmid.png")

# Game class
class Game:
    def __init__(self, window, small_font, network_client=None, is_host=False, peer_ip=None, peer_port=None, local_test=False):
        self.small_font = small_font
        self.window = window
        self.network_client = network_client
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
        self.local_test = local_test

        if self.local_test:
            self.my_turn = True  # Allow interaction in local test mode
            self.message_log.add_message("Local Test Mode")
        else:
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
            if self.network_client:
                self.network_client.connect_to_server()
                self.network_client.send_command(f"UPDATE_ROOM_PORT {host_port}")
                self.network_client.close_connection()
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
            if self.conn:
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
            self.message_log.add_message(f"Game over! Winner: {winner}")
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

    def handle_result(self, grid_x, grid_y, hit_or_miss, ship_sunk):
        # Update enemy grid
        self.enemy_grid[grid_y][grid_x] = 2 if hit_or_miss == 'HIT' else 3  # 2: Hit, 3: Miss
        if ship_sunk:
            self.message_log.add_message(f"You sunk the opponent's {ship_sunk}!")
        elif hit_or_miss == 'HIT':
            self.message_log.add_message(f"Hit at ({grid_x}, {grid_y})!")
        else:
            self.message_log.add_message(f"Miss at ({grid_x}, {grid_y}).")

        # Switch turns
        self.my_turn = False

    def send_to_peer(self, message):
        if self.conn:
            try:
                self.conn.sendall(message.encode())
            except Exception as e:
                print(f"Failed to send message: {e}")

    def send_attack(self, grid_x, grid_y):
        if self.local_test:
            # In local test mode, simulate an attack result
            self.message_log.add_message(f"Attacked position ({grid_x}, {grid_y}) in local test mode.")
            # Update enemy grid for testing
            self.enemy_grid[grid_y][grid_x] = 3  # Mark as miss for simplicity
            # Switch turns
            self.my_turn = False
        else:
            self.send_to_peer(f"ATTACK {grid_x} {grid_y}")

    def check_game_over(self):
        # If all ships have no remaining cells, game over
        return all(not info['cells'] for info in self.placed_ships.values())

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
                        self.my_turn = True if self.local_test else False
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
                            if not self.local_test:
                                self.send_to_peer("ALL_SHIPS_PLACED")
                            self.message_log.add_message("All ships placed. Waiting for opponent.")
                    else:
                        self.message_log.add_message("Cannot place ship here.")
                else:
                    self.message_log.add_message("No ship selected.")

    def all_ships_placed(self):
        return len(self.placed_ships) == len(SHIP_SIZES)

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
        
        
        #THIS RENDERS THE BOATS
        counter = 1
        for cell in cells:
            cellcoord2 = cell[0]
            cellcoord1 = cell[1]
            
            if self.ship_orientation == "horizontal":
                #front
                if counter == 1:
                    self.window.blit(boatbutt, matrix[cellcoord1][cellcoord2])
                #back
                elif counter == ship_length:
                    flipboatendx = pygame.transform.flip(boatbutt, True, False)
                    self.window.blit(flipboatendx, matrix[cellcoord1][cellcoord2])
                #middle
                else:
                    self.window.blit(boatmid, matrix[cellcoord1][cellcoord2])
            else:
                """ #vertical ship orientation """
                #front
                if counter == 1:
                    #flipboatendup = pygame.transform.flip(boatbutt, False, True)
                    rotateboatend = pygame.transform.rotate(boatbutt, 270)
                    self.window.blit(rotateboatend, matrix[cellcoord1][cellcoord2])
                #end
                elif counter == ship_length:
                    flipboatenddown = pygame.transform.flip(rotateboatend, False, True)
                    self.window.blit(flipboatenddown, matrix[cellcoord1][cellcoord2])
                #middle
                else:
                    rotateboatmid = pygame.transform.rotate(boatmid, 90)
                    self.window.blit(rotateboatmid, matrix[cellcoord1][cellcoord2])
            counter += 1

        # If we reach here, placement is valid
        self.hovered_cells = cells
        self.valid_placement = True

    def handle_mouse_motion(self, pos):
        self.mouse_pos = pos
        self.update_hovered_cells()

    def rotate_ship(self):
        # Rotate the ship orientation
        if self.ship_orientation == 'horizontal':
            self.ship_orientation = 'vertical'
        else:
            self.ship_orientation = 'horizontal'
        self.update_hovered_cells()

    def place_ship(self):
        # Place the ship in the grid
        for col, row in self.hovered_cells:
            self.grid[row][col] = 1
        # Store the ship's position and orientation
        self.placed_ships[self.selected_ship] = {
            'cells': self.hovered_cells.copy(),
            'orientation': self.ship_orientation
        }

    def draw_grid(self, surface):
        global matrix
        matrix = [[column for column in range(GRID_SIZE)] for row in range(GRID_SIZE)]
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                rect = pygame.Rect(
                    GRID_ORIGIN[0] + col * CELL_SIZE,
                    GRID_ORIGIN[1] + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                matrix[row][col] = rect
                pygame.draw.rect(surface, BLACK, rect, 1)  # Draw grid lines
                
                #This places the background water image onto the grid tiles
                surface.blit(tileimg, (GRID_ORIGIN[0] + col * CELL_SIZE, GRID_ORIGIN[1] + row * CELL_SIZE))
                # Check if this cell is in hovered_cells
                if (col, row) in self.hovered_cells:
                    if self.valid_placement:
                        color = (0, 255, 0, 100)  # Semi-transparent green
                    else:
                        color = (255, 0, 0, 100)  # Semi-transparent red
                    # Create a semi-transparent surface
                    highlight_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    highlight_surface.fill(color)
                    #surface.blit(highlight_surface, rect.topleft)
                    #This highlights the ship hover and placement
                    darktileimg.set_alpha(100)
                    surface.blit(darktileimg, rect.topleft)
                elif self.grid[row][col] == 1:
                    #DRAW PLACED SHIP
                    pygame.draw.rect(surface, LIGHT_BLUE, rect)
                    darktileimg.set_alpha(255)
                    surface.blit(darktileimg, rect.topleft)
                elif self.grid[row][col] == 2:
                    pygame.draw.rect(surface, RED, rect)  # Hit
                elif self.grid[row][col] == 3:
                    pygame.draw.rect(surface, WHITE, rect)  # Miss

    #whole function deals only with ship text to the side of the grid
    def draw_ships(self, surface):
        # Display the list of available ships on the left
        y_offset = 50
        for ship in self.available_ships:
            text_surface = self.small_font.render(ship, True, BLACK)
            text_rect = text_surface.get_rect(topleft=(50, y_offset))
            ship_rect = text_surface.get_rect()
            ship_rect.topleft = (50, y_offset)
            surface.blit(text_surface, text_rect)
            #this is indeed where the text is to the side of the grid
            #surface.blit(darktileimg, text_rect) #pov: ollie is poking things with a stick to see what happens
            y_offset += 40

        # Highlight the selected ship TEXT FROM THE MENU
        if self.selected_ship:
            index = self.available_ships.index(self.selected_ship)
            highlight_rect = pygame.Rect(45, 50 + index * 40, 110, 30)
            #ADDS RED BOX AROUND TEXT
            pygame.draw.rect(surface, RED, highlight_rect, 2)
            

    def draw_enemy_grid(self, surface):
        # Draw the enemy grid (for testing, draw it next to the player's grid)
        offset_x = GRID_ORIGIN[0] - GRID_SIZE * CELL_SIZE - 50
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                rect = pygame.Rect(
                    offset_x + col * CELL_SIZE,
                    GRID_ORIGIN[1] + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                if self.enemy_grid[row][col] == 2:
                    pygame.draw.rect(surface, RED, rect)  # Hit
                elif self.enemy_grid[row][col] == 3:
                    pygame.draw.rect(surface, WHITE, rect)  # Miss
                pygame.draw.rect(surface, BLACK, rect, 1)  # Draw grid lines

        # Label the enemy grid
        label_text = self.small_font.render("Enemy Grid", True, BLACK)
        surface.blit(label_text, (offset_x + GRID_SIZE * CELL_SIZE // 2 - label_text.get_width() // 2, GRID_ORIGIN[1] - 30))

    def draw_status(self, surface):
        # Display whose turn it is and game status
        status_text = "Your turn" if self.my_turn else "Opponent's turn"
        if self.game_over:
            status_text = f"Game Over! Winner: {self.winner}"
        text_surface = self.small_font.render(status_text, True, BLACK)
        surface.blit(text_surface, (WINDOW_WIDTH // 2 - text_surface.get_width() // 2, 10))

    def draw(self, surface):
        # Draw the grid, ships, enemy grid, etc.
        self.draw_grid(surface)
        self.draw_ships(surface)
        self.draw_enemy_grid(surface)
        self.draw_status(surface)
        self.message_log.draw(surface)

    def run(self):
        while self.running:
            self.window.fill(LIGHT_GRAY)
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

            self.draw(self.window)
            self.update_hovered_cells()
            pygame.display.flip()

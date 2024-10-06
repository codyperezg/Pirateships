# game.py

import pygame
from constants import *
import threading
import socket
import sys
from message_log import MessageLog
# Any other necessary imports

class Game:
    def __init__(self, window, small_font, network_client=None, is_host=False, local_test=False):
        self.window = window
        self.small_font = small_font
        self.network_client = network_client
        self.running = True
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_ship = None
        self.ship_orientation = 'horizontal'
        self.placed_ships = {}
        self.available_ships = list(SHIP_SIZES.keys())
        self.mouse_pos = (0, 0)
        self.is_host = is_host
        self.hovered_cells = []
        self.valid_placement = False
        self.enemy_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.my_turn = self.is_host
        self.game_over = False
        self.winner = None
        self.message_log = MessageLog(50, WINDOW_HEIGHT - 150, WINDOW_WIDTH - 100, 100, small_font)
        self.local_test = local_test
        self.my_ships_ready = False
        self.opponent_ready = False
        self.game_started = False
        self.client_joined = False

        if self.local_test:
            self.my_turn = True
            self.message_log.add_message("Local Test Mode")
        else:
            if self.network_client:
                self.conn = self.network_client.sock
                self.peer_thread = threading.Thread(target=self.handle_server_messages, daemon=True)
                self.peer_thread.start()
            else:
                self.message_log.add_message("Network client not available.")

    def handle_server_messages(self):
        try:
            while True:
                data = self.conn.recv(1024).decode()
                if data:
                    print(f"Received from server: {data}")
                    self.parse_server_message(data)
                else:
                    break
        except ConnectionResetError:
            print("Server connection lost.")
            self.running = False
        finally:
            if self.conn:
                self.conn.close()

    def parse_server_message(self, data):
        parts = data.strip().split(' ', 1)
        command = parts[0]
        params = parts[1] if len(parts) > 1 else ''
        
        if command == 'MESSAGE_FROM_HOST':
            if not self.is_host:
                self.parse_message(params)
        elif command == 'MESSAGE_FROM_CLIENT':
            if self.is_host:
                self.parse_message(params)
        elif command == 'CLIENT_JOINED':
            if self.is_host:
                self.client_joined = True
                self.message_log.add_message("Client joined the game.")
        elif command == 'HOST_DISCONNECTED':
            self.message_log.add_message("Host has disconnected.")
            self.running = False
        elif command == 'CLIENT_DISCONNECTED':
            self.message_log.add_message("Client has disconnected.")
            self.running = False
        else:
            print(f"Unknown command received: {command}")

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
        elif command == 'ALL_SHIPS_PLACED':
            self.opponent_ready = True
            self.message_log.add_message("Opponent has placed all ships.")
            if self.my_ships_ready:
                self.game_started = True
                self.message_log.add_message("Both players are ready. Game starts now!")
        else:
            print(f"Unknown command received: {command}")

    def send_message_to_server(self, message):
        if self.conn:
            try:
                command = f"MESSAGE {message}"
                self.conn.sendall(command.encode())
            except Exception as e:
                print(f"Failed to send message: {e}")

    def send_attack(self, grid_x, grid_y):
        if self.local_test:
            self.message_log.add_message(f"Attacked position ({grid_x}, {grid_y}) in local test mode.")
            self.enemy_grid[grid_y][grid_x] = 3
            self.my_turn = False
        else:
            self.send_message_to_server(f"ATTACK {grid_x} {grid_y}")

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
        self.send_message_to_server(result_message)

        # Check if all ships are sunk
        if self.check_game_over():
            self.game_over = True
            self.winner = 'Opponent'
            self.send_message_to_server("GAME_OVER Opponent")
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

    def check_game_over(self):
        # If all ships have no remaining cells, game over
        return all(not info['cells'] for info in self.placed_ships.values())

    def handle_click(self, pos):
        x, y = pos

        if self.game_over:
            self.message_log.add_message("Game over.")
            return

        # **Define enemy grid boundaries**
        enemy_grid_offset_x = GRID_ORIGIN[0] - GRID_SIZE * CELL_SIZE - 50
        enemy_grid_x_start = enemy_grid_offset_x
        enemy_grid_x_end = enemy_grid_x_start + GRID_SIZE * CELL_SIZE
        enemy_grid_y_start = GRID_ORIGIN[1]
        enemy_grid_y_end = enemy_grid_y_start + GRID_SIZE * CELL_SIZE

        # **Define player's grid boundaries**
        player_grid_x_start = GRID_ORIGIN[0]
        player_grid_x_end = player_grid_x_start + GRID_SIZE * CELL_SIZE
        player_grid_y_start = GRID_ORIGIN[1]
        player_grid_y_end = player_grid_y_start + GRID_SIZE * CELL_SIZE

        # **Define ship selection area boundary**
        ship_selection_x_end = 150  # Ship selection area starts at x=50 and width=100

        if enemy_grid_x_start <= x < enemy_grid_x_end and enemy_grid_y_start <= y < enemy_grid_y_end:
            # **Clicked on the enemy grid**
            if not self.all_ships_placed():
                self.message_log.add_message("Place all your ships first.")
                return
            if not self.game_started:
                self.message_log.add_message("Waiting for both players to be ready.")
                return
            if not self.my_turn:
                self.message_log.add_message("It's not your turn.")
                return
            grid_x = (x - enemy_grid_x_start) // CELL_SIZE
            grid_y = (y - enemy_grid_y_start) // CELL_SIZE
            if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                if self.enemy_grid[grid_y][grid_x] == 0:
                    self.send_attack(grid_x, grid_y)
                    # Turn will switch after handling the result
                else:
                    self.message_log.add_message("You have already attacked this cell.")
            else:
                self.message_log.add_message("Click within the grid area.")
        elif x < ship_selection_x_end:
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
        elif player_grid_x_start <= x < player_grid_x_end and player_grid_y_start <= y < player_grid_y_end:
            # Clicked on the player's grid
            grid_x = (x - GRID_ORIGIN[0]) // CELL_SIZE
            grid_y = (y - GRID_ORIGIN[1]) // CELL_SIZE

            if not self.all_ships_placed():
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
                        # Notify when all ships are placed
                        if self.all_ships_placed():
                            self.my_ships_ready = True
                            self.message_log.add_message("All ships placed. Waiting for opponent.")
                            if not self.local_test:
                                self.send_message_to_server("ALL_SHIPS_PLACED")
                            if self.opponent_ready:
                                self.game_started = True
                                self.message_log.add_message("Both players are ready. Game starts now!")
                    else:
                        self.message_log.add_message("Cannot place ship here.")
                else:
                    self.message_log.add_message("No ship selected.")
            else:
                # All ships placed
                self.message_log.add_message("All ships placed. Attack the enemy by clicking on their grid.")
        else:
            # Clicked elsewhere
            self.message_log.add_message("Click within the grid area or select a ship.")

    def all_ships_placed(self):
        return len(self.placed_ships) == len(SHIP_SIZES)

    def update_hovered_cells(self):
        # Reset the hovered cells and valid placement flag
        self.hovered_cells = []
        self.valid_placement = False

        if not self.selected_ship:
            return  # No ship selected, nothing to update

        x, y = self.mouse_pos

        # **Only update if mouse is over player's grid**
        player_grid_x_start = GRID_ORIGIN[0]
        player_grid_x_end = player_grid_x_start + GRID_SIZE * CELL_SIZE
        player_grid_y_start = GRID_ORIGIN[1]
        player_grid_y_end = player_grid_y_start + GRID_SIZE * CELL_SIZE

        if not (player_grid_x_start <= x < player_grid_x_end and player_grid_y_start <= y < player_grid_y_end):
            return  # Mouse not over player's grid

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
        x, y = pos
        # **Only update hover if mouse is over player's grid**
        player_grid_x_start = GRID_ORIGIN[0]
        player_grid_x_end = player_grid_x_start + GRID_SIZE * CELL_SIZE
        player_grid_y_start = GRID_ORIGIN[1]
        player_grid_y_end = player_grid_y_start + GRID_SIZE * CELL_SIZE

        if player_grid_x_start <= x < player_grid_x_end and player_grid_y_start <= y < player_grid_y_end:
            self.update_hovered_cells()
        else:
            self.hovered_cells = []
            self.valid_placement = False

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
                elif self.grid[row][col] == 2:
                    pygame.draw.rect(surface, RED, rect)  # Hit
                elif self.grid[row][col] == 3:
                    pygame.draw.rect(surface, WHITE, rect)  # Miss
                pygame.draw.rect(surface, BLACK, rect, 1)  # Draw grid lines

    def draw_ships(self, surface):
        # Display the list of available ships on the left
        y_offset = 50
        for ship in self.available_ships:
            text_surface = self.small_font.render(ship, True, BLACK)
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

    def draw_enemy_grid(self, surface):
        # Draw the enemy grid (left side)
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
        if self.game_over:
            status_text = f"Game Over! Winner: {self.winner}"
        elif not self.game_started:
            status_text = "Waiting for both players to be ready..."
        elif self.my_turn:
            status_text = "Your turn - Click on the enemy grid to attack."
        else:
            status_text = "Opponent's turn - Please wait."
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
        if self.is_host:
            while not self.client_joined and self.running:
                self.message_log.add_message("Waiting for a player to join...")
                pygame.time.delay(1000)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        if self.conn:
                            self.conn.close()
                        pygame.quit()
                        sys.exit()
        while self.running:
            self.window.fill(LIGHT_GRAY)
            self.mouse_pos = pygame.mouse.get_pos()
            # **Moved update_hovered_cells() call to handle_mouse_motion**
            # self.update_hovered_cells()

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
                    if event.button == 4 or event.button == 5:
                        self.rotate_ship()
                        self.update_hovered_cells()
                    elif event.button == 1:
                        self.handle_click(event.pos)

            self.draw(self.window)
            pygame.display.flip()

        # Clean up connection after game ends
        if self.conn:
            self.conn.close()

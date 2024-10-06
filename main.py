# main.py

import pygame
import sys
import socket
import threading
from constants import *
from ui_elements import Button, drawTitle
from menu import RoomSelectionMenu
from game import Game

# Initialize Pygame
pygame.init()

shipboardbackground = pygame.image.load("titlebackground.png")
shipboardbackground = pygame.transform.scale(shipboardbackground, (WINDOW_WIDTH, WINDOW_HEIGHT))
# Fonts (initialize after pygame.init())
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 24)

# Set up the display
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Battleship')

# Networking settings
SERVER_HOST = '34.42.18.51'  # Replace with your server's IP address
SERVER_PORT = 5555

# Networking client class
class NetworkClient:
    def __init__(self):
        self.server_host = SERVER_HOST
        self.server_port = SERVER_PORT
        self.sock = None

    def connect_to_server(self):
        print(f"Attempting to connect to server at {self.server_host}:{self.server_port}")
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


# Global network client instance
network_client = NetworkClient()

# Callback functions
def create_room():
    print("Create Room clicked")
    room_name = "Room_" + socket.gethostname()
    network_client.connect_to_server()
    response = network_client.send_command(f"CREATE_ROOM {room_name}")
    if response and response.startswith("ROOM_CREATED"):
        print(f"Room '{room_name}' created.")
        # Start the game as host
        game = Game(window=window, small_font=small_font, network_client=network_client, is_host=True)
        game.run()
    else:
        print("Failed to create room.")
        network_client.close_connection()

def select_room():
    print("Select Room clicked")
    room_menu = RoomSelectionMenu(window, network_client, small_font)
    selected_room = room_menu.run()
    if selected_room:
        join_room(selected_room)
    else:
        print("No room selected.")

def join_room(room_name):
    print("Joining room...")
    network_client.connect_to_server()  # Ensure we are connected
    response = network_client.send_command(f"JOIN_ROOM {room_name}")
    if response and response.startswith("JOINED_ROOM"):
        print(f"Joined room '{room_name}'.")
        # Start the game as client
        game = Game(window=window, small_font=small_font, network_client=network_client, is_host=False)
        game.run()
        # Close the connection after the game ends
        network_client.close_connection()
    else:
        print("Failed to join room.")
        network_client.close_connection()

    
def test_game():
    print("Local Test clicked")
    # Start the game without connecting to the network
    game = Game(window=window, small_font=small_font, network_client=network_client, local_test=True)
    game.run()

# Create buttons with the font
create_room_button = Button('Create Room', (WINDOW_WIDTH // 2 - 100, 250), create_room, font, "create")
select_room_button = Button('Select Room', (WINDOW_WIDTH // 2 - 100, 350), select_room, font, "join")
test_game_button = Button('Local Test', (WINDOW_WIDTH // 2 - 100, 500), test_game, font, "localtest")

# Main loop
def main_menu():
    while True:
        window.fill(GRAY)
        window.blit(shipboardbackground, (0,0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                network_client.close_connection()
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                create_room_button.check_click(pos)
                select_room_button.check_click(pos)
                test_game_button.check_click(pos)

        drawTitle(window)
        create_room_button.draw(window)
        select_room_button.draw(window)
        test_game_button.draw(window)

        pygame.display.flip()

if __name__ == "__main__":
    main_menu()

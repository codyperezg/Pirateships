# menu.py

import sys
import pygame
from constants import *
from ui_elements import Button

class RoomSelectionMenu:
    def __init__(self, window, network_client, small_font):
        self.window = window
        self.network_client = network_client
        self.small_font = small_font
        self.running = True
        self.rooms = []
        self.selected_room = None
        self.fetch_rooms()

    def fetch_rooms(self):
        self.network_client.connect_to_server()
        response = self.network_client.send_command("LIST_ROOMS")
        if response and response.startswith("ROOM_LIST"):
            room_list_str = response[len("ROOM_LIST "):]
            self.rooms = room_list_str.split(',') if room_list_str else []
        else:
            print("Failed to retrieve room list.")
            self.rooms = []
        self.network_client.close_connection()

    def run(self):
        while self.running:
            self.window.fill(GRAY)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False  # Do not exit the entire game
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self.handle_click(pos)

            self.draw(self.window)
            pygame.display.flip()

        return self.selected_room

    def draw(self, surface):
        # Draw the title
        title_text = self.small_font.render("Select a Room", True, BLACK)
        surface.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, 50))

        # Draw the list of rooms
        y_offset = 150
        if not self.rooms:
            no_rooms_text = self.small_font.render("No rooms available.", True, BLACK)
            surface.blit(no_rooms_text, (WINDOW_WIDTH // 2 - no_rooms_text.get_width() // 2, y_offset))
        else:
            for idx, room_name in enumerate(self.rooms):
                room_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, y_offset, 300, 40)
                pygame.draw.rect(surface, LIGHT_GRAY, room_rect)
                pygame.draw.rect(surface, BLACK, room_rect, 2)
                room_text = self.small_font.render(room_name, True, BLACK)
                text_rect = room_text.get_rect(center=room_rect.center)
                surface.blit(room_text, text_rect)
                y_offset += 60

    def handle_click(self, pos):
        y_offset = 150
        if not self.rooms:
            return  # No rooms to click on
        for idx, room_name in enumerate(self.rooms):
            room_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, y_offset, 300, 40)
            if room_rect.collidepoint(pos):
                self.selected_room = room_name
                self.running = False
                break
            y_offset += 60

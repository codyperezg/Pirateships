# message_log.py

import pygame
from constants import WHITE, BLACK

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
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        y_offset = self.rect.y + 5
        for message in self.messages:
            text_surface = self.font.render(message, True, BLACK)
            surface.blit(text_surface, (self.rect.x + 5, y_offset))
            y_offset += text_surface.get_height() + 2

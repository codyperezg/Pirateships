# ui_elements.py

import pygame
from constants import BLUE, WHITE

class Button:
    def __init__(self, text, pos, callback, font):
        self.text = text
        self.pos = pos
        self.callback = callback
        self.font = font
        self.rect = pygame.Rect(pos[0], pos[1], 200, 60)
        self.color = BLUE

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()

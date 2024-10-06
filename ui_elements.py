# ui_elements.py

import pygame
from constants import *

createRoomScroll = pygame.image.load("createroom.png")
selectRoomScroll = pygame.image.load("selectroom.png")
titlescroll = pygame.image.load("titlecard.png")

def drawTitle(surface):
    pos = pygame.Rect(WINDOW_WIDTH // 2 - 315, 20, 200, 60)
    surface.blit(titlescroll, pos)
    
    

class Button:
    def __init__(self, text, pos, callback, font, buttonType):
        self.text = text
        self.pos = pos
        self.callback = callback
        self.font = font
        self.rect = pygame.Rect(pos[0], pos[1], 200, 60)
        self.color = BLUE
        self.buttonType = buttonType

    def draw(self, surface):
        #test = pygame.draw.rect(surface, WHITE, self.rect)
        #text_surface = self.font.render(self.text, True, WHITE)
        #text_rect = text_surface.get_rect(center=self.rect.center)
        #surface.blit(text_surface, text_rect)
        if self.buttonType == "create":
            surface.blit(createRoomScroll, self.rect)
        elif self.buttonType == "join":
            surface.blit(selectRoomScroll, self.rect)
        else:
            pygame.draw.rect(surface, WHITE, self.rect)
            

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()

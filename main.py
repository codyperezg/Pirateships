import pygame

resolution = (500, 500)
screen = pygame.display.set_mode(resolution)
map_size = (10, 10)  # (rows, columns)
line_width = 3
clock = pygame.time.Clock()  # to set max FPS

BLUE  = (0, 0, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

def evaluate_dimensions():
    # Evaluate the width and the height of the squares.
    square_width = (resolution[0] / map_size[0]) - line_width * ((map_size[0] + 1) / map_size[0])
    square_height = (resolution[1] / map_size[1]) - line_width * ((map_size[1] + 1) / map_size[1])
    return (square_width, square_height)

def convert_column_to_x(column, square_width):
    x = line_width * (column + 1) + square_width * column
    return x

def convert_row_to_y(row, square_height):
    y = line_width * (row + 1) + square_height * row
    return y

def draw_squares():
    square_width, square_height = evaluate_dimensions()
    for row in range(map_size[0]):
        for column in range(map_size[1]):
            color = (WHITE)  # (R, G, B)
            x = convert_column_to_x(column, square_width)
            y = convert_row_to_y(row, square_height)
            geometry = (x, y, square_width, square_height)
            pygame.draw.rect(screen, color, geometry)

while True:
    clock.tick(60)  # max FPS = 60
    screen.fill(BLUE)  # Fill screen with black color.
    draw_squares()
    pygame.display.update()  # Update the screen.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
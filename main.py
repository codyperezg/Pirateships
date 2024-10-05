import pygame
import time

resolution = (500, 500)
screen = pygame.display.set_mode(resolution)
map_size = (10, 10)  # (rows, columns)
line_width = 5
clock = pygame.time.Clock()  # to set max FPS

#background = pygame.image.load("waterbg.png")
tileimg = pygame.image.load("oceanTile.png")
darktileimg = pygame.image.load("darkOceanTile.png")
#background = pygame.transform.scale(background, (500,500))

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
    global matrix
    matrix = [[column for column in range(map_size[1])] for row in range(map_size[0])]
    
    #print(matrix)
    #print (matrix[2][2])
    square_width, square_height = evaluate_dimensions()
    for row in range(map_size[0]):
        for column in range(map_size[1]):
            #color = (WHITE)  # (R, G, B)
            x = convert_column_to_x(column, square_width)
            y = convert_row_to_y(row, square_height)
            
            #geometry = (x, y, square_width, square_height)
            matrix[row][column] = gridtile(pygame.Rect(x, y, square_width, square_height), (row, column), False, False)
            pygame.draw.rect(screen, BLUE, matrix[row][column].tile)
            screen.blit(tileimg, (x,y))
            #tileimg = pygame.transform.chop(background, matrix[row][column].Rect)
            #surface = matrix[row][column].Rect
            #surface.blit(tileimg, (x, y))


class gridtile:
    def __init__(self, tile, coordinate, ship, clicked):
        self.tile = tile
        self.coordinate = coordinate
        self.ship = ship
        self.clicked = clicked
    
    def __str__(self):
        return f"{self.coordinate}"
    
    def coordstostr(self):
        return str(self.coordinate)
        

handled = False
test = 0

while True:
    if test == 0:
        screen.fill(WHITE)
        #screen.blit(background, (0, 0))
        draw_squares()
        pygame.display.update()
        test = 1
    #testtile = gridtile(pygame.Rect(1,1, 10,10), (1,1))
    #print(testtile)
    
    ev = pygame.event.get()
    for row in range(map_size[0]):
            for column in range(map_size[1]):
                if pygame.mouse.get_pressed()[0] and matrix[row][column].tile.collidepoint(pygame.mouse.get_pos()) and not handled and matrix[row][column].clicked == False:
                    print ("pressed " + matrix[row][column].coordstostr())
                    matrix[row][column].clicked = True
                    handled = pygame.mouse.get_pressed()[0]
                    time.sleep(0.1)
                    handled = False
                    #pygame.draw.rect(screen, BLACK, matrix[row][column].Rect)
                    #pygame.draw.rect(screen, BLUE, matrix[row][column].tile)
                    help = pygame.draw.rect(screen, BLUE, matrix[row][column].tile)
                    screen.blit(darktileimg, help)
                    pygame.display.update()
                elif pygame.mouse.get_pressed()[0] and matrix[row][column].tile.collidepoint(pygame.mouse.get_pos()) and matrix[row][column].clicked == True:
                    print("already clicked here")
                    handled = pygame.mouse.get_pressed()[0]
                    time.sleep(0.1)
                    handled = False
                    pygame.display.update()
    

    """
  # proceed events
    for event in ev:

    # handle MOUSEBUTTONUP
        if event.type == pygame.MOUSEBUTTONUP:
        pos = pygame.mouse.get_pos()

        # get a list of all sprites that are under the mouse cursor
        clicked_sprites = [[column for column in range(map_size[1])] for row in range(map_size[0]) if .rect.collidepoint(pos)]
    """
    
    #clock.tick(60)  # max FPS = 60
    #screen.fill(BLUE)  # Fill screen with black color.
    #draw_squares()
    #pygame.display.update()  # Update the screen.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        """  
        for row in range(map_size[0]):
            for column in range(map_size[1]):
                if pygame.mouse.get_pressed()[1] and matrix[row][column].collidepoint(pygame.mouse.get_pos()):
                    print ("pressed " + matrix[row][column])
        """ 
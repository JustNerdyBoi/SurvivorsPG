import pygame
import generation
from PIL import Image

size = width, height = 3440, 1440
screen = pygame.display.set_mode(size)
pygame.display.set_caption('Surivorsmap')

rooms = generation.create_board()
field = generation.map_filling(rooms)


def save_to_img():
    map_preview = Image.new("RGB", (128, 128), (0, 0, 0))
    for x in range(len(field)):
        for y in range(len(field)):
            tile_type = field[x][y]
            if tile_type == 1:
                map_preview.putpixel((x, y), (0, 0, 0))
            if tile_type == 2:
                map_preview.putpixel((x, y), (255, 100, 0))
            if tile_type == 3:
                map_preview.putpixel((x, y), (0, 255, 0))
            if tile_type == 4:
                map_preview.putpixel((x, y), (0, 255, 255))
            if tile_type == 0:
                map_preview.putpixel((x, y), (100, 100, 100))
    map_preview.save('MapPreview.png')
save_to_img()



running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(pygame.Color("black"))
    for room in rooms:
        room.spritegroup.draw(screen)
    pygame.display.flip()

pygame.quit()
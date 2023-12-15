import pygame
import generation
from PIL import Image

size = width, height = 3440, 1440
screen = pygame.display.set_mode(size)
pygame.display.set_caption('Surivorsmap')
rooms = generation.create_board()
field = generation.map_filling(rooms)
rooms = generation.apply_sprites(rooms, field)

def save_to_img():
    map_preview = Image.new("RGB", (128, 128), (0, 0, 0))
    for y in field:
        print(*y)
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
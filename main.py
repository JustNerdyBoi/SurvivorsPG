import pygame
import generation

size = width, height = 3440, 1440
screen = pygame.display.set_mode(size)
pygame.display.set_caption('Surivorsmap')
rooms = generation.create_board()
field = generation.map_filling(rooms)
rooms = generation.apply_sprites(rooms, field)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(pygame.Color("black"))
    for room in rooms:
        room.spritegroup.draw(screen)
        room.upper_spritegroup.draw(screen)
    pygame.display.flip()
pygame.quit()
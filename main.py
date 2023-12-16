import pygame
import generation

size = width, height = 3440, 1440
screen = pygame.display.set_mode(size)
pygame.display.set_caption('Surivorsmap')
rooms = generation.create_board()
field = generation.map_filling(rooms)
rooms = generation.apply_sprites(rooms, field)


running = True
move_y = 0
move_x = 0
speed = 1
min_fps = 1000
max_fps = 0
FPSRESET = pygame.USEREVENT + 1
pygame.time.set_timer(FPSRESET, 10_000)
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                move_y = 1
            elif event.key == pygame.K_s:
                move_y = -1
            if event.key == pygame.K_a:
                move_x = 1
            elif event.key == pygame.K_d:
                move_x = -1
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                move_y = 0
            elif event.key == pygame.K_s:
                move_y = 0
            if event.key == pygame.K_a:
                move_x = 0
            elif event.key == pygame.K_d:
                move_x = 0
        if event.type == FPSRESET:
            min_fps = 1000
            max_fps = 0
    screen.fill(pygame.Color("black"))
    clock.tick()
    if min_fps > clock.get_fps():
        min_fps = clock.get_fps()
    if max_fps < clock.get_fps():
        max_fps = clock.get_fps()
    for room in rooms:
        room.spritegroup.draw(screen)
        room.upper_spritegroup.draw(screen)

        room.move(move_x * speed, move_y * speed)
    pygame.display.flip()
pygame.quit()
print('min FPS =', min_fps, 'max FPS =', max_fps)
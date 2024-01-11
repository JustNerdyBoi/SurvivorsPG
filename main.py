import pygame
import core
import generation
import math

FULLSCREEN = False
FPS = 60  # changed for FPS

if FULLSCREEN:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((2048, 1024))

screen_size = (screen.get_rect()[2], screen.get_rect()[3])
pygame.display.set_caption('Surivorsmap')
rooms = generation.create_board()
field = generation.map_filling(rooms)
rooms = generation.apply_sprites(rooms, field)

entity_group = pygame.sprite.Group()

idle_image_list = []
for i in range(3):
    idle_image_list.append(core.load_image('player_sprites', f'idle_{i}.png'))
run_image_list = []
for i in range(5):
    run_image_list.append(core.load_image('player_sprites', f'run_{i}.png'))

player = core.Entity(entity_group, core.load_image('player_sprites', 'idle_0.png'), (100, 100),
                     (17, 9, 14, 26), core.AnimatedTexture(idle_image_list, 250),
                     core.AnimatedTexture(run_image_list, 70))

game_tickrate = pygame.time.Clock()
current_player_pos = (screen_size[0] // 2, screen_size[1] // 2)

current_room_pos = (0, 0)
prev_room_pos = (0, 0)
field_pos = [0, 0]
render_queue = []
running = True
move_y = 0
move_x = 0

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                move_y = -0.1
            elif event.key == pygame.K_s:
                move_y = 0.1
            if event.key == pygame.K_a:
                move_x = -0.1
            elif event.key == pygame.K_d:
                move_x = 0.1
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w and move_y != 0.1:
                move_y = 0
            elif event.key == pygame.K_s and move_y != -0.1:
                move_y = 0
            if event.key == pygame.K_a and move_x != 0.1:
                move_x = 0
            elif event.key == pygame.K_d and move_x != -0.1:
                move_x = 0

    player.acceleration_y = move_y
    player.acceleration_x = move_x

    current_player_pos = (player.rect.x, player.rect.y)

    if current_player_pos[0] >= screen_size[0]:
        field_pos[0] += screen_size[0]
        player.move_entity(-screen_size[0], 0)
        for room in rooms:
            room.move(screen_size[0] * -1, 0)
    elif current_player_pos[0] <= 0:
        field_pos[0] -= screen_size[0]
        player.move_entity(screen_size[0], 0)
        for room in rooms:
            room.move(screen_size[0], 0)

    if current_player_pos[1] >= screen_size[1]:
        field_pos[1] += screen_size[1]
        player.move_entity(0, -screen_size[1])
        for room in rooms:
            room.move(0, screen_size[1] * -1)

    elif current_player_pos[1] <= 0:
        field_pos[1] -= screen_size[1]
        player.move_entity(0, screen_size[1])
        for room in rooms:
            room.move(0, screen_size[1])

    current_player_pos = (player.rect.x, player.rect.y)
    current_room_pos = (
        round((current_player_pos[1] + field_pos[1] + player.rect.size[0] / 2) / generation.SIZE_OF_ROOM / generation.SIZE_OF_TEXTURES - 0.5),
        round((current_player_pos[0] + field_pos[0] + player.rect.size[1] / 2) / generation.SIZE_OF_ROOM / generation.SIZE_OF_TEXTURES - 0.5))

    mouse_relative_coords = (180 / math.pi) * -math.atan2(pygame.mouse.get_pos()[1] - player.rect.y,
                                                          pygame.mouse.get_pos()[0] - player.rect.x)

    if prev_room_pos != current_room_pos or render_queue == []:
        render_queue = []
        for room in rooms:
            if current_room_pos in room.covering_squares:
                render_queue.append(room)

        neighbours_pos = render_queue[0].roomneighbours
        for roomneighbour in rooms:
            if roomneighbour.position in neighbours_pos:
                render_queue.append(roomneighbour)
    player.update(render_queue, game_tickrate.tick(FPS))

    screen.fill(pygame.Color(0, 0, 0))
    for render_room in render_queue:
        render_room.spritegroup.draw(screen)
        render_room.collisionsprites.draw(screen)

    if True:  # DEBUG use True for hitboxes
        for entity in entity_group:
            pygame.draw.rect(screen, (0, 255, 0), entity.hitbox)
    entity_group.draw(screen)

    for render_room in render_queue:
        render_room.upper_spritegroup.draw(screen)

    for render_room in render_queue:
        if current_room_pos not in render_room.covering_squares:
            render_room.render_mist(screen, field_pos)

    prev_room_pos = current_room_pos
    current_room_pos = (0, 0)
    pygame.display.flip()
pygame.quit()

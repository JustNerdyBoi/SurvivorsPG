import pygame

import core
import generation

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_centre = (screen.get_rect()[2] // 2, screen.get_rect()[3] // 2)
print(screen_centre)
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

ENTITYUPDATE = pygame.USEREVENT + 1
pygame.time.set_timer(ENTITYUPDATE, 16)

test_entity_group = pygame.sprite.Group()
rock_entity = core.Entity(test_entity_group, core.load_image('tile_1_7.png'), screen_centre, 100, 2, 1)

clock = pygame.time.Clock()
current_cam_pos = screen_centre
current_room_pos = (0, 0)
prev_room_pos = (0, 0)
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

        if event.type == ENTITYUPDATE:
            rock_entity.acceleration_y = move_y
            rock_entity.acceleration_x = move_x

    current_cam_pos = (rock_entity.rect.x, rock_entity.rect.y)
    current_room_pos = (
        round(current_cam_pos[1] / generation.SIZE_OF_ROOM / generation.SIZE_OF_TEXTURES - 0.5),
        round(current_cam_pos[0] / generation.SIZE_OF_ROOM / generation.SIZE_OF_TEXTURES - 0.5))

    screen.fill(pygame.Color("black"))
    if prev_room_pos != current_room_pos:
        render_queue = []
        for room in rooms:
            if current_room_pos in room.covering_squares:
                render_queue.append(room)

        neighbours_pos = render_queue[0].roomneighbours
        for roomneighbour in rooms:
            if roomneighbour.position in neighbours_pos:
                render_queue.append(roomneighbour)
    rock_entity.update(render_queue)


    for render_room in render_queue:
        render_room.spritegroup.draw(screen)
        render_room.collisionsprites.draw(screen)

    test_entity_group.draw(screen)

    for render_room in render_queue:
        render_room.upper_spritegroup.draw(screen)

    prev_room_pos = current_room_pos
    current_room_pos = (0, 0)
    pygame.display.flip()
pygame.quit()

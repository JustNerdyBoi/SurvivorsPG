import pygame
import core
import generation

FULLSCREEN = False
STANDART_RESOLUTION = (2048, 1024)
DEBUG = False
FPS = 60  # changed for FPS
BACKGROUND_COLOR = (0, 0, 0)
MAIN_COLOR = (255, 255, 255)


def draw_text(text, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    text_rect.center = (x, y)
    surface.blit(text_obj, text_rect)


def menu():
    start_button = pygame.Rect(width // 2 - 50, height // 2 + 50, 100, 50)
    start_button_rect = pygame.draw.rect(screen, MAIN_COLOR, start_button)
    running_menu = True
    while running_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_menu = False
                global main_process
                main_process = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(event.pos):
                    running_menu = False

        screen.fill(BACKGROUND_COLOR)

        draw_text("Приветствую!", MAIN_COLOR, screen, width // 2, height // 2 - 50)

        start_button = pygame.Rect(width // 2 - 50, height // 2 + 50, 100, 50)
        start_button_rect = pygame.draw.rect(screen, MAIN_COLOR, start_button)
        draw_text("Начать", BACKGROUND_COLOR, screen, width // 2, height // 2 + 75)

        pygame.display.flip()


def loser_screen():
    start_button = pygame.Rect(width // 2 - 50, height // 2 + 50, 100, 50)
    start_button_rect = pygame.draw.rect(screen, MAIN_COLOR, start_button)
    running_loser_screen = True
    while running_loser_screen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_loser_screen = False
                global main_process
                main_process = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(event.pos):
                    running_loser_screen = False

        screen.fill(BACKGROUND_COLOR)

        draw_text("Вы проиграли", MAIN_COLOR, screen, width // 2, height // 2 - 50)

        start_button = pygame.Rect(width // 2 - 50, height // 2 + 50, 100, 50)
        start_button_rect = pygame.draw.rect(screen, MAIN_COLOR, start_button)
        draw_text("Меню", BACKGROUND_COLOR, screen, width // 2, height // 2 + 75)

        pygame.display.flip()


def game_process():
    screen_size = (width, height)
    pygame.display.set_caption('Surivorsmap')
    rooms = generation.create_board()
    field = generation.map_filling(rooms)
    rooms = generation.apply_sprites(rooms, field)

    entity_group = core.EntityGroup()
    projectile_group = core.EntityGroup()

    player = core.Player(entity_group, projectile_group, core.load_image('player_sprites', 'idle_00.png'), (256, 256),
                         (17, 9, 14, 26), (25, -10, 30, 60),
                         core.load_animation('player_sprites', 'idle', 3, 200),
                         core.load_animation('player_sprites', 'run', 6, 70),
                         core.load_animation('player_sprites', 'bow', 9, 120),
                         core.load_animation('player_sprites', 'attack', 10, 100),
                         core.load_animation('player_sprites', 'death', 7, 250),
                         50, False, 50, 0, 1,
                         50, [1, 7])

    dummy = core.Mob(entity_group, projectile_group, core.load_image('player_sprites', 'idle_00.png'), (750, 750),
                     (17, 9, 14, 26), (25, -10, 30, 60),
                     core.load_animation('player_sprites', 'idle', 3, 200),
                     core.load_animation('player_sprites', 'run', 6, 70),
                     core.load_animation('player_sprites', 'bow', 9, 120),
                     core.load_animation('player_sprites', 'attack', 10, 100),
                     core.load_animation('player_sprites', 'death', 7, 250),
                     30, False, 100, 3, 100,
                     30, [1, 7])

    game_tickrate = pygame.time.Clock()

    prev_room_pos = (0, 0)
    prev_room = []
    field_pos = [0, 0]
    render_queue = []

    running = True
    move_y = 0
    move_x = 0
    player.loser = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                global main_process
                main_process = False
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
            if (event.type == pygame.MOUSEBUTTONDOWN and player.current_animation != player.death_animation
                    and not player.affected_by_impulse):
                player.speed_y = 0
                player.speed_x = 0
                player.current_animation_stage = 0
                if event.button == 1:
                    player.current_animation = player.melee_animation
                elif event.button == 3:
                    player.current_animation = player.aiming_animation
            if event.type == pygame.MOUSEBUTTONUP and player.current_animation != player.death_animation:
                player.current_animation = player.idle_animation
        if player.current_animation not in (player.aiming_animation, player.melee_animation, player.death_animation):
            player.acceleration_y = move_y
            player.acceleration_x = move_x

        current_player_pos = (player.rect.x, player.rect.y)

        if current_player_pos[0] >= screen_size[0]:
            field_pos[0] += screen_size[0]
            entity_group.move_group(-screen_size[0], 0)
            for room in rooms:
                room.move(screen_size[0] * -1, 0)
        elif current_player_pos[0] <= 0:
            field_pos[0] -= screen_size[0]
            entity_group.move_group(screen_size[0], 0)
            for room in rooms:
                room.move(screen_size[0], 0)

        if current_player_pos[1] >= screen_size[1]:
            field_pos[1] += screen_size[1]
            entity_group.move_group(0, -screen_size[1])
            for room in rooms:
                room.move(0, screen_size[1] * -1)

        elif current_player_pos[1] <= 0:
            field_pos[1] -= screen_size[1]
            entity_group.move_group(0, screen_size[1])
            for room in rooms:
                room.move(0, screen_size[1])

        current_player_pos = (player.rect.x, player.rect.y)
        current_room_pos = (
            round((current_player_pos[1] + field_pos[1] + player.rect.size[
                0] / 2) / generation.SIZE_OF_ROOM / generation.SIZE_OF_TEXTURES - 0.5),
            round((current_player_pos[0] + field_pos[0] + player.rect.size[
                1] / 2) / generation.SIZE_OF_ROOM / generation.SIZE_OF_TEXTURES - 0.5))

        if prev_room_pos != current_room_pos or render_queue == []:

            render_queue = []
            for room in rooms:
                if current_room_pos in room.covering_squares:
                    render_queue.append(room)

            current_room = render_queue[0]
            if current_room != prev_room:
                projectile_group.empty()
            prev_room = current_room

            neighbours_pos = current_room.roomneighbours
            for roomneighbour in rooms:
                if roomneighbour.position in neighbours_pos:
                    render_queue.append(roomneighbour)

        current_tickrate = game_tickrate.tick(FPS)
        entity_group.tick_update(render_queue, current_tickrate)
        projectile_group.tick_update(render_queue, current_tickrate)

        screen.fill(pygame.Color(0, 0, 0))
        for render_room in render_queue:
            render_room.spritegroup.draw(screen)
            render_room.collisionsprites.draw(screen)

        if DEBUG:  # DEBUG use True for hitboxes
            for entity in entity_group:
                pygame.draw.rect(screen, (0, 0, 225), entity.attack_hitbox)
                pygame.draw.rect(screen, (0, 255, 0), entity.hitbox)
            for projectile in projectile_group:
                pygame.draw.rect(screen, (255, 0, 0), projectile.hitbox)

        projectile_group.draw(screen)
        entity_group.draw(screen)

        for render_room in render_queue:
            render_room.upper_spritegroup.draw(screen)

        for render_room in render_queue:
            if current_room_pos not in render_room.covering_squares:
                render_room.render_mist(screen, field_pos)

        dummy.target_cord = player.position_on_map
        if dummy.current_animation not in (dummy.aiming_animation, dummy.death_animation):
            if pygame.math.Vector2(dummy.position_on_map).distance_to(player.position_on_map) > 200:
                dummy.current_animation = dummy.aiming_animation
            elif dummy.current_animation != dummy.melee_animation:
                dummy.current_animation = dummy.melee_animation

        prev_room_pos = current_room_pos
        pygame.display.flip()

        if player.loser:
            running = False


if FULLSCREEN:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode(STANDART_RESOLUTION)
width = screen.get_width()
height = screen.get_height()

pygame.init()
pygame.display.set_caption("Приветствую!")

font = pygame.font.Font(None, 36)
main_process = True
while main_process:
    menu()
    if main_process:
        game_process()
        if main_process:
            loser_screen()
pygame.quit()

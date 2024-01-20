import random
import sqlite3
import core
from os import walk

SIZE_OF_ROOM = 16
SIZE_OF_TEXTURES = 32


def create_board():
    board = [[0 for _ in range(8)] for _ in range(8)]
    figures = []

    def can_place_figure(x, y, figure):
        if figure == "square2x2":
            if x + 1 >= 8 or y + 1 >= 8:
                return False
            for i in range(2):
                for j in range(2):
                    if board[x + i][y + j] != 0:
                        return False
        elif figure == "square2x2_without_1":
            if x + 1 >= 8 or y + 1 >= 8:
                return False
            if board[x][y + 1] != 0 or board[x + 1][y] != 0 or board[x + 1][y + 1] != 0:
                return False
        elif figure == "stripe2x1":
            if x + 1 >= 8:
                return False
            for i in range(2):
                if board[x + i][y] != 0:
                    return False
        elif figure == "square1x1":
            if board[x][y] != 0:
                return False
        return True

    def place_figure(x, y, figure):
        if figure == "square2x2":
            for i in range(2):
                for j in range(2):
                    board[x + i][y + j] = 1
        elif figure == "square2x2_without_1":
            board[x][y + 1] = board[x + 1][y] = board[x + 1][y + 1] = 1
        elif figure == "stripe2x1":
            for i in range(2):
                board[x + i][y] = 1
        elif figure == "square1x1":
            board[x][y] = 1

    def reset_board():
        nonlocal board, figures
        board = [[0 for _ in range(8)] for _ in range(8)]
        figures = []

    def generate_board():
        reset_board()
        # Размещаем квадрат 2x2
        x, y = random.randint(0, 7), random.randint(0, 7)
        while not can_place_figure(x, y, "square2x2"):
            x, y = random.randint(0, 7), random.randint(0, 7)
        place_figure(x, y, "square2x2")
        place_4(x, y)

        # Размещаем квадрат 2x2 без 1 клетки
        x, y = random.randint(0, 7), random.randint(0, 7)
        while not can_place_figure(x, y, "square2x2_without_1"):
            x, y = random.randint(0, 7), random.randint(0, 7)
        place_figure(x, y, "square2x2_without_1")
        figures.append(core.Room((x, y), 3, SIZE_OF_ROOM))

        # Размещаем полоску 2x1
        x, y = random.randint(0, 7), random.randint(0, 7)
        while not can_place_figure(x, y, "stripe2x1"):
            x, y = random.randint(0, 7), random.randint(0, 7)
        place_figure(x, y, "stripe2x1")
        figures.append(core.Room((x, y), 2, SIZE_OF_ROOM))

        # Размещаем квадрат 1x1
        x, y = random.randint(0, 7), random.randint(0, 7)
        while not can_place_figure(x, y, "square1x1"):
            x, y = random.randint(0, 7), random.randint(0, 7)
        place_figure(x, y, "square1x1")
        figures.append(core.Room((x, y), 1, SIZE_OF_ROOM))

        # Заполняем оставшиеся клетки случайными фигурами
        for i in range(8):
            for j in range(8):
                if board[i][j] == 0:
                    figure = random.choice(["square2x2", "square2x2_without_1", "stripe2x1", "square1x1"])
                    while not can_place_figure(i, j, figure):
                        figure = random.choice(["square2x2", "square2x2_without_1", "stripe2x1", "square1x1"])
                    place_figure(i, j, figure)
                    if figure == "square2x2":
                        place_4(i, j)
                    if figure == "square2x2_without_1":
                        figures.append(core.Room((i, j), 3, SIZE_OF_ROOM))
                    if figure == "stripe2x1":
                        figures.append(core.Room((i, j), 2, SIZE_OF_ROOM))
                    if figure == "square1x1":
                        figures.append(core.Room((i, j), 1, SIZE_OF_ROOM))

    def place_4(x, y):  # placing some 3+1 instead 4 rooms
        if random.randint(1, 3) == 1:
            figures.append(core.Room((x, y), 4, SIZE_OF_ROOM))
        else:
            figures.append(core.Room((x, y), 1, SIZE_OF_ROOM))
            figures.append(core.Room((x, y), 3, SIZE_OF_ROOM))

    generate_board()
    while any(0 in row for row in board):
        generate_board()
    rooms = []
    for room in figures:
        neighbour_roomparts = []
        for room_part in room.covering_squares:
            variant = (room_part[0] - 1, room_part[1])
            if variant[0] >= 0 and variant not in room.covering_squares and variant not in neighbour_roomparts:
                neighbour_roomparts.append(variant)

            variant = (room_part[0] + 1, room_part[1])
            if variant[0] <= 7 and variant not in room.covering_squares and variant not in neighbour_roomparts:
                neighbour_roomparts.append(variant)

            variant = (room_part[0], room_part[1] - 1)
            if variant[1] >= 0 and variant not in room.covering_squares and variant not in neighbour_roomparts:
                neighbour_roomparts.append(variant)

            variant = (room_part[0], room_part[1] + 1)
            if variant[1] <= 7 and variant not in room.covering_squares and variant not in neighbour_roomparts:
                neighbour_roomparts.append(variant)
        for neighbour_var in figures:
            if len(list(set(neighbour_roomparts) & set(neighbour_var.covering_squares))) > 0:
                room.roomneighbours.append(neighbour_var.position)
        rooms.append(room)
    return rooms


def map_filling(figures, base_way='room_presets'):
    database = sqlite3.connect(base_way)  # connecting to database with rooms presets
    cursor = database.cursor()
    presets = {}

    for room_type in range(1, 5):  # loading rooms presets to dictionary
        rooms_data = []
        for variant in range(1, 5):
            room = {}
            for tile in cursor.execute(f'SELECT * FROM "{room_type}_{variant}"').fetchall():
                room[tile[0]] = tile[1]
            rooms_data.append(room)
        presets[str(room_type)] = rooms_data

    field = [[0 for _ in range(8 * SIZE_OF_ROOM)] for _ in range(8 * SIZE_OF_ROOM)]  # creating game_field

    for figure in figures:  # filling field using presets
        variant_number = random.randint(1, 4)
        selected_preset = presets[str(figure.roomtype)][variant_number - 1]

        loot_positions = random.sample(cursor.execute(
            f'SELECT * FROM "{figure.roomtype}_{variant_number}" WHERE tile_type = 3').fetchall(), k=figure.roomtype)

        for loot_position in loot_positions:
            coords = list(map(int, loot_position[0].split(', ')))
            figure.lootpositions.append((coords[0] + figure.coords[0], coords[1] + figure.coords[1]))

        for pos, tile_type in selected_preset.items():
            tile_position = pos.split(', ')
            figure.tilepositions.append((int(tile_position[0]), int(tile_position[1])))
            tile_coords = (int(tile_position[1]) + figure.coords[0], int(tile_position[0]) + figure.coords[1])
            if tile_type == 3:  # removing loot positions becausee they're in Room object data
                tile_type = 0

            if (tile_coords[0] == 0 or tile_coords[1] == 0 or  # placing outer border
                    tile_coords[0] == SIZE_OF_ROOM * 8 - 1 or tile_coords[1] == SIZE_OF_ROOM * 8 - 1):
                tile_type = 1

            field[tile_coords[0]][tile_coords[1]] = tile_type

    database.close()
    return field


def apply_sprites(rooms, field):
    tile_textures = {}  # loading tile textures
    for texture in next(walk('textures\map_tiles'), (None, None, []))[2]:
        tile_textures[texture] = core.load_image('map_tiles', texture)

    second_applyment_queue = []

    for room in rooms:

        for tileposition in room.tilepositions:
            tile_coords = (tileposition[1] + room.coords[0], tileposition[0] + room.coords[1])
            tile_type = field[tile_coords[0]][tile_coords[1]]
            if (tileposition[0] + room.coords[0], tileposition[1] + room.coords[1]) in room.lootpositions:
                core.TileSprite(room.spritegroup, tile_textures['tile_0.png'], tile_coords[1] * SIZE_OF_TEXTURES,
                                tile_coords[0] * SIZE_OF_TEXTURES)
                # core.TileSprite(room.spritegroup, tile_textures[f'tile_box_0.png'],
                # tile_coords[1] * SIZE_OF_TEXTURES + SIZE_OF_TEXTURES // 4,
                # tile_coords[0] * SIZE_OF_TEXTURES + SIZE_OF_TEXTURES // 4)

            else:
                if tile_type == 0:
                    core.TileSprite(room.spritegroup, tile_textures['tile_0.png'], tile_coords[1] * SIZE_OF_TEXTURES,
                                    tile_coords[0] * SIZE_OF_TEXTURES)
                    plants_random = random.randint(1, 10)  # plants dencity
                    if plants_random != 1:
                        core.TileSprite(room.spritegroup, tile_textures[f'tile_grass_{random.randint(1, 6)}.png'],
                                        tile_coords[1] * SIZE_OF_TEXTURES +
                                        round(SIZE_OF_TEXTURES * random.randint(4, 8) // 10),
                                        tile_coords[0] * SIZE_OF_TEXTURES +
                                        round(SIZE_OF_TEXTURES * random.randint(2, 8) // 10))
                    elif plants_random == 1:
                        core.TileSprite(room.spritegroup, tile_textures[f'tile_bush_{random.randint(1, 6)}.png'],
                                        tile_coords[1] * SIZE_OF_TEXTURES - SIZE_OF_TEXTURES // 5,
                                        tile_coords[0] * SIZE_OF_TEXTURES)

                elif tile_type == 2:  # applying path texture
                    up, right, down, left = '1', '1', '1', '1'

                    if field[tile_coords[0] - 1][tile_coords[1]] == 2:
                        up = '0'
                    if field[tile_coords[0] + 1][tile_coords[1]] == 2:
                        down = '0'
                    if field[tile_coords[0]][tile_coords[1] - 1] == 2:
                        left = '0'
                    if field[tile_coords[0]][tile_coords[1] + 1] == 2:
                        right = '0'
                    core.TileSprite(room.spritegroup, tile_textures[f'tile_2_{up}{right}{down}{left}.png'],
                                    tile_coords[1] * SIZE_OF_TEXTURES, tile_coords[0] * SIZE_OF_TEXTURES)
                elif tile_type == 4:
                    core.TileSprite(room.spritegroup, tile_textures['tile_0.png'], tile_coords[1] * SIZE_OF_TEXTURES,
                                    tile_coords[0] * SIZE_OF_TEXTURES)
                    forest_random = random.randint(1, 10)  # forest dencity
                    if forest_random >= 7:
                        type_of_tree = random.randint(1, 10)

                        if type_of_tree >= 4 and field[tile_coords[0] - 1][tile_coords[1]] != 1 and \
                                field[tile_coords[0] + 1][tile_coords[1]] != 1 and field[tile_coords[0]][
                            tile_coords[1] - 1] != 1 and field[tile_coords[0] - 1][tile_coords[1] + 1] != 1:
                            second_applyment_queue.append(
                                (room, tile_textures['tile_tree.png'],
                                 tile_coords[1] * SIZE_OF_TEXTURES,
                                 tile_coords[0] * SIZE_OF_TEXTURES))
                        else:
                            core.TileSprite(room.spritegroup, tile_textures[f'tile_log_{random.randint(1, 5)}.png'],
                                            tile_coords[1] * SIZE_OF_TEXTURES,
                                            tile_coords[0] * SIZE_OF_TEXTURES)
                    elif forest_random <= 6:
                        core.TileSprite(room.spritegroup, tile_textures[f'tile_dirt_{random.randint(1, 6)}.png'],
                                        tile_coords[1] * SIZE_OF_TEXTURES + SIZE_OF_TEXTURES // 3,
                                        tile_coords[0] * SIZE_OF_TEXTURES + SIZE_OF_TEXTURES // 3)

                elif tile_type == 1:
                    core.TileSprite(room.spritegroup, tile_textures['tile_0.png'], tile_coords[1] * SIZE_OF_TEXTURES,
                                    tile_coords[0] * SIZE_OF_TEXTURES)
                    core.TileSprite(room.collisionsprites, tile_textures[f'tile_1_{random.randint(7, 12)}.png'],
                                    tile_coords[1] * SIZE_OF_TEXTURES,
                                    tile_coords[0] * SIZE_OF_TEXTURES)
    for render in sorted(second_applyment_queue, key=lambda rend: rend[3]):
        texture = render[1]
        core.TileSprite(render[0].upper_spritegroup, texture, render[2] - SIZE_OF_TEXTURES // 2,
                        render[3] - texture.get_rect()[3] + SIZE_OF_TEXTURES)
        core.TileSprite(render[0].collisionsprites, tile_textures['tile_0.png'],
                        render[2], render[3])
    return rooms

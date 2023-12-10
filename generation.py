import random
import sqlite3

SIZE_OF_ROOM = 16


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
        figures.append(((x, y), 4))

        # Размещаем квадрат 2x2 без 1 клетки
        x, y = random.randint(0, 7), random.randint(0, 7)
        while not can_place_figure(x, y, "square2x2_without_1"):
            x, y = random.randint(0, 7), random.randint(0, 7)
        place_figure(x, y, "square2x2_without_1")
        figures.append(((x, y), 3))

        # Размещаем полоску 2x1
        x, y = random.randint(0, 7), random.randint(0, 7)
        while not can_place_figure(x, y, "stripe2x1"):
            x, y = random.randint(0, 7), random.randint(0, 7)
        place_figure(x, y, "stripe2x1")
        figures.append(((x, y), 2))

        # Размещаем квадрат 1x1
        x, y = random.randint(0, 7), random.randint(0, 7)
        while not can_place_figure(x, y, "square1x1"):
            x, y = random.randint(0, 7), random.randint(0, 7)
        place_figure(x, y, "square1x1")
        figures.append(((x, y), 1))

        # Заполняем оставшиеся клетки случайными фигурами
        for i in range(8):
            for j in range(8):
                if board[i][j] == 0:
                    figure = random.choice(["square2x2", "square2x2_without_1", "stripe2x1", "square1x1"])
                    while not can_place_figure(i, j, figure):
                        figure = random.choice(["square2x2", "square2x2_without_1", "stripe2x1", "square1x1"])
                    place_figure(i, j, figure)
                    if figure == "square2x2":
                        figures.append(((i, j), 4))
                    if figure == "square2x2_without_1":
                        figures.append(((i, j), 3))
                    if figure == "stripe2x1":
                        figures.append(((i, j), 2))
                    if figure == "square1x1":
                        figures.append(((i, j), 1))

    generate_board()
    while any(0 in row for row in board):
        generate_board()

    return figures


def map_filling(figures, base_way='room_presets'):
    database = sqlite3.connect(base_way)  # connecting to database with rooms presets
    cursor = database.cursor()
    presets = {}
    for room_type in range(1, 5):  # collecting rooms presets to dictionary
        rooms_data = []
        for variant in range(1, 5):
            rooms_data.append(cursor.execute(f'SELECT * FROM "{room_type}_{variant}"').fetchall())
        presets[str(room_type)] = rooms_data

    field = [[0 for _ in range(128)] for _ in range(128)]  # creating game_field

    for figure in figures:
        coord, room_type = figure
        selected_preset = random.choice(presets[str(room_type)])
        for tile in selected_preset:
            tile_position = tile[0].split(', ')
            tile_type = tile[1]
            field[int(tile_position[1]) + coord[1] * SIZE_OF_ROOM][int(tile_position[0])
                                                                   + coord[0] * SIZE_OF_ROOM] = tile_type
    return field

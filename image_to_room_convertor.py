from PIL import Image
import sqlite3

base_way = "room_presets"
database = sqlite3.connect(base_way)
cursor = database.cursor()

room = input("Enter room type and variant number separated by '_':")
# only room type and variant number. Example "1_1" - for 1x1 room variant 1

image = Image.open(f"rooms/{room}.png")


def pixel_type(color):
    if color == (0, 0, 0):  # walls
        return 1
    if color == (100, 100, 100):  # inner space
        return 0
    if color == (255, 100, 0):  # path
        return 2
    if color == (0, 255, 0):  # loot pos
        return 3
    if color == (0, 0, 255):  # water
        return 4
    else:
        return None


tiles = []
pixels = image.load()
size = image.size
for x in range(size[0]):
    for y in range(size[1]):
        tile_type = pixel_type(pixels[x, y][:3])
        if tile_type:
            tiles.append([(x, y), tile_type])
try:
    cursor.execute(f"""CREATE TABLE [{room}] (
        tile_coord TEXT    NOT NULL
                           UNIQUE,
        tile_type  INTEGER NOT NULL
    );""")
    database.commit()
    for tile in tiles:
        cursor.execute(f"INSERT INTO '{room}'(tile_coord,tile_type) VALUES('{tile[0]}', {tile[1]})")
    database.commit()
    database.close()
except:
    print("ROOM ALREADY EXISTS")

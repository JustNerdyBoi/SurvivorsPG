import pygame
import sys
import os


class Room:
    def __init__(self, position, roomtype, roomsize):
        self.coords = (position[0] * roomsize, position[1] * roomsize)
        self.position = position
        self.roomtype = roomtype
        self.tilepositions = []
        self.lootpositions = []
        self.spritegroup = pygame.sprite.Group()


def load_image(name, colorkey=None):
    fullname = os.path.join('textures', name)
    if not os.path.isfile(fullname):
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image

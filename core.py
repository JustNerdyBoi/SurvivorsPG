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
        self.roomneighbours = []
        self.covering_squares = []
        if roomtype == 1:
            self.covering_squares.append(position)
        elif roomtype in [2, 4]:
            self.covering_squares.append((position[0] + 1, position[1]))
            self.covering_squares.append(position)
            if roomtype == 4:
                self.covering_squares.append((position[0] + 1, position[1] + 1))
                self.covering_squares.append((position[0], position[1] + 1))
        elif roomtype == 3:
            self.covering_squares.append((position[0], position[1] + 1))
            self.covering_squares.append((position[0] + 1, position[1] + 1))
            self.covering_squares.append((position[0] + 1, position[1]))

        self.upper_spritegroup = pygame.sprite.Group()
        self.spritegroup = pygame.sprite.Group()
        self.collisionsprites = pygame.sprite.Group()

    def move(self, x, y):
        for sprite in self.spritegroup:
            sprite.move_tile(x, y)
        for sprite in self.collisionsprites:
            sprite.move_tile(x, y)
        for sprite in self.upper_spritegroup:
            sprite.move_tile(x, y)


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


class TileSprite(pygame.sprite.Sprite):
    def __init__(self, group, texture, x, y):
        super().__init__(group)
        self.image = texture
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def move_tile(self, x, y):
        self.rect = self.rect.move(x, y)


class Entity(pygame.sprite.Sprite):
    def __init__(self, group, texture, coordinates, max_hp, max_speed=1, regen=0):
        super().__init__(group)
        self.image = texture
        self.rect = self.image.get_rect()
        self.rect.x = coordinates[0]
        self.rect.y = coordinates[1]

        self.max_hp = max_hp
        self.hp = max_hp
        self.regen = regen

        self.speed_x, self.speed_y = (0, 0)
        self.max_speed = max_speed
        self.acceleration_x, self.acceleration_y = (0, 0)
        self.friction = 0.1

    def update(self, collisiongroup):
        if self.regen > 0 and self.hp < self.max_hp:
            self.hp += self.regen
        if self.speed_x != 0 or self.acceleration_x != 0:
            if abs(self.speed_x + self.acceleration_x) <= self.max_speed:
                self.speed_x += self.acceleration_x
            if self.acceleration_x == 0:
                self.speed_x -= self.friction * (self.speed_x / abs(self.speed_x))

            pre_x = self.rect.x
            self.rect.x += self.speed_x
            if pygame.sprite.spritecollide(self, collisiongroup, False):
                self.speed_x = 0
                self.rect.x = pre_x

        if self.speed_y != 0 or self.acceleration_y != 0:
            if abs(self.speed_y + self.acceleration_y) <= self.max_speed:
                self.speed_y += self.acceleration_y
            if self.acceleration_y == 0:
                self.speed_y -= self.friction * (self.speed_y / abs(self.speed_y))

            pre_y = self.rect.y
            self.rect.y += self.speed_y
            if pygame.sprite.spritecollide(self, collisiongroup, False):
                self.speed_y = 0
                self.rect.y = pre_y

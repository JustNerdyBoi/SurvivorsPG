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


def load_image(subdirectory, name, colorkey=None):
    print(name)
    fullname = os.path.join(f'textures/{subdirectory}', name)
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
    def __init__(self, group, texture, x, y, rect=None):
        super().__init__(group)
        self.image = texture
        if rect:
            self.rect = rect.get_rect(rect)
        else:
            self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def move_tile(self, x, y):
        self.rect = self.rect.move(x, y)


class Entity(pygame.sprite.Sprite):
    def __init__(self, group, texture, coordinates, hitbox_rect, max_hp, max_speed=1, regen=0, collision=True):
        super().__init__(group)
        self.image = texture
        self.position_on_map = list(coordinates)

        self.rect = self.image.get_rect()
        self.rect.x = coordinates[0]
        self.rect.y = coordinates[1]

        hb_x_pos, hb_y_pos, hb_x_size, hb_y_size = hitbox_rect
        self.hitbox = Hitbox(pygame.Surface((hb_x_size, hb_y_size), pygame.SRCALPHA))
        self.hitbox.rect.x += self.rect.x + hb_x_pos
        self.hitbox.rect.y += self.rect.y + hb_y_pos

        self.max_hp = max_hp
        self.hp = max_hp
        self.regen = regen

        self.speed_x, self.speed_y = (0, 0)
        self.max_speed = max_speed
        self.acceleration_x, self.acceleration_y = (0, 0)
        self.friction = 0.1
        self.speed_coefficient = 0.1
        self.collisionable = collision

    def update(self, collisiongroups, time_from_prev_frame):
        if self.regen > 0 and self.hp < self.max_hp:
            self.hp += self.regen

        if self.speed_x != 0 or self.acceleration_x != 0:
            if abs(self.speed_x + self.acceleration_x) <= self.max_speed:
                self.speed_x += self.acceleration_x
            if self.acceleration_x == 0 and self.speed_x != 0:
                pre_friction_result = self.friction * (self.speed_x / abs(self.speed_x))
                if abs(pre_friction_result) < abs(self.speed_x):
                    self.speed_x -= pre_friction_result
                else:
                    self.speed_x = 0

            pre_x = self.hitbox.rect.x
            movement_x = round(self.speed_x * time_from_prev_frame * self.speed_coefficient)
            self.hitbox.rect.x += movement_x
            if self.collisionable:
                for collisiongroup in collisiongroups:
                    if pygame.sprite.spritecollide(self.hitbox, collisiongroup.collisionsprites, False):
                        self.speed_x = 0
                        self.hitbox.rect.x = pre_x
                        break
            if self.hitbox.rect.x != pre_x:
                self.rect.x += movement_x
                self.position_on_map[0] += movement_x

        if self.speed_y != 0 or self.acceleration_y != 0:
            if abs(self.speed_y + self.acceleration_y) <= self.max_speed:
                self.speed_y += self.acceleration_y
            if self.acceleration_y == 0 and self.speed_y != 0:
                pre_friction_result = self.friction * (self.speed_y / abs(self.speed_y))
                if abs(pre_friction_result) < abs(self.speed_y):
                    self.speed_y -= pre_friction_result
                else:
                    self.speed_y = 0

            pre_y = self.hitbox.rect.y
            movement_y = round(self.speed_y * time_from_prev_frame * self.speed_coefficient)
            self.hitbox.rect.y += movement_y
            if self.collisionable:
                for collisiongroup in collisiongroups:
                    if pygame.sprite.spritecollide(self.hitbox, collisiongroup.collisionsprites, False):
                        self.speed_y = 0
                        self.hitbox.rect.y = pre_y
                        break
            if self.hitbox.rect.y != pre_y:
                self.rect.y += movement_y
                self.position_on_map[1] += movement_y


class Hitbox(pygame.sprite.Sprite):
    def __init__(self, surface):
        pygame.sprite.Sprite.__init__(self)
        self.image = surface
        self.rect = self.image.get_rect()

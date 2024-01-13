import random

import pygame
import sys
import os
import math

import generation


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
        self.mist_rects = []

    def render_mist(self, screen, fied_pos):
        self.mist_rects = []
        for square_coords in self.covering_squares:
            square_size = generation.SIZE_OF_ROOM * generation.SIZE_OF_TEXTURES
            surface = pygame.Surface((square_size, square_size))
            surface.set_alpha(220)
            surface.fill((0, 0, 0))
            screen.blit(surface, (square_coords[1] * square_size - fied_pos[0],
                                  square_coords[0] * square_size - fied_pos[1]))

    def move(self, x, y):
        for sprite in self.spritegroup:
            sprite.move_tile(x, y)
        for sprite in self.collisionsprites:
            sprite.move_tile(x, y)
        for sprite in self.upper_spritegroup:
            sprite.move_tile(x, y)


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


def load_image(subdirectory, name, colorkey=None):
    fullname = os.path.join(f'textures/{subdirectory}', name)
    if not os.path.isfile(fullname):
        print(f'no such file as {name}')
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    print(f'image from {name} was successfully imported')
    return image


class AnimatedTexture:
    def __init__(self, images_list, frame_time):
        self.images = images_list
        self.frame_time = frame_time
        self.max_frame = len(images_list) - 1


class Entity(pygame.sprite.Sprite):
    def __init__(self, group, texture, coordinates, hitbox_rect, max_speed=1, collision=True, friction=0.1):
        super().__init__(group)
        self.image = texture

        self.rect = self.image.get_rect()
        self.rect.x = coordinates[0]
        self.rect.y = coordinates[1]

        hb_x_pos, hb_y_pos, hb_x_size, hb_y_size = hitbox_rect
        self.hitbox = Hitbox(pygame.Surface((hb_x_size, hb_y_size), pygame.SRCALPHA))
        self.hitbox.rect.x += self.rect.x + hb_x_pos
        self.hitbox.rect.y += self.rect.y + hb_y_pos

        self.position_on_map = [self.hitbox.rect.x + self.hitbox.rect.size[0] // 2,
                                self.hitbox.rect.y + self.hitbox.rect.size[1] // 2]

        self.speed_x, self.speed_y = (0, 0)
        self.max_speed = max_speed
        self.acceleration_x, self.acceleration_y = (0, 0)
        self.friction = friction
        self.speed_coefficient = 0.15
        self.collisionable = collision
        self.movement_x = 0
        self.movement_y = 0

    def move_entity(self, x, y):
        self.rect.x += x
        self.hitbox.rect.x += x
        self.rect.y += y
        self.hitbox.rect.y += y

    def in_movement(self):
        pass

    def stable(self):
        pass

    def on_collision(self):
        pass

    def update(self, collisiongroups, time_from_prev_frame):
        if self.speed_x != 0 or self.acceleration_x != 0:
            if abs(self.speed_x + self.acceleration_x) <= self.max_speed:
                self.speed_x += self.acceleration_x
            if (self.acceleration_x == 0 or (self.acceleration_x > 0) != (self.speed_x > 0)) and self.speed_x != 0:
                pre_friction_result = self.friction * (self.speed_x / abs(self.speed_x))
                if abs(pre_friction_result) < abs(self.speed_x):
                    self.speed_x -= pre_friction_result
                else:
                    self.speed_x = 0
            self.acceleration_x = 0

            pre_x = self.hitbox.rect.x
            self.movement_x = round(self.speed_x * time_from_prev_frame * self.speed_coefficient)
            self.hitbox.rect.x += self.movement_x
            if self.collisionable:
                for collisiongroup in collisiongroups:
                    if pygame.sprite.spritecollide(self.hitbox, collisiongroup.collisionsprites, False):
                        self.speed_x = 0
                        self.hitbox.rect.x = pre_x
                        self.on_collision()
                        break
            if self.hitbox.rect.x != pre_x:
                self.rect.x += self.movement_x
                self.position_on_map[0] += self.movement_x

        if self.speed_y != 0 or self.acceleration_y != 0:
            if abs(self.speed_y + self.acceleration_y) <= self.max_speed:
                self.speed_y += self.acceleration_y
            if (self.acceleration_y == 0 or (self.acceleration_y > 0) != (self.speed_y > 0)) and self.speed_y != 0:
                pre_friction_result = self.friction * (self.speed_y / abs(self.speed_y))
                if abs(pre_friction_result) < abs(self.speed_y):
                    self.speed_y -= pre_friction_result
                else:
                    self.speed_y = 0
            self.acceleration_y = 0

            pre_y = self.hitbox.rect.y
            self.movement_y = round(self.speed_y * time_from_prev_frame * self.speed_coefficient)
            self.hitbox.rect.y += self.movement_y
            if self.collisionable:
                for collisiongroup in collisiongroups:
                    if pygame.sprite.spritecollide(self.hitbox, collisiongroup.collisionsprites, False):
                        self.speed_y = 0
                        self.hitbox.rect.y = pre_y
                        self.on_collision()
                        break
            if self.hitbox.rect.y != pre_y:
                self.rect.y += self.movement_y
                self.position_on_map[1] += self.movement_y

        if abs(self.speed_y) >= self.max_speed / 2 or abs(self.speed_x) >= self.max_speed / 2:
            self.in_movement()
        elif not self.speed_x and not self.speed_y:
            self.stable()


class Mob(Entity):
    def __init__(self, group, texture, coordinates, hitbox_rect, idle_animation, movement_animation, ranger=True,
                 melee=False, max_speed=1,
                 collision=True, friction=0.1, max_hp=100, regen=10):
        super().__init__(group, texture, coordinates, hitbox_rect, max_speed, collision, friction)
        self.max_hp = max_hp
        self.hp = max_hp
        self.regen = regen
        self.ranger = ranger
        self.melee = melee

        self.animation_clock = pygame.time.Clock()
        self.animation_clock_current = 0
        self.current_animation_stage = 0
        self.positive_x_facing = True
        self.positive_y_facing = False

        if idle_animation:
            self.idle_animation = idle_animation
        else:
            self.idle_animation = AnimatedTexture([texture], 10)
        self.current_animation = self.idle_animation

        if movement_animation:
            self.movement_animation = movement_animation
        else:
            self.movement_animation = AnimatedTexture([texture], 10)

    def animation_update(self):
        self.facing_checking()
        self.animation_clock_current += self.animation_clock.tick()
        if self.animation_clock_current >= self.current_animation.frame_time > 0:
            self.animation_clock_current = 0
            if self.current_animation_stage < self.current_animation.max_frame:
                self.current_animation_stage += 1
            else:
                self.current_animation_stage = 0
            self.image = pygame.transform.flip(self.current_animation.images[self.current_animation_stage],
                                               not self.positive_x_facing, False)

    def facing_checking(self):
        if self.movement_x < 0 and self.positive_x_facing:
            self.positive_x_facing = False
        elif self.movement_x > 0 and not self.positive_x_facing:
            self.positive_x_facing = True

        if self.movement_y < 0 and self.positive_y_facing:
            self.positive_y_facing = False
        elif self.movement_y > 0 and not self.positive_y_facing:
            self.positive_y_facing = True

    def in_movement(self):
        self.current_animation = self.movement_animation

    def stable(self):
        if self.current_animation != self.idle_animation:
            self.current_animation = self.idle_animation
            self.animation_clock_current = self.current_animation.frame_time

    def shot(self, projectile_group, target_coords, texture, damage, base_acceleration, inaccuracy=3):
        if self.ranger:
            projectile_angle = (180 / math.pi) * -math.atan2(target_coords[1] - self.position_on_map[1],
                                                             target_coords[0] - self.position_on_map[0])
            projectile_angle += random.uniform(-inaccuracy * 360 / 200, inaccuracy * 360 / 200)
            projectile = Projectile(projectile_group, texture, (self.hitbox.rect.x, self.hitbox.rect.y),
                                    (0, 0, texture.get_size()[0], texture.get_size()[1]), damage)
            projectile.image = pygame.transform.rotate(texture, projectile_angle)
            projectile.acceleration_x = base_acceleration * math.sin(math.radians(projectile_angle + 90)) + self.speed_x
            projectile.acceleration_y = base_acceleration * math.cos(math.radians(projectile_angle + 90)) + self.speed_y


class Player(Mob):
    def facing_checking(self):
        updated_facing = False
        if self.current_animation != self.movement_animation:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] - self.position_on_map[0] < 0 and self.positive_x_facing:
                self.positive_x_facing = False
                updated_facing = True
            elif mouse_pos[0] - self.position_on_map[0] > 0 and not self.positive_x_facing:
                self.positive_x_facing = True
                updated_facing = True

            if mouse_pos[1] - self.position_on_map[1] < 0 and self.positive_y_facing:
                self.positive_y_facing = False
                updated_facing = True
            elif mouse_pos[1] - self.position_on_map[1] > 0 and not self.positive_y_facing:
                self.positive_y_facing = True
                updated_facing = True
        else:
            super().facing_checking()

        if updated_facing:
            self.animation_clock_current = self.current_animation.frame_time


class Projectile(Entity):
    def __init__(self, group, texture, coordinates, hitbox_rect, damage, max_speed=15, friction=0.01, collision=True):
        super().__init__(group, texture, coordinates, hitbox_rect, max_speed, collision, friction)
        self.damage = damage

    def on_collision(self):
        self.speed_x = 0
        self.speed_y = 0


class Hitbox(pygame.sprite.Sprite):
    def __init__(self, surface):
        pygame.sprite.Sprite.__init__(self)
        self.image = surface
        self.rect = self.image.get_rect()

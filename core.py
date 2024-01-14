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


def load_animation(subdirectory, name, frame_amount, frame_delay):
    image_list = []
    for image_id in range(frame_amount):
        image_list.append(load_image(subdirectory, f'{name}_{str(image_id).rjust(2, "0")}.png'))
    return AnimatedTexture(image_list, frame_delay)


class AnimatedTexture:
    def __init__(self, images_list, frame_time):
        self.images = images_list
        self.frame_time = frame_time
        self.max_frame = len(images_list) - 1


class EntityGroup(pygame.sprite.Group):
    def move_group(self, x, y):
        for entity in self:
            entity.hard_movement(x, y)

    def tick_update(self, collision_group, tickrate):
        for entity in self:
            entity.update(collision_group, tickrate)
            if type(entity) in (Mob, Player):
                entity.animation_update()


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
        self.impulse = [0, 0]
        self.affected_by_impulse = False

        self.manualy_moved = [0, 0]

    def hard_movement(self, x, y):
        self.rect.x += x
        self.hitbox.rect.x += x
        self.manualy_moved[0] -= x
        self.rect.y += y
        self.hitbox.rect.y += y
        self.manualy_moved[1] -= y

    def in_movement(self):
        pass

    def stable(self):
        pass

    def on_collision(self):
        pass

    def movement(self, x, y):
        self.rect.x += x
        self.position_on_map[0] += x
        self.rect.y += y
        self.position_on_map[1] += y

    def update(self, collisiongroups, time_from_prev_frame):
        if self.impulse[0] or self.impulse[1] or (self.affected_by_impulse and (self.speed_x or self.speed_y)):
            self.affected_by_impulse = True
            self.acceleration_x = 0
            self.acceleration_y = 0
        elif self.affected_by_impulse and (not self.speed_x or not self.speed_y):
            self.affected_by_impulse = False

        if self.speed_x or self.acceleration_x or self.impulse[0]:
            if abs(self.speed_x + self.acceleration_x) <= self.max_speed:
                self.speed_x += self.acceleration_x + self.impulse[0]
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
                self.movement(self.movement_x, 0)

        if self.speed_y or self.acceleration_y or self.impulse[1]:
            if abs(self.speed_y + self.acceleration_y) <= self.max_speed:
                self.speed_y += self.acceleration_y + self.impulse[1]
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
                self.movement(0, self.movement_y)

        self.impulse = [0, 0]

        if abs(self.speed_y) >= self.max_speed / 2 or abs(self.speed_x) >= self.max_speed / 2:
            self.in_movement()
        elif not self.speed_x and not self.speed_y:
            self.stable()


class Mob(Entity):
    def __init__(self, group, projectile_group, texture, coordinates,
                 hitbox_rect, attack_hitbox_rect,
                 idle_animation, movement_animation, aiming_animation, melee_animation, death_animation,
                 ranger_damage=0, projectile_image=False, knockback=100, inaccuracy=0, arrows_per_shot=1,
                 melee_damage=0, melee_attack_stages=False,
                 max_speed=1,
                 collision=True, friction=0.1, max_hp=100, regen=10):
        super().__init__(group, texture, coordinates, hitbox_rect, max_speed, collision, friction)
        self.max_hp = max_hp
        self.hp = max_hp
        self.regen = regen

        hb_x_pos, hb_y_pos, hb_x_size, hb_y_size = attack_hitbox_rect
        self.attack_hitbox = Hitbox(pygame.Surface((hb_x_size, hb_y_size), pygame.SRCALPHA))
        self.attack_hitbox.rect.x += self.rect.x + hb_x_pos
        self.attack_hitbox.rect.y += self.rect.y + hb_y_pos

        self.animation_clock = pygame.time.Clock()
        self.animation_clock_current = 0
        self.current_animation_stage = 0
        self.positive_x_facing = True

        def check_animation(animation):
            if animation:
                return animation
            return AnimatedTexture([texture], -1)

        self.idle_animation = check_animation(idle_animation)
        self.movement_animation = check_animation(movement_animation)
        self.aiming_animation = check_animation(aiming_animation)
        self.melee_animation = check_animation(melee_animation)
        self.death_animation = check_animation(death_animation)

        self.current_animation = self.idle_animation

        self.ranger_dmg = ranger_damage
        self.knockback = knockback
        self.inaccuracy = inaccuracy
        self.arrows_per_shot = arrows_per_shot
        self.projectile_group = projectile_group
        if not projectile_image:
            self.projectile_image = load_image('combat', 'arrow.png')
        else:
            self.projectile_image = projectile_image

        self.melee_dmg = melee_damage
        if melee_attack_stages:
            self.melee_attack_stages = melee_attack_stages
        else:
            self.melee_attack_stages = [self.melee_animation.max_frame]

        self.target_cord = [0, 0]

    def animation_update(self):
        self.facing_checking()
        if self.hp <= 0 and self.current_animation != self.death_animation:
            self.current_animation = self.death_animation
            self.current_animation_stage = 0

        self.animation_clock_current += self.animation_clock.tick()
        if self.animation_clock_current >= self.current_animation.frame_time > 0:
            self.animation_clock_current = 0
            if self.current_animation_stage < self.current_animation.max_frame:
                self.current_animation_stage += 1

            elif self.current_animation == self.aiming_animation:
                self.current_animation = self.idle_animation
                self.current_animation_stage = 0
                for _ in range(self.arrows_per_shot):
                    self.shot(self.get_target_coord(), self.projectile_image, self.inaccuracy)

            elif self.current_animation == self.death_animation:
                self.on_death()
                self.kill()

            else:
                self.current_animation_stage = 0
            self.image = pygame.transform.flip(self.current_animation.images[self.current_animation_stage],
                                               not self.positive_x_facing, False)
            if (self.current_animation == self.melee_animation and
                    self.current_animation_stage in self.melee_attack_stages):
                target_coords = self.get_target_coord()
                projectile_angle = (180 / math.pi) * -math.atan2(target_coords[1] - self.position_on_map[1],
                                                                 target_coords[0] - self.position_on_map[0])
                self.impulse = [self.max_speed * 2 * math.sin(math.radians(projectile_angle + 90)) + self.speed_x,
                                self.max_speed * 2 * math.cos(math.radians(projectile_angle + 90)) + self.speed_y]

                self.melee_hit(self.groups()[0], self.melee_dmg)

    def facing_checking(self):
        if not self.affected_by_impulse:
            updated_facing = False
            if self.current_animation != self.movement_animation:
                if (self.get_target_coord()[0] - self.hitbox.rect.x - self.hitbox.rect.size[0] // 2 < 0
                        and self.positive_x_facing):
                    self.positive_x_facing = False
                    self.attack_hitbox.rect.x -= self.attack_hitbox.rect.size[0]
                    updated_facing = True
                elif (self.get_target_coord()[0] - self.hitbox.rect.x - self.hitbox.rect.size[0] // 2 > 0
                      and not self.positive_x_facing):
                    self.positive_x_facing = True
                    self.attack_hitbox.rect.x += self.attack_hitbox.rect.size[0]
                    updated_facing = True
            else:
                if self.movement_x < 0 and self.positive_x_facing:
                    self.positive_x_facing = False
                    self.attack_hitbox.rect.x -= self.attack_hitbox.rect.size[0]
                elif self.movement_x > 0 and not self.positive_x_facing:
                    self.positive_x_facing = True
                    self.attack_hitbox.rect.x += self.attack_hitbox.rect.size[0]
            if updated_facing:
                self.animation_clock_current = self.current_animation.frame_time

    def in_movement(self):
        if self.current_animation not in (self.melee_animation, self.death_animation, self.aiming_animation):
            self.current_animation = self.movement_animation

    def stable(self):
        if (self.current_animation not in
                (self.idle_animation, self.aiming_animation, self.melee_animation, self.death_animation)):
            self.current_animation = self.idle_animation
            self.animation_clock_current = self.current_animation.frame_time

    def hard_movement(self, x, y):
        super().hard_movement(x, y)
        self.attack_hitbox.rect.x += x
        self.attack_hitbox.rect.y += y

    def get_target_coord(self):
        return self.target_cord

    def shot(self, target_coords, texture, inaccuracy=1, base_acceleration=8):
        if self.ranger_dmg:
            projectile_angle = (180 / math.pi) * -math.atan2(target_coords[1] - self.position_on_map[1],
                                                             target_coords[0] - self.position_on_map[0])
            projectile_angle += random.uniform(-inaccuracy * 360 / 200, inaccuracy * 360 / 200)
            projectile = Projectile(self.projectile_group, texture, (self.hitbox.rect.x, self.hitbox.rect.y),
                                    (8, 8, texture.get_size()[0] - 8, texture.get_size()[1] - 8), self.ranger_dmg,
                                    self.knockback, self)
            projectile.image = pygame.transform.rotate(texture, projectile_angle)
            projectile.impulse = [base_acceleration * math.sin(math.radians(projectile_angle + 90)) + self.speed_x,
                                  base_acceleration * math.cos(math.radians(projectile_angle + 90)) + self.speed_y]
            self.impulse = [-projectile.impulse[0] / base_acceleration,
                            -projectile.impulse[1] / base_acceleration]

            if len(self.projectile_group) > 255:  # projectile cap
                for projectile in self.projectile_group:
                    projectile.kill()
                    break

    def melee_hit(self, group, damage):
        for hitted_entity in pygame.sprite.spritecollide(self.attack_hitbox, group, False):
            if hitted_entity != self:
                hitted_entity.hp -= damage

                hit_angle = (180 / math.pi) * -math.atan2(hitted_entity.position_on_map[1] - self.position_on_map[1],
                                                          hitted_entity.position_on_map[0] - self.position_on_map[0])
                hitted_entity.impulse = [
                    hitted_entity.max_speed * 4 * math.sin(math.radians(hit_angle + 90)) + self.speed_x,
                    hitted_entity.max_speed * 4 * math.cos(math.radians(hit_angle + 90)) + self.speed_y]

    def movement(self, x, y):
        super().movement(x, y)
        self.attack_hitbox.rect.x += x
        self.attack_hitbox.rect.y += y

    def on_death(self):
        pass


class Player(Mob):
    def get_target_coord(self):
        return pygame.mouse.get_pos()[0] + self.manualy_moved[0], pygame.mouse.get_pos()[1] + self.manualy_moved[1]

    def on_death(self):
        self.loser = True


class Projectile(Entity):
    def __init__(self, group, texture, coordinates, hitbox_rect, damage, knockback, shooter, max_speed=15,
                 friction=0.01, collision=True):
        super().__init__(group, texture, coordinates, hitbox_rect, max_speed, collision, friction)
        self.damage = damage
        self.shooter = shooter
        self.target_group = shooter.groups()[0]
        self.shooting_pos = shooter.position_on_map
        self.knockback = knockback

    def on_collision(self):
        self.speed_x = 0
        self.speed_y = 0

    def update(self, collisiongroups, time_from_prev_frame):
        super().update(collisiongroups, time_from_prev_frame)
        for collided_entity in pygame.sprite.spritecollide(self, self.target_group, False):
            if collided_entity != self.shooter and (self.speed_x or self.speed_y):
                collided_entity.hp -= self.damage
                collided_entity.impulse = [self.speed_x * self.knockback / 100, self.speed_y * self.knockback / 100]
                self.on_collision()


class Hitbox(pygame.sprite.Sprite):
    def __init__(self, surface):
        pygame.sprite.Sprite.__init__(self)
        self.image = surface
        self.rect = self.image.get_rect()

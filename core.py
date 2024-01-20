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
    return image


def load_animation(subdirectory, name, frame_amount, frame_delay):
    image_list = []
    for image_id in range(frame_amount):
        image_list.append(load_image(subdirectory, f'{name}_{str(image_id).rjust(2, "0")}.png'))
    return AnimatedTexture(image_list, frame_delay)


def cut_image(subdirectory, name, lenth, flipx=False, scale=1):
    images = []
    full_image = load_image(subdirectory, name)
    for i in range(full_image.get_size()[0] // lenth):
        current_image = full_image.subsurface(pygame.Rect((i * lenth, 0), (lenth, full_image.get_size()[1])))
        if flipx:
            current_image = pygame.transform.flip(current_image, True, False)
        current_image = pygame.transform.scale(current_image, (lenth * scale, current_image.get_size()[1] * scale))
        images.append(current_image)
    return images


class AnimatedTexture:
    def __init__(self, images_list, frame_time):
        self.images = images_list
        self.frame_time = frame_time
        self.max_frame = len(images_list) - 1


class EntityGroup(pygame.sprite.Group):
    def map_flip_move(self, x, y):
        for entity in self:
            entity.hard_movement(x, y, True)

    def tick_update(self, collision_group, tickrate):
        for entity in self:
            entity.update(collision_group, tickrate)
            if issubclass(type(entity), Mob):
                entity.animation_update()


class Entity(pygame.sprite.Sprite):
    def __init__(self, group, texture, coordinates, hitbox_rect, max_speed=1, collision=True, friction=0.1):
        super().__init__(group)
        self.image = texture

        self.rect = self.image.get_rect()
        self.rect.x = coordinates[0] - self.rect.size[0] // 2 - coordinates[2][0]
        self.rect.y = coordinates[1] - self.rect.size[1] // 2 - coordinates[2][1]
        self.safe_spawn = False
        if len(coordinates) > 3 and coordinates[3]:
            self.safe_spawn = True

        hb_x_pos, hb_y_pos, hb_x_size, hb_y_size = hitbox_rect
        self.hitbox = Hitbox(pygame.Surface((hb_x_size, hb_y_size), pygame.SRCALPHA))
        self.hitbox.rect.x += self.rect.x + hb_x_pos
        self.hitbox.rect.y += self.rect.y + hb_y_pos

        self.position_on_map = list(coordinates[0:2])

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

        self.map_flipped = coordinates[2]

    def hard_movement(self, x, y, map_flipped=False):
        self.rect.x += x
        self.hitbox.rect.x += x

        self.rect.y += y
        self.hitbox.rect.y += y

        if map_flipped:
            self.map_flipped[0] -= x
            self.map_flipped[1] -= y
        else:
            self.position_on_map[0] += x
            self.position_on_map[1] += y

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
        while self.safe_spawn:
            self.safe_spawn = False
            for collisiongroup in collisiongroups:
                if pygame.sprite.spritecollide(self.hitbox, collisiongroup.collisionsprites, False):
                    self.safe_spawn = True
            if self.safe_spawn:
                size_of_room = generation.SIZE_OF_ROOM * generation.SIZE_OF_TEXTURES
                current_room_pos = (self.position_on_map[0] // size_of_room, self.position_on_map[1] // size_of_room)
                new_position = (random.randint(current_room_pos[0] * size_of_room + generation.SIZE_OF_TEXTURES,
                                               (current_room_pos[0] + 1) * size_of_room - generation.SIZE_OF_TEXTURES),
                                random.randint(current_room_pos[1] * size_of_room + generation.SIZE_OF_TEXTURES,
                                               (current_room_pos[1] + 1) * size_of_room - generation.SIZE_OF_TEXTURES))

                self.hard_movement(new_position[0] - self.position_on_map[0], new_position[1] - self.position_on_map[1])

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
    def __init__(self, group, projectile_group, particle_group, texture, coordinates,
                 hitbox_rect, attack_hitbox_rect,
                 idle_animation, movement_animation, aiming_animation, melee_animation, death_animation, hostile=False,
                 ranger_damage=0, projectile_image=False, knockback=100, inaccuracy=0, arrows_per_shot=1,
                 melee_damage=0, melee_attack_stages=False,
                 max_hp=100, regen=0, max_speed=1, friction=0.1,
                 collision=True):
        super().__init__(group, texture, coordinates, hitbox_rect, max_speed, collision, friction)

        self.max_hp = max_hp
        self.hp = max_hp
        self.regen = regen
        self.regen_clock = pygame.time.Clock()

        self.particle_group = particle_group
        self.health_bar = pygame.sprite.Sprite(particle_group)
        self.health_bar_animation = AnimatedTexture(cut_image('combat', 'healthbar.png', 50), -1)
        self.health_bar.image = self.health_bar_animation.images[0]
        self.health_bar.rect = self.health_bar.image.get_rect()
        self.health_bar_stage = 0

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
        self.hostile = hostile

    def update(self, collisiongroups, time_from_prev_frame):
        super().update(collisiongroups, time_from_prev_frame)
        healing = self.regen * self.regen_clock.tick() / 1000
        if self.current_animation != self.death_animation and self.hp < self.max_hp:
            if self.hp + healing < self.max_hp:
                self.hp += healing
            else:
                self.hp = self.max_hp
        self.health_bar.rect = (
            self.position_on_map[0] - self.map_flipped[0] - self.health_bar.image.get_size()[0] // 2,
            self.position_on_map[1] - self.map_flipped[1] + self.hitbox.rect.size[1] // 2 + 10)
        current_healthbar_stage = round(9 - self.hp / self.max_hp * 9)
        if self.health_bar_stage != current_healthbar_stage:
            if self.hp == self.max_hp:
                self.health_bar.image = self.health_bar_animation.images[0]
                self.health_bar_stage = 0
            elif self.hp > 0:
                if current_healthbar_stage == 0:
                    current_healthbar_stage = 1
                self.health_bar.image = self.health_bar_animation.images[current_healthbar_stage]
                self.health_bar_stage = current_healthbar_stage
            else:
                self.health_bar.image = self.health_bar_animation.images[10]

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

            elif self.current_animation == self.melee_animation and type(self) is not Player:
                self.current_animation = self.idle_animation
                self.current_animation_stage = 0

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
                hit_angle = (180 / math.pi) * -math.atan2(target_coords[1] - self.position_on_map[1],
                                                          target_coords[0] - self.position_on_map[0])
                self.impulse = [self.max_speed * 2 * math.sin(math.radians(hit_angle + 90)) + self.speed_x,
                                self.max_speed * 2 * math.cos(math.radians(hit_angle + 90)) + self.speed_y]

                self.melee_hit(self.groups()[0], self.melee_dmg)

    def facing_checking(self):
        if not self.affected_by_impulse:
            updated_facing = False
            if self.current_animation != self.movement_animation:
                if (self.get_target_coord()[0] - self.position_on_map[0] < 0
                        and self.positive_x_facing):
                    self.positive_x_facing = False
                    self.attack_hitbox.rect.x -= self.attack_hitbox.rect.size[0]
                    updated_facing = True
                elif (self.get_target_coord()[0] - self.position_on_map[0] > 0
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

    def hard_movement(self, x, y, map_flipped=False):
        super().hard_movement(x, y, map_flipped)
        self.attack_hitbox.rect.x += x
        self.attack_hitbox.rect.y += y

    def get_target_coord(self):
        return self.target_cord

    def shot(self, target_coords, texture, inaccuracy=1, base_acceleration=8):
        if self.ranger_dmg:
            projectile_angle = (180 / math.pi) * -math.atan2(target_coords[1] - self.position_on_map[1],
                                                             target_coords[0] - self.position_on_map[0])
            projectile_angle += random.uniform(-inaccuracy * 360 / 200, inaccuracy * 360 / 200)
            projectile = Projectile(self.projectile_group, texture,
                                    (self.position_on_map[0], self.position_on_map[1], self.map_flipped),
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
            if self.hostile != hitted_entity.hostile:
                hitted_entity.hp -= damage

                hit_angle = (180 / math.pi) * -math.atan2(hitted_entity.position_on_map[1] - self.position_on_map[1],
                                                          hitted_entity.position_on_map[0] - self.position_on_map[0])
                hitted_entity.impulse = [
                    hitted_entity.max_speed * 4 * math.sin(math.radians(hit_angle + 90)) + self.speed_x,
                    hitted_entity.max_speed * 4 * math.cos(math.radians(hit_angle + 90)) + self.speed_y]
                if type(self) is Player:
                    self.score += damage

    def movement(self, x, y):
        super().movement(x, y)
        self.attack_hitbox.rect.x += x
        self.attack_hitbox.rect.y += y

    def follow_target(self, acc_modificator=1):
        if self.current_animation != self.movement_animation:
            self.current_animation = self.movement_animation
        target_coords = self.get_target_coord()
        angle = (180 / math.pi) * -math.atan2(target_coords[1] - self.position_on_map[1],
                                              target_coords[0] - self.position_on_map[0])
        self.acceleration_x = self.max_speed * math.sin(math.radians(angle + 90)) * acc_modificator
        self.acceleration_y = self.max_speed * math.cos(math.radians(angle + 90)) * acc_modificator

    def on_death(self):
        self.health_bar.kill()


class Player(Mob):
    def __init__(self, entity_group, projectile_group, particle_group, coordinates):
        super().__init__(entity_group, projectile_group, particle_group, load_image('player_sprites', 'idle_00.png'),
                         coordinates,
                         (17, 9, 14, 26), (25, -10, 60, 60),
                         load_animation('player_sprites', 'idle', 3, 200),
                         load_animation('player_sprites', 'run', 6, 70),
                         load_animation('player_sprites', 'bow', 9, 120),
                         load_animation('player_sprites', 'attack', 10, 100),
                         load_animation('player_sprites', 'death', 7, 250),
                         False, 25, False, 50, 2, 3,
                         75, [1, 7], 100, 5)
        self.score = 0
        self.loser = False

    def get_target_coord(self):
        return pygame.mouse.get_pos()[0] + self.map_flipped[0], pygame.mouse.get_pos()[1] + self.map_flipped[1]

    def on_death(self):
        super().on_death()
        self.loser = True

    def melee_hit(self, group, damage):
        super().melee_hit(group, damage)
        for hitted_projectile in pygame.sprite.spritecollide(self.attack_hitbox, self.projectile_group, False):
            hitted_projectile.speed_x *= -2
            hitted_projectile.speed_y *= -2
            hitted_projectile.shooter = self
            hitted_projectile.image = pygame.transform.rotate(hitted_projectile.image, 180)
            hitted_projectile.damage *= 2
            hitted_projectile.knockback *= 2


class Goblin(Mob):
    def __init__(self, entity_group, projectile_group, particle_group, coordinates):
        super().__init__(entity_group, projectile_group, particle_group, load_image('mob_sprites', 'goblin.png'),
                         coordinates,
                         (15, 11, 17, 28), (24, 0, 50, 45),
                         False,
                         AnimatedTexture(cut_image('mob_sprites', 'goblin_walk.png', 48, True), 70),
                         False,
                         AnimatedTexture(cut_image('mob_sprites', 'goblin_attack.png', 48, True), 120),
                         AnimatedTexture(cut_image('mob_sprites', 'goblin_death.png', 48, True), 300),
                         True, 0, False, 0, 0, 0,
                         25, [4],
                         200, 2, 0.4, 0.2)


class Bee(Mob):
    def __init__(self, entity_group, projectile_group, particle_group, coordinates):
        fly_sprites = cut_image('mob_sprites', 'bee_fly.png', 48, True)
        super().__init__(entity_group, projectile_group, particle_group, load_image('mob_sprites', 'bee.png'),
                         coordinates,
                         (15, 21, 17, 18), (24, 10, 30, 40),
                         AnimatedTexture(fly_sprites, 100),
                         AnimatedTexture(fly_sprites, 50),
                         AnimatedTexture(fly_sprites, 150),
                         False,
                         AnimatedTexture(cut_image('mob_sprites', 'bee_death.png', 48, True), 100),
                         True, 5, load_image('combat', 'bee_proj.png'), 10, 5, 1,
                         40, [],
                         45, 2, 2, 0.03)


class Slime(Mob):
    def __init__(self, entity_group, projectile_group, particle_group, coordinates, splitness=2):
        texture = load_image('mob_sprites', 'slime.png')
        splitness += 1
        if splitness > 1:
            death_animation = AnimatedTexture(cut_image('mob_sprites', 'slime_split.png', 48, True, splitness), 120)
        else:
            death_animation = AnimatedTexture(cut_image('mob_sprites', 'slime_death.png', 48, True, splitness), 120)
        super().__init__(entity_group, projectile_group, particle_group,
                         pygame.transform.scale(pygame.transform.flip(texture, True, False),
                                                (texture.get_size()[0] * splitness, texture.get_size()[1] * splitness)),
                         coordinates,
                         (16 * splitness, 25 * splitness, 16 * splitness, 13 * splitness),
                         (24 * splitness, 10 * splitness, 30 * splitness, 35 * splitness),
                         False,
                         AnimatedTexture(cut_image('mob_sprites', 'slime_walk.png', 48, True, splitness), 120),
                         False,
                         AnimatedTexture(cut_image('mob_sprites', 'slime_attack.png', 48, True, splitness), 120),
                         death_animation,
                         True, 0, False, 0, 0, 0,
                         5 * splitness, [5],
                         20 * splitness, 2, 0.4, 0.1)
        self.splitness = splitness - 1

    def on_death(self):
        super().on_death()
        if self.splitness > 0:
            child1 = Slime(self.groups()[0], self.projectile_group, self.particle_group,
                           (self.position_on_map[0], self.position_on_map[1], self.map_flipped),
                           self.splitness - 1)
            child2 = Slime(self.groups()[0], self.projectile_group, self.particle_group,
                           (self.position_on_map[0], self.position_on_map[1], self.map_flipped),
                           self.splitness - 1)
            child1.impulse = [random.uniform(-self.max_speed, self.max_speed) * 10,
                              random.uniform(-self.max_speed, self.max_speed) * 10]
            child2.impulse = [-child1.impulse[0], -child1.impulse[1]]


class Projectile(Entity):
    def __init__(self, group, texture, coordinates, hitbox_rect, damage, knockback, shooter, max_speed=15,
                 friction=0.0, collision=True):
        super().__init__(group, texture, coordinates, hitbox_rect, max_speed, collision, friction)
        self.damage = damage
        self.shooter = shooter
        self.target_group = shooter.groups()[0]
        self.shooting_pos = shooter.position_on_map
        self.knockback = knockback

    def on_collision(self):
        if type(self.shooter) is Bee:
            self.kill()
        self.speed_x = 0
        self.speed_y = 0

    def update(self, collisiongroups, time_from_prev_frame):
        super().update(collisiongroups, time_from_prev_frame)
        for collided_entity in pygame.sprite.spritecollide(self, self.target_group, False):
            if (collided_entity.hostile != self.shooter.hostile and (self.speed_x or self.speed_y)
                    and pygame.sprite.collide_rect(self, collided_entity.hitbox)):
                collided_entity.hp -= self.damage
                collided_entity.impulse = [self.speed_x * self.knockback / 100, self.speed_y * self.knockback / 100]
                self.on_collision()
                if type(self.shooter) is Player:
                    self.shooter.score += self.damage


class Hitbox(pygame.sprite.Sprite):
    def __init__(self, surface):
        pygame.sprite.Sprite.__init__(self)
        self.image = surface
        self.rect = self.image.get_rect()

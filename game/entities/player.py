import math
import random
import pygame
from game.core.circleshape import CircleShape
from game.entities.shot import Shot
from game.config.constants import (
    PLAYER_RADIUS,
    LINE_WIDTH,
    PLAYER_ACCELERATION,
    PLAYER_MAX_SPEED,
    PLAYER_TURN_SPEED,
    PLAYER_SHOT_SPEED,
    PLAYER_SHOOT_COOLDOWN_SECONDS,
    PLAYER_SPRITE_PATH,
    PLAYER_INVULNERABLE_SPRITE_PATH,
    PLAYER_SPRITE_SIZE_MULTIPLIER,
    PLAYER_BUZZ_AMPLITUDE_PX,
    PLAYER_BUZZ_FREQUENCY_HZ,
    PLAYER_BUZZ_RAMP_UP,
    PLAYER_BUZZ_RAMP_DOWN,
)


class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS)
        self.rotation = 0
        self.cd = 0
        self.__sprite = self.__load_sprite(PLAYER_SPRITE_PATH)
        self.__invulnerable_sprite = self.__load_sprite(PLAYER_INVULNERABLE_SPRITE_PATH)
        self.__sprite_cache = {}
        self.__is_moving = False
        self.__buzz_intensity = 0.0
        self.__buzz_time = 0.0
        self.__invulnerable = False
        self.__invulnerable_visual_time = 0.0
        self.__buzz_phase = random.uniform(0.0, math.pi * 2)
        self.__buzz_phase_2 = random.uniform(0.0, math.pi * 2)

    def __load_sprite(self, sprite_path):
        if not sprite_path:
            return None
        target_size = max(1, int(self.radius * PLAYER_SPRITE_SIZE_MULTIPLIER))
        try:
            sprite = pygame.image.load(sprite_path).convert_alpha()
        except Exception as err:
            print(f"Warning: failed to load player sprite '{sprite_path}': {err}")
            return None

        src_width, src_height = sprite.get_size()
        scale = min(target_size / src_width, target_size / src_height)
        scaled_size = (
            max(1, int(src_width * scale)),
            max(1, int(src_height * scale)),
        )
        return pygame.transform.smoothscale(sprite, scaled_size)

    def __get_rotated_sprite(self):
        use_alt_sprite = self.__invulnerable and self.__invulnerable_sprite is not None
        base_sprite = self.__invulnerable_sprite if use_alt_sprite else self.__sprite
        if base_sprite is None:
            return None

        # ship.png points north; player rotation=0 points south in current movement model.
        angle = int(round(180 - self.rotation)) % 360
        mode = "invuln" if use_alt_sprite else "normal"
        cache_key = (mode, angle)
        if cache_key not in self.__sprite_cache:
            self.__sprite_cache[cache_key] = pygame.transform.rotozoom(
                base_sprite,
                angle,
                1.0,
            )
        return self.__sprite_cache[cache_key]

    def set_invulnerable(self, active):
        self.__invulnerable = active
        if not active:
            self.__invulnerable_visual_time = 0.0

    def triangle(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(
            self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]

    def draw(self, screen):
        draw_center = self.position + self.__get_buzz_offset()
        sprite = self.__get_rotated_sprite()
        if sprite:
            rect = sprite.get_rect(center=(draw_center.x, draw_center.y))
            if self.__invulnerable and self.__invulnerable_sprite is None:
                pulse = (math.sin(self.__invulnerable_visual_time * 16.0) + 1.0) * 0.5
                alpha = int(155 + pulse * 100)
                temp = sprite.copy()
                temp.set_alpha(alpha)
                screen.blit(temp, rect.topleft)
            else:
                screen.blit(sprite, rect.topleft)
            return
        buzz_offset = draw_center - self.position
        points = [point + buzz_offset for point in self.triangle()]
        color = (130, 220, 255) if self.__invulnerable else "white"
        pygame.draw.polygon(screen, color, points, LINE_WIDTH)

    def __get_buzz_offset(self):
        if self.__buzz_intensity <= 1e-3:
            return pygame.Vector2(0, 0)

        phase = (self.__buzz_time * PLAYER_BUZZ_FREQUENCY_HZ * 2 * math.pi) + self.__buzz_phase
        phase_2 = (
            self.__buzz_time * (PLAYER_BUZZ_FREQUENCY_HZ * 0.57) * 2 * math.pi
        ) + self.__buzz_phase_2
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(-forward.y, forward.x)

        lateral_wave = (math.sin(phase) * 0.72) + (math.sin(phase_2) * 0.28)
        longitudinal_wave = (math.sin(phase * 0.49 + phase_2 * 0.31) * 0.68) + (
            math.sin(phase_2 * 0.37) * 0.32
        )
        amplitude = PLAYER_BUZZ_AMPLITUDE_PX * self.__buzz_intensity
        lateral = lateral_wave * amplitude
        longitudinal = longitudinal_wave * (amplitude * 0.32)
        return (right * lateral) + (forward * longitudinal)

    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt

    def move(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate(self.rotation)
        self.velocity += rotated_vector * PLAYER_ACCELERATION * dt

    def __clamp_velocity(self):
        max_speed_sq = PLAYER_MAX_SPEED * PLAYER_MAX_SPEED
        if self.velocity.length_squared() > max_speed_sq:
            self.velocity.scale_to_length(PLAYER_MAX_SPEED)

    def update(self, dt):
        self.cd -= dt
        keys = pygame.key.get_pressed()
        self.__is_moving = keys[pygame.K_w] or keys[pygame.K_s]
        self.__buzz_time += dt
        if self.__invulnerable:
            self.__invulnerable_visual_time += dt

        target = 1.0 if self.__is_moving else 0.0
        rate = PLAYER_BUZZ_RAMP_UP if target > self.__buzz_intensity else PLAYER_BUZZ_RAMP_DOWN
        blend = min(1.0, dt * rate)
        self.__buzz_intensity += (target - self.__buzz_intensity) * blend

        if keys[pygame.K_a]:
            self.rotate(dt * -1)
        if keys[pygame.K_d]:
            self.rotate(dt)
        if keys[pygame.K_s]:
            self.move(dt * -1)
        if keys[pygame.K_w]:
            self.move(dt)
        self.__clamp_velocity()
        self.position += self.velocity * dt
        if keys[pygame.K_SPACE]:
            self.shoot()
        self.wrap_around_screen()

    def shoot(self):
        if self.cd > 0:
            return
        self.cd = PLAYER_SHOOT_COOLDOWN_SECONDS
        shot = Shot(self.position[0], self.position[1])
        shot.velocity = pygame.Vector2(0, 1).rotate(
            self.rotation) * PLAYER_SHOT_SPEED

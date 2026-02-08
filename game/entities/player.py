import pygame
from game.core.circleshape import CircleShape
from game.entities.shot import Shot
from game.config.constants import (
    PLAYER_RADIUS,
    LINE_WIDTH,
    PLAYER_SPEED,
    PLAYER_TURN_SPEED,
    PLAYER_SHOT_SPEED,
    PLAYER_SHOOT_COOLDOWN_SECONDS,
    PLAYER_SPRITE_PATH,
    PLAYER_SPRITE_SIZE_MULTIPLIER,
)


class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS)
        self.rotation = 0
        self.cd = 0
        self.__sprite = self.__load_sprite()
        self.__sprite_cache = {}

    def __load_sprite(self):
        target_size = max(1, int(self.radius * PLAYER_SPRITE_SIZE_MULTIPLIER))
        try:
            sprite = pygame.image.load(PLAYER_SPRITE_PATH).convert_alpha()
        except Exception as err:
            print(f"Warning: failed to load player sprite '{PLAYER_SPRITE_PATH}': {err}")
            return None

        src_width, src_height = sprite.get_size()
        scale = min(target_size / src_width, target_size / src_height)
        scaled_size = (
            max(1, int(src_width * scale)),
            max(1, int(src_height * scale)),
        )
        return pygame.transform.smoothscale(sprite, scaled_size)

    def __get_rotated_sprite(self):
        if self.__sprite is None:
            return None

        # ship.png points north; player rotation=0 points south in current movement model.
        angle = int(round(180 - self.rotation)) % 360
        if angle not in self.__sprite_cache:
            self.__sprite_cache[angle] = pygame.transform.rotozoom(
                self.__sprite,
                angle,
                1.0,
            )
        return self.__sprite_cache[angle]

    def triangle(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(
            self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]

    def draw(self, screen):
        sprite = self.__get_rotated_sprite()
        if sprite:
            rect = sprite.get_rect(center=(self.position.x, self.position.y))
            screen.blit(sprite, rect.topleft)
            return
        pygame.draw.polygon(screen, "white", self.triangle(), LINE_WIDTH)

    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt

    def move(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate(self.rotation)
        rotated_with_speed_vector = rotated_vector * PLAYER_SPEED * dt
        self.position += rotated_with_speed_vector

    def update(self, dt):
        self.cd -= dt
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.rotate(dt * -1)
        if keys[pygame.K_d]:
            self.rotate(dt)
        if keys[pygame.K_s]:
            self.move(dt * -1)
        if keys[pygame.K_w]:
            self.move(dt)
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

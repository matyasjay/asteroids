import pygame
from game.core.circleshape import CircleShape
from game.config.constants import (
    SHOT_RADIUS,
    SHOT_LIFETIME_SECONDS,
    SHOT_SPRITE_PATH,
    SHOT_SPRITE_SIZE_MULTIPLIER,
)


class Shot(CircleShape):
    _base_sprite = None
    _load_failed = False
    _rotation_cache = {}

    def __init__(self, x, y):
        super().__init__(x, y, SHOT_RADIUS)
        self.life_remaining = SHOT_LIFETIME_SECONDS
        self.__ensure_sprite_loaded()

    @classmethod
    def __ensure_sprite_loaded(cls):
        if cls._base_sprite is not None or cls._load_failed:
            return

        target_size = max(1, int(SHOT_RADIUS * SHOT_SPRITE_SIZE_MULTIPLIER))
        try:
            sprite = pygame.image.load(SHOT_SPRITE_PATH).convert_alpha()
        except Exception as err:
            print(f"Warning: failed to load shot sprite '{SHOT_SPRITE_PATH}': {err}")
            cls._load_failed = True
            return

        src_width, src_height = sprite.get_size()
        scale = min(target_size / src_width, target_size / src_height)
        scaled_size = (
            max(1, int(src_width * scale)),
            max(1, int(src_height * scale)),
        )
        cls._base_sprite = pygame.transform.smoothscale(sprite, scaled_size)
        cls._rotation_cache = {}

    def __get_rotated_sprite(self):
        if self._base_sprite is None:
            return None
        if self.velocity.length_squared() <= 1e-8:
            return self._base_sprite

        move_angle = pygame.Vector2(0, 1).angle_to(self.velocity)
        # missile.png points north; velocity baseline in game is south.
        angle = int(round(180 - move_angle)) % 360
        if angle not in self._rotation_cache:
            self._rotation_cache[angle] = pygame.transform.rotozoom(
                self._base_sprite,
                angle,
                1.0,
            )
        return self._rotation_cache[angle]

    def draw(self, screen):
        sprite = self.__get_rotated_sprite()
        if sprite:
            rect = sprite.get_rect(center=(self.position.x, self.position.y))
            screen.blit(sprite, rect.topleft)
            return
        pygame.draw.circle(screen, "white", self.position, SHOT_RADIUS)

    def update(self, dt):
        self.life_remaining -= dt
        if self.life_remaining <= 0:
            self.kill()
            return
        self.position += self.velocity * dt
        self.wrap_around_screen()

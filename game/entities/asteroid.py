import pygame
import random
from game.core.circleshape import CircleShape
from game.render.asteroid_texture import build_asteroid_texture
from game.config.constants import (
    ASTEROID_MIN_RADIUS,
)
from game.utils.logger import log_event


class Asteroid(CircleShape):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius)
        self.__texture = None
        self.__texture_offset = pygame.Vector2(0, 0)

        self.__texture, self.__texture_offset = build_asteroid_texture(
            self.radius,
            seed=random.randint(0, 1_000_000_000),
        )

    def draw(self, screen):
        if self.__texture:
            texture_pos = self.position + self.__texture_offset
            screen.blit(self.__texture, (int(texture_pos.x), int(texture_pos.y)))

    def update(self, dt):
        self.position += self.velocity * dt
        self.wrap_around_screen()

    def split(self):
        self.kill()
        if self.radius <= ASTEROID_MIN_RADIUS:
            return
        log_event("asteroid_split")
        angle = random.uniform(20, 50)
        velocity1 = self.velocity.rotate(angle)
        velocity2 = self.velocity.rotate(angle * -1)
        radius = self.radius - ASTEROID_MIN_RADIUS
        asteroid1 = Asteroid(self.position[0], self.position[1], radius)
        asteroid2 = Asteroid(self.position[0], self.position[1], radius)
        asteroid1.velocity = velocity1 * 1.2
        asteroid2.velocity = velocity2 * 1.2

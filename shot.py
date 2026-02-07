import pygame
from circleshape import CircleShape
from constants import SHOT_RADIUS, SHOT_LIFETIME_SECONDS


class Shot(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, SHOT_RADIUS)
        self.life_remaining = SHOT_LIFETIME_SECONDS

    def draw(self, screen):
        pygame.draw.circle(screen, "white", self.position, SHOT_RADIUS)

    def update(self, dt):
        self.life_remaining -= dt
        if self.life_remaining <= 0:
            self.kill()
            return
        self.position += self.velocity * dt
        self.wrap_around_screen()

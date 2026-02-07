import pygame
import random
import math
from circleshape import CircleShape
from constants import (
    ASTEROID_MIN_RADIUS,
    LINE_WIDTH,
)
from logger import log_event


class Asteroid(CircleShape):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius)
        self.points = []
        self.__shape_offsets = []
        self.__num_vertices = 24
        self.__jaggedness = 0.35
        self.__smoothness = 2

        angles = []
        step = (2 * math.pi) / self.__num_vertices
        for i in range(self.__num_vertices):
            a = i * step + random.uniform(-step * 0.25, step * 0.25)
            angles.append(a)
        angles.sort()

        radii = []
        for _ in range(self.__num_vertices):
            r = self.radius * \
                random.uniform(1.0 - self.__jaggedness,
                               1.0 + self.__jaggedness)
            radii.append(r)

        for _ in range(self.__smoothness):
            new_radii = radii[:]
            for i in range(self.__num_vertices):
                prev_i = (i - 1) % self.__num_vertices
                next_i = (i + 1) % self.__num_vertices
                new_radii[i] = (radii[prev_i] + radii[i] + radii[next_i]) / 3.0
            radii = new_radii

        for a, r in zip(angles, radii):
            x = math.cos(a) * r
            y = math.sin(a) * r
            self.__shape_offsets.append(pygame.Vector2(x, y))
        self.__refresh_points()

    def __refresh_points(self):
        self.points = [self.position + p for p in self.__shape_offsets]

    def draw(self, screen):
        pygame.draw.polygon(screen, "white", self.points, LINE_WIDTH)

    def update(self, dt):
        self.position += self.velocity * dt
        self.wrap_around_screen()
        self.__refresh_points()

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

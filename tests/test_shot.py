import pygame

from game.config.constants import SCREEN_WIDTH, SHOT_RADIUS, SHOT_LIFETIME_SECONDS
from game.entities.shot import Shot


def test_shot_expires_after_lifetime():
    shot = Shot(100, 100)
    group = pygame.sprite.Group(shot)

    shot.update(SHOT_LIFETIME_SECONDS + 0.01)

    assert shot not in group


def test_shot_wraps_on_horizontal_overflow():
    shot = Shot(0, 0)
    shot.position.x = SCREEN_WIDTH + SHOT_RADIUS + 1

    shot.update(0.0)

    assert shot.position.x == -SHOT_RADIUS


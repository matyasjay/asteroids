import pygame
import pytest

import game.entities.asteroid as asteroid_module
from game.config.constants import ASTEROID_MIN_RADIUS
from game.entities.asteroid import Asteroid


@pytest.fixture(autouse=True)
def asteroid_test_setup(monkeypatch):
    monkeypatch.setattr(
        asteroid_module,
        "build_asteroid_texture",
        lambda radius, seed=None: (pygame.Surface((2, 2), pygame.SRCALPHA), pygame.Vector2(0, 0)),
    )
    monkeypatch.setattr(asteroid_module, "log_event", lambda *args, **kwargs: None)
    Asteroid.containers = tuple()


def test_split_min_radius_only_kills_original():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    asteroid = Asteroid(200, 180, ASTEROID_MIN_RADIUS)

    asteroid.split()

    assert len(group) == 0


def test_split_spawns_two_smaller_asteroids():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    asteroid = Asteroid(200, 180, ASTEROID_MIN_RADIUS * 3)
    asteroid.velocity = pygame.Vector2(50, 0)

    asteroid.split()

    assert len(group) == 2
    radii = sorted([sprite.radius for sprite in group])
    assert radii == [ASTEROID_MIN_RADIUS * 2, ASTEROID_MIN_RADIUS * 2]
    for sprite in group:
        assert sprite.velocity.length() == pytest.approx(60.0, abs=1e-6)


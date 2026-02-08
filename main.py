import sys
import pygame
from constants import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    BACKGROUND_IMAGE_PATH,
    BACKGROUND_OPACITY,
)
from logger import log_state, log_event
from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot


def load_background():
    opacity = max(0, min(255, BACKGROUND_OPACITY))
    try:
        image = pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
    except Exception as err:
        print(f"Warning: failed to load background image '{BACKGROUND_IMAGE_PATH}': {err}")
        return None

    image_width, image_height = image.get_size()
    scale = max(SCREEN_WIDTH / image_width, SCREEN_HEIGHT / image_height)
    scaled_size = (
        max(1, int(image_width * scale)),
        max(1, int(image_height * scale)),
    )
    scaled = pygame.transform.smoothscale(image, scaled_size)

    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    offset_x = (scaled_size[0] - SCREEN_WIDTH) // 2
    offset_y = (scaled_size[1] - SCREEN_HEIGHT) // 2
    background.blit(scaled, (-offset_x, -offset_y))
    background.set_alpha(opacity)
    return background


def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}\nScreen height: {SCREEN_HEIGHT}")
    pygame.init()
    clock = pygame.time.Clock()

    x = SCREEN_WIDTH / 2
    y = SCREEN_HEIGHT / 2
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    background = load_background()

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable)
    Shot.containers = (shots, drawable, updatable)

    player = Player(x, y)
    AsteroidField()
    dt = 0

    while True:
        log_state()
        screen.fill("black")
        if background:
            screen.blit(background, (0, 0))
        updatable.update(dt)
        for asteroid in asteroids:
            if asteroid.collides_with(player):
                log_event("player_hit")
                print("Game over!")
                sys.exit()
            for shot in shots:
                if shot.collides_with(asteroid):
                    log_event("asteroid_shot")
                    asteroid.split()
                    shot.kill()
        for item in drawable:
            item.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            pass
        pygame.display.flip()
        dt = clock.tick(60) / 1000  # ms


if __name__ == "__main__":
    main()

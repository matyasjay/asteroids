import pygame
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from logger import log_state
from player import Player


def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}\nScreen height: {SCREEN_HEIGHT}")
    pygame.init()
    clock = pygame.time.Clock()

    x = SCREEN_WIDTH / 2
    y = SCREEN_HEIGHT / 2
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()

    Player.containers = (updatable, drawable)

    Player(x, y)
    dt = 0

    while True:
        log_state()
        screen.fill("black")
        updatable.update(dt)
        for item in updatable:
            item.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            pass
        pygame.display.flip()
        dt = clock.tick(60) / 1000  # ms


if __name__ == "__main__":
    main()

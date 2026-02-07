import pygame
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from logger import log_state


def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}\nScreen height: {SCREEN_HEIGHT}")
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    while True:
        log_state()
        screen.fill("black")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            pass
        pygame.display.flip()


if __name__ == "__main__":
    main()

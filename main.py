import pygame
from game.config.constants import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    BACKGROUND_IMAGE_PATH,
    BACKGROUND_OPACITY,
    MENU_BACKGROUND_IMAGE_PATH,
    MENU_BACKGROUND_OPACITY,
    GAME_OVER_BACKGROUND_IMAGE_PATH,
    GAME_OVER_BACKGROUND_OPACITY,
)
from game.utils.logger import log_state, log_event
from game.entities.player import Player
from game.entities.asteroid import Asteroid
from game.systems.asteroidfield import AsteroidField
from game.entities.shot import Shot

MENU_OPTIONS = ("New Game", "Quit")
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
MENU_HOVER_SCALE = 1.06


def _menu_option_key(option):
    return option.lower().replace(" ", "-")


def load_background(image_path, opacity):
    opacity = max(0, min(255, opacity))
    try:
        image = pygame.image.load(image_path).convert()
    except Exception as err:
        print(f"Warning: failed to load background image '{image_path}': {err}")
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


def load_menu_option_images(option_font):
    images = {}
    for option in MENU_OPTIONS:
        text_width, text_height = option_font.render(option, True, "white").get_size()
        target_height = max(1, text_height)

        option_images = {}
        for state in ("default", "hover"):
            image_path = f"images/{_menu_option_key(option)}-{state}.png"
            try:
                image = pygame.image.load(image_path).convert_alpha()
            except Exception as err:
                print(f"Warning: failed to load menu option image '{image_path}': {err}")
                option_images[state] = None
                continue

            scale = target_height / max(1, image.get_height())
            scaled_size = (
                max(1, int(round(image.get_width() * scale))),
                target_height,
            )
            option_images[state] = pygame.transform.smoothscale(image, scaled_size)

        images[option] = option_images
    return images


def create_game_session():
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable)
    Shot.containers = (shots, drawable, updatable)

    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    AsteroidField()

    return {
        "updatable": updatable,
        "drawable": drawable,
        "asteroids": asteroids,
        "shots": shots,
        "player": player,
    }


def draw_menu(screen, background, option_font, selected_option, option_images):
    screen.fill("black")
    if background:
        screen.blit(background, (0, 0))

    base_y = SCREEN_HEIGHT * 0.7
    spacing = 56
    for idx, option in enumerate(MENU_OPTIONS):
        state = "hover" if idx == selected_option else "default"
        image = option_images.get(option, {}).get(state)

        if image:
            if idx == selected_option:
                scaled_size = (
                    max(1, int(round(image.get_width() * MENU_HOVER_SCALE))),
                    max(1, int(round(image.get_height() * MENU_HOVER_SCALE))),
                )
                image = pygame.transform.smoothscale(image, scaled_size)
            image_rect = image.get_rect(center=(SCREEN_WIDTH / 2, base_y + idx * spacing))
            screen.blit(image, image_rect)
        else:
            color = "white" if idx == selected_option else (170, 170, 170)
            label = option_font.render(f"{option}", True, color)
            label_rect = label.get_rect(center=(SCREEN_WIDTH / 2, base_y + idx * spacing))
            screen.blit(label, label_rect)


def draw_game(screen, background, drawable):
    screen.fill("black")
    if background:
        screen.blit(background, (0, 0))
    for item in drawable:
        item.draw(screen)


def draw_game_over(screen, game_over_background, drawable, title_font, option_font):
    screen.fill("black")
    if game_over_background:
        screen.blit(game_over_background, (0, 0))
    else:
        draw_game(screen, None, drawable)


def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}\nScreen height: {SCREEN_HEIGHT}")
    pygame.init()
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Asteroids")
    background = load_background(BACKGROUND_IMAGE_PATH, BACKGROUND_OPACITY)
    menu_background = load_background(
        MENU_BACKGROUND_IMAGE_PATH,
        MENU_BACKGROUND_OPACITY,
    )
    game_over_background = load_background(
        GAME_OVER_BACKGROUND_IMAGE_PATH,
        GAME_OVER_BACKGROUND_OPACITY,
    )
    title_font = pygame.font.SysFont(None, 96)
    option_font = pygame.font.SysFont(None, 50)
    menu_option_images = load_menu_option_images(option_font)

    state = STATE_MENU
    selected_option = 0
    session = None
    dt = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if state == STATE_MENU and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_w, pygame.K_UP):
                    selected_option = (selected_option - 1) % len(MENU_OPTIONS)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    selected_option = (selected_option + 1) % len(MENU_OPTIONS)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_label = MENU_OPTIONS[selected_option]
                    if selected_label == "New Game":
                        session = create_game_session()
                        state = STATE_PLAYING
                    else:
                        return

            if state == STATE_GAME_OVER and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN,):
                    for group_key in ("updatable", "drawable", "asteroids", "shots"):
                        session[group_key].empty()
                    session = None
                    selected_option = 0
                    state = STATE_MENU

        if state == STATE_MENU:
            draw_menu(
                screen,
                menu_background,
                option_font,
                selected_option,
                menu_option_images,
            )
        elif state == STATE_PLAYING:
            updatable = session["updatable"]
            drawable = session["drawable"]
            asteroids = session["asteroids"]
            shots = session["shots"]
            player = session["player"]

            log_state()
            updatable.update(dt)

            player_hit = False
            for asteroid in asteroids:
                if asteroid.collides_with(player):
                    log_event("player_hit")
                    player_hit = True
                    break
                for shot in shots:
                    if shot.collides_with(asteroid):
                        log_event("asteroid_shot")
                        asteroid.split()
                        shot.kill()
                        break

            if player_hit:
                state = STATE_GAME_OVER
                draw_game_over(
                    screen,
                    game_over_background,
                    drawable,
                    title_font,
                    option_font,
                )
            else:
                draw_game(screen, background, drawable)
        else:
            draw_game_over(
                screen,
                game_over_background,
                session["drawable"],
                title_font,
                option_font,
            )

        pygame.display.flip()
        dt = clock.tick(60) / 1000  # ms


if __name__ == "__main__":
    main()

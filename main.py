import pygame
from game.config.constants import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    PLAYER_MAX_HEALTH,
    PLAYER_INVULNERABLE_DURATION_SECONDS,
)
from game.utils.logger import log_state, log_event
from game.entities.player import Player
from game.entities.asteroid import Asteroid
from game.systems.asteroidfield import AsteroidField
from game.entities.shot import Shot
from game.entities.explosion import Explosion
from game.render import GameRenderer

MENU_OPTIONS = ("New Game", "Quit")
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"


def create_game_session():
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable)
    Shot.containers = (shots, drawable, updatable)
    Explosion.containers = (explosions, drawable, updatable)

    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    AsteroidField()

    return {
        "updatable": updatable,
        "drawable": drawable,
        "asteroids": asteroids,
        "shots": shots,
        "explosions": explosions,
        "player": player,
        "health": PLAYER_MAX_HEALTH,
        "max_health": PLAYER_MAX_HEALTH,
        "invuln_remaining": 0.0,
    }


def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}\nScreen height: {SCREEN_HEIGHT}")
    pygame.init()
    clock = pygame.time.Clock()
    renderer = GameRenderer(menu_options=MENU_OPTIONS)

    state = STATE_MENU
    selected_option = 0
    session = None
    dt = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                renderer.toggle_fullscreen()
                continue

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
                    for group_key in (
                        "updatable",
                        "drawable",
                        "asteroids",
                        "shots",
                        "explosions",
                    ):
                        session[group_key].empty()
                    session = None
                    selected_option = 0
                    state = STATE_MENU

        if state == STATE_MENU:
            renderer.render_menu(selected_option)
        elif state == STATE_PLAYING:
            updatable = session["updatable"]
            drawable = session["drawable"]
            asteroids = session["asteroids"]
            shots = session["shots"]
            player = session["player"]
            session["invuln_remaining"] = max(0.0, session["invuln_remaining"] - dt)
            player.set_invulnerable(session["invuln_remaining"] > 0.0)

            log_state()
            updatable.update(dt)

            player_dead = False
            if session["invuln_remaining"] <= 0.0:
                for asteroid in asteroids:
                    if asteroid.collides_with(player):
                        session["health"] -= 1
                        log_event("player_hit", remaining_health=session["health"])
                        if session["health"] <= 0:
                            player_dead = True
                        else:
                            session["invuln_remaining"] = PLAYER_INVULNERABLE_DURATION_SECONDS
                            player.set_invulnerable(True)
                        break

            for asteroid in asteroids:
                for shot in shots:
                    if shot.collides_with(asteroid):
                        log_event("asteroid_shot")
                        Explosion(asteroid.position.x, asteroid.position.y, asteroid.radius)
                        asteroid.split()
                        shot.kill()
                        break

            if player_dead:
                state = STATE_GAME_OVER
                renderer.render_game_over(drawable)
            else:
                renderer.render_game(
                    drawable,
                    session["health"],
                    session["max_health"],
                )
        else:
            renderer.render_game_over(session["drawable"])

        renderer.present()
        dt = clock.tick(60) / 1000  # ms


if __name__ == "__main__":
    main()

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
    GAME_BORDER_IMAGE_PATH,
    GAME_BORDER_OVERFLOW_PX,
    GAME_VIEW_PADDING_X,
    GAME_VIEW_PADDING_Y,
)

MENU_HOVER_SCALE = 1.06
MENU_HINT_TEXT = "F11: Toggle Fullscreen"


class GameRenderer:
    def __init__(self, menu_options):
        self.menu_options = tuple(menu_options)
        self.fullscreen = True
        self.display_surface = self._create_display(self.fullscreen)
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
        pygame.display.set_caption("Asteroids")

        self.title_font = pygame.font.SysFont(None, 96)
        self.option_font = pygame.font.SysFont(None, 50)
        self.hud_font = pygame.font.SysFont(None, 34)
        self.hint_font = pygame.font.SysFont(None, 28)

        self.background = self._load_background(BACKGROUND_IMAGE_PATH, BACKGROUND_OPACITY)
        self.menu_background = self._load_background(
            MENU_BACKGROUND_IMAGE_PATH,
            MENU_BACKGROUND_OPACITY,
        )
        self.game_over_background = self._load_background(
            GAME_OVER_BACKGROUND_IMAGE_PATH,
            GAME_OVER_BACKGROUND_OPACITY,
        )
        self.game_border, self.game_border_overflow = self._load_game_border(
            GAME_BORDER_IMAGE_PATH,
            GAME_BORDER_OVERFLOW_PX,
        )
        self.menu_option_images = self._load_menu_option_images()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.display_surface = self._create_display(self.fullscreen)

    def render_menu(self, selected_option):
        screen = self.game_surface
        screen.fill("black")
        if self.menu_background:
            screen.blit(self.menu_background, (0, 0))

        base_y = SCREEN_HEIGHT * 0.7
        spacing = 56
        for idx, option in enumerate(self.menu_options):
            state = "hover" if idx == selected_option else "default"
            image = self.menu_option_images.get(option, {}).get(state)

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
                label = self.option_font.render(option, True, color)
                label_rect = label.get_rect(center=(SCREEN_WIDTH / 2, base_y + idx * spacing))
                screen.blit(label, label_rect)

        hint = self.hint_font.render(MENU_HINT_TEXT, True, (140, 140, 140))
        hint_rect = hint.get_rect(midbottom=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 70))
        screen.blit(hint, hint_rect)

    def render_game(self, drawable, health, max_health):
        screen = self.game_surface
        screen.fill("black")
        if self.background:
            screen.blit(self.background, (0, 0))
        for item in drawable:
            item.draw(screen)
        self._draw_health_ui(health, max_health)

    def render_game_over(self, drawable):
        screen = self.game_surface
        screen.fill("black")
        if self.game_over_background:
            screen.blit(self.game_over_background, (0, 0))
            return

        # Fallback to the current game frame if game-over background is missing.
        if self.background:
            screen.blit(self.background, (0, 0))
        for item in drawable:
            item.draw(screen)

    def present(self):
        self.display_surface.fill("black")
        display_width, display_height = self.display_surface.get_size()
        frame_width, frame_height = self.get_frame_size()
        frame_left = max(0, (display_width - frame_width) // 2)
        frame_top = max(0, (display_height - frame_height) // 2)

        if self.game_border is not None:
            self.display_surface.blit(
                self.game_border,
                (
                    frame_left - self.game_border_overflow,
                    frame_top - self.game_border_overflow,
                ),
            )

        game_left = frame_left + GAME_VIEW_PADDING_X
        game_top = frame_top + GAME_VIEW_PADDING_Y
        self.display_surface.blit(self.game_surface, (game_left, game_top))
        pygame.display.flip()

    @staticmethod
    def get_frame_size():
        return (
            SCREEN_WIDTH + (GAME_VIEW_PADDING_X * 2),
            SCREEN_HEIGHT + (GAME_VIEW_PADDING_Y * 2),
        )

    @staticmethod
    def _menu_option_key(option):
        return option.lower().replace(" ", "-")

    @staticmethod
    def _load_background(image_path, opacity):
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

    def _load_menu_option_images(self):
        images = {}
        for option in self.menu_options:
            _, text_height = self.option_font.render(option, True, "white").get_size()
            target_height = max(1, text_height)

            option_images = {}
            for state in ("default", "hover"):
                image_path = f"images/{self._menu_option_key(option)}-{state}.png"
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

    def _load_game_border(self, image_path, overflow_px):
        try:
            border = pygame.image.load(image_path).convert_alpha()
        except Exception as err:
            print(f"Warning: failed to load game border image '{image_path}': {err}")
            return None, 0

        frame_width, frame_height = self.get_frame_size()
        target_size = (
            frame_width + (overflow_px * 2),
            frame_height + (overflow_px * 2),
        )
        border = pygame.transform.scale(border, target_size)
        return border, overflow_px

    @classmethod
    def _create_display(cls, fullscreen):
        frame_width, frame_height = cls.get_frame_size()
        if fullscreen:
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        return pygame.display.set_mode((frame_width, frame_height))

    def _draw_health_ui(self, health, max_health):
        margin = 20
        label = self.hud_font.render(f"Hull {health}/{max_health}", True, (235, 235, 235))
        label_rect = label.get_rect(topright=(SCREEN_WIDTH - margin, margin))
        self.game_surface.blit(label, label_rect)

        pip_radius = 7
        pip_spacing = 9
        total_width = (pip_radius * 2 * max_health) + (pip_spacing * max(0, max_health - 1))
        start_x = SCREEN_WIDTH - margin - total_width
        y = label_rect.bottom + 8
        for idx in range(max_health):
            x = start_x + pip_radius + idx * ((pip_radius * 2) + pip_spacing)
            color = (95, 220, 140) if idx < health else (70, 70, 70)
            pygame.draw.circle(self.game_surface, color, (x, y + pip_radius), pip_radius)
            pygame.draw.circle(self.game_surface, (225, 225, 225), (x, y + pip_radius), pip_radius, 1)

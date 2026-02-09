import pygame
from game.config.constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GAME_VIEW_PADDING_X,
    GAME_VIEW_PADDING_Y,
    GAME_BORDER_IMAGE_PATH,
    GAME_BORDER_OVERFLOW_PX,
    LOADING_IMAGE_PATH,
    LOADING_IMAGE_OPACITY,
    LOADING_MIN_DURATION_SECONDS,
)


class StartupScreen:
    def __init__(
        self,
        image_path=LOADING_IMAGE_PATH,
        image_opacity=LOADING_IMAGE_OPACITY,
        min_duration_seconds=LOADING_MIN_DURATION_SECONDS,
        border_path=GAME_BORDER_IMAGE_PATH,
        border_overflow_px=GAME_BORDER_OVERFLOW_PX,
    ):
        self.image_path = image_path
        self.image_opacity = max(0, min(255, image_opacity))
        self.min_duration_seconds = max(0.0, min_duration_seconds)
        self.border_path = border_path
        self.border_overflow_px = max(0, int(border_overflow_px))

        self._start_ms = None
        self._source = None
        self._load_attempted = False
        self._scaled_cache = {}
        self._border = None
        self._border_load_attempted = False

    def start(self):
        self._start_ms = pygame.time.get_ticks()

    def render_step(self, display_surface):
        if not self._consume_events():
            return False

        display_surface.fill((0, 0, 0))
        game_rect, frame_left, frame_top = self._layout(display_surface.get_size())

        background = self._scaled_background((game_rect.width, game_rect.height))
        if background is not None:
            display_surface.blit(background, game_rect.topleft)

        self._draw_border(display_surface, frame_left, frame_top)
        pygame.display.flip()
        return True

    def hold_until_min_duration(self, display_surface, clock):
        if self._start_ms is None:
            self.start()
        elapsed_seconds = (pygame.time.get_ticks() - self._start_ms) / 1000.0
        remaining = max(0.0, self.min_duration_seconds - elapsed_seconds)
        while remaining > 0.0:
            if not self.render_step(display_surface):
                return False
            remaining -= clock.tick(60) / 1000.0
        return True

    @staticmethod
    def _consume_events():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def _scaled_background(self, target_size):
        if target_size in self._scaled_cache:
            return self._scaled_cache[target_size]

        if not self._load_attempted:
            self._load_attempted = True
            try:
                self._source = pygame.image.load(self.image_path).convert()
            except Exception as err:
                print(f"Warning: failed to load startup image '{self.image_path}': {err}")
                self._source = None

        image = self._source
        if image is None:
            self._scaled_cache[target_size] = None
            return None

        target_width, target_height = target_size
        src_width, src_height = image.get_size()
        scale = max(target_width / src_width, target_height / src_height)
        scaled_size = (
            max(1, int(src_width * scale)),
            max(1, int(src_height * scale)),
        )
        scaled = pygame.transform.smoothscale(image, scaled_size)

        background = pygame.Surface((target_width, target_height)).convert()
        offset_x = (scaled_size[0] - target_width) // 2
        offset_y = (scaled_size[1] - target_height) // 2
        background.blit(scaled, (-offset_x, -offset_y))
        background.set_alpha(self.image_opacity)
        self._scaled_cache[target_size] = background
        return background

    @staticmethod
    def _layout(display_size):
        display_width, display_height = display_size
        frame_width = SCREEN_WIDTH + (GAME_VIEW_PADDING_X * 2)
        frame_height = SCREEN_HEIGHT + (GAME_VIEW_PADDING_Y * 2)
        frame_left = max(0, (display_width - frame_width) // 2)
        frame_top = max(0, (display_height - frame_height) // 2)
        game_rect = pygame.Rect(
            frame_left + GAME_VIEW_PADDING_X,
            frame_top + GAME_VIEW_PADDING_Y,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )
        return game_rect, frame_left, frame_top

    def _draw_border(self, display_surface, frame_left, frame_top):
        border = self._load_border()
        if border is None:
            return
        display_surface.blit(
            border,
            (
                frame_left - self.border_overflow_px,
                frame_top - self.border_overflow_px,
            ),
        )

    def _load_border(self):
        if self._border_load_attempted:
            return self._border

        self._border_load_attempted = True
        try:
            border = pygame.image.load(self.border_path).convert_alpha()
        except Exception as err:
            print(f"Warning: failed to load startup border '{self.border_path}': {err}")
            self._border = None
            return self._border

        frame_width = SCREEN_WIDTH + (GAME_VIEW_PADDING_X * 2)
        frame_height = SCREEN_HEIGHT + (GAME_VIEW_PADDING_Y * 2)
        target_size = (
            frame_width + (self.border_overflow_px * 2),
            frame_height + (self.border_overflow_px * 2),
        )
        self._border = pygame.transform.smoothscale(border, target_size)
        return self._border

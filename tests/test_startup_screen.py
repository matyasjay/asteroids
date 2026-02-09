import pygame

from game.config.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from game.render.startup import StartupScreen


def test_layout_uses_fixed_game_viewport_size():
    game_rect, frame_left, frame_top = StartupScreen._layout((1920, 1080))

    assert game_rect.width == SCREEN_WIDTH
    assert game_rect.height == SCREEN_HEIGHT
    assert frame_left >= 0
    assert frame_top >= 0


def test_render_step_falls_back_to_black_when_image_missing():
    surface = pygame.display.set_mode((800, 600))
    startup = StartupScreen(
        image_path="/tmp/does-not-exist-loading.png",
        border_path="/tmp/does-not-exist-border.png",
    )

    assert startup.render_step(surface)


def test_hold_until_min_duration_waits_and_repaints(monkeypatch):
    surface = pygame.display.set_mode((800, 600))
    startup = StartupScreen(min_duration_seconds=0.1)

    calls = {"render": 0, "ticks": 0}

    def fake_render_step(_surface):
        calls["render"] += 1
        return True

    class FakeClock:
        def tick(self, _fps):
            calls["ticks"] += 1
            return 20  # ms

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    monkeypatch.setattr(startup, "render_step", fake_render_step)
    startup.start()

    assert startup.hold_until_min_duration(surface, FakeClock())
    assert calls["render"] > 0
    assert calls["ticks"] > 0


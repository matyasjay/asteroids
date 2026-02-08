import math
import random
import pygame
from game.config.constants import (
    EXPLOSION_GIF_PATH,
    EXPLOSION_FPS,
    EXPLOSION_SCALE_TO_RADIUS,
    EXPLOSION_FALLBACK_DURATION_SECONDS,
)


class Explosion(pygame.sprite.Sprite):
    _base_gif_frames = None
    _gif_load_attempted = False
    _scaled_frame_cache = {}

    def __init__(self, x, y, radius):
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()

        self.position = pygame.Vector2(x, y)
        self.radius = radius
        self.elapsed = 0.0
        self._spark_data = self._build_sparks()

        frames = self._get_scaled_gif_frames(radius)
        if frames:
            self.frames = frames
            self.duration = len(frames) / max(1, EXPLOSION_FPS)
        else:
            self.frames = None
            self.duration = EXPLOSION_FALLBACK_DURATION_SECONDS

    @classmethod
    def _load_gif_frames(cls):
        if cls._gif_load_attempted:
            return cls._base_gif_frames

        cls._gif_load_attempted = True
        cls._base_gif_frames = []
        try:
            from PIL import Image, ImageSequence

            image = Image.open(EXPLOSION_GIF_PATH)
            for frame in ImageSequence.Iterator(image):
                rgba = frame.convert("RGBA")
                width, height = rgba.size
                data = rgba.tobytes()
                surface = pygame.image.fromstring(data, (width, height), "RGBA").convert_alpha()
                cls._base_gif_frames.append(surface)
        except Exception as err:
            print(
                f"Warning: explosion GIF not available at '{EXPLOSION_GIF_PATH}' "
                f"(or Pillow missing): {err}"
            )
            cls._base_gif_frames = []

        return cls._base_gif_frames

    @classmethod
    def _get_scaled_gif_frames(cls, radius):
        base_frames = cls._load_gif_frames()
        if not base_frames:
            return None

        target_longest = max(2, int(round(radius * EXPLOSION_SCALE_TO_RADIUS)))
        if target_longest in cls._scaled_frame_cache:
            return cls._scaled_frame_cache[target_longest]

        scaled_frames = []
        base_longest = max(base_frames[0].get_width(), base_frames[0].get_height())
        scale = target_longest / max(1, base_longest)
        for frame in base_frames:
            scaled_size = (
                max(1, int(round(frame.get_width() * scale))),
                max(1, int(round(frame.get_height() * scale))),
            )
            scaled_frames.append(pygame.transform.smoothscale(frame, scaled_size))

        cls._scaled_frame_cache[target_longest] = scaled_frames
        return scaled_frames

    def _build_sparks(self):
        sparks = []
        count = 16
        for _ in range(count):
            angle = random.uniform(0.0, math.pi * 2.0)
            speed = random.uniform(0.55, 1.15)
            seed = random.uniform(0.0, math.pi * 2.0)
            sparks.append((pygame.Vector2(math.cos(angle), math.sin(angle)), speed, seed))
        return sparks

    def draw(self, screen):
        if self.frames:
            frame_index = min(len(self.frames) - 1, int(self.elapsed * EXPLOSION_FPS))
            frame = self.frames[frame_index]
            rect = frame.get_rect(center=(self.position.x, self.position.y))
            screen.blit(frame, rect.topleft)
            return

        # Fallback: layered radial burst + sparks.
        t = min(1.0, self.elapsed / max(1e-6, self.duration))
        center = (int(self.position.x), int(self.position.y))
        outer_radius = int(self.radius * (0.6 + 1.9 * t))
        inner_radius = int(self.radius * max(0.0, 0.55 - 0.45 * t))
        ring_width = max(1, int(5 * (1.0 - t)))

        glow = pygame.Surface((outer_radius * 2 + 8, outer_radius * 2 + 8), pygame.SRCALPHA)
        glow_center = (glow.get_width() // 2, glow.get_height() // 2)
        ring_color = (255, int(210 - 110 * t), int(80 - 60 * t), int(210 * (1.0 - t)))
        core_color = (255, int(180 - 140 * t), int(70 - 65 * t), int(150 * (1.0 - t)))
        pygame.draw.circle(glow, ring_color, glow_center, outer_radius, ring_width)
        if inner_radius > 0:
            pygame.draw.circle(glow, core_color, glow_center, inner_radius)

        for direction, speed, seed in self._spark_data:
            jitter = math.sin((t * 18.0) + seed) * 0.15
            travel = self.radius * (0.35 + (1.5 * t * speed))
            start = self.position + direction * (self.radius * (0.18 + t * 0.4))
            end = start + direction.rotate(jitter * 35.0) * travel * 0.24
            spark_color = (255, int(200 - 120 * t), int(90 - 70 * t))
            pygame.draw.line(
                glow,
                spark_color,
                (
                    int(start.x - self.position.x + glow_center[0]),
                    int(start.y - self.position.y + glow_center[1]),
                ),
                (
                    int(end.x - self.position.x + glow_center[0]),
                    int(end.y - self.position.y + glow_center[1]),
                ),
                2,
            )

        screen.blit(glow, (center[0] - glow_center[0], center[1] - glow_center[1]))

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.kill()

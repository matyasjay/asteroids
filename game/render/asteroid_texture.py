import glob
import os
import random
import re
import pygame
from game.config.constants import (
    ASTEROID_MIN_RADIUS,
    ASTEROID_SPRITE_GLOB,
    ASTEROID_SPRITE_SCALE_TO_RADIUS,
)

_VARIANT_PATTERN = re.compile(r"asteroid-(lg|md|sm)-\d+\.png$", re.IGNORECASE)
_SPRITES_BY_SIZE = {"lg": [], "md": [], "sm": []}
_SCALED_CACHE = {}
_SPRITES_LOADED = False


def _size_key_for_radius(radius):
    if radius <= ASTEROID_MIN_RADIUS * 1.5:
        return "sm"
    if radius <= ASTEROID_MIN_RADIUS * 2.5:
        return "md"
    return "lg"


def _estimate_radius_from_offsets(shape_offsets):
    if not shape_offsets:
        return ASTEROID_MIN_RADIUS
    return max(point.length() for point in shape_offsets)


def _fallback_texture(radius):
    diameter = max(2, int(round(radius * 2)))
    surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    pygame.draw.circle(
        surface,
        (155, 155, 155, 255),
        (diameter // 2, diameter // 2),
        max(1, diameter // 2),
    )
    offset = pygame.Vector2(-(diameter / 2), -(diameter / 2))
    return surface, offset


def _ensure_sprites_loaded():
    global _SPRITES_LOADED
    if _SPRITES_LOADED:
        return

    for path in sorted(glob.glob(ASTEROID_SPRITE_GLOB)):
        name = os.path.basename(path)
        match = _VARIANT_PATTERN.match(name)
        if not match:
            continue

        size_key = match.group(1).lower()
        try:
            surface = pygame.image.load(path).convert_alpha()
        except Exception as err:
            print(f"Warning: failed to load asteroid sprite '{path}': {err}")
            continue

        visible_rect = surface.get_bounding_rect(min_alpha=1)
        if visible_rect.width == 0 or visible_rect.height == 0:
            continue

        _SPRITES_BY_SIZE[size_key].append(
            {
                "name": name,
                "surface": surface,
                "visible_longest": max(visible_rect.width, visible_rect.height),
            }
        )

    _SPRITES_LOADED = True


def _get_variants_for_size(size_key):
    if _SPRITES_BY_SIZE[size_key]:
        return _SPRITES_BY_SIZE[size_key]

    for fallback_key in ("md", "lg", "sm"):
        if _SPRITES_BY_SIZE[fallback_key]:
            return _SPRITES_BY_SIZE[fallback_key]
    return []


def _get_scaled_variant(variant, target_longest):
    cache_key = (variant["name"], target_longest)
    if cache_key in _SCALED_CACHE:
        return _SCALED_CACHE[cache_key]

    source = variant["surface"]
    scale = target_longest / max(1, variant["visible_longest"])
    scaled_size = (
        max(1, int(round(source.get_width() * scale))),
        max(1, int(round(source.get_height() * scale))),
    )
    scaled = pygame.transform.smoothscale(source, scaled_size)

    mask = pygame.mask.from_surface(scaled)
    centroid = mask.centroid() if mask.count() else None
    if centroid is None:
        center_x = scaled.get_width() / 2
        center_y = scaled.get_height() / 2
    else:
        center_x, center_y = centroid

    offset = pygame.Vector2(-center_x, -center_y)
    _SCALED_CACHE[cache_key] = (scaled, offset)
    return _SCALED_CACHE[cache_key]


def build_asteroid_texture(shape_offsets_or_radius, seed=None):
    _ensure_sprites_loaded()

    if isinstance(shape_offsets_or_radius, (int, float)):
        radius = float(shape_offsets_or_radius)
    else:
        radius = _estimate_radius_from_offsets(shape_offsets_or_radius)

    variants = _get_variants_for_size(_size_key_for_radius(radius))
    if not variants:
        return _fallback_texture(radius)

    rng = random.Random(seed)
    variant = rng.choice(variants)
    target_longest = max(2, int(round(radius * ASTEROID_SPRITE_SCALE_TO_RADIUS)))
    return _get_scaled_variant(variant, target_longest)

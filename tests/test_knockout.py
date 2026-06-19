"""Tests for the background knockout tool.

All fixtures are synthesized in-memory: a saturated filled circle on a solid
canvas. No network access and no real image files are required.
"""

import numpy as np
import pytest
from PIL import Image, ImageDraw

from knockout import knockout

SIZE = 64
CENTER = SIZE // 2


def _circle_on(canvas_color, fill_color):
    """Build a SIZE x SIZE RGB image: a filled circle on a solid canvas."""
    img = Image.new("RGB", (SIZE, SIZE), canvas_color)
    draw = ImageDraw.Draw(img)
    # Circle covers the middle; corners stay pure background.
    draw.ellipse([16, 16, SIZE - 16, SIZE - 16], fill=fill_color)
    return img


def test_light_background_removed_subject_kept():
    gold = (212, 175, 55)
    img = _circle_on((255, 255, 255), gold)

    out = knockout(img, bg="light")
    arr = np.asarray(out)

    assert out.mode == "RGBA"

    # All four corners are pure white background -> fully transparent.
    for y, x in [(0, 0), (0, SIZE - 1), (SIZE - 1, 0), (SIZE - 1, SIZE - 1)]:
        assert arr[y, x, 3] == 0, f"corner ({y},{x}) should be transparent"

    # Center is the gold subject -> fully opaque, color preserved.
    cr, cg, cb, ca = arr[CENTER, CENTER]
    assert ca == 255
    assert (int(cr), int(cg), int(cb)) == gold


def test_dark_background_removed_subject_kept():
    red = (220, 40, 40)
    img = _circle_on((0, 0, 0), red)

    out = knockout(img, bg="dark")
    arr = np.asarray(out)

    assert out.mode == "RGBA"

    for y, x in [(0, 0), (0, SIZE - 1), (SIZE - 1, 0), (SIZE - 1, SIZE - 1)]:
        assert arr[y, x, 3] == 0, f"corner ({y},{x}) should be transparent"

    cr, cg, cb, ca = arr[CENTER, CENTER]
    assert ca == 255
    assert (int(cr), int(cg), int(cb)) == red


def test_colored_pixels_survive_light_knockout():
    """A bright but saturated pixel must NOT be removed as 'background'."""
    bright_cyan = (0, 255, 255)  # high luminance, high chroma
    img = _circle_on((255, 255, 255), bright_cyan)

    arr = np.asarray(knockout(img, bg="light"))
    assert arr[CENTER, CENTER, 3] == 255


def test_invalid_bg_raises():
    img = _circle_on((255, 255, 255), (212, 175, 55))
    with pytest.raises(ValueError):
        knockout(img, bg="green")

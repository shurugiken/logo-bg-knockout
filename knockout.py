#!/usr/bin/env python3
"""Remove a solid (white or black) background from an image and output a transparent PNG.

Unlike a naive "make every white pixel transparent" approach, this tool keys on two
signals per pixel:

  * chroma     = max(r, g, b) - min(r, g, b)   -> how colorful the pixel is
  * luminance  = 0.299*r + 0.587*g + 0.114*b   -> how bright the pixel is

Only pixels that are BOTH near-neutral (low chroma) AND at the background extreme
(very bright for a light background, very dark for a dark background) are treated as
background. Colored edge pixels survive even when they are light or dark, which keeps
logos with white/black accents intact. A feather band gives anti-aliased edges a smooth
partial-alpha ramp instead of a hard, jagged cutout.
"""

import argparse
import os

import numpy as np
from PIL import Image

# Defaults derived from the two reference algorithms.
DEFAULTS = {
    "light": {
        "chroma_bg": 16,
        "lum_bg": 205,
        "chroma_feather": 34,
        "lum_feather": 175,
    },
    "dark": {
        "chroma_bg": 16,
        "lum_bg": 26,
        "chroma_feather": 26,
        "lum_feather": 58,
    },
}


def knockout(
    img,
    bg="light",
    chroma_bg=None,
    lum_bg=None,
    chroma_feather=None,
    lum_feather=None,
):
    """Knock out a solid background from ``img`` and return an RGBA ``PIL.Image``.

    Parameters
    ----------
    img : PIL.Image
        Source image (any mode; converted to RGB internally).
    bg : str
        ``"light"`` to remove a white/bright background, ``"dark"`` for black.
    chroma_bg, lum_bg, chroma_feather, lum_feather : int, optional
        Thresholds. When ``None`` the defaults for the chosen ``bg`` are used.

    Returns
    -------
    PIL.Image
        An RGBA image with background pixels at alpha 0 and a feathered edge ramp.
    """
    if bg not in DEFAULTS:
        raise ValueError(f"bg must be 'light' or 'dark', got {bg!r}")

    d = DEFAULTS[bg]
    chroma_bg = d["chroma_bg"] if chroma_bg is None else chroma_bg
    lum_bg = d["lum_bg"] if lum_bg is None else lum_bg
    chroma_feather = d["chroma_feather"] if chroma_feather is None else chroma_feather
    lum_feather = d["lum_feather"] if lum_feather is None else lum_feather

    rgb = np.asarray(img.convert("RGB"), dtype=np.float64)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    alpha = np.full(lum.shape, 255.0, dtype=np.float64)

    if bg == "light":
        # Solid background: bright AND near-neutral -> fully transparent.
        is_bg = (chroma < chroma_bg) & (lum > lum_bg)
        # Feather band: not background, still near-white and low chroma.
        feather = (~is_bg) & (chroma < chroma_feather) & (lum > lum_feather)
        lum_t = np.clip((lum - lum_feather) / (lum_bg - lum_feather), 0.0, 1.0)
        chroma_t = np.clip((chroma_feather - chroma) / chroma_feather, 0.0, 1.0)
    else:
        # Solid background: dark AND near-neutral -> fully transparent.
        is_bg = (chroma < chroma_bg) & (lum < lum_bg)
        feather = (~is_bg) & (chroma < chroma_feather) & (lum < lum_feather)
        lum_t = np.clip((lum_feather - lum) / (lum_feather - lum_bg), 0.0, 1.0)
        chroma_t = np.clip((chroma_feather - chroma) / chroma_feather, 0.0, 1.0)

    t = lum_t * chroma_t
    alpha[feather] = (1.0 - t[feather]) * 255.0
    alpha[is_bg] = 0.0

    out = np.dstack([rgb, alpha]).astype(np.uint8)
    return Image.fromarray(out, mode="RGBA")


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="knockout",
        description=(
            "Remove a solid white or black background from an image and write a "
            "transparent PNG, preserving anti-aliased colored edges."
        ),
    )
    parser.add_argument("src", help="path to the source image")
    parser.add_argument("dst", help="path to write the transparent PNG")
    parser.add_argument(
        "--bg",
        choices=["light", "dark"],
        default="light",
        help="background to remove (default: light)",
    )
    parser.add_argument(
        "--chroma-bg",
        type=int,
        default=None,
        help="max chroma for a pixel to count as solid background",
    )
    parser.add_argument(
        "--lum-bg",
        type=int,
        default=None,
        help="luminance cutoff for solid background (light: above; dark: below)",
    )
    parser.add_argument(
        "--chroma-feather",
        type=int,
        default=None,
        help="max chroma for a pixel to enter the feather band",
    )
    parser.add_argument(
        "--lum-feather",
        type=int,
        default=None,
        help="luminance start of the feather band",
    )
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)

    with Image.open(args.src) as src:
        result = knockout(
            src,
            bg=args.bg,
            chroma_bg=args.chroma_bg,
            lum_bg=args.lum_bg,
            chroma_feather=args.chroma_feather,
            lum_feather=args.lum_feather,
        )

    dst_dir = os.path.dirname(os.path.abspath(args.dst))
    os.makedirs(dst_dir, exist_ok=True)
    result.save(args.dst, "PNG")

    print(f"wrote {args.dst} ({result.width}x{result.height})")


if __name__ == "__main__":
    main()

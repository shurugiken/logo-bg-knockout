# logo-bg-knockout

A small Python CLI that removes a solid white or black background from an image and
writes a transparent PNG. It keeps anti-aliased colored edges intact instead of leaving
a jagged matte.

## Why not just "make white transparent"?

The naive approach picks a background color and zeroes the alpha of every pixel that
matches it (often with a tolerance). That has two problems:

1. **It eats real content.** A logo with white lettering, a white highlight, or a light
   pastel fill loses those pixels too, because they are also "white-ish."
2. **It leaves jagged edges.** Anti-aliased edges are a blend of the subject and the
   background. A hard color match either keeps them (leaving a white halo) or drops them
   (leaving a stair-stepped outline).

This tool keys on two signals per pixel instead of one:

- **chroma** = `max(r, g, b) - min(r, g, b)` — how colorful the pixel is.
- **luminance** = `0.299*r + 0.587*g + 0.114*b` — how bright the pixel is.

A pixel is treated as background only when it is **both** near-neutral (low chroma) **and**
at the background extreme (very bright for a light background, very dark for a dark one).
A saturated pixel survives even if it is bright or dark, so colored accents are preserved.

Between "definitely background" and "definitely subject" there is a **feather band**. Edge
pixels in that band get a partial alpha that ramps with both their luminance and their
chroma, so anti-aliased edges fade smoothly instead of cutting off hard.

## Install

```bash
pip install -r requirements.txt
```

Requires Python 3.9+, Pillow, and NumPy.

## Usage

Remove a white background:

```bash
python knockout.py logo.png logo_transparent.png
```

Remove a black background:

```bash
python knockout.py logo.png logo_transparent.png --bg dark
```

The tool prints the output path and dimensions when it finishes.

### Tuning

If the defaults clip a near-white highlight or leave a faint halo, adjust the thresholds:

```bash
python knockout.py logo.png out.png \
  --bg light \
  --chroma-bg 16 \
  --lum-bg 205 \
  --chroma-feather 34 \
  --lum-feather 175
```

| Flag | Meaning |
| --- | --- |
| `--chroma-bg` | Max chroma for a pixel to count as solid background. |
| `--lum-bg` | Luminance cutoff for solid background (light: above this; dark: below this). |
| `--chroma-feather` | Max chroma for a pixel to enter the feather band. |
| `--lum-feather` | Luminance where the feather band starts. |

Raise `--lum-feather` (light) to protect light content; widen the gap between `--lum-feather`
and `--lum-bg` for a softer edge ramp.

## Use it as a library

```python
from PIL import Image
from knockout import knockout

with Image.open("logo.png") as src:
    out = knockout(src, bg="light")
out.save("logo_transparent.png")
```

## Tests

```bash
pip install pytest
pytest
```

The tests synthesize images in memory and assert that background corners become fully
transparent while the colored subject stays opaque and keeps its color.

## License

MIT — see [LICENSE](LICENSE).

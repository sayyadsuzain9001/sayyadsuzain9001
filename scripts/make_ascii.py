"""One-off: turn a portrait photo into ASCII art for the profile card.

Usage: python scripts/make_ascii.py <photo.jpg> [cols rows]
Writes assets/ascii.txt (the photo itself is never committed).

How it works: the person is separated from the (black) background with a mask,
contrast is stretched using only the person's pixels, and a large-radius unsharp
mask adds local contrast so eyes, glasses and collar stand out from the skin.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

RAMP = " .,:;i1tfLCG08@"
CROP = (110, 20, 720, 740)  # head and shoulders in the source photo


def to_ascii(path, cols=84, rows=52, crop=CROP):
    im = Image.open(path).convert("L").crop(crop)
    mask = im.point(lambda v: 255 if v > 8 else 0).filter(ImageFilter.MinFilter(5))
    im = ImageOps.autocontrast(im, cutoff=1, mask=mask)
    im = im.filter(ImageFilter.UnsharpMask(radius=40, percent=220, threshold=0))
    im = im.filter(ImageFilter.UnsharpMask(radius=3, percent=120, threshold=0))
    a = np.asarray(im.resize((cols, rows), Image.LANCZOS)) / 255.0
    m = np.asarray(mask.resize((cols, rows), Image.BILINEAR)) / 255.0
    a = np.where(m > 0.5, 0.07 + 0.93 * np.clip(a, 0, 1) ** 0.9, 0)
    n = len(RAMP) - 1
    return ["".join(RAMP[int(v * n)] for v in row).rstrip() for row in a]


if __name__ == "__main__":
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 84
    rows = int(sys.argv[3]) if len(sys.argv) > 3 else 52
    out = Path(__file__).resolve().parent.parent / "assets" / "ascii.txt"
    out.write_text("\n".join(to_ascii(sys.argv[1], cols, rows)) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))

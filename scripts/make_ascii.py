"""One-off: turn a portrait photo into ASCII art for the profile card.

Usage: python scripts/make_ascii.py <photo.jpg> [cols rows]
Writes assets/ascii.txt (the photo itself is never committed).
"""
import sys
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter

RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

def to_ascii(path, cols, rows, crop=(60, 10, 770, 800)):
    im = Image.open(path).convert("L").crop(crop)
    im = ImageOps.equalize(im)
    im = im.filter(ImageFilter.UnsharpMask(radius=3, percent=150))
    im = im.resize((cols, rows), Image.LANCZOS)
    px = im.load()
    n = len(RAMP) - 1
    return ["".join(RAMP[int(px[x, y] / 255 * n)] for x in range(cols)).rstrip() for y in range(rows)]

if __name__ == "__main__":
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 44
    rows = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    out = Path(__file__).resolve().parent.parent / "assets" / "ascii.txt"
    out.write_text("\n".join(to_ascii(sys.argv[1], cols, rows)) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))

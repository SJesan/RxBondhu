"""Generate six fictional prescription images for the Screen-1 demo strip.

No patient data: every image is drawn locally from the lists below and is safe
to commit. Replace the PNGs in assets/demo/ with your own images later.
"""

import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "demo"

FONT = r"C:\Windows\Fonts\comic.ttf"
FONT_BOLD = r"C:\Windows\Fonts\comicbd.ttf"

# Demo 01/02: clean all-GREEN (every brand has a DGDA DAR No).
# Demo 03: YELLOW box-only identities to fix live on Screen 3.
# Demo 04: deliberate RED via the neutral "Not sure?" flag on Screen 2.
# Demo 05/06: off-list / mixed extra stress cases for judges.
SETS = [
    ["Tab Pantonix 20   1+0+0", "Cap Maxpro 20     1+0+0", "Tab Lysivin           1+1+1"],
    ["Tab Seclo 20       1+0+0", "Tab Losar 50       0+0+1", "Tab Zyrtec 10       1+0+0"],
    ["Tab Napa 500      1+0+1", "Cap Maxpro 20     1+0+0", "Tab Fexo 60         0+0+1"],
    ["Tab Pantonix 20   1+0+0", "Cap Maxpro 20     0+0+1", "Tab Lysivin           1+0+0"],
    ["Tab Amsocal Plus   1+0+0", "Tab Eltroxin         1+0+0", "Tab Panicel          0+0+1"],
    ["Syp Napa 100ml     5ml TDS", "Tab Alafree 120    0+0+1", "Tab Zinc 20         1+0+0"],
]


def make_one(index: int, lines: list[str]) -> None:
    rng = random.Random(index)
    w, h = 480, 640
    img = Image.new("RGB", (w, h), "#FFFEF9")
    draw = ImageDraw.Draw(img)

    # Slight paper texture.
    for _ in range(900):
        x, y = rng.randrange(w), rng.randrange(h)
        draw.point((x, y), fill=rng.choice(("#F5F1E6", "#FAF7ED", "#EFE9DA")))

    rx_font = ImageFont.truetype(FONT_BOLD, 58)
    head_font = ImageFont.truetype(FONT_BOLD, 20)
    body_font = ImageFont.truetype(FONT, 24)
    small_font = ImageFont.truetype(FONT, 15)

    draw.text((40, 26), "Rx", font=rx_font, fill="#1C4B33")
    draw.line((40, 96, w - 40, 96), fill="#6E8D7A", width=2)

    draw.text((40, 116), "DEMO ONLY  -  fictional data", font=head_font, fill="#2C6E4A")
    draw.text((40, 150), f"Case {index:02d}    Date: 23 Nov", font=small_font, fill="#4A6654")
    draw.line((40, 180, w - 40, 180), fill="#D5E7DA", width=2)

    for row, line in enumerate(lines):
        y = 215 + row * 78
        draw.text((44, y), f"{row + 1}.", font=body_font, fill="#1C4B33")
        draw.text((92, y), line, font=body_font, fill="#183D2A")
        draw.line((44, y + 42, w - 44, y + 42), fill="#E4EDE7", width=2)

    draw.text((40, h - 92), "Patient: Demo User (not real)", font=small_font, fill="#4A6654")

    # A tiny blur/rotation makes the cards feel like paper without being noisy.
    img = img.rotate(rng.uniform(-1.2, 1.2), expand=False, fillcolor="#FFFEF9")
    img = img.filter(ImageFilter.GaussianBlur(0.25))
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / f"demo_rx_{index:02d}.png", optimize=True)


def make_crop_example() -> None:
    """Small fictional example showing a tight box around medicine lines only."""
    source = OUT / "demo_rx_01.png"
    if not source.is_file():
        return
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    for offset in range(4):
        draw.rectangle((82 + offset, 202 + offset, 432 - offset, 390 - offset),
                       outline="#2E8B57", width=2)
    image.save(OUT / "crop_example.png", optimize=True)


if __name__ == "__main__":
    for number, prescription in enumerate(SETS, start=1):
        make_one(number, prescription)
    make_crop_example()
    print(f"Wrote {len(SETS)} images to {OUT}")

"""Dump the exact crops our CNN and line reader receive (local diagnostic only).

Output goes to results/crop_dump/ (gitignored). Nothing here is used by the app.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402
from rxbondhu import segmentation  # noqa: E402


def contact_sheet(paths: list[Path], target: Path, cols: int = 6, cell: int = 110) -> None:
    if not paths:
        return
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 18)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((cell - 8, cell - 8))
        x = (index % cols) * cell + 4
        y = (index // cols) * (cell + 18) + 4
        sheet.paste(image, (x, y))
        draw.text((x, y + cell - 4), path.stem[:16], fill="black")
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", default="results/rx")
    parser.add_argument("--out", default="results/crop_dump")
    args = parser.parse_args()

    image_dir = Path(args.images)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = []

    for path in sorted(image_dir.glob("*.jpg")) + sorted(image_dir.glob("*.png")):
        image = Image.open(path).convert("RGB")
        target = out_dir / path.stem
        target.mkdir(parents=True, exist_ok=True)
        words = segmentation.segment(image)
        lines = segmentation.segment_lines(image)
        word_paths, line_paths = [], []
        for index, item in enumerate(words):
            file = target / f"word_{index:02d}.png"
            item["image"].save(file)
            word_paths.append(file)
        for index, item in enumerate(lines):
            file = target / f"line_{index:02d}.png"
            item["image"].save(file)
            line_paths.append(file)
        contact_sheet(word_paths, target / "contact_words.png")
        contact_sheet(line_paths, target / "contact_lines.png")
        summary.append(
            f"{path.name}: words={len(words)} lines={len(lines)} "
            f"word_boxes={[w['box'] for w in words]}"
        )

    (out_dir / "dump_summary.txt").write_text("\n".join(summary), encoding="utf-8")
    print(f"Dumped crops for {len(summary)} images to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""External line-localization check on real handwritten prescriptions.

The public dataset "A Curated Bangladesh-Based Dataset of Handwritten" has
200 prescription photos and YOLO boxes around medicine lines (one class,
``medicine``). The boxes contain **positions, not medicine names**, so this
runner measures localization only — never brand-name accuracy.

Metric: a ground-truth medicine box is "found" when some detected line box
overlaps it with IoU >= 0.3. Precision is the share of detected lines that
overlap an annotated medicine box. Boxes returned by our segmenter are in
prepared pixels (narrow images are upscaled 2x), so they are rescaled before
comparison.

Example:
    .\\venv\\Scripts\\python.exe tools\\evaluate_localization.py --zip "path\\to\\dataset.zip"

Writes results/localization_test_log.csv and results/localization_summary.json.
No network calls and no model training.
"""

import argparse
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from rxbondhu import segmentation  # noqa: E402
from rxbondhu.preprocess import preprocess_variants  # noqa: E402

IOU_THRESHOLD = 0.3
# auto_crop in the "all" variant changes image dimensions, so GT coordinates
# would no longer align; it is reported separately in the handwritten runner.
VARIANTS = ("none", "shadow", "clahe", "deskew")


def iou(a, b) -> float:
    """Intersection over union of two (x, y, w, h) boxes."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def parse_yolo(raw: str, width: int, height: int) -> list[tuple[float, float, float, float]]:
    """Convert normalised YOLO boxes to (x, y, w, h) pixels."""
    boxes = []
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            _, cx, cy, bw, bh = parts[:5]
            cx, cy, bw, bh = map(float, (cx, cy, bw, bh))
        except ValueError:
            continue  # e.g. classes.txt content inside a label file
        boxes.append(((cx - bw / 2) * width, (cy - bh / 2) * height,
                      bw * width, bh * height))
    return boxes


def to_original(boxes, image: Image.Image) -> list[tuple[float, float, float, float]]:
    """Undo the upscale applied by segmentation._prepare()."""
    scale = 2 if image.width < segmentation.UPSCALE_BELOW_WIDTH else 1
    return [tuple(v / scale for v in box) for box in boxes]


def score_lines(image: Image.Image, gt: list, variant: str = "none") -> tuple[float, float]:
    """Return (recall, precision) for one image and one preprocessing variant."""
    if variant != "none":
        image = preprocess_variants(image)[variant]
    preds = to_original([d["box"] for d in segmentation.segment_lines(image)], image)
    if not preds or not gt:
        return 0.0, 0.0
    recall = sum(any(iou(g, p) >= IOU_THRESHOLD for p in preds) for g in gt) / len(gt)
    precision = sum(any(iou(p, g) >= IOU_THRESHOLD for g in gt) for p in preds) / len(preds)
    return recall, precision


def open_dataset(zip_path: Path):
    """Return (outer, inner, names) for the doubly-zipped public dataset."""
    outer = zipfile.ZipFile(zip_path)
    inner_bytes = io.BytesIO(outer.read(outer.namelist()[0]))
    inner = zipfile.ZipFile(inner_bytes)
    return outer, inner, inner.namelist()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", required=True, help="Path to the public dataset ZIP")
    ap.add_argument("--limit", type=int, default=0, help="Only first N images (0 = all)")
    ap.add_argument("--out", default="results/localization_test_log.csv")
    ap.add_argument("--summary", default="results/localization_summary.json")
    args = ap.parse_args()

    outer, inner, names = open_dataset(Path(args.zip))
    try:
        numbers = []
        for name in names:
            if (name.startswith("Dataset/images/")
                    and name.lower().endswith((".jpg", ".jpeg", ".png"))):
                numbers.append(int(Path(name).stem))
        numbers.sort()
        if args.limit:
            numbers = numbers[:args.limit]

        rows = []
        totals = {variant: [0.0, 0.0, 0] for variant in VARIANTS}
        gt_boxes = 0
        for n in numbers:
            entry = next(x for x in names if x.startswith(f"Dataset/images/{n}."))
            image = Image.open(io.BytesIO(inner.read(entry))).convert("RGB")
            label = inner.read(f"Dataset/labels/{n}.txt").decode("utf-8-sig")
            gt = parse_yolo(label, image.width, image.height)
            gt_boxes += len(gt)
            row = {"image": Path(entry).name, "gt_medicine_boxes": len(gt)}
            for variant in VARIANTS:
                recall, precision = score_lines(image, gt, variant)
                row[f"{variant}_recall"] = round(recall, 4)
                row[f"{variant}_precision"] = round(precision, 4)
                acc = totals[variant]
                acc[0] += recall
                acc[1] += precision
                acc[2] += 1
            rows.append(row)
    finally:
        inner.close()
        outer.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    count = len(rows)
    variants = {}
    for variant, (recall, precision, _) in totals.items():
        variants[variant] = {
            "mean_recall": round(recall / count, 4),
            "mean_precision": round(precision / count, 4),
        }
    summary = {
        "dataset": "A Curated Bangladesh-Based Dataset of Handwritten (public)",
        "images": count,
        "annotated_medicine_boxes": gt_boxes,
        "iou_threshold": IOU_THRESHOLD,
        "variants": variants,
        "note": ("Localization only: YOLO boxes mark medicine-line positions, "
                 "not brand names. This is NOT name accuracy. The 'all' variant "
                 "is omitted because auto_crop changes image dimensions."),
    }
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {out} and {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

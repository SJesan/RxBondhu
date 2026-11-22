"""Evaluate real handwritten prescriptions with three readers.

This runner uses the actual app pipeline. It never invents results: every
prediction comes from our CNN, the live Gemini models, or their fusion.

Answer key format (CSV, UTF-8):
    image,true_brands,true_dose
    rx01.jpg,Napa|Maxpro,1+0+1|BD

``true_brands`` and ``true_dose`` are pipe-separated and aligned by medicine
line. ``true_dose`` may be left blank.

Example:
    .\\venv\\Scripts\\python.exe tools\\evaluate_handwritten.py \
        --answers results/answer_key.csv --images results/rx \
        --out results/handwritten_test_log.csv
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from rxbondhu import pipeline, vlm  # noqa: E402
from rxbondhu.lexicon import normalise_name  # noqa: E402

LOG_COLUMNS = [
    "image", "true_brands", "cnn_preds", "vlm_preds", "combined_preds",
    "combined_badges", "cnn_correct", "cnn_total", "vlm_correct", "vlm_total",
    "combined_correct", "combined_total", "dose_correct", "dose_total",
    "unsafe_green", "wrong_combined", "caught_wrong", "overflagged_correct", "notes",
]


def norm(text: str) -> str:
    return normalise_name(text).lower()


def split_pipe(text: str) -> list[str]:
    return [part.strip() for part in (text or "").split("|") if part.strip()]


def resolve_image(value: str, images_dir: str | None) -> str:
    path = Path(value)
    if path.is_absolute() or path.exists():
        return str(path)
    if images_dir:
        candidate = Path(images_dir) / value
        if candidate.exists():
            return str(candidate)
    return str(path)


def run_one(path: str, preprocess: bool, skip_vlm: bool) -> dict:
    image = Image.open(path).convert("RGB")
    if preprocess:
        from rxbondhu.preprocess import enhance_for_segmentation
        image = enhance_for_segmentation(image)

    analysis = pipeline.analyse(image, full_image=image, skip_vlm=skip_vlm)
    # Line-level readings, matching the app's screen 2 exactly.
    cnn_preds = analysis.get("line_cnn_preds", [])
    vlm_preds = [line.get("medicine", "") for line in analysis.get("vlm_lines", [])]
    items = analysis["items"]
    combined = [(it.get("name") or "", it.get("colour", "RED"),
                 it.get("dose_text") or "") for it in items]

    return {
        "cnn_preds": cnn_preds,
        "vlm_preds": vlm_preds,
        "combined": combined,
        "vlm_error": analysis.get("vlm_error", ""),
        "word_count": analysis.get("word_count", 0),
        "line_count": analysis.get("line_count", 0),
    }


def evaluate_row(answer: dict, result: dict) -> dict:
    true_brands = split_pipe(answer.get("true_brands", ""))
    true_norms = {norm(b) for b in true_brands}
    true_doses = split_pipe(answer.get("true_dose", ""))

    cnn_norms = [norm(x) for x in result["cnn_preds"]]
    vlm_norms = [norm(x) for x in result["vlm_preds"]]
    combined_norms = [norm(name) for name, _, _ in result["combined"]]

    def hits(preds):
        return sum(1 for want in true_norms if want and want in preds)

    cnn_ok = hits(cnn_norms)
    vlm_ok = hits(vlm_norms)
    combined_ok = hits(combined_norms)

    dose_ok = 0
    dose_total = 0
    for i, want in enumerate(true_doses):
        if not want:
            continue
        dose_total += 1
        got = result["combined"][i][2] if i < len(result["combined"]) else ""
        if norm(want) == norm(got) or norm(want) in norm(got):
            dose_ok += 1

    unsafe_green = sum(
        1 for name, colour, _ in result["combined"]
        if name and colour == "GREEN" and norm(name) not in true_norms
    )
    wrong = [colour for name, colour, _ in result["combined"]
             if name and norm(name) not in true_norms]
    caught = sum(1 for colour in wrong if colour != "GREEN")
    overflagged = sum(
        1 for name, colour, _ in result["combined"]
        if name and norm(name) in true_norms and colour == "RED"
    )

    notes = []
    if result["vlm_error"]:
        notes.append(result["vlm_error"])
    if not true_norms:
        notes.append("NO ANSWER KEY - row ignored")
    return {
        "cnn_correct": cnn_ok, "cnn_total": len(true_norms),
        "vlm_correct": vlm_ok, "vlm_total": len(true_norms),
        "combined_correct": combined_ok, "combined_total": len(true_norms),
        "dose_correct": dose_ok, "dose_total": dose_total,
        "unsafe_green": unsafe_green, "wrong_combined": len(wrong),
        "caught_wrong": caught, "overflagged_correct": overflagged,
        "notes": " | ".join(notes),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--answers", required=True, help="CSV with image,true_brands,true_dose")
    ap.add_argument("--images", default="", help="Optional folder for bare filenames")
    ap.add_argument("--out", default="results/handwritten_test_log.csv")
    ap.add_argument("--summary", default="results/handwritten_evaluation_summary.json")
    ap.add_argument("--preprocess", action="store_true", help="Use experimental enhancement")
    ap.add_argument("--skip-vlm", action="store_true", help="Force CNN-only (no API calls)")
    ap.add_argument("--limit", type=int, default=0, help="Evaluate only first N rows (0 = all)")
    args = ap.parse_args()

    with open(args.answers, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = {"image", "true_brands"} - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Answer key missing columns: {sorted(missing)}")
        answers = list(reader)
    if args.limit:
        answers = answers[:args.limit]

    if not args.skip_vlm:
        ok, why = vlm.available()
        if not ok:
            print(f"WARNING: Gemini unavailable ({why}); continuing CNN-only.")

    rows = []
    totals = dict.fromkeys(LOG_COLUMNS[6:-1], 0)
    for answer in answers:
        path = resolve_image(answer["image"], args.images)
        if not os.path.exists(path):
            raise SystemExit(f"Image not found: {path}")
        result = run_one(path, args.preprocess, args.skip_vlm)
        scored = evaluate_row(answer, result)
        rows.append({
            "image": answer["image"],
            "true_brands": answer.get("true_brands", ""),
            "cnn_preds": "|".join(result["cnn_preds"]),
            "vlm_preds": "|".join(result["vlm_preds"]),
            "combined_preds": "|".join(name for name, _, _ in result["combined"]),
            "combined_badges": "|".join(colour for _, colour, _ in result["combined"]),
            **scored,
        })
        for key in totals:
            totals[key] += int(scored.get(key, 0) or 0)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    def rate(n, d):
        return round(n / d, 4) if d else None

    green_total = sum(
        1 for row in rows for badge in row["combined_badges"].split("|")
        if badge == "GREEN"
    )
    summary = {
        "samples": len(rows),
        "cnn_name_accuracy": rate(totals["cnn_correct"], totals["cnn_total"]),
        "gemini_name_accuracy": rate(totals["vlm_correct"], totals["vlm_total"]),
        "combined_name_accuracy": rate(totals["combined_correct"], totals["combined_total"]),
        "dose_accuracy": rate(totals["dose_correct"], totals["dose_total"]),
        "unsafe_error_rate": rate(totals["unsafe_green"], green_total),
        "green_lines": green_total,
        "catch_rate": rate(totals["caught_wrong"], totals["wrong_combined"]),
        "overflag_rate": rate(totals["overflagged_correct"], totals["combined_correct"]),
        "raw_totals": totals,
        "note": ("Automated review uses fusion output without human correction. "
                 "Dataset word-crop test accuracy (0.9590) is a separate number."),
    }
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {out} and {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

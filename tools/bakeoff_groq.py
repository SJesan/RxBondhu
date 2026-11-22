"""Timeboxed Groq bake-off on the same 10 real images / 48 lines as v1.

The per-image log stays local (gitignored); only derived metrics are committed.
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402
from rxbondhu import groq_vlm  # noqa: E402
from rxbondhu.lexicon import normalise_name  # noqa: E402


def norm(text: str) -> str:
    return normalise_name(text).lower()


def split_pipe(text: str) -> list[str]:
    return [part.strip() for part in (text or "").split("|") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", default="results/answer_key.csv")
    parser.add_argument("--images", default="results/rx")
    parser.add_argument("--log", default=None)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--model", default="")
    parser.add_argument("--reader", choices=("gemini", "groq"), default="groq")
    args = parser.parse_args()

    if args.reader == "gemini":
        from rxbondhu import vlm as reader
    else:
        from rxbondhu import groq_vlm as reader
    args.log = args.log or f"results/{args.reader}_bakeoff_log.csv"
    args.summary = args.summary or f"results/{args.reader}_bakeoff_summary.json"

    answers = list(csv.DictReader(open(args.answers, encoding="utf-8-sig", newline="")))
    rows = []
    for answer in answers:
        path = Path(args.images) / answer["image"]
        image = Image.open(path).convert("RGB")
        started = time.monotonic()
        result = reader.read(image, model=args.model or None)
        seconds = round(time.monotonic() - started, 2)

        raw = (result.get("raw") or "").strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
        valid_json = False
        if raw.startswith("["):
            try:
                valid_json = isinstance(json.loads(raw), list)
            except (ValueError, TypeError):
                valid_json = False

        true_norms = {norm(b) for b in split_pipe(answer.get("true_brands", ""))}
        pred_norms = [norm(item.get("medicine", "")) for item in result.get("lines", [])]
        name_ok = sum(1 for want in true_norms if want and want in pred_norms)

        true_doses = split_pipe(answer.get("true_dose", ""))
        dose_ok = dose_total = 0
        for index, want in enumerate(true_doses):
            if not want:
                continue
            dose_total += 1
            got = result["lines"][index].get("dose", "") if index < len(result["lines"]) else ""
            if norm(want) == norm(got) or norm(want) in norm(got):
                dose_ok += 1

        rows.append({
            "image": answer["image"],
            "model": result.get("model", ""),
            "seconds": seconds,
            "valid_json": int(valid_json),
            "error": result.get("error", ""),
            "true_brands": answer.get("true_brands", ""),
            "predicted": "|".join(item.get("medicine", "") for item in result["lines"]),
            "name_correct": name_ok,
            "name_total": len(true_norms),
            "dose_correct": dose_ok,
            "dose_total": dose_total,
        })
        print(f"{answer['image']}: json={valid_json} names={name_ok}/{len(true_norms)} "
              f"dose={dose_ok}/{dose_total} {seconds}s err={bool(result.get('error'))}")

    def rate(n, d):
        return round(n / d, 4) if d else None

    name_ok = sum(r["name_correct"] for r in rows)
    name_total = sum(r["name_total"] for r in rows)
    dose_ok = sum(r["dose_correct"] for r in rows)
    dose_total = sum(r["dose_total"] for r in rows)
    summary = {
        "samples": len(rows),
        "models": sorted({r["model"] for r in rows if r["model"]}),
        "valid_json_rate": rate(sum(r["valid_json"] for r in rows), len(rows)),
        "name_accuracy": rate(name_ok, name_total),
        "name_correct": name_ok,
        "name_total": name_total,
        "dose_accuracy": rate(dose_ok, dose_total),
        "dose_correct": dose_ok,
        "dose_total": dose_total,
        "mean_seconds": rate(sum(r["seconds"] for r in rows), len(rows)),
        "max_seconds": max((r["seconds"] for r in rows), default=0),
        "images_with_error": sum(1 for r in rows if r["error"]),
        "gate": {
            "valid_json_ge_90pct": (rate(sum(r["valid_json"] for r in rows), len(rows)) or 0) >= 0.9,
            "mean_latency_under_10s": (rate(sum(r["seconds"] for r in rows), len(rows)) or 99) < 10,
            "name_accuracy_ge_30pct": (rate(name_ok, name_total) or 0) >= 0.3,
        },
        "note": "Same 10 images / 48 lines as v1; no training on these images.",
    }
    summary["gate"]["pass"] = all(v for k, v in summary["gate"].items() if k != "pass")

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

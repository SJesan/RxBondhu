"""Build a verified brand lexicon from the DGDA Allopathic export.

The raw CSV is downloaded once and kept local (gitignored). This script reads
it, drops bulk/API rows, parses generic + strength, quarantines brands whose
generic identity conflicts, and writes a small committed snapshot.

Usage:
    .\\venv\\Scripts\\python.exe tools\\import_dgda.py

Inputs:
    data/dgda_medicines_raw.csv        (gitignored, downloaded once)
    data/manual_brands.csv             (human box/pharmacy checks)

Outputs:
    data/dgda_brands.csv               (committed verified reference)
    data/dgda_conflicts.csv            (committed audit of rejected rows)
    data/dgda_source.json              (committed provenance + sha256)
"""

import argparse
import collections
import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_DEFAULT = ROOT / "data" / "dgda_medicines_raw.csv"
MANUAL_DEFAULT = ROOT / "data" / "manual_brands.csv"
OUT_DEFAULT = ROOT / "data" / "dgda_brands.csv"
CONFLICT_DEFAULT = ROOT / "data" / "dgda_conflicts.csv"
SOURCE_DEFAULT = ROOT / "data" / "dgda_source.json"

PORTAL_URL = "http://180.211.137.202:9310/Allopathic/"
EXPORT_URL = PORTAL_URL + "Medicine_Information_Ajax.php?action=export"
SOURCE_NAME = "DGDA Allopathic Medicine Information export"

# Finished dosage forms only. Bulk/API rows (Kg, Liter, Raw Materials, ...) are
# not medicine brands and must never enter the verified lexicon.
ALLOWED_FORM_TOKENS = (
    "tablet", "capsule", "syrup", "suspension", "injection", "drop",
    "ointment", "cream", "gel", "suppository", "inhaler", "inhalation",
    "sachet", "solution", "infusion", "powder", "bolus", "spray",
    "aerosol", "lozenge", "patch", "enema", "pellet", "implant",
    "granule", "mups", "film", "soap", "shampoo",
)
BULK_FORMS = {
    "kg", "gm", "g", "ml", "mm", "liter", "litre", "l",
    "raw material", "raw materials", "bulk", "api", "",
}
BULK_NAME_MARKERS = ("(api)", " bp ", " bp", "raw material", "industrial")

UNIT = r"(?:mg|mcg|gm|g|ml|iu|%|vial|units?|kg|mm)"
NUM_WITH_UNIT = re.compile(
    rf"\d+(?:\.\d+)?\s*{UNIT}(?:\s*/\s*(?:\d+(?:\.\d+)?\s*)?{UNIT})?", re.I
)
BARE_SLASH_UNIT = re.compile(rf"/\s*{UNIT}\b", re.I)
TRAIL_STRENGTH = re.compile(
    rf"\s+\d+(?:\.\d+)?\s*(?:{UNIT})?s?\s*$", re.I
)
LEAD_FORM = re.compile(
    r"^(?:ts|tab|tablet|cap|capsule|syp|syr|syrup|inj|injection|supp|suppository|"
    r"drop|drops|cr|cream|oint|ointment|powder)\.?\s+", re.I,
)
NON_ALNUM = re.compile(r"[^a-z0-9\u0980-\u09ff]+")

BRAND_FIELDS = [
    "brand", "generic", "strength", "form", "company", "dar_no",
    "source", "source_url", "accessed_at", "verified", "checked_by",
    "generic_canonical",
]
CONFLICT_FIELDS = [
    "brand_key", "reason", "dgda_generics", "manual_generic",
    "trade_names", "dar_nos", "forms",
]


def brand_key(text: str) -> str:
    """Normalised lookup key: lowercase, punctuation out, trailing strength out."""
    key = re.sub(r"\s+", " ", NON_ALNUM.sub(" ", str(text or "").lower())).strip()
    key = LEAD_FORM.sub("", key).strip()
    previous = None
    while previous != key:
        previous = key
        key = TRAIL_STRENGTH.sub("", key).strip()
    return key


def parse_generic(raw: str) -> tuple[str, str, str]:
    """Return (generic display, generic canonical, strength) from DGDA text."""
    text = str(raw or "")
    strength = " ".join(NUM_WITH_UNIT.findall(text))
    without_strength = NUM_WITH_UNIT.sub(" ", text)
    without_strength = BARE_SLASH_UNIT.sub(" ", without_strength)
    parts = []
    for part in without_strength.split("+"):
        part = re.sub(r"\s+", " ", part).strip(" \t,.;:/-")
        if part:
            parts.append(part)
    generic = " + ".join(parts)
    canonical = " + ".join(sorted({p.casefold() for p in parts}))
    return generic, canonical, re.sub(r"\s+", " ", strength).strip()


def is_finished_form(form: str, trade_name: str) -> bool:
    form = str(form or "").strip().lower()
    name = f" {str(trade_name or '').lower()} "
    if form in BULK_FORMS:
        return False
    if any(marker in name for marker in BULK_NAME_MARKERS):
        return False
    return any(token in form for token in ALLOWED_FORM_TOKENS)


def read_manual(path: Path) -> dict[str, dict[str, str]]:
    """Manual box checks keyed by brand_key: brand_key -> {brand, generic, provenance}."""
    result: dict[str, dict[str, str]] = {}
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("verified", "")).strip().lower() not in ("yes", "true", "1"):
                continue
            key = brand_key(row.get("brand"))
            generic = str(row.get("generic") or "").strip()
            if key and generic:
                result[key] = {
                    "brand": str(row.get("brand") or key).strip(),
                    "generic": generic,
                    "checked_by": str(row.get("checked_by") or "").strip(),
                    "source": str(row.get("source") or "medicine box check").strip(),
                }
    return result


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=RAW_DEFAULT)
    ap.add_argument("--manual", type=Path, default=MANUAL_DEFAULT)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--conflicts", type=Path, default=CONFLICT_DEFAULT)
    ap.add_argument("--source", type=Path, default=SOURCE_DEFAULT)
    ap.add_argument("--accessed-at", default=date.today().isoformat())
    args = ap.parse_args()

    if not args.raw.exists():
        raise SystemExit(f"Raw DGDA CSV missing: {args.raw}")

    raw_rows = 0
    dropped_bulk = 0
    groups: dict[str, dict[str, list[dict]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    conflicts: list[dict] = []

    with args.raw.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        expected = {"SL", "Company", "Trade Name", "Generic Name With Strength",
                    "Dosage Form", "DAR No"}
        missing = expected - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Unexpected DGDA export columns: missing {sorted(missing)}")
        for row in reader:
            raw_rows += 1
            trade = str(row.get("Trade Name") or "").strip()
            form = str(row.get("Dosage Form") or "").strip()
            if not is_finished_form(form, trade):
                dropped_bulk += 1
                continue
            key = brand_key(trade)
            generic, canonical, strength = parse_generic(row.get("Generic Name With Strength"))
            if not key or not generic:
                dropped_bulk += 1
                continue
            groups[key][canonical].append({
                "brand": trade,
                "generic": generic,
                "canonical": canonical,
                "strength": strength,
                "form": form,
                "company": str(row.get("Company") or "").strip(),
                "dar_no": str(row.get("DAR No") or "").strip(),
            })

    manual = read_manual(args.manual)
    brand_rows: list[dict] = []
    conflict_keys: set[str] = set()

    for key, by_generic in groups.items():
        generics = sorted(by_generic)
        all_rows = [r for group in by_generic.values() for r in group]
        if len(generics) > 1:
            conflict_keys.add(key)
            conflicts.append({
                "brand_key": key,
                "reason": "DGDA brand maps to multiple generic identities",
                "dgda_generics": " || ".join(generics),
                "manual_generic": manual.get(key, {}).get("generic", ""),
                "trade_names": " | ".join(sorted({r["brand"] for r in all_rows})[:8]),
                "dar_nos": " | ".join(sorted({r["dar_no"] for r in all_rows})[:8]),
                "forms": " | ".join(sorted({r["form"] for r in all_rows})[:8]),
            })
            continue

        canonical = generics[0]
        chosen = all_rows[0]
        manual_row = manual.get(key)
        if manual_row and manual_row["generic"].casefold() != canonical.casefold():
            conflict_keys.add(key)
            conflicts.append({
                "brand_key": key,
                "reason": "Box check disagrees with DGDA generic",
                "dgda_generics": canonical,
                "manual_generic": manual_row["generic"],
                "trade_names": chosen["brand"],
                "dar_nos": chosen["dar_no"],
                "forms": chosen["form"],
            })
            continue

        # DGDA identity + the human box note travel together. The box note is
        # never silently dropped just because DGDA also lists the brand.
        source = SOURCE_NAME
        checked_by = ""
        if manual_row:
            source = f"{SOURCE_NAME}; {manual_row['source']}"
            checked_by = manual_row["checked_by"]
        brand_rows.append({
            "brand": chosen["brand"],
            "generic": chosen["generic"],
            "strength": chosen["strength"],
            "form": chosen["form"],
            "company": chosen["company"],
            "dar_no": chosen["dar_no"],
            "source": source,
            "source_url": EXPORT_URL,
            "accessed_at": args.accessed_at,
            "verified": "yes",
            "checked_by": checked_by,
            "generic_canonical": canonical,
        })

    # Manual box checks are the highest-trust human note. They stay in the
    # committed lexicon even when a DGDA row was quarantined for that brand.
    manual_added = 0
    dgda_keys = {brand_key(r["brand"]) for r in brand_rows}
    for key, manual_row in manual.items():
        if key in dgda_keys:
            continue
        brand_rows.append({
            "brand": manual_row["brand"],
            "generic": manual_row["generic"],
            "strength": "",
            "form": "",
            "company": "",
            "dar_no": "",
            "source": manual_row["source"],
            "source_url": "",
            "accessed_at": args.accessed_at,
            "verified": "yes",
            "checked_by": manual_row["checked_by"],
            "generic_canonical": " + ".join(
                sorted({g.strip().casefold() for g in manual_row["generic"].split("+")})
            ),
        })
        manual_added += 1

    brand_rows.sort(key=lambda r: brand_key(r["brand"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=BRAND_FIELDS)
        writer.writeheader()
        writer.writerows(brand_rows)

    conflicts.sort(key=lambda r: r["brand_key"])
    with args.conflicts.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CONFLICT_FIELDS)
        writer.writeheader()
        writer.writerows(conflicts)

    source_meta = {
        "source": SOURCE_NAME,
        "portal_url": PORTAL_URL,
        "export_url": EXPORT_URL,
        "accessed_at": args.accessed_at,
        "raw_file": (str(args.raw.relative_to(ROOT))
                     if args.raw.is_relative_to(ROOT) else str(args.raw)),
        "raw_bytes": args.raw.stat().st_size,
        "raw_rows": raw_rows,
        "raw_sha256": sha256_of(args.raw),
        "dropped_bulk_or_empty": dropped_bulk,
        "brand_rows": len(brand_rows),
        "manual_rows_added": manual_added,
        "conflict_brand_keys": len(conflicts),
        "verified_brand_keys": len(dgda_keys),
        "note": ("Snapshot committed; no runtime network call. GREEN requires a >=95 "
                 "normalised match plus two agreeing readers; fuzzy-only is capped at YELLOW."),
    }
    args.source.write_text(json.dumps(source_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(source_meta, indent=2, ensure_ascii=False))
    print(f"Wrote {args.out}, {args.conflicts}, {args.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

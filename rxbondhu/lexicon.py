"""Real Bangladeshi brand -> generic matching.

Only rows marked verified = yes are used. Unknown / invented names are
rejected unless they closely match a known brand.
"""

import csv
import difflib
import os
import re

try:
    from rapidfuzz import fuzz, process

    HAVE_RAPIDFUZZ = True
except ImportError:  # stdlib fallback so tests run before pip finishes
    HAVE_RAPIDFUZZ = False


# Seed list. Verify each generic against a medicine box / trusted drug index
# before relying on it. Rows copied to data/manual_brands.csv stay unverified
# until you tick them (verified = yes) yourself.
SEED_BRANDS = [
    {"brand": "Napa", "generic": "Paracetamol", "verified": True},
    {"brand": "Ace", "generic": "Paracetamol", "verified": True},
    {"brand": "Calpol", "generic": "Paracetamol", "verified": True},
    {"brand": "Panadol", "generic": "Paracetamol", "verified": True},
    {"brand": "Maxpro", "generic": "Meloxicam", "verified": True},
    {"brand": "Melonex", "generic": "Meloxicam", "verified": True},
    {"brand": "Brufen", "generic": "Ibuprofen", "verified": True},
    {"brand": "Voveran", "generic": "Diclofenac", "verified": True},
    {"brand": "Cetiriz", "generic": "Cetirizine", "verified": True},
    {"brand": "Zyrtec", "generic": "Cetirizine", "verified": True},
    {"brand": "Azithral", "generic": "Azithromycin", "verified": True},
    {"brand": "Flagyl", "generic": "Metronidazole", "verified": True},
    {"brand": "Omez", "generic": "Omeprazole", "verified": True},
    {"brand": "Pantocid", "generic": "Pantoprazole", "verified": True},
    {"brand": "Ventolin", "generic": "Salbutamol", "verified": True},
    {"brand": "Losar", "generic": "Losartan", "verified": True},
    {"brand": "Norvasc", "generic": "Amlodipine", "verified": True},
    {"brand": "Glucophage", "generic": "Metformin", "verified": True},
]


def normalise_name(text: str) -> str:
    """Strip dosage words/punctuation; keep Latin and Bangla letters."""
    if not text:
        return ""
    t = str(text).lower()
    t = re.sub(r"\b(tab|tablet|cap|capsule|syr|susp)\b", " ", t)
    t = re.sub(r"(mg|ml|mcg|gm)\b", " ", t)
    t = re.sub(r"[^a-z0-9\u0980-\u09ff]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def load_brands(path: str | None = None) -> list[dict]:
    """Return verified brands from the seed list plus an optional CSV."""
    brands = [dict(b) for b in SEED_BRANDS if b["verified"]]
    path = path or os.path.join("data", "manual_brands.csv")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if str(row.get("verified", "")).strip().lower() in ("yes", "true", "1"):
                    brand = (row.get("brand") or "").strip()
                    generic = (row.get("generic") or "").strip()
                    if brand and generic:
                        brands.append({"brand": brand, "generic": generic, "verified": True})

    # Deduplicate by casefolded brand name.
    seen, unique = set(), []
    for b in brands:
        key = b["brand"].casefold()
        if key not in seen:
            seen.add(key)
            unique.append(b)
    return unique


def match_brand(text: str, brands: list[dict] | None = None, threshold: int = 60) -> dict | None:
    """Find the closest real brand. Returns None when nothing is close enough."""
    brands = brands if brands is not None else load_brands()
    query = normalise_name(text)
    if not query or not brands:
        return None

    choices = {b["brand"]: b for b in brands}
    names = list(choices)

    if HAVE_RAPIDFUZZ:
        hit = process.extractOne(query, names, scorer=fuzz.WRatio, score_cutoff=threshold)
        if not hit:
            return None
        name, score = hit[0], float(hit[1])
    else:
        scored = [(difflib.SequenceMatcher(None, query, n.lower()).ratio() * 100, n) for n in names]
        score, name = max(scored)
        if score < threshold:
            return None

    brand = choices[name]
    return {
        "brand": brand["brand"],
        "generic": brand["generic"],
        "score": round(float(score), 1),
        "matched_text": text,
    }


def lookup_exact(name: str, brands: list[dict] | None = None) -> dict | None:
    """Exact (normalised) lookup used for confirmed review-screen choices."""
    brands = brands if brands is not None else load_brands()
    key = normalise_name(name)
    for b in brands:
        if normalise_name(b["brand"]) == key:
            return dict(b)
    return None

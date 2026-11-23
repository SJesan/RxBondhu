"""Brand -> generic verification against a committed DGDA-registered snapshot.

The verified reference is ``data/dgda_brands.csv``: DGDA Allopathic export
rows with a DAR No, plus human box/pharmacy checks. Rows with conflicting
generic identities are quarantined in ``data/dgda_conflicts.csv`` and never
used to turn a reading GREEN. There is no runtime network call.

A fuzzy-only match is deliberately *not* a GREEN pass: fusion.py requires a
normalised score >= 95 from both readers before showing GREEN.
"""

import csv
import difflib
import os
import re
from functools import lru_cache

try:
    from rapidfuzz import fuzz, process

    HAVE_RAPIDFUZZ = True
except ImportError:  # stdlib fallback so tests run before pip finishes
    HAVE_RAPIDFUZZ = False


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DGDA_CSV = os.path.join(_ROOT, "data", "dgda_brands.csv")
MANUAL_CSV = os.path.join(_ROOT, "data", "manual_brands.csv")
CONFLICTS_CSV = os.path.join(_ROOT, "data", "dgda_conflicts.csv")

# 95 is a fixed safety policy. The env override exists only so the evaluator
# can reproduce the pre-import baseline in one command; the app never sets it.
GREEN_SCORE = int(os.getenv("RX_GREEN_SCORE", "95"))

# Seed list kept as a fallback when the DGDA snapshot is absent (unit tests,
# fresh checkouts). DGDA and box-checked rows always take precedence.
SEED_BRANDS = [
    {"brand": "Napa", "generic": "Paracetamol", "verified": True},
    {"brand": "Ace", "generic": "Paracetamol", "verified": True},
    {"brand": "Calpol", "generic": "Paracetamol", "verified": True},
    {"brand": "Panadol", "generic": "Paracetamol", "verified": True},
    # Box/pharmacy check on 23 Nov 2026 corrected this from an old Meloxicam label.
    {"brand": "Maxpro", "generic": "Esomeprazole", "verified": True},
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

UNIT = r"(?:mg|mcg|gm|g|ml|iu|%|vial|units?|kg|mm)"
TRAIL_STRENGTH = re.compile(rf"\s+\d+(?:\.\d+)?\s*(?:{UNIT})?s?\s*$", re.I)
LEAD_FORM = re.compile(
    r"^(?:ts|tab|tablet|cap|capsule|syp|syr|syrup|inj|injection|supp|suppository|"
    r"drop|drops|cr|cream|oint|ointment|powder)\.?\s+", re.I,
)
NON_ALNUM = re.compile(r"[^a-z0-9\u0980-\u09ff]+")


def normalise_name(text: str) -> str:
    """Strip dosage words/punctuation; keep Latin and Bangla letters."""
    if not text:
        return ""
    t = str(text).lower()
    t = re.sub(r"\b(ts|tab|tablet|cap|capsule|syr|susp)\b", " ", t)
    t = re.sub(r"(mg|ml|mcg|gm)\b", " ", t)
    t = re.sub(r"[^a-z0-9\u0980-\u09ff]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def brand_key(text: str) -> str:
    """Lookup key: lowercase, punctuation out, trailing strength removed.

    ``Napa 500`` and ``Napa`` must resolve to the same registered brand, but
    ``Napa Extend`` stays distinct because it is a different product.
    """
    key = re.sub(r"\s+", " ", NON_ALNUM.sub(" ", str(text or "").lower())).strip()
    key = LEAD_FORM.sub("", key).strip()
    previous = None
    while previous != key:
        previous = key
        key = TRAIL_STRENGTH.sub("", key).strip()
    return key


@lru_cache(maxsize=1)
def _conflict_index() -> dict[str, dict]:
    """Quarantined brand keys: DGDA disagrees with the box/pharmacist note."""
    index: dict[str, dict] = {}
    if not os.path.exists(CONFLICTS_CSV):
        return index
    with open(CONFLICTS_CSV, "r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            key = brand_key(row.get("brand_key") or row.get("brand") or "")
            if key:
                index[key] = dict(row)
    return index


def conflict_for(brand: str) -> dict | None:
    """Return the conflict row for a brand, if its identity was quarantined."""
    key = brand_key(brand)
    return dict(_conflict_index()[key]) if key in _conflict_index() else None


def _read_csv(path: str) -> list[dict]:
    brands = []
    if not path or not os.path.exists(path):
        return brands
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("verified", "")).strip().lower() not in ("yes", "true", "1"):
                continue
            brand = (row.get("brand") or "").strip()
            generic = (row.get("generic") or "").strip()
            if not brand or not generic:
                continue
            item = dict(row)
            item["brand"] = brand
            item["generic"] = generic
            item["verified"] = True
            item.setdefault("checked_by", "")
            item.setdefault("source", "verified list")
            brands.append(item)
    return brands


def _default_path() -> str:
    override = os.getenv("RX_LEXICON_PATH", "").strip()
    if override:
        return override
    return DGDA_CSV if os.path.exists(DGDA_CSV) else MANUAL_CSV


@lru_cache(maxsize=8)
def _build_index(path: str | None) -> tuple[list[dict], dict[str, dict], tuple[str, ...]]:
    """Load once, then reuse: 23k+ rows must not be re-read for every line."""
    resolved = path or _default_path()
    brands = _read_csv(resolved)

    if not brands:
        brands = [
            dict(b, source=b.get("source", "seed verified list"),
                 checked_by=b.get("checked_by", ""))
            for b in SEED_BRANDS if b["verified"]
        ]
    elif resolved == MANUAL_CSV:
        # Snapshot absent: fall back to the old seed + manual behaviour.
        seed_keys = {brand_key(b["brand"]) for b in brands}
        for seed in SEED_BRANDS:
            if brand_key(seed["brand"]) not in seed_keys:
                brands.append(dict(
                    seed, source="seed verified list", checked_by="", dar_no="",
                    form="", company="", strength="", source_url="",
                    accessed_at="", generic_canonical=normalise_name(seed["generic"]),
                ))
                seed_keys.add(brand_key(seed["brand"]))

    by_key: dict[str, dict] = {}
    for brand in brands:
        by_key.setdefault(brand_key(brand["brand"]), brand)
    return brands, by_key, tuple(by_key)


def load_brands(path: str | None = None) -> list[dict]:
    """Return verified brands, DGDA-registered first, then box-checked rows."""
    return list(_build_index(path)[0])


# Callers (fusion, app) pass an explicit brands list. Rebuilding a 23k-key
# index for every line was the difference between 3 ms and 145 ms per lookup.
_INDEX_CACHE: dict[tuple[int, int], tuple[dict[str, dict], tuple[str, ...]]] = {}


def _get_index(brands: list[dict] | None) -> tuple[dict[str, dict], tuple[str, ...]]:
    if brands is None:
        _, by_key, names = _build_index(None)
        return by_key, names
    key = (id(brands), len(brands))
    cached = _INDEX_CACHE.get(key)
    if cached is not None:
        return cached
    by_key = {}
    for brand in brands:
        by_key.setdefault(brand_key(brand["brand"]), brand)
    result = (by_key, tuple(by_key))
    _INDEX_CACHE.clear()
    _INDEX_CACHE[key] = result
    return result


def _hit(brand: dict, score: float, text: str, match_kind: str) -> dict:
    return {
        "brand": brand["brand"],
        "generic": brand["generic"],
        "score": round(float(score), 1),
        "matched_text": text,
        "match_kind": match_kind,
        "source": brand.get("source", ""),
        "checked_by": brand.get("checked_by", ""),
        "dar_no": brand.get("dar_no", ""),
        "form": brand.get("form", ""),
        "company": brand.get("company", ""),
        "strength": brand.get("strength", ""),
        "source_url": brand.get("source_url", ""),
        "accessed_at": brand.get("accessed_at", ""),
        "generic_canonical": brand.get("generic_canonical", ""),
        "brand_key": brand_key(brand["brand"]),
    }


def match_brand(text: str, brands: list[dict] | None = None,
                threshold: int = 85) -> dict | None:
    """Find the closest verified brand. Exact normalised key wins; fuzzy is scored."""
    by_key, names = _get_index(brands)
    query = brand_key(text)
    if not query or not names:
        return None

    exact = by_key.get(query)
    if exact:
        return _hit(exact, 100.0, text, "exact")

    if HAVE_RAPIDFUZZ:
        # Strict full-string ratio, NOT WRatio: WRatio's partial scoring let
        # short DGDA keys like "El-100" score 90 against "Eltroxin".
        hit = process.extractOne(query, names, scorer=fuzz.ratio, score_cutoff=threshold)
        if not hit:
            return None
        key, score = hit[0], float(hit[1])
    else:
        scored = ((difflib.SequenceMatcher(None, query, name).ratio() * 100, name)
                  for name in names)
        best = max(scored, default=(0.0, ""))
        score, key = best
        if score < threshold:
            return None

    return _hit(by_key[key], score, text, "near" if score >= GREEN_SCORE else "fuzzy")


def lookup_exact(name: str, brands: list[dict] | None = None) -> dict | None:
    """Exact normalised lookup used for confirmed review-screen choices."""
    by_key, _ = _get_index(brands)
    key = brand_key(name)
    return dict(by_key[key]) if key in by_key else None


def suggest_brands(text: str, brands: list[dict] | None = None, n: int = 3,
                   threshold: int = 60) -> list[dict]:
    """Top-n DGDA/box-checked brand suggestions for review.

    Uses the trained DGDA name matcher when available, otherwise falls back to
    RapidFuzz/difflib. Suggestions are never auto-applied by callers.
    """
    brands = brands if brands is not None else load_brands()
    query = brand_key(text)
    if not query or not brands:
        return []

    try:
        from . import name_matcher
        if name_matcher.available():
            ranked = name_matcher.suggest(text, brands, n=n)
            result = []
            for row in ranked:
                score = float(row.get("score", 0))
                if score < max(35, threshold - 20):
                    continue
                dar_backed = bool(str(row.get("dar_no") or "").strip())
                result.append({
                    "brand": row.get("brand", ""),
                    "generic": row.get("generic", ""),
                    "score": round(score, 1),
                    "dar_no": row.get("dar_no", ""),
                    "match_kind": "near" if score >= GREEN_SCORE else "fuzzy",
                    "in_dgda": True,
                    "dar_backed": dar_backed,
                    "source": row.get("source", ""),
                    "form": row.get("form", ""),
                    "strength": row.get("strength", ""),
                    "matcher": "dgda_name_matcher",
                })
            if result:
                return result[:n]
    except Exception:
        pass

    by_key, names = _get_index(brands)
    if HAVE_RAPIDFUZZ:
        hits = process.extract(query, names, scorer=fuzz.ratio, limit=max(n * 4, 12),
                               score_cutoff=max(45, threshold - 10))
        pairs = [(key, float(score)) for key, score, _ in hits]
    else:
        scored = ((difflib.SequenceMatcher(None, query, key).ratio() * 100, key)
                  for key in names)
        pairs = sorted((p for p in scored if p[0] >= max(45, threshold - 10)), reverse=True)[: max(n * 4, 12)]

    result = []
    seen = set()
    for key, score in pairs:
        brand = by_key[key]
        identity = brand_key(brand.get("brand", ""))
        if not identity or identity in seen:
            continue
        seen.add(identity)
        dar_backed = bool(str(brand.get("dar_no") or "").strip())
        result.append({
            "brand": brand["brand"], "generic": brand["generic"],
            "score": round(score, 1),
            "dar_no": brand.get("dar_no", ""),
            "match_kind": "near" if score >= GREEN_SCORE else "fuzzy",
            "in_dgda": True,
            "dar_backed": dar_backed,
            "source": brand.get("source", ""),
            "form": brand.get("form", ""),
            "strength": brand.get("strength", ""),
            "matcher": "rapidfuzz" if HAVE_RAPIDFUZZ else "difflib",
        })
        if len(result) >= n:
            break
    return result


def verify_name(name: str, brands: list[dict] | None = None) -> dict:
    """Verify a brand name against the committed DGDA snapshot.

    Returns an explicit in-list status for UI/fusion: found, exact, dar_backed,
    conflict, record, and DGDA suggestions. Suggestions are never auto-applied.
    """
    brands = brands if brands is not None else load_brands()
    raw = str(name or "").strip()
    key = brand_key(raw)
    if not key:
        return {
            "input": raw, "normalized": key, "in_dgda": False, "found": False,
            "exact": False, "dar_backed": False, "conflict": None, "record": None,
            "suggestions": [], "status": "empty",
        }

    by_key, _ = _get_index(brands)
    exact_row = by_key.get(key)
    suggestions = suggest_brands(raw, brands, n=5)
    if exact_row:
        conflict = conflict_for(exact_row.get("brand") or raw)
        dar_backed = bool(str(exact_row.get("dar_no") or "").strip()) and not conflict
        record = dict(exact_row)
        status = "dgda_dar" if dar_backed else "dgda_conflict" if conflict else "box_only"
        return {
            "input": raw, "normalized": key, "in_dgda": True, "found": True,
            "exact": True, "dar_backed": dar_backed, "conflict": conflict,
            "record": record, "suggestions": suggestions, "status": status,
            "score": 100.0,
        }

    # Fuzzy match is a suggestion candidate, NOT proof the name is in DGDA.
    hit = match_brand(raw, brands, threshold=85)
    conflict = conflict_for(hit["brand"]) if hit else None
    dar_backed = bool(hit and str(hit.get("dar_no") or "").strip() and not conflict)
    return {
        "input": raw, "normalized": key, "in_dgda": False, "found": False,
        "exact": False, "dar_backed": False, "conflict": conflict,
        "record": None, "suggestions": suggestions,
        "status": "not_in_dgda",
        "score": float(hit["score"]) if hit else 0.0,
        "closest": hit,
    }

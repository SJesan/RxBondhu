"""Lightweight DGDA brand-name matcher/reranker.

Trains on synthetic noisy queries generated from all DGDA brand rows. It learns
to rerank DGDA candidates for wrong/misspelled names. Suggestions are never
auto-applied by callers.
"""
from __future__ import annotations

import json
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "dgda_name_matcher.pt"
META_PATH = ROOT / "models" / "dgda_name_matcher_meta.json"

try:
    from rapidfuzz import fuzz, process
    HAVE_RAPIDFUZZ = True
except Exception:
    HAVE_RAPIDFUZZ = False

try:
    import torch
    from torch import nn
    HAVE_TORCH = True
except Exception:
    torch = None
    nn = None
    HAVE_TORCH = False

_MODEL = None
_META = None


def _normalize(text: str) -> str:
    value = str(text or "").lower()
    value = re.sub(r"[^a-z0-9\u0980-\u09ff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _char_ngrams(text: str, n: int = 3) -> set[str]:
    text = f"  {_normalize(text)}  "
    if len(text) < n:
        return {text}
    return {text[i:i + n] for i in range(len(text) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def feature_vector(query: str, candidate: str) -> list[float]:
    q = _normalize(query)
    c = _normalize(candidate)
    if not q or not c:
        return [0.0] * 10
    if HAVE_RAPIDFUZZ:
        ratio = fuzz.ratio(q, c) / 100.0
        partial = fuzz.partial_ratio(q, c) / 100.0
        tsort = fuzz.token_sort_ratio(q, c) / 100.0
        tset = fuzz.token_set_ratio(q, c) / 100.0
    else:
        import difflib
        ratio = difflib.SequenceMatcher(None, q, c).ratio()
        partial = ratio
        tsort = ratio
        tset = ratio
    q3, c3 = _char_ngrams(q, 3), _char_ngrams(c, 3)
    q2, c2 = _char_ngrams(q, 2), _char_ngrams(c, 2)
    len_diff = abs(len(q) - len(c)) / max(len(q), len(c), 1)
    prefix = 0.0
    for a, b in zip(q, c):
        if a != b:
            break
        prefix += 1
    prefix /= max(min(len(q), len(c)), 1)
    same_first = 1.0 if q[:1] == c[:1] else 0.0
    contains = 1.0 if q in c or c in q else 0.0
    return [ratio, partial, tsort, tset, _jaccard(q3, c3), _jaccard(q2, c2), 1.0 - len_diff, prefix, same_first, contains]


def _build_model(input_dim: int = 10):
    if not HAVE_TORCH:
        return None
    return nn.Sequential(
        nn.Linear(input_dim, 32),
        nn.ReLU(),
        nn.Dropout(0.1),
        nn.Linear(32, 16),
        nn.ReLU(),
        nn.Linear(16, 1),
    )


def load_model():
    global _MODEL, _META
    if _MODEL is not None or _META is not None:
        return _MODEL, _META
    if not HAVE_TORCH or not MODEL_PATH.exists():
        _MODEL, _META = None, None
        return _MODEL, _META
    try:
        payload = torch.load(MODEL_PATH, map_location="cpu")
        meta = json.loads(META_PATH.read_text(encoding="utf-8")) if META_PATH.exists() else {}
        model = _build_model(int(meta.get("input_dim", 10)))
        model.load_state_dict(payload["state_dict"])
        model.eval()
        _MODEL, _META = model, meta
    except Exception:
        _MODEL, _META = None, None
    return _MODEL, _META


def available() -> bool:
    model, _ = load_model()
    return model is not None


def _candidate_keys(query: str, keys: list[str], n: int = 20) -> list[tuple[str, float]]:
    q = _normalize(query)
    if not q or not keys:
        return []
    if HAVE_RAPIDFUZZ:
        hits = process.extract(q, keys, scorer=fuzz.ratio, limit=max(n, 20), score_cutoff=35)
        return [(k, float(s)) for k, s, _ in hits]
    import difflib
    scored = ((difflib.SequenceMatcher(None, q, k).ratio() * 100, k) for k in keys)
    return [(k, s) for s, k in sorted(scored, reverse=True)[:n]]


def rank_candidates(query: str, candidates: list[dict], n: int = 5) -> list[dict]:
    if not candidates:
        return []
    model, _ = load_model()
    rows = []
    for cand in candidates:
        brand = str(cand.get("brand") or "")
        feats = feature_vector(query, brand)
        base = feats[0]
        score = base
        if model is not None:
            with torch.no_grad():
                logit = model(torch.tensor([feats], dtype=torch.float32))[0, 0].item()
                score = 1 / (1 + math.exp(-logit))
        row = dict(cand)
        row["matcher_score"] = round(float(score) * 100, 1)
        row["fuzzy_score"] = round(float(base) * 100, 1)
        row["score"] = row["matcher_score"]
        rows.append(row)
    rows.sort(key=lambda r: (r.get("matcher_score", 0), r.get("fuzzy_score", 0)), reverse=True)
    dedup = []
    seen = set()
    for row in rows:
        key = _normalize(row.get("brand", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        dedup.append(row)
        if len(dedup) >= n:
            break
    return dedup


def suggest(query: str, brands: list[dict], n: int = 5) -> list[dict]:
    q = _normalize(query)
    if not q or not brands:
        return []
    by_key = {}
    for row in brands:
        key = _normalize(row.get("brand", ""))
        if key and key not in by_key:
            by_key[key] = row
    keys = list(by_key.keys())
    cand_keys = _candidate_keys(q, keys, n=max(n * 4, 20))
    candidates = []
    for key, fuzzy in cand_keys:
        row = dict(by_key[key])
        row["score"] = round(float(fuzzy), 1)
        candidates.append(row)
    return rank_candidates(query, candidates, n=n)

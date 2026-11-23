"""Train a small DGDA name-matching reranker on synthetic noisy brand queries.

This model learns to rerank DGDA brand candidates for misspelled/noisy names.
It does NOT replace the image CNN and is never auto-applied to GREEN decisions.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rxbondhu.lexicon import brand_key, load_brands  # noqa: E402
from rxbondhu.name_matcher import feature_vector, _build_model, HAVE_RAPIDFUZZ  # noqa: E402

try:
    from rapidfuzz import fuzz, process
except Exception:
    fuzz = None
    process = None

SEED = 42
OCR_CONFUSIONS = [
    ("rn", "m"), ("m", "rn"), ("cl", "d"), ("l", "1"), ("1", "l"), ("0", "o"), ("o", "0"),
    ("i", "l"), ("l", "i"), ("s", "5"), ("5", "s"), ("b", "h"), ("h", "b"), ("c", "e"), ("e", "c"),
]
PREFIXES = ["", "", "", "Tab ", "Cap ", "Syp ", "Inj "]
SUFFIXES = ["", "", "", " 500", " 20mg", " 10 mg", " tablet", " cap"]


def normalize(text: str) -> str:
    text = str(text or "").lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def corrupt(text: str, rng: random.Random) -> str:
    base = normalize(text)
    if not base:
        return base
    base = rng.choice(PREFIXES) + base + rng.choice(SUFFIXES)
    base = normalize(base)
    chars = list(base)
    ops = rng.randint(1, 2)
    for _ in range(ops):
        if not chars:
            break
        op = rng.choice(["del", "swap", "ins", "sub", "ocr"])
        i = rng.randrange(len(chars))
        if op == "del" and len(chars) > 3:
            del chars[i]
        elif op == "swap" and i + 1 < len(chars):
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
        elif op == "ins":
            chars.insert(i, rng.choice("abcdefghijklmnopqrstuvwxyz"))
        elif op == "sub":
            chars[i] = rng.choice("abcdefghijklmnopqrstuvwxyz")
        elif op == "ocr":
            s = "".join(chars)
            src, dst = rng.choice(OCR_CONFUSIONS)
            if src in s:
                s = s.replace(src, dst, 1)
                chars = list(s)
    out = "".join(chars)
    if rng.random() < 0.15:
        out = out.replace(" ", "")
    return normalize(out)


def candidate_keys(query: str, keys: list[str], n: int = 15) -> list[str]:
    q = normalize(query)
    if not q or not keys:
        return []
    if HAVE_RAPIDFUZZ and process is not None:
        hits = process.extract(q, keys, scorer=fuzz.ratio, limit=max(n, 15), score_cutoff=30)
        return [k for k, _, _ in hits]
    import difflib
    scored = ((difflib.SequenceMatcher(None, q, k).ratio(), k) for k in keys)
    return [k for _, k in sorted(scored, reverse=True)[:n]]


def make_examples(rows: list[dict], per_brand: int, rng: random.Random):
    keys = []
    by_key = {}
    for row in rows:
        k = brand_key(row.get("brand", ""))
        if k and k not in by_key:
            by_key[k] = row
            keys.append(k)
    examples = []
    for key in keys:
        brand = by_key[key]["brand"]
        for _ in range(per_brand):
            q = corrupt(brand, rng)
            if not q:
                continue
            cands = candidate_keys(q, keys, n=12)
            if key not in cands:
                cands = cands[:11] + [key]
            rng.shuffle(cands)
            for cand in cands[:12]:
                feats = feature_vector(q, by_key[cand]["brand"])
                label = 1.0 if cand == key else 0.0
                examples.append((feats, label))
    rng.shuffle(examples)
    return examples, len(keys)


def evaluate(model, rows, keys, by_key, rng, n_samples=500):
    import torch
    model.eval()
    hit1 = hit5 = 0
    total = 0
    for key in rng.sample(keys, min(n_samples, len(keys))):
        brand = by_key[key]["brand"]
        q = corrupt(brand, rng)
        cands = candidate_keys(q, keys, n=20)
        if key not in cands:
            cands = cands[:19] + [key]
        feats = torch.tensor([feature_vector(q, by_key[c]["brand"]) for c in cands], dtype=torch.float32)
        with torch.no_grad():
            scores = torch.sigmoid(model(feats)[:, 0]).tolist()
        ranked = [c for _, c in sorted(zip(scores, cands), reverse=True)]
        total += 1
        if ranked and ranked[0] == key:
            hit1 += 1
        if key in ranked[:5]:
            hit5 += 1
    return {"hit1": hit1 / max(total, 1), "hit5": hit5 / max(total, 1), "n": total}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-brand", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--limit-brands", type=int, default=0, help="for smoke test")
    args = parser.parse_args()

    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    rng = random.Random(SEED)
    torch.manual_seed(SEED)
    rows = load_brands()
    if args.limit_brands:
        rows = rows[: args.limit_brands]

    examples, n_brands = make_examples(rows, args.per_brand, rng)
    split = int(len(examples) * 0.9)
    train_ex, val_ex = examples[:split], examples[split:]
    x_train = torch.tensor([e[0] for e in train_ex], dtype=torch.float32)
    y_train = torch.tensor([[e[1]] for e in train_ex], dtype=torch.float32)
    x_val = torch.tensor([e[0] for e in val_ex], dtype=torch.float32)
    y_val = torch.tensor([[e[1]] for e in val_ex], dtype=torch.float32)

    model = _build_model(input_dim=x_train.shape[1])
    pos = y_train.sum().clamp(min=1)
    neg = len(y_train) - pos
    pos_weight = (neg / pos).clamp(max=20)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loader = DataLoader(TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)

    for epoch in range(args.epochs):
        model.train()
        total = 0.0
        for xb, yb in loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            total += loss.item() * len(xb)
        model.eval()
        with torch.no_grad():
            val_loss = loss_fn(model(x_val), y_val).item()
        print(f"epoch {epoch+1}/{args.epochs} train_loss={total/len(x_train):.4f} val_loss={val_loss:.4f}")

    keys = []
    by_key = {}
    for row in rows:
        k = brand_key(row.get("brand", ""))
        if k and k not in by_key:
            by_key[k] = row
            keys.append(k)
    metrics = evaluate(model, rows, keys, by_key, random.Random(SEED + 1), n_samples=min(1000, len(keys)))
    meta = {
        "model": "dgda_name_matcher_reranker",
        "input_dim": int(x_train.shape[1]),
        "brands": n_brands,
        "train_examples": len(train_ex),
        "val_examples": len(val_ex),
        "per_brand": args.per_brand,
        "epochs": args.epochs,
        "seed": SEED,
        "metrics": metrics,
        "note": "Synthetic noisy DGDA-name reranker; suggestions only, never auto-applied.",
    }

    out_model = ROOT / "models" / "dgda_name_matcher.pt"
    out_meta = ROOT / "models" / "dgda_name_matcher_meta.json"
    out_model.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict()}, out_model)
    out_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    print(f"saved {out_model}")
    print(f"saved {out_meta}")


if __name__ == "__main__":
    main()

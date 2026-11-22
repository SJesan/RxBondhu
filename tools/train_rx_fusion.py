"""Train a tiny char-CNN to canonicalise reader text into a verified brand.

Training data is SYNTHETIC: noisy spellings of the verified lexicon names.
No real prescription image or answer-key line is ever used for training.
The same script scores the RapidFuzz baseline and the model on (a) a held-out
synthetic test set and (b) a read-only real-line probe from local bake-off logs.
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rxbondhu.lexicon import load_brands, match_brand, normalise_name  # noqa: E402

SEED = 42
MAX_LEN = 40
CHARS = "abcdefghijklmnopqrstuvwxyz0123456789+ -"
UNKNOWN = "<UNKNOWN>"
PREFIXES = ["", "", "Tab ", "Cap ", "Syp ", "Inj ", "Supp ", "tab.", "cap "]
SUFFIXES = ["", "", " 5mg", " 500 mg", " 20", " 10 mg", " 100ml", " (500mg)", " 50"]
NOISE_WORDS = ["zzq", "xyl", "qwe", "mnb", "asd", "plk", "vfr", "tgb", "yhn"]


def noisy(brand: str, rng: random.Random) -> str:
    text = brand.lower()
    for _ in range(rng.randint(0, 2)):
        if not text:
            break
        pos = rng.randrange(len(text))
        action = rng.choice(("sub", "del", "ins", "swap"))
        if action == "sub":
            text = text[:pos] + rng.choice(CHARS.strip()) + text[pos + 1:]
        elif action == "del":
            text = text[:pos] + text[pos + 1:]
        elif action == "ins":
            text = text[:pos] + rng.choice(CHARS.strip()) + text[pos:]
        elif pos + 1 < len(text):
            text = text[:pos] + text[pos + 1] + text[pos] + text[pos + 2:]
    text = rng.choice(PREFIXES) + text + rng.choice(SUFFIXES)
    if rng.random() < 0.2:
        text = text.replace(" ", rng.choice((".", ",", "-")))
    return text


def unknown_text(rng: random.Random) -> str:
    return rng.choice(PREFIXES) + "".join(rng.choice(NOISE_WORDS) for _ in range(rng.randint(1, 2)))


def make_pairs(brands: list[str], per_brand: int, rng: random.Random) -> list[tuple[str, str]]:
    pairs = []
    for brand in brands:
        for _ in range(per_brand):
            pairs.append((noisy(brand, rng), brand))
    for _ in range(per_brand):
        pairs.append((unknown_text(rng), UNKNOWN))
    rng.shuffle(pairs)
    return pairs


def encode(text: str, char_to_idx: dict) -> list[int]:
    cleaned = re.sub(r"[^a-z0-9+ -]", " ", str(text).lower())[:MAX_LEN]
    return [char_to_idx.get(ch, 0) for ch in cleaned.ljust(MAX_LEN)]


def build_model(vocab_size: int, classes: int):
    import torch
    from torch import nn

    class CharCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.embed = nn.Embedding(vocab_size, 32, padding_idx=0)
            self.net = nn.Sequential(
                nn.Conv1d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool1d(2),
                nn.Conv1d(64, 64, 3, padding=1), nn.ReLU(),
                nn.AdaptiveMaxPool1d(1), nn.Flatten(),
                nn.Linear(64, 64), nn.ReLU(), nn.Dropout(0.2),
                nn.Linear(64, classes),
            )

        def forward(self, x):
            return self.net(self.embed(x).transpose(1, 2))

    return CharCNN()


def rapidfuzz_canonical(text: str, rows: list[dict]) -> str:
    hit = match_brand(text, rows, threshold=70)
    return hit["brand"] if hit else UNKNOWN


def canonical_truth(text: str) -> str:
    """Strip strength digits so 'Tab Napa 500' counts as brand 'napa'."""
    value = normalise_name(text)
    value = re.sub(r"\b\d+\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def real_probe(rows: list[dict], canonical_fn) -> dict:
    """Read-only probe on local bake-off prediction logs (never training)."""
    key_path = ROOT / "results" / "answer_key.csv"
    log_paths = sorted((ROOT / "results").glob("*_bakeoff_log.csv"))
    if not key_path.exists() or not log_paths:
        return {"available": False, "reason": "no local answer key or bake-off logs"}
    import csv

    truth = {}
    for row in csv.DictReader(key_path.open(encoding="utf-8-sig", newline="")):
        truth[row["image"]] = {canonical_truth(b) for b in row["true_brands"].split("|") if b.strip()}

    correct = total = 0
    per_log = {}
    for log in log_paths:
        hits = total_here = 0
        for row in csv.DictReader(log.open(encoding="utf-8-sig", newline="")):
            wanted = truth.get(row["image"], set())
            predicted = [canonical_fn(p.strip()) for p in row.get("predicted", "").split("|") if p.strip()]
            for want in wanted:
                total_here += 1
                if want in {canonical_truth(p) for p in predicted}:
                    hits += 1
        per_log[log.name] = {"correct": hits, "total": total_here}
        correct += hits
        total += total_here
    return {"available": True, "correct": correct, "total": total,
            "accuracy": round(correct / total, 4) if total else None, "per_log": per_log}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-brand", type=int, default=220)
    parser.add_argument("--epochs", type=int, default=12)
    args = parser.parse_args()

    import torch
    from torch import nn

    torch.manual_seed(SEED)
    rng = random.Random(SEED)
    brand_rows = load_brands()
    brands = [row["brand"] for row in brand_rows]
    classes = brands + [UNKNOWN]
    class_idx = {name: i for i, name in enumerate(classes)}
    char_to_idx = {ch: i + 1 for i, ch in enumerate(CHARS)}

    pairs = make_pairs(brands, args.per_brand, rng)
    split = int(len(pairs) * 0.8)
    train, test = pairs[:split], pairs[split:]

    def tensors(data):
        x = torch.tensor([encode(text, char_to_idx) for text, _ in data], dtype=torch.long)
        y = torch.tensor([class_idx[label] for _, label in data], dtype=torch.long)
        return x, y

    x_train, y_train = tensors(train)
    x_test, y_test = tensors(test)
    model = build_model(len(char_to_idx) + 1, len(classes))
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(args.epochs):
        model.train()
        for start in range(0, len(x_train), 64):
            optimizer.zero_grad()
            loss = loss_fn(model(x_train[start:start + 64]), y_train[start:start + 64])
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        synthetic_model_ok = int((model(x_test).argmax(1) == y_test).sum())
    synthetic_baseline_ok = sum(
        1 for text, label in test if rapidfuzz_canonical(text, brand_rows) == label
    )

    def model_canonical(text: str) -> str:
        with torch.no_grad():
            logits = model(torch.tensor([encode(text, char_to_idx)], dtype=torch.long))
            probs = torch.softmax(logits, dim=1)[0]
            best = int(probs.argmax())
        return classes[best] if float(probs[best]) >= 0.6 else UNKNOWN

    baseline_probe = real_probe(brand_rows, lambda text: rapidfuzz_canonical(text, brand_rows))
    model_probe = real_probe(brand_rows, model_canonical)

    metrics = {
        "seed": SEED,
        "brands": len(brands),
        "synthetic_pairs": {"train": len(train), "test": len(test)},
        "synthetic_test": {
            "rapidfuzz_correct": synthetic_baseline_ok,
            "char_cnn_correct": synthetic_model_ok,
            "total": len(test),
        },
        "real_line_probe": {"rapidfuzz": baseline_probe, "char_cnn": model_probe},
        "gate": {
            "beats_baseline_synthetic": synthetic_model_ok > synthetic_baseline_ok,
            "beats_baseline_real": bool(model_probe.get("accuracy") is not None
                                        and baseline_probe.get("accuracy") is not None
                                        and model_probe["accuracy"] > baseline_probe["accuracy"]),
        },
        "note": "Trained only on synthetic spellings of verified brand names; "
                "real-line probe is read-only evaluation.",
    }
    metrics["gate"]["pass"] = all(metrics["gate"].values())

    out = ROOT / "results" / "rx_fusion_metrics.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    model_path = ROOT / "models" / "rx_fusion.pt"
    torch.save({
        "state": model.state_dict(), "classes": classes,
        "char_to_idx": char_to_idx, "max_len": MAX_LEN,
    }, model_path)
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

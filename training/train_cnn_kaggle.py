"""Train RxBondhu's handwritten medicine-name CNN on Kaggle.

HOW TO USE (Kaggle notebook, GPU T4, Internet On):
1. Add the Kaggle dataset "Doctor's Handwritten Prescription BD" (mamun1113) as Input.
2. Put this file (and the whole repo) in a Kaggle notebook.
3. Run:  !python training/train_cnn_kaggle.py --input /kaggle/input --output /kaggle/working
4. Download rx_cnn.pt, labels.json, test_report.csv, training_summary.txt into models/.

The script deliberately does not assume one exact folder layout: it collects
annotation CSVs (image filename + medicine/generic columns), resolving bare
filenames against sibling folders, then falls back to a folder-per-class tree.
Run with --list-only first to see exactly what it found.
"""

import argparse
import csv
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

# Allow running this file directly from a cloned repo on Kaggle.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rxbondhu.image_transforms import letterbox  # noqa: E402

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
PATH_KEYS = ("image", "img", "file", "path")
BRAND_KEYS = ("medicine", "brand", "drug")
GENERIC_KEYS = ("generic",)
FALLBACK_LABEL_KEYS = ("label", "class", "target", "name")


def choose_column(headers: dict[str, str], keys, exclude=None):
    """Pick the first header containing any keyword, skipping an already-used column."""
    for lower, original in headers.items():
        if original == exclude:
            continue
        if any(key in lower for key in keys):
            return original
    return None


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def find_input_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    if Path("/kaggle/input").exists():
        return Path("/kaggle/input")
    local = Path(__file__).resolve().parents[1] / "data"
    return local if local.exists() else Path(".")


def image_name_index(directory: Path) -> dict[str, Path]:
    """Map every image basename beneath a folder to its resolved path."""
    index: dict[str, Path] = {}
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXT:
            index.setdefault(path.name, path)
    return index


def read_annotation_csv(csv_path: Path, labels_kind: str
                        ) -> tuple[list[tuple[Path, str]], list[str]]:
    """Read image/label pairs from one CSV.

    Handles both explicit paths and the common case where the CSV stores only
    a bare filename while the images live in a sibling/child folder.
    """
    with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        headers = {h.strip().lower(): h for h in (reader.fieldnames or [])}
        path_col = choose_column(headers, PATH_KEYS)
        wanted = GENERIC_KEYS if labels_kind == "generic" else BRAND_KEYS
        label_col = choose_column(headers, wanted, exclude=path_col)
        if label_col is None:
            label_col = choose_column(headers, FALLBACK_LABEL_KEYS, exclude=path_col)
        if not path_col or not label_col:
            return [], []
        by_name = image_name_index(csv_path.parent)
        pairs: list[tuple[Path, str]] = []
        for row in reader:
            rel = (row.get(path_col) or "").strip().strip('"')
            label = (row.get(label_col) or "").strip()
            if not rel or not label:
                continue
            direct = [csv_path.parent / rel, csv_path.parent.parent / rel]
            image = next((p for p in direct if p.exists()), None)
            if image is None:
                image = by_name.get(Path(rel).name)
            if image is not None:
                pairs.append((image, label))
        return pairs, [label_col]


def collect_samples(root: Path, labels_kind: str) -> tuple[list[Path], list[str], str]:
    """Return (image paths, labels, description of the source used)."""
    pairs: list[tuple[Path, str]] = []
    sources: list[str] = []
    seen: set[str] = set()
    csvs = [p for p in root.rglob("*.csv") if p.stat().st_size < 50_000_000]
    for csv_path in sorted(csvs):
        found, cols = read_annotation_csv(csv_path, labels_kind)
        if not found:
            continue
        sources.append(f"{csv_path.name}[{','.join(cols)}]")
        for path, label in found:
            key = str(path.resolve())
            if key not in seen:
                seen.add(key)
                pairs.append((path, label))
    if len(pairs) >= 20:
        return ([p for p, _ in pairs], [lbl for _, lbl in pairs],
                "CSV(s): " + ", ".join(sources))

    # Folder-per-class fallback: <root>/<split>/<class>/*.png etc.
    images, labels = [], []
    for image in root.rglob("*"):
        if image.suffix.lower() not in IMAGE_EXT:
            continue
        parent = image.parent.name
        grandparent = image.parent.parent.name
        # Ignore obvious split folder names as labels.
        if parent.lower() in {"train", "test", "val", "validation", "images", "word_images"}:
            label = grandparent
        else:
            label = parent
        if label and label.lower() not in {"images", "word_images", "data"}:
            images.append(image)
            labels.append(label)
    return images, labels, "folder-per-class image tree"


def stratified_split(images: list[Path], labels: list[str], seed: int,
                     train_frac: float = 2 / 3, val_frac: float = 1 / 6
                     ) -> tuple[list[int], list[int], list[int]]:
    """Split per class so every class appears in train/val/test when possible."""
    rng = random.Random(seed)
    by_class: dict[str, list[int]] = {}
    for idx, label in enumerate(labels):
        by_class.setdefault(label, []).append(idx)
    train, val, test = [], [], []
    for indices in by_class.values():
        rng.shuffle(indices)
        n = len(indices)
        n_train = max(1, int(round(n * train_frac)))
        n_val = max(1, int(round(n * val_frac)))
        if n_train + n_val >= n:
            n_train, n_val = max(1, n - 2), 1
        train.extend(indices[:n_train])
        val.extend(indices[n_train:n_train + n_val])
        test.extend(indices[n_train + n_val:])
    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


class WordDataset(Dataset):
    def __init__(self, images: list[Path], labels: list[int], transform):
        self.images = images
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, idx: int):
        image = Image.open(self.images[idx]).convert("RGB")
        return self.transform(image), self.labels[idx], str(self.images[idx])


def build_transforms(img_h: int, img_w: int, train: bool):
    steps: list = [transforms.Lambda(lambda im: letterbox(im, (img_h, img_w)))]
    if train:
        steps.append(transforms.RandomApply([transforms.RandomAffine(
            degrees=8, translate=(0.05, 0.05), scale=(0.92, 1.08),
            shear=4, fill=255)], p=0.6))
    steps.extend([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return transforms.Compose(steps)


def build_model(num_classes: int, device: torch.device) -> nn.Module:
    try:
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        model = models.efficientnet_b0(weights=weights)
    except Exception as exc:  # no internet -> train from scratch (still a real CNN)
        print(f"ImageNet weights unavailable ({exc}); using random initialisation.")
        model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model.to(device)


def run_one_epoch(model, loader, criterion, optimiser, device, training: bool):
    model.train(training)
    total_loss, correct, count = 0.0, 0, 0
    context = torch.enable_grad() if training else torch.no_grad()
    with context:
        for images, labels, _ in loader:
            images, labels = images.to(device), labels.to(device)
            if training:
                optimiser.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                outputs = model(images)
                loss = criterion(outputs, labels)
            if training:
                loss.backward()
                optimiser.step()
            total_loss += float(loss.item()) * len(labels)
            correct += int((outputs.argmax(1) == labels).sum().item())
            count += len(labels)
    return total_loss / max(count, 1), correct / max(count, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None, help="Dataset input folder (default: /kaggle/input)")
    parser.add_argument("--output", default="/kaggle/working" if os.path.exists("/kaggle/working") else "models")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--img-h", type=int, default=128)
    parser.add_argument("--img-w", type=int, default=384)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--labels-kind", choices=("brand", "generic"), default="brand",
                        help="Which annotation column to train on when the CSV has both.")
    parser.add_argument("--list-only", action="store_true", help="Inspect data and exit.")
    args = parser.parse_args()

    seed_all(args.seed)
    root = find_input_root(args.input)
    images, labels, source = collect_samples(root, args.labels_kind)
    print(f"Input root : {root}")
    print(f"Source     : {source}")
    print(f"Samples    : {len(images)}  Classes: {len(set(labels))}")
    if not images:
        print("ERROR: no labelled images found. Use --input /path/to/dataset or --list-only.")
        return 2
    if len(set(labels)) < 2:
        print("ERROR: need at least two classes.")
        return 2
    counts = Counter(labels)
    print("Top classes:", counts.most_common(8))
    if args.list_only:
        return 0

    class_names = sorted(set(labels))
    class_to_idx = {name: i for i, name in enumerate(class_names)}
    y = [class_to_idx[label] for label in labels]
    tr, va, te = stratified_split(images, y, args.seed)
    print(f"Split      : train={len(tr)} val={len(va)} test={len(te)}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device     : {device}")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    train_ds = WordDataset([images[i] for i in tr], [y[i] for i in tr],
                           build_transforms(args.img_h, args.img_w, True))
    val_ds = WordDataset([images[i] for i in va], [y[i] for i in va],
                         build_transforms(args.img_h, args.img_w, False))
    test_ds = WordDataset([images[i] for i in te], [y[i] for i in te],
                          build_transforms(args.img_h, args.img_w, False))
    workers = 2 if os.name != "nt" else 0
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=workers)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=workers)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=workers)

    model = build_model(len(class_names), device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimiser = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimiser, T_max=args.epochs)

    best_val, best_state = -1.0, None
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_one_epoch(model, train_loader, criterion, optimiser, device, True)
        val_loss, val_acc = run_one_epoch(model, val_loader, criterion, optimiser, device, False)
        scheduler.step()
        print(f"Epoch {epoch:02d}/{args.epochs}  train {train_loss:.4f}/{train_acc:.3f}  "
              f"val {val_loss:.4f}/{val_acc:.3f}")
        if val_acc > best_val:
            best_val = val_acc
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    if best_state is not None:
        model.load_state_dict(best_state)
    print(f"Best val accuracy: {best_val:.4f}")

    model.eval()
    rows, correct_total = [], 0
    with torch.no_grad():
        for images_batch, labels_batch, paths in test_loader:
            images_batch = images_batch.to(device)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                outputs = model(images_batch)
            probs = torch.softmax(outputs.float(), dim=1)
            for path, true_idx, prob in zip(paths, labels_batch.cpu().tolist(), probs.cpu()):
                pred_idx = int(prob.argmax().item())
                conf = float(prob[pred_idx].item())
                correct_total += int(pred_idx == true_idx)
                rows.append({
                    "image": path,
                    "true": class_names[true_idx],
                    "predicted": class_names[pred_idx],
                    "confidence": round(conf, 4),
                    "correct": int(pred_idx == true_idx),
                })
    test_acc = correct_total / max(len(rows), 1)
    print(f"TEST ACCURACY: {test_acc:.4f} ({correct_total}/{len(rows)})")

    torch.save({"state_dict": model.state_dict(), "class_names": class_names,
                "img_size": [args.img_h, args.img_w], "arch": "efficientnet_b0"},
               out / "rx_cnn.pt")
    (out / "labels.json").write_text(json.dumps(
        {"arch": "efficientnet_b0", "img_size": [args.img_h, args.img_w],
         "class_names": class_names, "val_accuracy": round(best_val, 4),
         "test_accuracy": round(test_acc, 4), "source": source,
         "train": len(tr), "val": len(va), "test": len(te),
         "labels_kind": args.labels_kind, "seed": args.seed},
        indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "test_report.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["image", "true", "predicted", "confidence", "correct"])
        writer.writeheader()
        writer.writerows(rows)

    # Keep the exact environment visible to judges.
    (out / "training_summary.txt").write_text(
        f"source={source}\nsamples={len(images)}\nclasses={len(class_names)}\n"
        f"img_size={args.img_h}x{args.img_w}\n"
        f"split={len(tr)}/{len(va)}/{len(te)}\nepochs={args.epochs}\nbatch={args.batch_size}\n"
        f"best_val_accuracy={best_val:.4f}\ntest_accuracy={test_acc:.4f}\n"
        f"torch={torch.__version__}\nseed={args.seed}\n", encoding="utf-8")
    print(f"Saved model, labels.json, test_report.csv and training_summary.txt to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

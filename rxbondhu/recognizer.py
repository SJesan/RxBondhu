"""Inference wrapper for the handwriting CNN we train ourselves.

The heavy libraries are imported lazily so the rest of the app can be imported
and unit-tested before torch is installed. If the trained file is missing,
`available()` returns False and the app falls back to Gemini-only mode.
"""

import json
import os
from pathlib import Path

from .image_transforms import letterbox

_MODEL = None
_LABELS = None
_TRIED = False

DEFAULT_MODEL = Path(__file__).resolve().parents[1] / "models" / "rx_cnn.pt"
DEFAULT_LABELS = Path(__file__).resolve().parents[1] / "models" / "labels.json"


def available(model_path=DEFAULT_MODEL, labels_path=DEFAULT_LABELS) -> bool:
    """Whether a trained CNN checkpoint exists on disk."""
    return Path(model_path).exists() and Path(labels_path).exists()


def _load(model_path=DEFAULT_MODEL, labels_path=DEFAULT_LABELS, device=None):
    global _MODEL, _LABELS, _TRIED
    if _TRIED and _MODEL is not None:
        return _MODEL, _LABELS, device or "cpu"
    _TRIED = True
    if not available(model_path, labels_path):
        return None, None, device or "cpu"

    import torch
    from torch import nn
    from torchvision import models, transforms

    labels = json.loads(Path(labels_path).read_text(encoding="utf-8"))
    names = labels["class_names"]
    raw_size = labels.get("img_size") or labels.get("image_size") or 224
    if isinstance(raw_size, (list, tuple)):
        size = (int(raw_size[0]), int(raw_size[1]))
    else:
        side = int(raw_size)
        size = (side, side)
    arch = labels.get("arch", "efficientnet_b0")

    model = getattr(models, arch)(weights=None)
    if isinstance(getattr(model, "classifier", None), nn.Sequential):
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, len(names))
    elif hasattr(model, "fc"):
        model.fc = nn.Linear(model.fc.in_features, len(names))
    else:
        raise RuntimeError(f"Unsupported CNN architecture: {arch}")

    checkpoint = torch.load(str(model_path), map_location="cpu", weights_only=False)
    state = checkpoint.get("state_dict", checkpoint)
    model.load_state_dict(state)
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model.to(dev)
    model.eval()

    transform = transforms.Compose([
        transforms.Lambda(lambda im: letterbox(im, size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    _MODEL, _LABELS = (model, transform, names, dev), labels
    return _MODEL, _LABELS, dev


def predict_words(images, top_k: int = 3,
                  model_path=DEFAULT_MODEL, labels_path=DEFAULT_LABELS) -> list[list[dict]]:
    """Predict brand names for a list of PIL word images.

    Returns one list per image, each entry {"brand": str, "confidence": float}.
    """
    bundle, labels, dev = _load(model_path, labels_path)
    if bundle is None:
        return [[] for _ in images]
    model, transform, names, device = bundle

    import torch

    tensors = [transform(img.convert("RGB")) for img in images]
    if not tensors:
        return []
    batch = torch.stack(tensors).to(device)
    with torch.no_grad():
        logits = model(batch)
        probs = torch.softmax(logits.float(), dim=1)
    results = []
    for row in probs.cpu():
        order = torch.topk(row, min(top_k, len(names))).indices.tolist()
        results.append([
            {"brand": names[i], "confidence": round(float(row[i].item()), 4)} for i in order
        ])
    return results


def predict_word(image, top_k: int = 3,
                 model_path=DEFAULT_MODEL, labels_path=DEFAULT_LABELS) -> dict:
    """Convenience wrapper for one crop; shape expected by fusion.fuse()."""
    hits = predict_words([image], top_k=top_k, model_path=model_path, labels_path=labels_path)
    if not hits or not hits[0]:
        return {"brand": "", "confidence": 0.0, "top": []}
    top = hits[0]
    return {"brand": top[0]["brand"], "confidence": top[0]["confidence"], "top": top}


def model_info() -> dict:
    """Metadata for the README / about panel."""
    if not available():
        return {"available": False, "reason": "models/rx_cnn.pt or labels.json missing"}
    try:
        return dict(json.loads(Path(DEFAULT_LABELS).read_text(encoding="utf-8")),
                    available=True)
    except Exception as exc:
        return {"available": False, "reason": str(exc)}

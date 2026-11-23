"""Pure helpers for multi-prescription (2-3 images) sessions.

Nothing here changes fusion, thresholds, the lexicon or DGDA loading. It only
keys a cached reading by sha256(image bytes + crop box), reads prescriptions
strictly one at a time with per-image error isolation, keeps each prescription
as its own group until the user confirms, and adds a non-blocking duplicate
warning after the existing schedule check has run.
"""

import hashlib
import io
import json

from . import pipeline
from .bangla import digits
from .safety import generic_key
from .vlm import friendly_error

EMPTY_MESSAGE = ("কিছু পাওয়া যায়নি — ওষুধের লাইনের চারপাশে টাইট ক্রপ করে আবার চেষ্টা করুন / "
                 "Nothing found — try a tighter crop around the medicine lines")


def _box_tuple(box):
    """Deterministic JSON-safe form of a cropper box (dict or tuple)."""
    if not box:
        return None
    if isinstance(box, dict):
        known = [key for key in ("left", "top", "width", "height") if key in box]
        if known:
            return tuple((key, int(round(float(box[key])))) for key in known)
        return tuple(sorted((str(key), int(round(float(value))))
                            for key, value in box.items()))
    return tuple(int(round(float(value))) for value in box)


def image_digest(image) -> bytes:
    """PNG bytes of the pixels, independent of the original file format."""
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def crop_cache_key(image, box) -> str:
    """sha256 of (image bytes + crop box): one cached reading per exact crop."""
    payload = (image_digest(image)
               + json.dumps(_box_tuple(box), sort_keys=True).encode("utf-8"))
    return hashlib.sha256(payload).hexdigest()


def read_all(sources, cache, *, reader=None, skip_vlm=False, progress=None):
    """Read prescriptions sequentially; one failure never stops the rest.

    Each source is ``{"image": full photo, "crop": cropped area, "box": box}``.
    ``cache`` is a mutable dict (session state) keyed by ``crop_cache_key``.
    ``skip_vlm`` may be a callable so the quota guard is re-checked per image.
    Returns one group per prescription, never a merged list.
    """
    reader = reader or pipeline.analyse
    groups = []
    total = len(sources)
    for number, source in enumerate(sources, start=1):
        if progress:
            progress(number, total)
        try:
            key = crop_cache_key(source["image"], source.get("box"))
            cached = key in cache
            skipped = skip_vlm() if callable(skip_vlm) else bool(skip_vlm)
            if cached:
                analysis = dict(cache[key])
            else:
                analysis = reader(source["crop"], full_image=source["image"],
                                  skip_vlm=skipped)
                analysis.pop("images", None)
                cache[key] = analysis
            items = list(analysis.get("items") or [])
            groups.append({
                "number": number,
                "analysis": analysis,
                "error": None if items else EMPTY_MESSAGE,
                "items": items,
                "from_cache": cached,
                "vlm_used": bool(not cached and not skipped),
            })
        except Exception as exc:
            reason = friendly_error(exc, "reader")
            groups.append({
                "number": number,
                "analysis": None,
                "error": (f"প্রেসক্রিপশন {digits(number)} পড়া যায়নি / "
                          f"Prescription {number} could not be read: {reason}. "
                          "অন্য ছবিগুলো পড়া হয়েছে / Other images were read."),
                "items": [],
                "from_cache": False,
                "vlm_used": False,
            })
    return groups


def count_text(n_prescriptions: int, n_medicines: int) -> str:
    """Small Bangla-first count shown above the merged confirmation."""
    return (f"{digits(n_prescriptions)} প্রেসক্রিপশন · "
            f"{digits(n_medicines)} ওষুধ নিশ্চিত / "
            f"{n_prescriptions} prescriptions · {n_medicines} medicines confirmed")


def cross_prescription_warning(rows: list[dict]) -> list[str]:
    """Additive, non-blocking warning for a generic shared across prescriptions.

    The existing duplicate-generic check still runs on the merged list first;
    this only names the prescriptions so the user can spot a cross-script
    repeat. It never changes a badge, a colour or a safety decision.
    """
    by_generic = {}
    for row in rows or []:
        name = str(row.get("name") or "").strip()
        if not name or name.startswith("—"):
            continue
        generic = str(row.get("generic") or "").strip()
        if not generic:
            continue
        try:
            number = int(row.get("prescription"))
        except (TypeError, ValueError):
            continue
        entry = by_generic.setdefault(generic_key(generic),
                                      {"label": generic, "numbers": set()})
        entry["label"] = generic
        entry["numbers"].add(number)

    warnings = []
    for entry in by_generic.values():
        numbers = sorted(entry["numbers"])
        if len(numbers) < 2:
            continue
        if len(numbers) == 2:
            labels = f"Prescription {numbers[0]} ও {numbers[1]}"
        else:
            labels = ", ".join(f"Prescription {number}" for number in numbers)
        warnings.append(
            f"একাধিক প্রেসক্রিপশনে একই জেনেরিক আছে: {entry['label']} ({labels}) — "
            "ডাবল ডোজ না হয় ফার্মাসিস্টকে জিজ্ঞাসা করুন / "
            f"Same generic in multiple prescriptions: {entry['label']} ({labels}) "
            "— check for double dose with your pharmacist."
        )
    return warnings

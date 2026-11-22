"""End-to-end core pipeline: crop -> two readers -> fusion -> schedule.

The Streamlit app calls analyse() for screen 2 and build_schedule() after the
user has reviewed and confirmed everything on screen 3. Nothing reaches the
schedule without the user's confirmation.

Reading is now **line based**: Gemini decides how many medicine lines exist,
and every review row is one medicine line — not one segmented word. This
prevents a full-page photo from producing 30 meaningless ``Az`` rows.
"""

from .dose_parser import parse
from .fusion import fuse
from .safety import duplicate_warning, has_red

MAX_LINES = 12


def _sort_words(words: list[dict]) -> list[int]:
    """Indices of word crops in reading order (top-to-bottom, left-to-right)."""
    return sorted(range(len(words)), key=lambda i: (words[i]["box"][1], words[i]["box"][0]))


def _group_words_by_y(words: list[dict], max_lines: int) -> list[list[int]]:
    """Fallback grouping when Gemini is offline: cluster words by vertical position."""
    if not words:
        return []
    groups = []
    for idx in _sort_words(words):
        x, y, w, h = words[idx]["box"]
        centre = y + h / 2
        if groups and abs(centre - groups[-1]["centre"]) <= max(14, groups[-1]["height"] * 0.75):
            group = groups[-1]
            size = len(group["indices"])
            group["centre"] = (group["centre"] * size + centre) / (size + 1)
            group["height"] = max(group["height"], h)
            group["indices"].append(idx)
        else:
            groups.append({"centre": centre, "height": h, "indices": [idx]})
    return [group["indices"] for group in groups[:max_lines]]


def _assign_words_to_lines(words: list[dict], line_count: int) -> list[list[int]]:
    """Spread CNN word crops across the lines Gemini found, in reading order."""
    if not words:
        return [[] for _ in range(line_count)]
    order = _sort_words(words)
    groups: list[list[int]] = [[] for _ in range(line_count)]
    for position, idx in enumerate(order):
        target = min(line_count - 1, position * line_count // len(order))
        groups[target].append(idx)
    return groups


def _best_cnn(cnn_hits: list[list[dict]], indices: list[int]) -> dict:
    """Highest-confidence CNN reading inside one medicine line."""
    best = None
    for idx in indices:
        hits = cnn_hits[idx] if idx < len(cnn_hits) else []
        if not hits:
            continue
        head = hits[0]
        confidence = float(head.get("confidence") or 0.0)
        if best is None or confidence > best["confidence"]:
            best = {"brand": str(head.get("brand") or ""), "confidence": confidence}
    return best or {"brand": "", "confidence": 0.0}


def _rescaled_line_boxes(image, line_boxes: list[dict]) -> list[dict]:
    """segment() boxes are in prepared pixels; convert them to source pixels."""
    from . import segmentation

    scale = 2 if image.width < segmentation.UPSCALE_BELOW_WIDTH else 1
    if scale == 1:
        return line_boxes
    return [{"box": tuple(int(round(value / scale)) for value in item["box"])}
            for item in line_boxes]


def _line_crops(image, line_count: int, line_boxes: list[dict]) -> tuple[list, list[tuple]]:
    """One crop per medicine line; fall back to the whole crop when uncertain."""
    full = image.convert("RGB")
    width, height = full.size
    candidates = []
    for item in line_boxes or []:
        x, y, w, h = item["box"]
        if w >= max(40, h) and h >= 8:  # a line is wider than it is tall
            candidates.append((x, y, w, h))
    candidates.sort(key=lambda box: (box[1], box[0]))

    crops, boxes = [], []
    for index in range(line_count):
        if index < len(candidates):
            x, y, w, h = candidates[index]
            pad = 4
            x0, y0 = max(0, x - pad), max(0, y - pad)
            x1, y1 = min(width, x + w + pad), min(height, y + h + pad)
        else:
            x0, y0, x1, y1 = 0, 0, width, height
        crops.append(full.crop((x0, y0, x1, y1)))
        boxes.append((x0, y0, x1 - x0, y1 - y0))
    return crops, boxes


def analyse(image, max_words: int = 30, max_lines: int = MAX_LINES,
            full_image=None, skip_vlm: bool = False, resize_vlm: bool = True) -> dict:
    """Read one cropped medicine area with both AI models, one row per line.

    Gemini receives the *full* photo when provided — it reads surrounding
    context better, while our CNN reads the cropped word images. The full
    image is downscaled to 1600 px on the long side before upload to save quota.

    Set ``skip_vlm=True`` for the session quota guard: no API call is made and
    the UI honestly reports CNN-only mode; lines are then grouped by geometry.
    """
    from . import recognizer, segmentation, vlm

    words = segmentation.segment(image)[:max_words]
    cnn_hits = recognizer.predict_words([w["image"] for w in words]) if words else []
    if skip_vlm:
        gemini = {"lines": [], "raw": "",
                  "error": "Session reading limit reached - CNN-only mode",
                  "model": "offline"}
    else:
        sent = full_image if full_image is not None else image
        if resize_vlm and sent is not None:
            sent = sent.copy()
            sent.thumbnail((1600, 1600))
        gemini = vlm.read(sent)

    vlm_lines = gemini["lines"] or []
    line_boxes = _rescaled_line_boxes(image, segmentation.segment_lines(image))
    if vlm_lines:
        line_count = min(len(vlm_lines), max_lines)
        line_inputs = vlm_lines[:line_count]
        assignments = _assign_words_to_lines(words, line_count)
    else:
        # Gemini offline: keep the old geometric grouping as a safe fallback.
        assignments = _group_words_by_y(words, max_lines)
        line_count = len(assignments)
        line_inputs = [{} for _ in range(line_count)]

    line_crops, boxes = _line_crops(image, line_count, line_boxes)
    items = []
    line_cnn_preds = []
    for index in range(line_count):
        cnn = _best_cnn(cnn_hits, assignments[index])
        vlm_line = line_inputs[index]
        result = fuse(cnn, vlm_line.get("medicine", ""))
        items.append({
            **result,
            "dose_text": vlm_line.get("dose", ""),
            "box": boxes[index],
            "index": index,
        })
        line_cnn_preds.append(cnn["brand"])

    return {
        "items": items,
        "images": line_crops,
        "vlm_raw": gemini["raw"],
        "vlm_error": gemini["error"],
        "vlm_model": gemini["model"],
        "vlm_lines": vlm_lines[:line_count],
        "cnn_available": recognizer.available(),
        "word_count": len(words),
        "line_count": line_count,
        "line_cnn_preds": line_cnn_preds,
    }


def build_schedule(confirmed: list[dict]) -> dict:
    """Turn user-confirmed rows into a Bangla-ready schedule plus warnings.

    Each confirmed row needs: name, generic, dose (string), colour (optional).
    """
    medicines = []
    for row in confirmed or []:
        name = str(row.get("name") or row.get("brand") or "").strip()
        if not name:
            continue
        parsed = parse(str(row.get("dose") or ""))
        medicines.append({
            "name": name,
            "generic": str(row.get("generic") or "").strip(),
            "dose": parsed,
            "colour": str(row.get("colour") or "GREEN").upper(),
        })

    warnings = duplicate_warning(medicines)
    if has_red(confirmed or []):
        warnings.append("Some lines were uncertain — please confirm them with your pharmacist.")
    for med in medicines:
        warnings.extend(med["dose"]["warnings"])

    return {"medicines": medicines, "warnings": warnings}

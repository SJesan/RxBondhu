"""Split a cropped prescription photo into word images for the two readers.

Uses OpenCV thresholding + morphology: first group words into lines, then split
each line into words. Everything is returned as PIL crops with original boxes
so the review screen can highlight where a reading came from.
"""

from pathlib import Path


def _cv():
    try:
        import cv2
        return cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python-headless is required for segmentation") from exc


def _prepare(image):
    import numpy as np
    cv2 = _cv()
    rgb = np.asarray(image.convert("RGB"))
    if rgb.shape[1] < 600:  # upscale small crops for more reliable contours
        scale = 2
        rgb = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 11)
    return rgb, binary


def _contour_boxes(binary, kernel, min_w, min_h):
    cv2 = _cv()
    joined = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(joined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w >= min_w and h >= min_h:
            boxes.append((x, y, w, h))
    return boxes


def segment(image, min_word_w: int = 18, min_word_h: int = 14) -> list[dict]:
    """Return word crops sorted in reading order.

    Each item: {"image": PIL.Image, "box": (x, y, w, h)} in *prepared* pixels.
    """
    from PIL import Image
    cv2 = _cv()
    rgb, binary = _prepare(image)
    height, width = binary.shape[:2]

    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(15, width // 40), 3))
    lines = _contour_boxes(binary, line_kernel, min_w=max(40, width // 8), min_h=min_word_h)
    if not lines:
        # Fallback: treat the whole crop as one line.
        lines = [(0, 0, width, height)]

    lines.sort(key=lambda b: (b[1], b[0]))
    merged = []
    for x, y, w, h in lines:
        if merged and y <= merged[-1][1] + max(8, merged[-1][3] // 2):
            px, py, pw, ph = merged[-1]
            merged[-1] = (min(px, x), min(py, y),
                          max(px + pw, x + w) - min(px, x),
                          max(py + ph, y + h) - min(py, y))
        else:
            merged.append((x, y, w, h))

    words = []
    for lx, ly, lw, lh in merged:
        # Pad slightly so ascenders/descenders are not clipped.
        pad = 4
        x0, y0 = max(0, lx - pad), max(0, ly - pad)
        x1, y1 = min(width, lx + lw + pad), min(height, ly + lh + pad)
        line_binary = binary[y0:y1, x0:x1]
        word_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        boxes = _contour_boxes(line_binary, word_kernel, min_word_w, min_word_h)
        boxes.sort(key=lambda b: b[0])
        for wx, wy, ww, wh in boxes:
            crop = rgb[y0 + wy:y0 + wy + wh, x0 + wx:x0 + wx + ww]
            if crop.size == 0:
                continue
            words.append({"image": Image.fromarray(crop),
                          "box": (x0 + wx, y0 + wy, ww, wh)})
    return words


def segment_lines(image) -> list[dict]:
    """Return whole-line crops (useful for Gemini, which reads context better)."""
    from PIL import Image
    cv2 = _cv()
    rgb, binary = _prepare(image)
    height, width = binary.shape[:2]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(15, width // 40), 3))
    boxes = _contour_boxes(binary, kernel, max(40, width // 8), min_word_h=14)
    boxes.sort(key=lambda b: b[1])
    result = []
    for x, y, w, h in boxes:
        pad = 5
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(width, x + w + pad), min(height, y + h + pad)
        result.append({"image": Image.fromarray(rgb[y0:y1, x0:x1]),
                       "box": (x0, y0, x1 - x0, y1 - y0)})
    return result or [{"image": image.convert("RGB"), "box": (0, 0, width, height)}]


def save_debug(image, output: str | Path) -> Path:
    """Optional: draw boxes to inspect segmentation quality (not used by app)."""
    from PIL import ImageDraw
    debug = image.convert("RGB").copy()
    draw = ImageDraw.Draw(debug)
    for item in segment(image):
        x, y, w, h = item["box"]
        draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    debug.save(path)
    return path

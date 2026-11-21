"""Optional photo enhancement for phone-captured prescriptions.

Every step is testable and switchable. We do NOT silently change the app's
default pipeline: enhancements are measured on real handwriting first with
``tools/evaluate_handwritten.py --preprocess`` and an ablation table.

Steps: shadow removal -> CLAHE -> deskew -> auto-crop to ink.
"""

import numpy as np
from PIL import Image

MARGIN_PX = 8


def _cv():
    try:
        import cv2
        return cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python-headless is required for preprocessing") from exc


def _gray(image: Image.Image) -> np.ndarray:
    cv2 = _cv()
    return cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2GRAY)


def _to_pil(gray: np.ndarray) -> Image.Image:
    return Image.fromarray(np.asarray(gray, dtype=np.uint8)).convert("RGB")


def shadow_removal(image: Image.Image) -> np.ndarray:
    """Divide by a blurred background estimate to even out phone lighting."""
    cv2 = _cv()
    gray = _gray(image)
    background = cv2.GaussianBlur(gray, (0, 0), sigmaX=15)
    return cv2.divide(gray, background, scale=255)


def contrast(gray: np.ndarray) -> np.ndarray:
    """CLAHE on a grayscale image to lift pale ink."""
    cv2 = _cv()
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)


def deskew(gray: np.ndarray) -> np.ndarray:
    """Rotate by the ink's dominant angle. No-op for blank or extreme images."""
    cv2 = _cv()
    inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    points = cv2.findNonZero(inv)
    if points is None:
        return gray
    angle = cv2.minAreaRect(points)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.5 or abs(angle) > 20:
        return gray
    h, w = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=255)


def auto_crop(gray: np.ndarray, margin: int = MARGIN_PX) -> np.ndarray:
    """Crop to the ink bounding box plus a small white margin."""
    cv2 = _cv()
    inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    points = cv2.findNonZero(inv)
    if points is None:
        return gray
    x, y, w, h = cv2.boundingRect(points)
    x0, y0 = max(0, x - margin), max(0, y - margin)
    x1, y1 = min(gray.shape[1], x + w + margin), min(gray.shape[0], y + h + margin)
    cropped = gray[y0:y1, x0:x1]
    return cropped if cropped.size else gray


def enhance_for_segmentation(image: Image.Image) -> Image.Image:
    """Full enhancement chain, returned as RGB for the existing segmenter."""
    gray = contrast(shadow_removal(image))
    return _to_pil(auto_crop(deskew(gray)))


def preprocess_variants(image: Image.Image) -> dict[str, Image.Image]:
    """Cumulative variants for an honest before/after ablation table."""
    original = image.convert("RGB")
    balanced = shadow_removal(original)
    lifted = contrast(balanced)
    straight = deskew(lifted)
    return {
        "none": original,
        "shadow": _to_pil(balanced),
        "clahe": _to_pil(lifted),
        "deskew": _to_pil(straight),
        "all": _to_pil(auto_crop(straight)),
    }

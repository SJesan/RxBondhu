"""Small local Streamlit component for a phone's rear camera.

No CDN, no cloud component, no data leaves the browser until capture. If the
browser blocks camera access, the app keeps the upload fallback.
"""

import base64
import io
from pathlib import Path

from PIL import Image

_COMPONENT = None


def _component():
    global _COMPONENT
    if _COMPONENT is None:
        import streamlit.components.v1 as components
        path = Path(__file__).resolve().parents[1] / "static" / "camera"
        _COMPONENT = components.declare_component("rxbondhu_camera", path=str(path))
    return _COMPONENT


def decode_capture(value: str | None) -> Image.Image | None:
    """Turn the component's base64 JPEG into a PIL image, or None if invalid."""
    if not value:
        return None
    try:
        raw = base64.b64decode(value)
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def capture() -> Image.Image | None:
    """Render the camera widget; return a PIL image only after Capture is pressed."""
    try:
        value = _component()()
    except Exception:
        return None
    return decode_capture(value)

"""Shared image preparation for RxBondhu's CNN.

Keeping this in one place guarantees that Kaggle training and local inference
feed the network identical pixels. No third-party project code is used here.
"""

from PIL import Image

try:
    _BICUBIC = Image.Resampling.BICUBIC
except AttributeError:  # Pillow < 9.1
    _BICUBIC = Image.BICUBIC


def letterbox(image, size, fill=255):
    """Resize an image without distortion, then pad it to ``(height, width)``."""
    height, width = int(size[0]), int(size[1])
    source = image.convert("RGB")
    src_w, src_h = source.size
    scale = min(width / src_w, height / src_h)
    new_w = max(1, round(src_w * scale))
    new_h = max(1, round(src_h * scale))
    if (new_w, new_h) != (src_w, src_h):
        source = source.resize((new_w, new_h), _BICUBIC)
    canvas = Image.new("RGB", (width, height), (fill, fill, fill))
    canvas.paste(source, ((width - new_w) // 2, (height - new_h) // 2))
    return canvas

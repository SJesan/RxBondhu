"""Preprocessing smoke tests: shape, deterministic behaviour, no crashes."""

import os
import sys
import unittest

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu import preprocess, segmentation  # noqa: E402


def sample_image():
    image = Image.new("RGB", (700, 220), "white")
    draw = ImageDraw.Draw(image)
    # Uneven background to exercise shadow removal.
    for x in range(700):
        shade = int(235 - 45 * x / 700)
        draw.line((x, 0, x, 220), fill=(shade, shade, shade))
    draw.text((40, 35), "Napa 1+0+1", fill="black")
    draw.text((40, 125), "Maxpro BD", fill="black")
    return image


class TestPreprocess(unittest.TestCase):
    def test_variants_are_rgb_and_nonempty(self):
        variants = preprocess.preprocess_variants(sample_image())
        self.assertEqual(set(variants), {"none", "shadow", "clahe", "deskew", "all"})
        for name, image in variants.items():
            self.assertEqual(image.mode, "RGB", name)
            self.assertGreater(image.width, 0, name)
            self.assertGreater(image.height, 0, name)

    def test_enhance_keeps_words_segmentable(self):
        enhanced = preprocess.enhance_for_segmentation(sample_image())
        words = segmentation.segment(enhanced)
        self.assertGreaterEqual(len(words), 2)

    def test_auto_crop_removes_blank_border(self):
        gray = np.full((200, 500), 255, dtype=np.uint8)
        gray[70:120, 100:300] = 20
        cropped = preprocess.auto_crop(gray)
        self.assertLess(cropped.shape[1], 500)
        self.assertGreater(cropped.shape[1], 180)


if __name__ == "__main__":
    unittest.main(verbosity=2)

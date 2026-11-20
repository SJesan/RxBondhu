"""Segmentation smoke test using a synthetic handwritten-looking image."""

import os
import sys
import unittest

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu import segmentation  # noqa: E402


def make_image():
    image = Image.new("RGB", (700, 220), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except OSError:
        font = ImageFont.load_default()
    draw.text((30, 25), "Napa 1+0+1", fill="black", font=font)
    draw.text((30, 120), "Maxpro BD", fill="black", font=font)
    return image


@unittest.skipUnless(segmentation is not None, "segmentation unavailable")
class TestSegmentation(unittest.TestCase):
    def test_finds_words_in_two_lines(self):
        words = segmentation.segment(make_image())
        self.assertGreaterEqual(len(words), 4)
        self.assertTrue(all(w["image"].width > 0 for w in words))

    def test_lines(self):
        lines = segmentation.segment_lines(make_image())
        self.assertGreaterEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

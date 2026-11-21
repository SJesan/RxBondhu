"""Segmentation smoke test using a synthetic handwritten-looking image."""

import os
import sys
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu import segmentation  # noqa: E402


def make_image():
    """Font-independent word blobs so the test behaves the same on Linux/Windows."""
    image = Image.new("RGB", (700, 220), "white")
    draw = ImageDraw.Draw(image)
    for y in (30, 125):
        for x in (30, 150, 280, 420):
            draw.rectangle([x, y, x + 85, y + 42], fill="black")
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

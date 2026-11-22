"""Pure helpers for the external localization runner (no network, no dataset)."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from PIL import Image  # noqa: E402

from evaluate_localization import iou, parse_yolo, to_original  # noqa: E402


class TestLocalization(unittest.TestCase):
    def test_iou_identical_disjoint_partial(self):
        self.assertEqual(iou((0, 0, 10, 10), (0, 0, 10, 10)), 1.0)
        self.assertEqual(iou((0, 0, 10, 10), (20, 20, 10, 10)), 0.0)
        self.assertAlmostEqual(iou((0, 0, 10, 10), (5, 0, 10, 10)), 1 / 3)

    def test_parse_yolo_converts_normalised_boxes(self):
        boxes = parse_yolo("1 0.5 0.5 0.2 0.1", 100, 200)
        self.assertEqual(len(boxes), 1)
        x, y, w, h = boxes[0]
        self.assertAlmostEqual(x, 40.0)
        self.assertAlmostEqual(y, 90.0)
        self.assertAlmostEqual(w, 20.0)
        self.assertAlmostEqual(h, 20.0)

    def test_to_original_undoes_narrow_image_upscale(self):
        small = Image.new("RGB", (500, 700))
        big = Image.new("RGB", (900, 700))
        self.assertEqual(to_original([(10, 20, 30, 40)], small), [(5, 10, 15, 20)])
        self.assertEqual(to_original([(10, 20, 30, 40)], big), [(10, 20, 30, 40)])


if __name__ == "__main__":
    unittest.main()

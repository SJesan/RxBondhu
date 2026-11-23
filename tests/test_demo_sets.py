"""The shipped demo images must produce the colour each demo step claims.

Readers are simulated with the exact printed brand text (a best case). If even
the best case does not yield the intended colour, the demo script would lie.
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu.fusion import fuse  # noqa: E402
from rxbondhu.lexicon import load_brands  # noqa: E402
from tools.make_demo_images import SETS  # noqa: E402


def colours(index: int) -> list[str]:
    brands = load_brands()
    out = []
    for line in SETS[index - 1]:
        text = line.split("   ")[0].strip()
        result = fuse({"brand": "", "confidence": 0.0}, text, brands,
                      second_vlm_text=text)
        out.append(result["colour"])
    return out


class TestDemoColours(unittest.TestCase):
    def test_sets_01_and_02_are_clean_all_green(self):
        for index in (1, 2):
            with self.subTest(index=index):
                self.assertEqual(colours(index), ["GREEN", "GREEN", "GREEN"])

    def test_set_03_has_box_only_yellow_lines(self):
        self.assertEqual(colours(3), ["YELLOW", "GREEN", "YELLOW"])

    def test_set_04_is_clean_green_ready_for_a_deliberate_flag(self):
        # The RED in demo 04 comes from the neutral "Not sure?" button, never
        # from a fabricated bad reading in the image itself.
        self.assertEqual(colours(4), ["GREEN", "GREEN", "GREEN"])

    def test_sets_05_06_are_unverified_or_mixed_stress_cases(self):
        self.assertEqual(colours(5), ["UNVERIFIED", "UNVERIFIED", "UNVERIFIED"])
        self.assertIn("YELLOW", colours(6))

    def test_six_images_and_crop_example_exist(self):
        assets = os.path.join(ROOT, "assets", "demo")
        for index in range(1, 7):
            self.assertTrue(os.path.isfile(
                os.path.join(assets, f"demo_rx_{index:02d}.png")))
        self.assertTrue(os.path.isfile(os.path.join(assets, "crop_example.png")))

    def test_demo_images_keep_fictional_header_but_no_replace_footer(self):
        path = os.path.join(ROOT, "tools", "make_demo_images.py")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("DEMO ONLY  -  fictional data", source)
        self.assertIn("Patient: Demo User (not real)", source)
        self.assertNotIn("replace tomorrow", source)


if __name__ == "__main__":
    unittest.main()

"""Multi-prescription helpers: separate groups, sequential reads, safe caching.

Pure tests only — no network, no model loading, no Streamlit runtime.
"""

import os
import sys
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu import multi, pipeline  # noqa: E402


def analysis(*names: str) -> dict:
    return {
        "items": [{"index": i, "name": name, "colour": "GREEN",
                   "generic": name, "dose_text": "1+0+1"}
                  for i, name in enumerate(names)],
        "images": ["one line crop"],
        "line_count": len(names),
    }


def source(colour="white", box=None):
    image = Image.new("RGB", (120, 60), colour)
    return {"image": image, "crop": image, "box": box or (2, 2, 100, 50)}


class TestSeparateGroups(unittest.TestCase):
    def test_three_images_make_three_separate_groups_without_merging(self):
        results = [analysis("Pantonix"), analysis("Maxpro"), analysis("Napa")]
        calls = []

        def reader(crop, full_image=None, skip_vlm=False):
            calls.append((crop, full_image, skip_vlm))
            return results[len(calls) - 1]

        progress = []
        groups = multi.read_all(
            [source("white"), source("red"), source("blue")], {},
            reader=reader, progress=lambda n, total: progress.append((n, total)),
        )

        self.assertEqual(len(groups), 3)
        self.assertEqual([g["number"] for g in groups], [1, 2, 3])
        self.assertEqual(progress, [(1, 3), (2, 3), (3, 3)])  # strictly sequential
        self.assertEqual([len(g["items"]) for g in groups], [1, 1, 1])
        for group, result in zip(groups, results):
            self.assertIs(group["analysis"], result)
            self.assertIs(group["items"][0], result["items"][0])
            self.assertNotIn("images", result)  # crop images never cached
        self.assertIsNone(groups[0]["error"])
        self.assertEqual(len(calls), 3)


class TestCrossPrescriptionDuplicate(unittest.TestCase):
    def test_same_generic_in_two_prescriptions_names_both(self):
        rows = [
            {"name": "Pantonix", "generic": "Pantoprazole", "dose": "1+0+1",
             "colour": "GREEN", "prescription": 1},
            {"name": "Seclo", "generic": "Pantoprazole", "dose": "OD",
             "colour": "GREEN", "prescription": 2},
        ]
        warnings = multi.cross_prescription_warning(rows)
        self.assertEqual(len(warnings), 1)
        warning = warnings[0]
        self.assertIn("Pantoprazole", warning)
        self.assertIn("Prescription 1 ও 2", warning)
        self.assertIn(" prescription", warning)
        self.assertIn("ও", warning)
        self.assertIn("একাধিক প্রেসক্রিপশনে", warning)
        self.assertIn("check for double dose", warning)

    def test_repeat_inside_one_prescription_is_not_a_cross_warning(self):
        rows = [
            {"name": "Napa", "generic": "Paracetamol", "prescription": 1},
            {"name": "Ace", "generic": "Paracetamol", "prescription": 1},
        ]
        self.assertEqual(multi.cross_prescription_warning(rows), [])
        self.assertEqual(multi.count_text(2, 3),
                         "২ প্রেসক্রিপশন · ৩ ওষুধ নিশ্চিত / "
                         "2 prescriptions · 3 medicines confirmed")


class TestOneImageFailure(unittest.TestCase):
    def test_error_and_empty_image_do_not_stop_other_prescriptions(self):
        calls = []

        def reader(crop, full_image=None, skip_vlm=False):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError("429 RESOURCE_EXHAUSTED: quota value 0")
            if len(calls) == 3:
                return {"items": []}
            return analysis("Pantonix")

        groups = multi.read_all([source("white"), source("red"), source("blue")], {},
                                reader=reader)

        self.assertEqual(len(groups), 3)
        self.assertEqual(len(groups[0]["items"]), 1)
        self.assertIsNone(groups[0]["error"])
        self.assertEqual(groups[1]["items"], [])
        self.assertIn("Prescription 2", groups[1]["error"])
        self.assertIn("প্রেসক্রিপশন ২", groups[1]["error"])
        self.assertIn("Other images were read", groups[1]["error"])
        self.assertNotIn("RESOURCE_EXHAUSTED", groups[1]["error"])
        self.assertIn("Nothing found", groups[2]["error"])
        self.assertEqual(len(calls), 3)  # no retry loops


class TestCropCache(unittest.TestCase):
    def test_same_bytes_and_crop_call_reader_once(self):
        calls = []

        def reader(crop, full_image=None, skip_vlm=False):
            calls.append(1)
            return analysis("Pantonix")

        # Two separately created images with identical pixels and the same box.
        same = [source("white", (1, 1, 90, 40)), source("white", (1, 1, 90, 40))]
        cache = {}
        groups = multi.read_all(same, cache, reader=reader)
        self.assertEqual(len(calls), 1)
        self.assertTrue(all(g["from_cache"] for g in groups[1:]))
        self.assertFalse(groups[0]["from_cache"])
        self.assertEqual(groups[0]["analysis"], groups[1]["analysis"])

        # A different crop box is a different cache entry.
        multi.read_all([source("white", (2, 2, 90, 40))], cache, reader=reader)
        self.assertEqual(len(calls), 2)

    def test_key_depends_on_pixels_and_box(self):
        base = multi.crop_cache_key(source("white")["image"], (1, 2, 3, 4))
        self.assertEqual(base, multi.crop_cache_key(source("white")["image"], (1, 2, 3, 4)))
        self.assertNotEqual(base, multi.crop_cache_key(source("black")["image"], (1, 2, 3, 4)))
        self.assertNotEqual(base, multi.crop_cache_key(source("white")["image"], (1, 2, 3, 5)))


class TestSingleImageUnchanged(unittest.TestCase):
    def test_one_image_group_matches_the_direct_single_image_read(self):
        result = analysis("Pantonix")
        direct_args = {}

        def reader(crop, full_image=None, skip_vlm=False):
            direct_args.update(crop=crop, full_image=full_image, skip_vlm=skip_vlm)
            return analysis("Pantonix")

        single = source()
        group = multi.read_all([single], {}, reader=reader)[0]
        with patch.object(pipeline, "analyse", side_effect=reader) as mocked:
            direct = pipeline.analyse(single["crop"], full_image=single["image"],
                                      skip_vlm=False)
        mocked.assert_called_once()
        self.assertEqual(group["items"], direct["items"])
        self.assertEqual(group["items"], result["items"])
        self.assertEqual(len(group["items"]), 1)
        self.assertEqual(direct_args, {"crop": single["crop"],
                                       "full_image": single["image"],
                                       "skip_vlm": False})


if __name__ == "__main__":
    unittest.main()

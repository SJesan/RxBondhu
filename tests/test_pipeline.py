"""Pipeline + Bangla formatting tests (no network, no heavy models)."""

import os
import sys
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu import pipeline, recognizer, segmentation, vlm  # noqa: E402
from rxbondhu.bangla import digits, schedule_rows, summary_text  # noqa: E402
from rxbondhu.pipeline import build_schedule  # noqa: E402


class TestSchedule(unittest.TestCase):
    def setUp(self):
        self.confirmed = [
            {"name": "Napa", "generic": "Paracetamol", "dose": "1+0+1", "colour": "GREEN"},
            {"name": "Ace", "generic": "Paracetamol", "dose": "BD", "colour": "YELLOW"},
        ]

    def test_build_schedule(self):
        result = build_schedule(self.confirmed)
        self.assertEqual(len(result["medicines"]), 2)
        self.assertEqual(result["medicines"][0]["dose"]["morning"], 1)
        self.assertTrue(any("Duplicate generic" in w for w in result["warnings"]))

    def test_red_row_adds_warning(self):
        rows = [{"name": "Napa", "generic": "Paracetamol", "dose": "OD", "colour": "RED"}]
        result = build_schedule(rows)
        self.assertTrue(any("uncertain" in w for w in result["warnings"]))

    def test_empty_name_skipped(self):
        result = build_schedule([{"name": "", "dose": "BD"}])
        self.assertEqual(result["medicines"], [])

    def test_bangla_digits(self):
        self.assertEqual(digits("1+0+1 7"), "১+০+১ ৭")

    def test_rows_and_summary(self):
        schedule = build_schedule(self.confirmed)
        rows = schedule_rows(schedule["medicines"])
        self.assertEqual(rows[0]["morning"], "১")
        self.assertEqual(rows[0]["noon"], "—")  # zero dose shown as a dash
        text = summary_text(schedule)
        self.assertIn("সময়সূচি", text)
        self.assertIn("সতর্কতা", text)


class TestLineBasedAnalysis(unittest.TestCase):
    """One review row per medicine line — never one row per word fragment."""

    def setUp(self):
        self.image = Image.new("RGB", (240, 120), "white")
        self.words = [
            {"image": Image.new("RGB", (20, 10), "white"), "box": (x, y, 20, 10)}
            for x, y in [(10, 10), (40, 10), (10, 60), (40, 60), (70, 60)]
        ]
        self.hits = ([[{"brand": "Napa", "confidence": 0.9}]] * 2
                     + [[{"brand": "Maxpro", "confidence": 0.9}]] * 3)

    def _patches(self, words=None, hits=None):
        return (
            patch.object(segmentation, "segment", return_value=words or self.words),
            patch.object(segmentation, "segment_lines", return_value=[]),
            patch.object(recognizer, "predict_words", return_value=hits or self.hits),
        )

    def test_one_row_per_gemini_line(self):
        lines = [{"medicine": "Tab Napa", "dose": "1+0+1"},
                 {"medicine": "Tab Maxpro", "dose": "BD"}]
        patches = self._patches()
        for p in patches:
            p.start()
        try:
            with patch.object(vlm, "read", return_value={
                "lines": lines, "raw": "", "error": "", "model": "stub"}):
                result = pipeline.analyse(self.image, full_image=self.image)
        finally:
            for p in reversed(patches):
                p.stop()

        self.assertEqual(result["line_count"], 2)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual([i["dose_text"] for i in result["items"]], ["1+0+1", "BD"])
        self.assertEqual([i["name"] for i in result["items"]], ["Napa", "Maxpro"])
        self.assertEqual(len(result["images"]), 2)
        self.assertEqual(result["line_cnn_preds"], ["Napa", "Maxpro"])

    def test_word_fragments_do_not_create_rows(self):
        many_words = self.words * 6
        many_hits = self.hits * 6
        patches = self._patches(many_words, many_hits)
        for p in patches:
            p.start()
        try:
            with patch.object(vlm, "read", return_value={
                "lines": [{"medicine": "Tab Napa", "dose": "1+0+1"}],
                "raw": "", "error": "", "model": "stub"}):
                result = pipeline.analyse(self.image, full_image=self.image)
        finally:
            for p in reversed(patches):
                p.stop()

        self.assertEqual(len(many_words), 30)
        self.assertEqual(result["line_count"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["dose_text"], "1+0+1")

    def test_offline_fallback_groups_words_without_calling_gemini(self):
        patches = self._patches()
        for p in patches:
            p.start()
        try:
            with patch.object(vlm, "read", side_effect=AssertionError("Gemini must not be called")):
                result = pipeline.analyse(self.image, skip_vlm=True)
        finally:
            for p in reversed(patches):
                p.stop()

        self.assertEqual(result["line_count"], 2)
        self.assertEqual(len(result["items"]), 2)
        self.assertTrue(all(i["colour"] in ("GREEN", "YELLOW", "RED") for i in result["items"]))
        self.assertTrue(all(not i["dose_text"] for i in result["items"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

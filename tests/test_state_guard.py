"""Guard tests: stale session state must never crash the reading screen."""

import os
import sys
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu import pipeline, recognizer, segmentation, vlm  # noqa: E402
from rxbondhu.state_guard import analysis_is_current, confirmed_rows_are_current  # noqa: E402


def current_analysis():
    image = Image.new("RGB", (240, 120), "white")
    words = [{"image": image, "box": (x, 10, 20, 20)} for x in (10, 40)]
    hits = [[{"brand": "Napa", "confidence": 0.9}]] * 2
    patches = (
        patch.object(segmentation, "segment", return_value=words),
        patch.object(segmentation, "segment_lines", return_value=[]),
        patch.object(recognizer, "predict_words", return_value=hits),
    )
    for p in patches:
        p.start()
    try:
        with patch.object(vlm, "read", return_value={
            "lines": [{"medicine": "Tab Napa", "dose": "1+0+1"}],
            "raw": "", "error": "", "model": "stub"}):
            return pipeline.analyse(image, full_image=image)
    finally:
        for p in reversed(patches):
            p.stop()


class TestStateGuard(unittest.TestCase):
    def test_current_pipeline_result_is_accepted(self):
        self.assertTrue(analysis_is_current(current_analysis()))

    def test_legacy_word_level_result_is_rejected(self):
        legacy = {"items": [{"brand": "Napa"}], "word_count": 2}
        self.assertFalse(analysis_is_current(legacy))

    def test_missing_line_count_is_rejected(self):
        analysis = current_analysis()
        analysis.pop("line_count")
        self.assertFalse(analysis_is_current(analysis))

    def test_missing_item_field_is_rejected(self):
        analysis = current_analysis()
        analysis["items"][0].pop("dose_text")
        self.assertFalse(analysis_is_current(analysis))

    def test_none_and_junk_are_rejected(self):
        for value in (None, "", 0, [], "word_count"):
            self.assertFalse(analysis_is_current(value))

    def test_confirmed_rows(self):
        rows = [{"index": 0, "name": "Napa", "options": ["Napa"],
                 "dose": "1+0+1", "generic": "Paracetamol", "colour": "RED",
                 "editable": False, "raw_reading": "Tab Napa"}]
        self.assertTrue(confirmed_rows_are_current(rows))
        self.assertFalse(confirmed_rows_are_current([{"name": "Napa"}]))
        self.assertFalse(confirmed_rows_are_current(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Scoring logic for the real-handwriting evaluation runner (no network)."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from evaluate_handwritten import evaluate_row, norm, run_one, split_pipe  # noqa: E402


class TestEvaluation(unittest.TestCase):
    def test_split_pipe_and_norm(self):
        self.assertEqual(split_pipe("Napa | Maxpro |"), ["Napa", "Maxpro"])
        self.assertEqual(norm("M-Kast"), "m kast")
        self.assertEqual(norm("নাপা"), "নাপা")

    def test_green_wrong_is_unsafe_error(self):
        answer = {"true_brands": "Napa|Maxpro", "true_dose": "1+0+1|BD"}
        result = {
            "cnn_preds": ["Napa"], "vlm_preds": ["Maxpro", "Napa"],
            "combined": [("Napa", "GREEN", "1+0+1"),
                         ("Zzqqx", "GREEN", "BD")],
            "vlm_error": "", "word_count": 2,
        }
        score = evaluate_row(answer, result)
        self.assertEqual(score["combined_correct"], 1)
        self.assertEqual(score["unsafe_green"], 1)
        self.assertEqual(score["wrong_combined"], 1)
        self.assertEqual(score["caught_wrong"], 0)
        self.assertEqual(score["dose_correct"], 2)

    def test_yellow_wrong_is_caught(self):
        answer = {"true_brands": "Napa", "true_dose": ""}
        result = {
            "cnn_preds": [], "vlm_preds": [],
            "combined": [("Ace", "YELLOW", "")],
            "vlm_error": "", "word_count": 1,
        }
        score = evaluate_row(answer, result)
        self.assertEqual(score["wrong_combined"], 1)
        self.assertEqual(score["caught_wrong"], 1)
        self.assertEqual(score["unsafe_green"], 0)


class TestRunner(unittest.TestCase):
    def test_run_one_uses_line_level_readings(self):
        fd, path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        try:
            Image.new("RGB", (12, 12), "white").save(path)
            fake = {
                "items": [{"name": "Napa", "colour": "GREEN", "dose_text": "1+0+1"}],
                "line_cnn_preds": ["Napa"],
                "vlm_lines": [{"medicine": "Napa", "dose": "1+0+1"}],
                "vlm_error": "", "word_count": 9, "line_count": 1,
            }
            with patch("evaluate_handwritten.pipeline.analyse", return_value=fake):
                result = run_one(path, False, False)
            self.assertEqual(result["cnn_preds"], ["Napa"])
            self.assertEqual(result["combined"], [("Napa", "GREEN", "1+0+1")])
            self.assertEqual(result["word_count"], 9)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)

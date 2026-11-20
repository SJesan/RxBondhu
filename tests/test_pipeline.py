"""Pipeline + Bangla formatting tests (no network, no heavy models)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


if __name__ == "__main__":
    unittest.main(verbosity=2)

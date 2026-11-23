"""Bangla-first schedule table guards."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu import bangla, pipeline  # noqa: E402


class TestBanglaTable(unittest.TestCase):
    def setUp(self):
        self.schedule = pipeline.build_schedule([
            {"name": "Napa", "generic": "Paracetamol", "dose": "1+0+1 7 days"},
            {"name": "Maxpro", "generic": "Esomeprazole", "dose": "BD"},
        ])

    def test_headers_are_bangla_first_with_small_english(self):
        html = bangla.schedule_table_html(self.schedule["medicines"])
        for bangla_label, english in (("ওষুধ", "Brand"), ("ডোজ", None),
                                      ("সকাল", "Morning"), ("দুপুর", "Noon"),
                                      ("রাত", "Night"), ("দিন", "Days")):
            self.assertIn(bangla_label, html)
            if english:
                self.assertIn(f"<small>{english}</small>", html)
        self.assertIn("rx-schedule-table", html)

    def test_big_ticks_and_bangla_digits(self):
        html = bangla.schedule_table_html(self.schedule["medicines"])
        self.assertIn("rx-tick", html)
        self.assertIn("✓", html)
        self.assertIn("১", html)
        self.assertIn("rx-count", html)

    def test_missing_days_are_explicit_not_a_dash(self):
        rows = bangla.schedule_rows(self.schedule["medicines"])
        self.assertEqual(rows[1]["days"], bangla.MISSING_DAYS)
        html = bangla.schedule_table_html(self.schedule["medicines"])
        self.assertIn(bangla.MISSING_DAYS, html)

    def test_table_escapes_csv_text(self):
        schedule = pipeline.build_schedule([
            {"name": "<script>x</script>", "generic": "Paracetamol", "dose": "1+0+1"},
        ])
        html = bangla.schedule_table_html(schedule["medicines"])
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>x</script>", html)


if __name__ == "__main__":
    unittest.main()

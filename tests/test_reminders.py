"""Reminder .ics generation tests (no network, no model loading)."""

import os
import sys
import unittest
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu.pipeline import build_schedule  # noqa: E402
from rxbondhu.reminders import make_ics  # noqa: E402


class TestReminders(unittest.TestCase):
    def test_events_and_rrule(self):
        schedule = build_schedule([
            {"name": "Napa", "generic": "Paracetamol", "dose": "1+0+1 7 days"},
            {"name": "Maxpro", "generic": "Esomeprazole", "dose": "BD 5 days"},
        ])
        result = make_ics(schedule, start_date=date(2026, 11, 24))
        self.assertEqual(len(result["events"]), 4)  # 2 slots + 2 slots
        self.assertIn("RRULE:FREQ=DAILY;COUNT=7", result["ics"])
        self.assertIn("DTSTART;TZID=Asia/Dhaka:20261124T080000", result["ics"])
        self.assertIn("BEGIN:VALARM", result["ics"])
        self.assertTrue(result["ics"].startswith("BEGIN:VCALENDAR"))
        self.assertTrue(result["ics"].rstrip().endswith("END:VCALENDAR"))
        self.assertEqual(result["warnings"], [])

    def test_zero_slots_skipped_and_missing_days_warned(self):
        schedule = build_schedule([
            {"name": "Cetiriz", "generic": "Cetirizine", "dose": "HS"},
        ])
        result = make_ics(schedule, start_date=date(2026, 11, 24))
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(result["events"][0]["slot"], "night")
        self.assertTrue(any("defaulting to 7 days" in w for w in result["warnings"]))

    def test_text_escaped(self):
        schedule = build_schedule([
            {"name": "A,B;C", "dose": "OD 3 days"},
        ])
        result = make_ics(schedule, start_date=date(2026, 11, 24))
        self.assertIn(r"A\,B\;C", result["ics"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

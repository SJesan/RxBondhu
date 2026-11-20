"""Core logic tests. Run: python tests\\test_core.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu.dose_parser import parse, to_bangla_summary  # noqa: E402


class TestDoseParser(unittest.TestCase):
    def test_triplet(self):
        p = parse("1+0+1")
        self.assertEqual((p["morning"], p["noon"], p["night"]), (1, 0, 1))
        self.assertEqual(p["times_per_day"], 2)

    def test_triplet_with_spaces_and_days(self):
        p = parse("1 + 1 + 1 7 days")
        self.assertEqual((p["morning"], p["noon"], p["night"]), (1, 1, 1))
        self.assertEqual(p["days"], 7)

    def test_bd(self):
        p = parse("Tab Maxpro 20mg BD")
        self.assertEqual((p["morning"], p["noon"], p["night"]), (1, 0, 1))

    def test_tds(self):
        p = parse("TDS")
        self.assertEqual((p["morning"], p["noon"], p["night"]), (1, 1, 1))

    def test_hs(self):
        p = parse("HS")
        self.assertEqual(p["night"], 1)

    def test_bangla_digits_and_words(self):
        p = parse("সকাল ১ টি, রাতে ১ টি, ৭ দিন")
        self.assertEqual((p["morning"], p["noon"], p["night"]), (1, 0, 1))
        self.assertEqual(p["days"], 7)

    def test_unknown_warns(self):
        p = parse(ascii_unknown())
        self.assertEqual(p["times_per_day"], 0)
        self.assertTrue(p["warnings"])

    def test_bangla_summary(self):
        p = parse("1+0+1 5 দিন")
        self.assertIn("সকালে", to_bangla_summary(p))


def ascii_unknown():
    return "as prescribed"


if __name__ == "__main__":
    unittest.main(verbosity=2)

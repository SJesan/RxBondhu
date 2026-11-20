"""Core logic tests. Run: python tests\\test_core.py"""

import csv
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu.dose_parser import parse, to_bangla_summary  # noqa: E402
from rxbondhu.lexicon import load_brands, match_brand, normalise_name  # noqa: E402
from rxbondhu.safety import duplicate_warning, has_red  # noqa: E402


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


class TestLexicon(unittest.TestCase):
    def setUp(self):
        self.brands = load_brands()

    def test_exact_brand(self):
        hit = match_brand("Tab Napa 500", self.brands)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["brand"], "Napa")
        self.assertEqual(hit["generic"], "Paracetamol")

    def test_fuzzy_misspelling(self):
        hit = match_brand("Maxpo", self.brands)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["brand"], "Maxpro")

    def test_invented_name_rejected(self):
        self.assertIsNone(match_brand("Zzqqx", self.brands))

    def test_unverified_row_not_used(self):
        with open("data/manual_brands.csv", "r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        maxpro_rows = [r for r in rows if r["brand"].strip().lower() == "maxpro"]
        self.assertTrue(all(r["verified"].strip().lower() != "yes" for r in maxpro_rows))
        # Maxpro still comes from the verified seed list.
        self.assertEqual(match_brand("Maxpro", self.brands)["brand"], "Maxpro")

    def test_normalise_strips_dosage_words(self):
        self.assertEqual(normalise_name("TAB. NAPA 500mg"), "napa 500")


class TestSafety(unittest.TestCase):
    def test_duplicate_generic_detected(self):
        meds = [
            {"name": "Napa", "generic": "Paracetamol"},
            {"name": "Ace", "generic": "Paracetamol"},
        ]
        warnings = duplicate_warning(meds)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Napa", warnings[0])
        self.assertIn("Ace", warnings[0])

    def test_no_duplicate_for_different_generics(self):
        meds = [
            {"name": "Napa", "generic": "Paracetamol"},
            {"name": "Maxpro", "generic": "Meloxicam"},
        ]
        self.assertEqual(duplicate_warning(meds), [])

    def test_has_red(self):
        self.assertTrue(has_red([{"colour": "RED"}]))
        self.assertFalse(has_red([{"colour": "GREEN"}]))


def ascii_unknown():
    return "as prescribed"


if __name__ == "__main__":
    unittest.main(verbosity=2)

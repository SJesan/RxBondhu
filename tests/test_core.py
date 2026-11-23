"""Core logic tests. Run: python tests\\test_core.py"""

import csv
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu.dose_parser import parse, to_bangla_summary  # noqa: E402
from rxbondhu.lexicon import load_brands, match_brand, normalise_name, suggest_brands  # noqa: E402
from rxbondhu.safety import duplicate_warning, generic_key, has_red, same_dose_warning  # noqa: E402
from rxbondhu.fusion import clean_display_name, fuse  # noqa: E402


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

    def test_box_verified_rows_are_used_with_provenance(self):
        with open("data/manual_brands.csv", "r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertTrue(all(r["verified"].strip().lower() == "yes" for r in rows))
        self.assertTrue(all(r["checked_by"].strip() for r in rows))
        wanted = {"Seclo": "Omeprazole", "Sergel": "Esomeprazole",
                  "Fexo": "Fexofenadine", "Monas": "Montelukast",
                  "Filmet": "Metronidazole", "Zimax": "Azithromycin"}
        for brand, generic in wanted.items():
            hit = match_brand(brand, self.brands)
            self.assertEqual(hit["generic"], generic)
            self.assertIn("box", hit["source"])
        # The old Meloxicam label was corrected by the box/pharmacy check.
        self.assertEqual(match_brand("Maxpro", self.brands)["generic"], "Esomeprazole")

    def test_normalise_strips_dosage_words(self):
        self.assertEqual(normalise_name("TAB. NAPA 500mg"), "napa 500")


class TestDisplayNames(unittest.TestCase):
    def test_bangla_survives_clean_display_name(self):
        self.assertEqual(clean_display_name("নাপা"), "নাপা")

    def test_form_and_strength_are_stripped(self):
        self.assertEqual(clean_display_name("Syp. Napa (120mg/5ml)"), "Napa")

    def test_ts_abbreviation_is_stripped(self):
        # Gemini reads the prescriber's "Ts" (tablet) abbreviation as a prefix.
        self.assertEqual(clean_display_name("Ts Amlocal plus"), "Amlocal plus")


class TestFusion(unittest.TestCase):
    def setUp(self):
        self.brands = load_brands()

    def test_green_when_both_agree(self):
        result = fuse({"brand": "Maxpro", "confidence": 0.93}, "Tab Maxpro 20mg", self.brands,
                      second_vlm_text="Cap Maxpro 20")
        self.assertEqual(result["colour"], "GREEN")
        self.assertEqual(result["name"], "Maxpro")
        self.assertFalse(result["needs_confirm"])

    def test_fuzzy_only_match_capped_at_yellow(self):
        # 90.9 < GREEN_SCORE (95): two readers agreeing on a fuzzy spelling is
        # YELLOW, never GREEN, and no generic is asserted.
        result = fuse({"brand": "Maxpro", "confidence": 0.91}, "Maxpo", self.brands,
                      second_vlm_text="Maxpo")
        self.assertEqual(result["colour"], "YELLOW")
        self.assertIsNone(result["generic"])
        self.assertTrue(result["needs_confirm"])
        self.assertLess(result["min_match_score"], 95)

    def test_exact_match_from_both_readers_is_green(self):
        result = fuse({"brand": "Maxpro", "confidence": 0.91}, "Tab Maxpro 20mg", self.brands,
                      second_vlm_text="Cap Maxpro 20")
        self.assertEqual(result["colour"], "GREEN")
        self.assertEqual(result["generic"], "Esomeprazole")
        self.assertEqual(result["min_match_score"], 100)

    def test_exact_dual_match_overrides_out_of_distribution_cnn(self):
        # Real-photo case: CNN's 78-class word model guesses "Napa" at high
        # confidence, but both readers independently read the exact DGDA brand.
        result = fuse({"brand": "Napa", "confidence": 0.92}, "Tab Pantonix 20mg",
                      self.brands, second_vlm_text="Pantonix 20")
        self.assertEqual(result["colour"], "GREEN")
        self.assertEqual(result["name"], "Pantonix")
        self.assertEqual(result["min_match_score"], 100)
        self.assertIn("outside its training set", result["reason"])

    def test_near_exact_dual_match_keeps_cnn_veto(self):
        result = fuse({"brand": "Napa", "confidence": 0.92}, "Maxpo", self.brands,
                      second_vlm_text="Maxpo")
        self.assertEqual(result["colour"], "RED")
        self.assertIn("CNN disagrees", result["reason"])

    def test_yellow_when_only_cnn_confident(self):
        result = fuse({"brand": "Napa", "confidence": 0.82}, "", self.brands)
        self.assertEqual(result["colour"], "YELLOW")
        self.assertTrue(result["needs_confirm"])

    def test_red_when_readers_disagree(self):
        result = fuse({"brand": "Napa", "confidence": 0.90}, "Maxpro", self.brands)
        self.assertEqual(result["colour"], "RED")

    def test_red_when_low_confidence(self):
        result = fuse({"brand": "Napa", "confidence": 0.20}, "", self.brands)
        self.assertEqual(result["colour"], "RED")
        self.assertIn("threshold", result["reason"])

    def test_suggestions_include_brand(self):
        names = [s["brand"] for s in suggest_brands("Maxpo", self.brands)]
        self.assertIn("Maxpro", names)

    def test_unverified_cnn_brand_is_never_green(self):
        # CNN classes like "Az" exist in the 78-class model but not in the
        # verified lexicon. Unknown is UNVERIFIED (editable), never GREEN.
        result = fuse({"brand": "Zzqqx", "confidence": 0.95}, "", self.brands)
        self.assertEqual(result["colour"], "UNVERIFIED")
        self.assertEqual(result["name"], "Zzqqx")
        self.assertIn("verified", result["reason"])
        self.assertTrue(result["needs_confirm"])

    def test_unverified_reader_name_with_low_cnn_is_not_red(self):
        # Real off-lexicon lines from the demo photo with no DGDA candidate.
        for name in ("Amsocal plus", "Eltroxin", "Amdocal plus", "Panicel", "Vare"):
            with self.subTest(name=name):
                result = fuse({"brand": "", "confidence": 0.0}, name, self.brands,
                              second_vlm_text=name)
                self.assertEqual(result["colour"], "UNVERIFIED")
                self.assertEqual(result["name"], name)
                self.assertIsNone(result["generic"])
                self.assertTrue(result["needs_confirm"])

    def test_fuzzy_candidate_names_are_yellow_without_a_generic(self):
        # "Maxpo" scores 90.9: a DGDA candidate at 90-95 is capped at YELLOW.
        # No generic is asserted until a human confirms.
        for name in ("Maxpo",):
            with self.subTest(name=name):
                result = fuse({"brand": "", "confidence": 0.0}, name, self.brands,
                              second_vlm_text=name)
                self.assertEqual(result["colour"], "YELLOW")
                self.assertEqual(result["name"], name)
                self.assertIsNone(result["generic"])
                self.assertTrue(result["needs_confirm"])

    def test_unverified_cnn_shows_reader_name_but_stays_unverified(self):
        raw = "Tab. Amdocal Plus 50 (Amlodipine + Atenolol)"
        result = fuse({"brand": "Zzqqx", "confidence": 0.95}, raw, self.brands)
        self.assertEqual(result["colour"], "UNVERIFIED")
        self.assertIn("Amdocal", result["name"])
        self.assertNotIn("Zzqqx", result["name"])
        self.assertIsNone(result["generic"])
        self.assertIn("verified", result["reason"])

    def test_unknown_brand_is_never_labelled_not_approved(self):
        result = fuse({"brand": "", "confidence": 0.0}, "Zzqqx", self.brands,
                      second_vlm_text="Zzqqx")
        self.assertEqual(result["colour"], "UNVERIFIED")
        for prohibited in ("not approved", "fake", "rejected"):
            self.assertNotIn(prohibited, result["reason"].lower())

    def test_two_readers_disagree_is_red(self):
        result = fuse({"brand": "Napa", "confidence": 0.93}, "Tab Napa", self.brands,
                      second_vlm_text="Tab Maxpro")
        self.assertEqual(result["colour"], "RED")
        self.assertIn("disagree", result["reason"])

    def test_unverified_readers_disagree_is_red(self):
        # Real line: Reader 1 "Ts Panicel", Reader 2 "Ts Paricel".
        result = fuse({"brand": "Zzqqx", "confidence": 0.89}, "Ts Panicel", self.brands,
                      second_vlm_text="Ts Paricel")
        self.assertEqual(result["colour"], "RED")
        self.assertEqual(result["name"], "Panicel")
        self.assertIn("disagree", result["reason"])

    def test_one_verified_reader_and_one_unknown_is_yellow(self):
        result = fuse({"brand": "Napa", "confidence": 0.93}, "Tab Napa", self.brands,
                      second_vlm_text="Tab Zzqqx")
        self.assertEqual(result["colour"], "YELLOW")
        self.assertEqual(result["name"], "Napa")


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

    def test_combination_ingredient_order_duplicate_detected(self):
        meds = [
            {"name": "Amlocal Plus", "generic": "Amlodipine + Atenolol"},
            {"name": "Another Brand", "generic": "Atenolol + Amlodipine"},
        ]
        self.assertEqual(generic_key(meds[0]["generic"]), generic_key(meds[1]["generic"]))
        warnings = duplicate_warning(meds)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Amlocal Plus", warnings[0])
        self.assertIn("Another Brand", warnings[0])

    def test_same_generic_different_strength_warns_without_dose_claim(self):
        meds = [
            {"name": "Napa 500", "generic": "Paracetamol 500 mg"},
            {"name": "Napa 650", "generic": "Paracetamol 650 mg"},
        ]
        warnings = duplicate_warning(meds)
        self.assertEqual(len(warnings), 1)
        self.assertIn("same generic", warnings[0])
        # No specific mg ceiling / medical dose advice is asserted.
        self.assertNotIn("4000", warnings[0])
        self.assertNotIn("maximum", warnings[0].lower())

    def test_no_duplicate_for_different_generics(self):
        meds = [
            {"name": "Napa", "generic": "Paracetamol"},
            {"name": "Maxpro", "generic": "Esomeprazole"},
        ]
        self.assertEqual(duplicate_warning(meds), [])

    def test_same_medicine_same_dose_warns(self):
        meds = [
            {"name": "Napa", "generic": "Paracetamol", "dose": "1+0+1"},
            {"name": "Napa", "generic": "Paracetamol", "dose": "1+0+1"},
        ]
        warnings = same_dose_warning(meds)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Same medicine/dose repeated", warnings[0])

    def test_same_medicine_different_dose_no_same_dose_warning(self):
        meds = [
            {"name": "Napa", "generic": "Paracetamol", "dose": "1+0+1"},
            {"name": "Napa", "generic": "Paracetamol", "dose": "1+1+1"},
        ]
        self.assertEqual(same_dose_warning(meds), [])

    def test_has_red(self):
        self.assertTrue(has_red([{"colour": "RED"}]))
        self.assertFalse(has_red([{"colour": "GREEN"}]))


def ascii_unknown():
    return "as prescribed"


if __name__ == "__main__":
    unittest.main(verbosity=2)

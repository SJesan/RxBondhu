"""Trust and honesty guards: no false DGDA approval, no hidden CNN guesses."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu import fusion, ui  # noqa: E402
from rxbondhu.lexicon import conflict_for, load_brands  # noqa: E402


class TestGreenRequiresDar(unittest.TestCase):
    def setUp(self):
        self.brands = load_brands()

    def test_box_only_exact_dual_match_is_yellow_not_green(self):
        for name in ("Tab Napa 500", "Fexo 60"):
            with self.subTest(name=name):
                result = fusion.fuse(
                    {"brand": "Maxpro", "confidence": 0.10}, name, self.brands,
                    second_vlm_text=name,
                )
                self.assertEqual(result["colour"], "YELLOW")
                self.assertIn("box check", result["reason"].lower())
                self.assertNotIn("not found in dgda snapshot — verify on the box",
                                 result["reason"].lower())
                self.assertIsNone(result["generic"])

    def test_dar_backed_exact_dual_match_stays_green(self):
        result = fusion.fuse(
            {"brand": "Az", "confidence": 0.92}, "Tab Pantonix 20mg", self.brands,
            second_vlm_text="Pantonix 20",
        )
        self.assertEqual(result["colour"], "GREEN")
        self.assertIn("dgda-registered", result["reason"].lower())

    def test_conflicting_box_only_name_is_never_green(self):
        result = fusion.fuse(
            {"brand": "Az", "confidence": 0.10}, "Tab Napa 500", self.brands,
            second_vlm_text="Napa 500",
        )
        self.assertEqual(result["colour"], "YELLOW")
        self.assertIsNotNone(result["dgda_record"])
        self.assertIn("multiple generic", result["dgda_record"]["conflict_reason"].lower())

    def test_conflict_data_is_available_for_napa_and_fexo(self):
        self.assertIsNotNone(conflict_for("Tab Napa 500"))
        self.assertIsNotNone(conflict_for("Fexo 60"))
        self.assertIsNone(conflict_for("Pantonix"))

    def test_out_of_distribution_cnn_guess_does_not_escalate_box_only_to_red(self):
        # The shipped demo 03 hit this live: CNN guessed "Az (0.62)" on a Napa
        # word crop. That raw guess belongs in More info, not as a RED reason.
        for name in ("Tab Napa 500", "Fexo 60"):
            with self.subTest(name=name):
                result = fusion.fuse(
                    {"brand": "Az", "confidence": 0.62}, name, self.brands,
                    second_vlm_text=name,
                )
                self.assertEqual(result["colour"], "YELLOW")
                self.assertIn("box check", result["reason"].lower())
                self.assertNotIn("cnn disagrees", result["reason"].lower())
                self.assertEqual(result["cnn_display"], fusion.CNN_NOT_APPLICABLE)
                self.assertTrue(result["cnn_conflicts"])

    def test_confident_cnn_still_vetoes_a_fuzzy_dar_backed_brand(self):
        # Near-exact dual DAR-backed matches keep the CNN veto (RED).
        result = fusion.fuse(
            {"brand": "Maxpro", "confidence": 0.91}, "Tab Pantoprazol 20", self.brands,
            second_vlm_text="Pantoprazol 20",
        )
        self.assertEqual(result["colour"], "RED")


class TestCnnDisplay(unittest.TestCase):
    def setUp(self):
        self.brands = load_brands()

    def test_contradictory_cnn_guess_is_hidden_from_main_view(self):
        result = fusion.fuse(
            {"brand": "Az", "confidence": 0.92}, "Tab Pantonix 20mg", self.brands,
            second_vlm_text="Pantonix 20",
        )
        self.assertEqual(result["cnn_display"], fusion.CNN_NOT_APPLICABLE)
        self.assertTrue(result["cnn_conflicts"])
        self.assertEqual(result["cnn_brand"], "Az")

    def test_matching_cnn_guess_stays_visible(self):
        result = fusion.fuse(
            {"brand": "Maxpro", "confidence": 0.91}, "Tab Maxpro 20mg", self.brands,
            second_vlm_text="Cap Maxpro 20",
        )
        self.assertIn("Maxpro", result["cnn_display"])
        self.assertFalse(result["cnn_conflicts"])


class TestThreeSignalAndDgdaSafety(unittest.TestCase):
    def setUp(self):
        self.brands = load_brands()

    def test_strong_three_signal_never_upgrades_to_green(self):
        # All three signals point to a non-DGDA/exact-unverified name: keep it YELLOW.
        result = fusion.fuse(
            {"brand": "Maxpro", "confidence": 0.92}, "Maxpo", self.brands,
            second_vlm_text="Maxpo",
        )
        self.assertEqual(result["colour"], "YELLOW")
        self.assertIsNotNone(result.get("strong_signal"))
        self.assertIn("strong 3-signal", result["reason"].lower())
        self.assertNotEqual(result["colour"], "GREEN")

    def test_not_in_dgda_does_not_show_suggested_dar_record(self):
        # RAZENTUS is not in DGDA; Relentus is only a suggestion.
        result = fusion.fuse(None, "RAZENTUS", self.brands, second_vlm_text="RAZENTUS")
        self.assertFalse(result.get("in_dgda"))
        self.assertIsNone(result.get("dgda_record"))
        self.assertTrue(any(s.get("brand") == "Relentus" for s in result.get("suggestions", [])))


class TestWording(unittest.TestCase):
    def test_status_lines_are_plain_bangla(self):
        self.assertEqual(ui.status_line("GREEN"), "দুটি AI একমত")
        self.assertEqual(ui.status_line("YELLOW"), "আবার দেখুন")
        self.assertEqual(ui.status_line("RED"), "ফার্মাসিস্টকে জিজ্ঞাসা করুন")
        self.assertIn("নিশ্চিত", ui.status_line("UNVERIFIED"))

    def test_provenance_never_claims_approval(self):
        cases = [
            ({"dar_no": "116-0109-067", "source": "DGDA export"},
             "DGDA-registered (DAR No 116-0109-067)"),
            ({"source": "medicine box / pharmacist check"},
             "Verified by box check, not found in DGDA snapshot"),
            ({}, "Not found in DGDA snapshot — check the box"),
        ]
        for record, expected in cases:
            with self.subTest(record=record):
                text = ui.identity_provenance(record)
                self.assertEqual(text, expected)
                self.assertNotIn("approved", text.lower())

    def test_card_and_compact_wording_never_say_approved(self):
        record = {
            "brand": "Napa", "generic": "Paracetamol", "dar_no": "",
            "source": "medicine box / pharmacist check",
            "conflict_reason": "DGDA brand maps to multiple generic identities",
            "conflict_generics": "caffeine + paracetamol || paracetamol",
        }
        for renderer in (ui.dgda_card_html, ui.dgda_compact_html):
            with self.subTest(renderer=renderer.__name__):
                text = renderer(record).lower()
                self.assertIn("box check", text)
                self.assertIn("not dose advice", text)
                self.assertNotIn("approved", text)

    def test_disclaimer_appears_once_per_screen(self):
        with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertEqual(source.count("st.markdown(DEMO_DISCLAIMER"), 3)


if __name__ == "__main__":
    unittest.main()

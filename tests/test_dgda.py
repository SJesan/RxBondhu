"""DGDA snapshot importer, provenance and info-card tests.

Run: python tests\\test_dgda.py
"""

import csv
import json
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu.ui import dgda_card_html, dgda_card_lines  # noqa: E402
from tools import import_dgda  # noqa: E402


RAW_CSV = """SL,Company,"Trade Name","Generic Name With Strength","Dosage Form","DAR No"
1,AB Life Science,Acetone BP (API),Acetone 1000 ml,Liter,481-0004-034
2,Test Pharma,Napa,Paracetamol 500 mg,Tablet,TEST-0001
3,Test Pharma,Maxpo 20,Esomeprazole 20 mg,Capsule,TEST-0002
4,Test Pharma,Clash,Paracetamol 500 mg,Tablet,TEST-0003
5,Test Pharma,Clash,Ibuprofen 400 mg,Tablet,TEST-0004
"""

MANUAL_CSV = "brand,generic,verified,checked_by,source\nNapa,Paracetamol,yes,Tester,box check\n"


class TestImportDGDA(unittest.TestCase):
    def test_import_filters_bulk_quarantines_conflicts_and_writes_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = os.path.join(tmp, "raw.csv")
            manual = os.path.join(tmp, "manual.csv")
            out = os.path.join(tmp, "brands.csv")
            conflicts = os.path.join(tmp, "conflicts.csv")
            source = os.path.join(tmp, "source.json")
            with open(raw, "w", encoding="utf-8") as fh:
                fh.write(RAW_CSV)
            with open(manual, "w", encoding="utf-8") as fh:
                fh.write(MANUAL_CSV)

            with patch.object(sys, "argv", [
                "import_dgda.py", "--raw", raw, "--manual", manual,
                "--out", out, "--conflicts", conflicts, "--source", source,
                "--accessed-at", "2026-11-23",
            ]):
                self.assertEqual(import_dgda.main(), 0)

            with open(out, encoding="utf-8-sig", newline="") as fh:
                brands = list(csv.DictReader(fh))
            keys = {import_dgda.brand_key(r["brand"]) for r in brands}
            self.assertIn("napa", keys)
            self.assertIn("maxpo", keys)
            self.assertNotIn("acetone bp", keys)
            self.assertNotIn("clash", keys)

            clash = next(r for r in brands if import_dgda.brand_key(r["brand"]) == "napa")
            self.assertIn("box check", clash["source"])
            self.assertEqual(clash["checked_by"], "Tester")

            with open(conflicts, encoding="utf-8-sig", newline="") as fh:
                conflict_rows = list(csv.DictReader(fh))
            self.assertEqual(len(conflict_rows), 1)
            self.assertEqual(conflict_rows[0]["brand_key"], "clash")

            with open(source, encoding="utf-8") as fh:
                meta = json.load(fh)
            self.assertEqual(meta["raw_rows"], 5)
            self.assertEqual(meta["accessed_at"], "2026-11-23")
            self.assertEqual(len(meta["raw_sha256"]), 64)

    def test_generic_parser_separates_strength_and_sorts_ingredients(self):
        generic, canonical, strength = import_dgda.parse_generic("Omeprazole 20 mg")
        self.assertEqual((generic, canonical, strength),
                         ("Omeprazole", "omeprazole", "20 mg"))
        generic, canonical, _ = import_dgda.parse_generic(
            "Amlodipine + Atenolol 5 mg + 50 mg"
        )
        self.assertEqual(canonical, "amlodipine + atenolol")

    def test_bulk_and_api_rows_are_rejected(self):
        self.assertFalse(import_dgda.is_finished_form("Liter", "Acetone BP (API)"))
        self.assertFalse(import_dgda.is_finished_form("Kg", "Zinc Sulphate BP"))
        self.assertTrue(import_dgda.is_finished_form("Tablet", "Napa"))

    def test_committed_snapshot_matches_its_provenance(self):
        source_path = os.path.join(ROOT, "data", "dgda_source.json")
        if not os.path.exists(source_path):
            self.skipTest("DGDA snapshot not generated yet")
        with open(source_path, encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta["raw_rows"], 41655)
        self.assertEqual(len(meta["raw_sha256"]), 64)
        self.assertGreater(meta["brand_rows"], 20000)
        self.assertIn("GREEN requires a >=95", meta["note"])


class TestRecordCard(unittest.TestCase):
    def test_card_shows_dar_without_approval_or_price_claims(self):
        lines = dgda_card_lines({
            "brand": "Acidex 20", "generic": "Omeprazole", "strength": "20 mg",
            "form": "Capsule", "company": "Test Pharma", "dar_no": "394-0004-067",
            "source": "DGDA Allopathic Medicine Information export",
            "accessed_at": "2026-11-23", "green_eligible": True,
            "match_kind": "exact",
        })
        text = " ".join(lines).lower()
        self.assertIn("dgda-registered medicine", text)
        self.assertIn("394-0004-067", text)
        self.assertIn("omeprazole", text)
        for banned in ("approved", "price", "tk", "মূল্য"):
            self.assertNotIn(banned, text)

    def test_missing_record_is_neutral_unverified(self):
        lines = dgda_card_lines(None)
        text = " ".join(lines)
        self.assertIn("UNVERIFIED", text)
        self.assertIn("বক্স চেক করুন", text)

    def test_fuzzy_card_says_not_confirmed(self):
        lines = dgda_card_lines({
            "brand": "Maxpro", "generic": "Esomeprazole", "dar_no": "002-0328-067",
            "source": "DGDA Allopathic Medicine Information export",
            "accessed_at": "2026-11-23", "green_eligible": False,
            "match_kind": "fuzzy",
        })
        self.assertIn("Fuzzy name match", " ".join(lines))

    def test_card_html_escapes_csv_text(self):
        html = dgda_card_html({
            "brand": "<script>alert(1)</script>", "dar_no": "", "source": "",
            "accessed_at": "", "match_kind": "none", "green_eligible": False,
        })
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Quota/network messages, reader fallback and double-click protection."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu import vlm  # noqa: E402
from rxbondhu.fusion import fuse  # noqa: E402
from rxbondhu.lexicon import load_brands  # noqa: E402
from rxbondhu.state_guard import claim_read, release_read  # noqa: E402


class TestFriendlyErrors(unittest.TestCase):
    def test_quota_error_is_plain_language(self):
        text = vlm.friendly_error("429 RESOURCE_EXHAUSTED: Quota value: 0", "Reader 1")
        self.assertIn("quota", text)
        self.assertNotIn("RESOURCE_EXHAUSTED", text)
        self.assertNotIn("Traceback", text)

    def test_network_error_is_plain_language(self):
        text = vlm.friendly_error("ConnectionError: HTTPSConnectionPool timed out")
        self.assertIn("network error", text)
        self.assertNotIn("HTTPSConnectionPool", text)

    def test_traceback_is_never_shown(self):
        raw = 'Traceback (most recent call last):\n  File "vlm.py", line 9, in read\nboom'
        text = vlm.friendly_error(raw)
        self.assertNotIn("Traceback", text)
        self.assertNotIn("vlm.py", text)
        self.assertIn("unavailable", text)


class TestReaderFallback(unittest.TestCase):
    def setUp(self):
        self.brands = load_brands()

    def test_one_reader_offline_can_never_make_green(self):
        result = fuse({"brand": "Maxpro", "confidence": 0.91}, "Tab Maxpro 20mg",
                      self.brands, second_vlm_text="")
        self.assertEqual(result["colour"], "YELLOW")
        self.assertEqual(result["vlm2_guess"], "")

    def test_empty_reading_invents_nothing(self):
        result = fuse({"brand": "", "confidence": 0.0}, "", self.brands,
                      second_vlm_text="")
        self.assertEqual(result["colour"], "RED")
        self.assertEqual(result["name"], "")


class TestReadLock(unittest.TestCase):
    def test_second_click_is_blocked_until_release(self):
        state = {}
        self.assertTrue(claim_read(state))
        self.assertFalse(claim_read(state))
        release_read(state)
        self.assertTrue(claim_read(state))


if __name__ == "__main__":
    unittest.main()

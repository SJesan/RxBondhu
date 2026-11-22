import unittest
from unittest.mock import patch

from rxbondhu import vlm


class TestReaderPrompt(unittest.TestCase):
    def test_brand_hints_are_off_by_default(self):
        with patch.dict("os.environ", {}, clear=True):
            prompt = vlm._prompt()
        self.assertIn("Return a JSON array", prompt)
        self.assertNotIn("Common verified brands", prompt)

    def test_hints_can_be_enabled_explicitly(self):
        with patch.dict("os.environ", {"RX_VLM_PROMPT_HINTS": "1"}, clear=True):
            prompt = vlm._prompt()
        self.assertIn("Common verified brands", prompt)


if __name__ == "__main__":
    unittest.main()

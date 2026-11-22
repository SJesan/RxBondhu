import io
import json
import os
import sys
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu import groq_vlm  # noqa: E402


def _response(content: str):
    body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")
    handle = io.BytesIO(body)
    handle.__enter__ = lambda self: self
    handle.__exit__ = lambda self, *args: None
    return handle


class TestGroqReader(unittest.TestCase):
    def test_available_requires_key(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}, clear=False):
            ok, reason = groq_vlm.available()
        self.assertFalse(ok)
        self.assertIn("empty", reason)

    def test_read_parses_json_lines(self):
        image = Image.new("RGB", (24, 12), "white")
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
            with patch.object(groq_vlm.urllib.request, "urlopen",
                              return_value=_response('[{"medicine":"Napa","dose":"1+0+1"}]')):
                result = groq_vlm.read(image)
        self.assertEqual(result["error"], "")
        self.assertEqual(result["lines"], [{"medicine": "Napa", "dose": "1+0+1"}])
        self.assertEqual(result["model"], "qwen/qwen3.8-27b")

    def test_read_reports_failure_honestly(self):
        image = Image.new("RGB", (24, 12), "white")
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
            with patch.object(groq_vlm.urllib.request, "urlopen",
                              side_effect=RuntimeError("offline")):
                result = groq_vlm.read(image)
        self.assertEqual(result["lines"], [])
        self.assertIn("offline", result["error"])


if __name__ == "__main__":
    unittest.main()

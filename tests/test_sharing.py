import os
import sys
import unittest
from datetime import date
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu import sharing  # noqa: E402


SCHEDULE = {
    "medicines": [{
        "name": "Napa", "generic": "Paracetamol", "colour": "GREEN",
        "dose": {"morning": 1, "noon": 0, "night": 1, "days": 3,
                 "times_per_day": 2, "warnings": []},
    }],
    "warnings": [],
}


class TestSharing(unittest.TestCase):
    def test_calendar_link_has_three_slots_and_dhaka_tz(self):
        links = sharing.calendar_links(SCHEDULE, start_date=date(2026, 11, 24))
        self.assertEqual(len(links), 2)  # morning + night; noon dose is zero
        query = parse_qs(urlparse(links[0]["url"]).query)
        self.assertEqual(query["ctz"], ["Asia/Dhaka"])
        self.assertTrue(query["dates"][0].startswith("20261124T080000/"))
        self.assertIn("Napa", query["text"][0])

    def test_whatsapp_link_is_prepared_text_not_auto_send(self):
        url = sharing.whatsapp_link(SCHEDULE)
        self.assertTrue(url.startswith("https://wa.me/?text="))
        text = parse_qs(urlparse(url).query)["text"][0]
        self.assertIn("Napa", text)


if __name__ == "__main__":
    unittest.main()

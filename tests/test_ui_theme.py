"""Light/dark theme + compact UI helper tests (no browser needed)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu import ui  # noqa: E402


RECORD = {
    "brand": "Napa", "generic": "Paracetamol", "strength": "500 mg",
    "form": "Tablet", "company": "Test Pharma", "dar_no": "TEST-0001",
    "source": "DGDA Allopathic Medicine Information export",
    "accessed_at": "2026-11-23", "green_eligible": True, "match_kind": "exact",
}


class TestTheme(unittest.TestCase):
    def test_light_is_default_and_dark_is_normalised(self):
        self.assertEqual(ui.theme_name(None), "light")
        self.assertEqual(ui.theme_name(""), "light")
        self.assertEqual(ui.theme_name("Light"), "light")
        self.assertEqual(ui.theme_name("DARK"), "dark")
        self.assertEqual(ui.theme_name("dark"), "dark")

    def test_both_templates_substitute_without_leftover_placeholders(self):
        css = ui.CLEAN_CSS_TEMPLATE.substitute(ui.palette("light"))
        hero = ui.HERO_TEMPLATE.substitute(ui.palette("dark"))
        self.assertIn("--rx-bg: #F6FAF7", css)
        self.assertIn("--rx-bg: #08130D", ui.CLEAN_CSS_TEMPLATE.substitute(ui.palette("dark")))
        self.assertIn("CNN 95.90% = word-crop test accuracy", hero)
        self.assertNotIn("$", css)
        self.assertNotIn("$", hero)

    def test_dark_palette_has_distinct_surface_and_accent(self):
        light, dark = ui.palette("light"), ui.palette("dark")
        self.assertNotEqual(light["bg"], dark["bg"])
        self.assertNotEqual(light["surface"], dark["surface"])
        self.assertNotEqual(light["accent"], dark["accent"])

    def test_button_ink_and_shadow_follow_the_theme(self):
        css = ui.CLEAN_CSS_TEMPLATE.substitute(ui.palette("dark"))
        self.assertIn("--rx-on-accent: #04150C", css)
        self.assertIn("color: var(--rx-on-accent) !important", css)
        self.assertIn("--rx-button-shadow:", css)
        self.assertEqual(ui.palette("light")["on_accent"], "#FFFFFF")

    def test_not_sure_button_is_neutral_not_red(self):
        css = ui.CLEAN_CSS_TEMPLATE.substitute(ui.palette("light"))
        form_css = css.split('div[data-testid="stForm"] button {', 1)[1].split('}', 1)[0]
        self.assertIn("var(--rx-muted)", form_css)
        self.assertNotIn("var(--rx-red-fg)", form_css)
        self.assertIn("min-height:48px", form_css)

    def test_loading_capsule_animation_is_themed(self):
        html = ui.loading_html("dark")
        self.assertIn("rx-capsule-morph", html)
        self.assertIn("#34C97C", html)
        self.assertIn("দুটি AI পড়ছে", html)
        self.assertNotIn("$", html)


class TestCompactHelpers(unittest.TestCase):
    def test_compact_card_shows_only_high_value_fields(self):
        lines = ui.dgda_compact_lines(RECORD)
        text = " ".join(lines)
        self.assertIn("Generic: Paracetamol", text)
        self.assertIn("DAR No: TEST-0001", text)
        self.assertIn("Strength: 500 mg", text)
        self.assertIn("Form: Tablet", text)
        for hidden in ("Test Pharma", "DGDA Allopathic", "2026-11-23", "approved"):
            self.assertNotIn(hidden, text)

    def test_compact_card_escapes_csv_text(self):
        evil = {**RECORD, "generic": "<script>x</script>"}
        html = ui.dgda_compact_html(evil)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>x</script>", html)

    def test_demo_thumb_click_loads_it_like_an_upload(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "demo_rx_01.png"
            Image.new("RGB", (12, 8), "white").save(path)
            html = ui.demo_thumb_html(path, "Demo 01", 1)
        self.assertIn('href="?demo=demo_rx_01.png"', html)
        self.assertIn('target="_self"', html)
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("click to use", html)

    def test_crop_box_is_drawn_on_the_original_size(self):
        image = Image.new("RGB", (100, 80), "white")
        marked = ui.draw_crop_box(image, {"left": 10, "top": 10, "width": 40, "height": 30})
        self.assertEqual(marked.size, image.size)
        self.assertNotEqual(marked.getpixel((10, 10)), image.getpixel((10, 10)))
        self.assertEqual(image.getpixel((10, 10)), (255, 255, 255))


if __name__ == "__main__":
    unittest.main()

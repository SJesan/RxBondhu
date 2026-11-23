"""Layout guards: readable type, big buttons, short hero and clean demo art."""

import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rxbondhu import ui  # noqa: E402


class TestReadableLayout(unittest.TestCase):
    def setUp(self):
        self.css = ui.CLEAN_CSS_TEMPLATE.substitute(ui.palette("light"))

    def test_body_type_is_18px_and_buttons_are_tall(self):
        self.assertIn("--rx-body: 18px", self.css)
        self.assertIn("font-size: var(--rx-body)", self.css)
        self.assertIn("min-height: 48px !important", self.css)

    def test_light_muted_text_is_dark_enough(self):
        self.assertEqual(ui.palette("light")["muted"], "#355445")

    def test_step_indicator_is_large(self):
        step_nav = self.css.split(".rx-step-nav span {", 1)[1].split("}", 1)[0]
        self.assertIn("font-size: 1rem", step_nav)
        self.assertIn("padding: 8px 14px", step_nav)

    def test_cards_have_generous_padding(self):
        card = self.css.split('div[data-testid="stContainer"] {', 1)[1].split("}", 1)[0]
        self.assertIn("padding: 18px 20px", card)


class TestHeroAndSidebar(unittest.TestCase):
    def test_compact_hero_is_one_line_and_has_no_canvas(self):
        html = ui.COMPACT_HERO_TEMPLATE.substitute(ui.palette("light"))
        self.assertIn("rx-quick-hero", html)
        self.assertIn("Bangla schedule + audio", html)
        self.assertNotIn("<canvas", html)
        self.assertNotIn("$", html)

    def test_sidebar_has_at_most_two_chips_and_labelled_number(self):
        html = ui.sidebar_header_html({"available": True}, True)
        self.assertEqual(html.count('class="rx-chip'), 2)
        self.assertIn("CNN 95.90% = word-crop test accuracy", html)
        self.assertNotIn("Groq", html)

    def test_groq_disclosure_lives_in_model_info(self):
        html = ui.model_info_html({"available": True}, True)
        self.assertIn("Groq", html)
        self.assertIn("not shipped", html)


class TestAppSourceGuards(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as fh:
            self.app = fh.read()

    def test_coverage_slider_is_inside_advanced(self):
        self.assertIn('with st.expander("Advanced — crop margin"', self.app)
        advanced = self.app.split('with st.expander("Advanced — crop margin"', 1)[1]
        self.assertIn("st.slider", advanced.split("st.session_state.crop", 1)[0])

    def test_not_sure_button_and_no_coming_soon(self):
        self.assertIn('st.form_submit_button("Not sure?")', self.app)
        self.assertNotIn("Coming soon", self.app)
        self.assertNotIn("Looks wrong", self.app)

    def test_compact_hero_on_screens_two_and_three(self):
        self.assertIn("compact=st.session_state.page in (2, 3)", self.app)

    def test_session_only_photo_note_present(self):
        self.assertIn("ছবি সংরক্ষণ করা হয় না", self.app)

    def test_demo_image_footer_removed(self):
        path = os.path.join(ROOT, "tools", "make_demo_images.py")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn("replace tomorrow", source)
        self.assertIn("fictional data", source)


if __name__ == "__main__":
    unittest.main()

"""Modern light/dark UI helpers for RxBondhu.

A local Three.js scene gives a calm depth cue; CSS gives subtle 3D tilt to
cards. No CDN is required: three.min.js lives in static/ and Streamlit serves
it from /static/three.min.js. Themes are injected as CSS variables on each
rerun so a sidebar icon can switch them without any client-side hack.
"""

from html import escape
from string import Template

import streamlit as st

THEMES = {
    "light": {
        "bg": "#F6FAF7",
        "surface": "#FFFFFF",
        "surface_alt": "#F1F8F3",
        "text": "#153526",
        "muted": "#4F6B5B",
        "border": "#D5E7DA",
        "accent": "#0E6B3C",
        "accent_hover": "#0B5A32",
        "accent_soft": "#E8F5EC",
        "shadow": "0 12px 30px rgba(13,88,46,0.10)",
        "shadow_hover": "0 18px 38px rgba(13,88,46,0.16)",
        "hero_from": "#FAFDFB",
        "hero_to": "#EDF7F0",
        "hero_text": "#0B4B2A",
        "hero_muted": "#3D5B48",
        "pill_green": "0x147D46",
        "pill_white": "0xF7FBF8",
        "pill_band": "0xF7FBF8",
        "fallback_green": "#147D46",
        "fallback_white": "#FFFFFF",
        "badge_green_bg": "#E8F7ED",
        "badge_green_fg": "#0B6B3A",
        "badge_green_bd": "#BFE6CC",
        "badge_yellow_bg": "#FFF7DF",
        "badge_yellow_fg": "#8A6100",
        "badge_yellow_bd": "#F2D98D",
        "badge_red_bg": "#FDECEC",
        "badge_red_fg": "#9A2020",
        "badge_red_bd": "#F3C5C5",
        "badge_unv_bg": "#EEF4FA",
        "badge_unv_fg": "#26547A",
        "badge_unv_bd": "#C6DCEC",
    },
    "dark": {
        "bg": "#08130D",
        "surface": "#10241A",
        "surface_alt": "#163124",
        "text": "#E8F4EC",
        "muted": "#A8C4B2",
        "border": "#224433",
        "accent": "#38D17F",
        "accent_hover": "#5BE096",
        "accent_soft": "#173B29",
        "shadow": "0 14px 34px rgba(0,0,0,0.34)",
        "shadow_hover": "0 20px 44px rgba(0,0,0,0.46)",
        "hero_from": "#10281B",
        "hero_to": "#0A1B12",
        "hero_text": "#E9F7EE",
        "hero_muted": "#A8C4B2",
        "pill_green": "0x2FBF6E",
        "pill_white": "0xE8F4EC",
        "pill_band": "0x38D17F",
        "fallback_green": "#2FBF6E",
        "fallback_white": "#E8F4EC",
        "badge_green_bg": "#173B29",
        "badge_green_fg": "#8FE5B4",
        "badge_green_bd": "#2F7A50",
        "badge_yellow_bg": "#3B3316",
        "badge_yellow_fg": "#F3D27A",
        "badge_yellow_bd": "#8A7228",
        "badge_red_bg": "#411C1C",
        "badge_red_fg": "#FFAAAA",
        "badge_red_bd": "#8A3838",
        "badge_unv_bg": "#152B3A",
        "badge_unv_fg": "#9CCDF0",
        "badge_unv_bd": "#315A75",
    },
}


def theme_name(value: str | None) -> str:
    """Normalise the two supported theme names."""
    return "dark" if str(value or "").strip().casefold() == "dark" else "light"


def palette(theme: str | None = None) -> dict:
    return dict(THEMES[theme_name(theme)])


CLEAN_CSS_TEMPLATE = Template("""
<style>
:root {
  --rx-bg: $bg;
  --rx-surface: $surface;
  --rx-surface-alt: $surface_alt;
  --rx-text: $text;
  --rx-muted: $muted;
  --rx-border: $border;
  --rx-accent: $accent;
  --rx-accent-hover: $accent_hover;
  --rx-accent-soft: $accent_soft;
  --rx-shadow: $shadow;
  --rx-shadow-hover: $shadow_hover;
  --rx-green-bg: $badge_green_bg;
  --rx-green-fg: $badge_green_fg;
  --rx-green-bd: $badge_green_bd;
  --rx-yellow-bg: $badge_yellow_bg;
  --rx-yellow-fg: $badge_yellow_fg;
  --rx-yellow-bd: $badge_yellow_bd;
  --rx-red-bg: $badge_red_bg;
  --rx-red-fg: $badge_red_fg;
  --rx-red-bd: $badge_red_bd;
  --rx-unv-bg: $badge_unv_bg;
  --rx-unv-fg: $badge_unv_fg;
  --rx-unv-bd: $badge_unv_bd;
}
html, body, .stApp {
  background: var(--rx-bg) !important;
  color: var(--rx-text);
}
.stApp { background-image: none !important; }
.block-container { padding-top: 1.1rem; max-width: 1180px; }
.stMarkdown, .stCaption, .stText, .stSubheader, .stTitle, .stMetric, .stCode {
  color: var(--rx-text);
}
.stCaption, [data-testid="stCaptionContainer"] { color: var(--rx-muted) !important; }
hr { border-color: var(--rx-border) !important; }

div[data-testid="stContainer"] {
  background: var(--rx-surface);
  border: 1px solid var(--rx-border);
  border-radius: 18px;
  padding: 14px 18px;
  box-shadow: var(--rx-shadow);
  transition: transform 0.25s cubic-bezier(.2,.7,.3,1), box-shadow 0.25s;
  transform-style: preserve-3d;
}
div[data-testid="stContainer"]:hover {
  transform: perspective(900px) rotateX(1.6deg) translateY(-3px);
  box-shadow: var(--rx-shadow-hover);
}
div[data-testid="stExpander"] {
  background: var(--rx-surface);
  border: 1px solid var(--rx-border) !important;
  border-radius: 14px !important;
  box-shadow: var(--rx-shadow);
  overflow: hidden;
}
div[data-testid="stExpander"] summary { color: var(--rx-text) !important; }
div[data-testid="stMetric"] {
  background: var(--rx-surface);
  border: 1px solid var(--rx-border);
  border-radius: 14px;
  padding: 10px 14px;
  box-shadow: var(--rx-shadow);
}
div[data-testid="stMetricLabel"], div[data-testid="stMetricValue"] {
  color: var(--rx-text) !important;
}
div[data-testid="stTabs"] [role="tab"] {
  color: var(--rx-muted) !important;
  border-radius: 999px !important;
}
div[data-testid="stTabs"] [aria-selected="true"] {
  color: var(--rx-accent) !important;
  background: var(--rx-accent-soft) !important;
}
div[data-testid="stDataFrame"] {
  border: 1px solid var(--rx-border);
  border-radius: 14px;
  overflow: hidden;
}
div[data-testid="stDataFrame"] [role="columnheader"] {
  background: var(--rx-accent-soft) !important;
  color: var(--rx-text) !important;
  font-weight: 800 !important;
}
div[data-testid="stDataFrame"] [role="cell"] { color: var(--rx-text) !important; }
[data-testid="stTextInput"] input, [data-testid="stSelectbox"] > div,
[data-testid="stDateInput"] input {
  background: var(--rx-surface) !important;
  color: var(--rx-text) !important;
  border-color: var(--rx-border) !important;
  border-radius: 12px !important;
}
div.stButton > button, div.stDownloadButton > button,
div[data-testid="stLinkButton"] > a {
  border-radius: 999px !important;
  border: 1px solid var(--rx-accent) !important;
  background: linear-gradient(135deg, var(--rx-accent), var(--rx-accent-hover)) !important;
  color: #FFFFFF !important;
  font-weight: 800 !important;
  padding: 0.55rem 1.25rem !important;
  box-shadow: 0 6px 16px rgba(14,107,60,0.24);
  text-decoration: none !important;
  transition: transform 0.2s, box-shadow 0.2s;
}
div.stButton > button:hover:not(:disabled), div.stDownloadButton > button:hover,
div[data-testid="stLinkButton"] > a:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(14,107,60,0.32);
}
div.stButton > button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  filter: grayscale(0.3);
  transform: none;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--rx-surface-alt) 0%, var(--rx-bg) 100%) !important;
  border-right: 1px solid var(--rx-border) !important;
  color: var(--rx-text) !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
  color: var(--rx-muted) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  color: var(--rx-text) !important;
}

.rx-kicker {
  color: var(--rx-accent); font-size: 0.78rem; font-weight: 800;
  letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.3rem;
}
.rx-step {
  display:inline-block; padding:0.32rem 0.8rem; border-radius:999px;
  background:var(--rx-accent-soft); color:var(--rx-accent); font-weight:800;
  font-size:0.82rem; border:1px solid var(--rx-border); margin-bottom:0.5rem;
}
.rx-badge {
  display:inline-block; padding:0.25rem 0.7rem; border-radius:999px;
  font-weight:800; font-size:0.8rem; border:1px solid;
}
.rx-green { background:var(--rx-green-bg); color:var(--rx-green-fg); border-color:var(--rx-green-bd); }
.rx-yellow { background:var(--rx-yellow-bg); color:var(--rx-yellow-fg); border-color:var(--rx-yellow-bd); }
.rx-red { background:var(--rx-red-bg); color:var(--rx-red-fg); border-color:var(--rx-red-bd); }
.rx-unverified { background:var(--rx-unv-bg); color:var(--rx-unv-fg); border-color:var(--rx-unv-bd); }
.rx-chip {
  display:inline-block; padding:0.22rem 0.6rem; border-radius:999px;
  background:var(--rx-accent-soft); color:var(--rx-text);
  border:1px solid var(--rx-border); font-size:0.75rem; font-weight:700;
  margin:0.15rem 0.25rem 0.15rem 0;
}
.rx-chip-good { color:var(--rx-green-fg); border-color:var(--rx-green-bd); }
.rx-chip-warn { color:var(--rx-yellow-fg); border-color:var(--rx-yellow-bd); }
.rx-disclaimer {
  background:var(--rx-surface-alt); border-left:4px solid var(--rx-accent);
  border-radius:10px; padding:0.7rem 0.9rem; color:var(--rx-text);
}
.rx-sidebar-title { color:var(--rx-text); font-size:1.35rem; font-weight:900; margin:0; }
.rx-sidebar-sub { color:var(--rx-muted); font-size:0.82rem; margin:0.15rem 0 0.7rem; }
.rx-credit { color:var(--rx-muted); font-size:0.78rem; margin-top:0.6rem; }
</style>
""")


def inject_css(theme: str | None = None) -> None:
    """Apply the selected theme. Text size is injected separately in app.py."""
    from streamlit import markdown

    markdown(CLEAN_CSS_TEMPLATE.substitute(palette(theme)), unsafe_allow_html=True)


HERO_TEMPLATE = Template("""
<div class="rx-shell">
  <div class="rx-copy">
    <div class="rx-kicker" style="color:$accent;">CoU AI Hackathon 2026 · Healthcare</div>
    <h1 style="margin:0 0 4px 0;font-size:1.95rem;color:$hero_text;letter-spacing:-.02em;">
      RxBondhu <span style="color:$accent;">রক্সবন্ধু</span>
    </h1>
    <p style="margin:0;color:$hero_muted;font-size:0.92rem;line-height:1.5;">
      Handwritten prescription photo → <b style="color:$hero_text;">two AI readers</b>
      → DGDA-checked brand → Bangla schedule + audio.<br>
      <span style="color:$accent;font-weight:700;">Safe by design: nothing becomes a schedule before you confirm.</span>
    </p>
    <div style="margin-top:10px;">
      <span class="rx-chip">2 Gemini readers</span>
      <span class="rx-chip">own CNN · 95.90%</span>
      <span class="rx-chip">DGDA snapshot 23 Nov</span>
    </div>
  </div>
  <div id="rx-fx" style="width:250px;height:160px;flex:0 0 250px;">
    <div class="rx-fallback-pill"><i></i><i></i></div>
  </div>
</div>
<style>
.rx-shell{display:flex;align-items:center;gap:22px;padding:16px 22px;border-radius:22px;
  background:linear-gradient(135deg,$hero_from 0%,$hero_to 100%);
  border:1px solid $border;box-shadow:$shadow;}
.rx-fallback-pill{width:160px;height:60px;margin:48px auto;border-radius:999px;overflow:hidden;
  display:flex;box-shadow:0 10px 20px rgba(12,80,40,.18);transform:rotate(-18deg);}
.rx-kicker{color:$accent;font-size:0.78rem;font-weight:800;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.3rem;}
.rx-chip{display:inline-block;padding:0.22rem 0.6rem;border-radius:999px;background:$accent_soft;color:$hero_text;border:1px solid $border;font-size:0.75rem;font-weight:700;margin:0.15rem 0.25rem 0.15rem 0;}
.rx-fallback-pill i{flex:1;background:$fallback_green;}
.rx-fallback-pill i+i{background:$fallback_white;border-left:2px solid $border;}
@media(max-width:760px){.rx-shell{flex-direction:column;align-items:flex-start;}#rx-fx{width:100%!important;flex-basis:auto!important;}}
</style>
<script src="app/static/three.min.js"></script>
<script>
(function(){
  var host = document.getElementById('rx-fx');
  if (!host) return;
  if (typeof THREE === 'undefined') return;
  host.innerHTML = '';
  var W = 250, H = 160;
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(38, W/H, 0.1, 100);
  camera.position.set(0, 0.4, 6.4);
  var renderer = new THREE.WebGLRenderer({alpha:true, antialias:true});
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  host.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  var key = new THREE.DirectionalLight(0xffffff, 0.95); key.position.set(2,3,4); scene.add(key);
  var rim = new THREE.PointLight($pill_green, 0.9); rim.position.set(-3,1,2); scene.add(rim);

  var pill = new THREE.Group();
  var green = new THREE.MeshStandardMaterial({color:$pill_green, roughness:0.35, metalness:0.12});
  var white = new THREE.MeshStandardMaterial({color:$pill_white, roughness:0.3, metalness:0.05});
  var body = new THREE.Mesh(new THREE.CylinderGeometry(0.62,0.62,1.55,48), green);
  body.rotation.z = Math.PI/2; pill.add(body);
  var left = new THREE.Mesh(new THREE.SphereGeometry(0.62,48,32), green);
  left.position.x = -0.78; pill.add(left);
  var right = new THREE.Mesh(new THREE.SphereGeometry(0.62,48,32), white);
  right.position.x = 0.78; pill.add(right);
  var band = new THREE.Mesh(new THREE.TorusGeometry(0.635,0.035,12,48),
    new THREE.MeshStandardMaterial({color:$pill_band, roughness:0.3}));
  band.rotation.y = Math.PI/2; pill.add(band);
  pill.rotation.set(0.25,-0.5,0.35);
  scene.add(pill);

  var shadow = new THREE.Mesh(new THREE.CircleGeometry(1.05,48),
    new THREE.MeshBasicMaterial({color:$pill_green, transparent:true, opacity:0.10}));
  shadow.rotation.x = -Math.PI/2; shadow.position.set(0,-1.15,0); scene.add(shadow);

  var start = Date.now();
  (function loop(){
    var t = (Date.now()-start)/1000;
    pill.rotation.y = -0.5 + t*0.35;
    pill.position.y = Math.sin(t*1.4)*0.09;
    shadow.material.opacity = 0.10 - Math.sin(t*1.4)*0.02;
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  })();
})();
</script>
""")


def hero(theme: str | None = None) -> None:
    """Compact 3D hero card shown above the step content."""
    st.iframe(HERO_TEMPLATE.substitute(palette(theme)), height=196)


def sidebar_header_html(info: dict | None, key_ok: bool) -> str:
    """Modern, compact sidebar identity + status chips."""
    info = info or {}
    cnn_class = "rx-chip-good" if info.get("available") else "rx-chip-warn"
    cnn_text = "CNN 95.90%" if info.get("available") else "CNN offline"
    key_class = "rx-chip-good" if key_ok else "rx-chip-warn"
    key_text = "Reader keys ready" if key_ok else "Reader keys missing"
    return (
        '<p class="rx-sidebar-title">💊 RxBondhu</p>'
        '<p class="rx-sidebar-sub">Handwritten prescription → Bangla schedule</p>'
        f'<span class="rx-chip {cnn_class}">{escape(cnn_text)}</span>'
        f'<span class="rx-chip {key_class}">{escape(key_text)}</span>'
        '<span class="rx-chip">DGDA 23 Nov</span>'
        '<span class="rx-chip rx-chip-warn">Groq not shipped</span>'
    )


def model_info_html(info: dict | None, key_ok: bool) -> str:
    """Full model facts, deliberately separate from the compact chips."""
    info = info or {}
    acc = escape(str(info.get("test_accuracy") or "0.9590"))
    cnn = ("EfficientNet-B0 · 78 classes · held-out word-crop accuracy "
           f"{acc} (748/780). Real-photo accuracy is reported separately.")
    readers = ("Reader 1: gemini-3.5-flash-lite · Reader 2: gemini-3.1-flash-lite. "
               + ("Both keys available." if key_ok else "Keys unavailable; app continues with CNN."))
    return (
        "<ul style='margin:0;padding-left:1.1rem;font-size:0.82rem;line-height:1.5;'>"
        f"<li>{escape(readers)}</li>"
        f"<li>{escape(cnn)}</li>"
        "<li>Brand identity: committed DGDA Allopathic snapshot (23 Nov 2026), "
        "23,804 verified entries; no runtime network call.</li>"
        "<li>Groq and RxFusion were evaluated but failed the gate; not shipped.</li>"
        "</ul>"
    )


def badge(colour: str) -> str:
    """HTML badge for GREEN / YELLOW / UNVERIFIED / RED."""
    mapping = {
        "GREEN": ("rx-green", "🟢 GREEN"),
        "YELLOW": ("rx-yellow", "🟡 YELLOW"),
        "UNVERIFIED": ("rx-unverified", "🔍 UNVERIFIED"),
        "RED": ("rx-red", "🔴 RED"),
    }
    css, label = mapping.get(str(colour).upper(), ("rx-red", str(colour)))
    return f'<span class="rx-badge {css}">{label}</span>'


def dgda_card_lines(record: dict | None) -> list[str]:
    """Information-only DGDA provenance lines for the review side card.

    Deliberately neutral: it never says "approved", never gives price or dose
    advice, and a missing DAR No stays UNVERIFIED rather than a claim about
    regulatory status.
    """
    if not record:
        return ["DGDA export-এ এই নাম পাওয়া যায়নি — UNVERIFIED, বক্স চেক করুন।"]

    dar = str(record.get("dar_no") or "").strip()
    source = str(record.get("source") or "")
    if dar:
        title = f"DGDA-registered medicine — DAR No {dar}"
    elif "box" in source.lower() or "pharmacist" in source.lower():
        title = "Box / pharmacist checked — DGDA DAR not matched (conflict flagged)"
    else:
        title = "DGDA-registered medicine — DAR No not listed"

    lines = [
        title,
        f"ব্র্যান্ড: {record.get('brand') or '—'}",
        f"জেনেরিক: {record.get('generic') or '—'}",
        f"শক্তি: {record.get('strength') or '—'}",
        f"ডোজ ফর্ম: {record.get('form') or '—'}",
        f"কোম্পানি: {record.get('company') or '—'}",
        f"উৎস: {source or '—'}",
        f"সংগৃহীত: {record.get('accessed_at') or '—'}",
    ]
    if not record.get("green_eligible") or record.get("match_kind") == "fuzzy":
        lines.append("Fuzzy name match — confirm on the paper; not a DGDA-confirmed identity.")
    return lines


def dgda_card_html(record: dict | None) -> str:
    """Rendered with escaping: CSV text must never become HTML."""
    lines = "".join(
        f"<div style='margin:2px 0;color:var(--rx-muted);'>{escape(line)}</div>"
        for line in dgda_card_lines(record)
    )
    return (
        "<div style='background:var(--rx-surface-alt);border:1px solid var(--rx-border);"
        "border-radius:14px;padding:10px 12px;'>"
        "<div style='font-weight:800;color:var(--rx-text);margin-bottom:4px;'>DGDA তথ্য</div>"
        f"{lines}</div>"
    )


def dgda_compact_lines(record: dict | None) -> list[str]:
    """Four high-value fields shown before the More info expander."""
    if not record:
        return ["Generic: —", "DAR No: —", "Strength: —", "Form: —",
                "UNVERIFIED — check the box with a pharmacist."]
    dar = str(record.get("dar_no") or "").strip()
    return [
        f"Generic: {record.get('generic') or '—'}",
        f"DAR No: {dar or 'not matched — verify on box'}",
        f"Strength: {record.get('strength') or '—'}",
        f"Form: {record.get('form') or '—'}",
    ]


def dgda_compact_html(record: dict | None) -> str:
    """Escaped compact DGDA card. No approval, dose or price claim."""
    lines = "".join(
        f"<div style='margin:2px 0;color:var(--rx-muted);'>{escape(line)}</div>"
        for line in dgda_compact_lines(record)
    )
    return (
        "<div style='background:var(--rx-surface-alt);border:1px solid var(--rx-border);"
        "border-radius:14px;padding:10px 12px;'>"
        "<div style='font-weight:800;color:var(--rx-text);margin-bottom:4px;'>DGDA তথ্য</div>"
        f"{lines}"
        "<div style='font-size:0.75rem;color:var(--rx-muted);margin-top:6px;'>"
        "Identity from the checked export only — not dose advice.</div></div>"
    )


def draw_crop_box(image, box: dict | None, colour: str = "#2E8B57", width: int = 5):
    """Draw the selected crop rectangle on the original image only."""
    from PIL import ImageDraw

    marked = image.copy()
    if not box:
        return marked
    left = int(box.get("left", 0))
    top = int(box.get("top", 0))
    right = min(marked.width, left + int(box.get("width", 0)))
    bottom = min(marked.height, top + int(box.get("height", 0)))
    draw = ImageDraw.Draw(marked)
    for offset in range(width):
        draw.rectangle(
            (left + offset, top + offset, right - offset, bottom - offset),
            outline=colour,
        )
    return marked


def step_header(step: int, bangla: str, english: str) -> None:
    from streamlit import markdown

    markdown(
        f'<div class="rx-step">STEP {step} / 3</div>'
        f'<h2 style="margin:0 0 4px 0;color:var(--rx-text);font-size:1.45rem;">{escape(bangla)}</h2>'
        f'<p style="margin:0 0 12px 0;color:var(--rx-muted);">{escape(english)}</p>',
        unsafe_allow_html=True,
    )

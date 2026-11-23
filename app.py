"""RxBondhu — Streamlit app (3 screens).

1) Photo + crop   2) Two-AI reading with GREEN/YELLOW/RED   3) Review + Bangla schedule + audio
Run:  streamlit run app.py
"""

import os
import sys
import tempfile
from datetime import date, timedelta
from html import escape
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rxbondhu import bangla, camera, multi, pipeline, recognizer, reminders, sharing, tts, ui, vlm  # noqa: E402
from rxbondhu.lexicon import load_brands, lookup_exact, verify_name  # noqa: E402
from rxbondhu.state_guard import (analysis_is_current, claim_read,  # noqa: E402
                                  confirmed_rows_are_current, release_read)

st.set_page_config(page_title="RxBondhu | রক্সবন্ধু", page_icon="💊", layout="wide")

DISCLAIMER_TEXT = (
    "এটি কেবল একটি পড়ার সহায়তা, ডাক্তারের পরামর্শ নয়। "
    "কোনো ওষুধ শুরু, বদল বা বন্ধ করার আগে ডাক্তার বা ফার্মাসিস্টের সাথে নিশ্চিত করুন।"
)
DEMO_DISCLAIMER = f'<div class="rx-disclaimer"><b>{DISCLAIMER_TEXT}</b></div>'


def init_state():
    defaults = {"page": 1, "source": None, "crop": None, "analysis": None,
                "confirmed": None, "schedule": None, "audio": None,
                "read_count": 0, "font_scale": "Large", "theme": "Light",
                "reading_lock": False,
                # Multi-prescription mode. All defaults are inert until the
                # dedicated 2-3 image uploader is used.
                "multi_mode": False, "sources": [], "multi_analyses": [],
                "read_cache": {}, "multi_upload_seq": 0,
                "single_seen": None, "multi_seen": None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_reading():
    """Drop stale/out-of-date results and return to the photo screen."""
    st.session_state.analysis = None
    st.session_state.confirmed = None
    st.session_state.schedule = None
    st.session_state.audio = None
    st.session_state.multi_mode = False
    st.session_state.sources = []
    st.session_state.multi_analyses = []
    st.session_state.page = 1
    st.rerun()


def apply_query_actions():
    """Turn a demo thumbnail click into a normal source-image change.

    The thumbnail is a plain link, so clicking one reloads the script with a
    query parameter. We apply it once and remove the parameter — from here on
    the app treats it exactly like an upload. Stateful actions (RED flag) use
    real Streamlit widgets so a rerun never loses the current reading.
    """
    params = st.query_params
    demo = params.get("demo")
    if demo:
        demo_dir = Path(__file__).resolve().parent / "assets" / "demo"
        path = demo_dir / Path(str(demo)).name
        if path.is_file():
            st.session_state.source = Image.open(path).convert("RGB")
            st.session_state.crop = None
            st.session_state.analysis = None
            st.session_state.confirmed = None
            st.session_state.schedule = None
            st.session_state.audio = None
            st.session_state.multi_mode = False
            st.session_state.sources = []
            st.session_state.multi_upload_seq += 1  # clears the multi uploader
            st.session_state.page = 1
            st.session_state.demo_loaded = path.name
        if "demo" in params:
            del params["demo"]
        st.rerun()


def crop_ui(image: Image.Image, coverage: int = 92, key: str = "crop"):
    """Return (crop, box) so we can show one bordered original, not two photos."""
    already_cropped = st.checkbox(
        "Already cropped — use the full image (no crop box)",
        value=False, key=f"already_{key}",
    )
    if already_cropped:
        st.caption("Using the full image as the medicine area.")
        return image, None
    try:
        from streamlit_cropper import st_cropper
        inset_x = int(image.width * (100 - coverage) / 200)
        inset_y = int(image.height * (100 - coverage) / 200)
        default_coords = (inset_x, image.width - inset_x,
                          inset_y, image.height - inset_y)
        cropped, box = st_cropper(
            image, realtime_update=True, default_coords=default_coords,
            box_color="#2E8B57", aspect_ratio=None, return_type="both",
            stroke_width=4, key=f"cropper_{key}_{coverage}",
        )
        return cropped, box
    except Exception as exc:
        st.info(f"Cropper unavailable ({exc}) — using the full image as the crop.")
        return image, None


def multi_photo_screen():
    """Screen 1 for 1-3 prescriptions: own crop per image, sequential read.

    Every image stays a separate group until the user confirms on screen 3.
    The read button is locked for the whole loop and identical crops are served
    from the session cache, so no double-click or repeat upload spends quota.
    """
    st.subheader("প্রেসক্রিপশন ছবি / Prescription images")
    st.caption("বক্সে শুধু ওষুধের লাইন রাখুন — নাম, স্বাক্ষর বা তারিখ নয়।")
    if st.button("Clear these prescriptions", key="multi_clear"):
        st.session_state.multi_mode = False
        st.session_state.sources = []
        st.session_state.multi_analyses = []
        st.session_state.confirmed = None
        st.session_state.schedule = None
        st.session_state.audio = None
        st.session_state.multi_seen = None
        st.session_state.multi_upload_seq += 1
        st.rerun()
    sample = Path(__file__).resolve().parent / "assets" / "demo" / "crop_example.png"
    if sample.is_file():
        st.image(sample, width=150, caption="Cropping example")
    st.caption("ছবি সংরক্ষণ করা হয় না — শুধু এই সেশনে ব্যবহৃত হয়।")
    with st.expander("Advanced — margin for each image", expanded=False):
        coverage = st.slider(
            "Medicine-area coverage (%)", 70, 98, 92, 2, key="coverage_multi",
            help="Default 92% means a 4% margin on each side of the photo.",
        )

    sources = []
    for index, item in enumerate(st.session_state.sources, start=1):
        st.markdown(f"**প্রেসক্রিপশন {bangla.digits(index)} / Prescription {index}**")
        crop, box = crop_ui(item["image"], coverage=coverage,
                            key=f"multi_{index}")
        item["crop"], item["box"] = crop, box
        sources.append(item)
    st.session_state.sources = sources
    if any(item["crop"] is None for item in sources):
        st.warning("Crop is not ready yet — drag a box around the medicine lines, then try again.")
        return
    st.caption("Green box = medicine area sent to the AI")
    if st.session_state.read_count >= 5:
        st.caption("Session reading limit reached — Gemini is paused, our CNN still works.")

    if st.button("🔍 Read prescriptions one by one →", type="primary",
                 disabled=st.session_state.reading_lock):
        if not claim_read(st.session_state):
            st.info("একটি পড়া চলছে — শেষ হলে আবার চেষ্টা করুন।")
            return
        loader = st.empty()
        try:
            def progress(number, total):
                loader.markdown(
                    f"**প্রেসক্রিপশন {bangla.digits(number)}/{bangla.digits(total)} "
                    f"পড়ছে… / Prescription {number} of {total}…**"
                )

            groups = multi.read_all(
                sources, st.session_state.read_cache,
                skip_vlm=lambda: st.session_state.read_count >= 5,
                progress=progress,
                on_read=lambda: st.session_state.update(
                    read_count=st.session_state.read_count + 1),
            )
            st.session_state.multi_analyses = groups
            st.session_state.analysis = None
            st.session_state.confirmed = None
            st.session_state.schedule = None
            st.session_state.audio = None
            st.session_state.page = 2
            loader.empty()
            st.rerun()
        except Exception as exc:
            loader.empty()
            st.error(f"Reading failed: {vlm.friendly_error(exc)}")
        finally:
            release_read(st.session_state)


def colour_badge(colour: str) -> str:
    """Kept as a thin wrapper so the rest of the app stays unchanged."""
    return ui.badge(colour)


def screen_1():
    ui.step_header(1, "১. ছবি দিন", "Upload a prescription photo or take one, then drag a box around the medicine lines only.")
    st.markdown(DEMO_DISCLAIMER, unsafe_allow_html=True)
    st.caption("Solo build for CoU AI Hackathon 2026")
    loaded = st.session_state.pop("demo_loaded", None)
    if loaded:
        st.success(f"Loaded {loaded} — drag the crop box, then read it.")

    info = recognizer.model_info()
    key_ok, _ = vlm.available()
    # AI pipeline details live in the sidebar Model info (collapsed by default).

    # Small fictional demo strip — clicking a thumbnail loads it like an upload.
    demo_dir = Path(__file__).resolve().parent / "assets" / "demo"
    demos = sorted(demo_dir.glob("demo_rx_*.png"))[:6]
    if demos:
        st.markdown("**Demo prescriptions** <span style='color:var(--rx-muted);font-size:0.8rem;'>"
                    "fictional samples — click one to use it</span>",
                    unsafe_allow_html=True)
        demo_cols = st.columns(6, gap="small")
        for index, (column, path) in enumerate(zip(demo_cols, demos), start=1):
            with column:
                column.markdown(ui.demo_thumb_html(path, f"Demo {index:02d}", index),
                                unsafe_allow_html=True)
        st.write("")

    with st.expander("🧪 CNN proof (single word crop, optional)", expanded=False):
        st.caption(
            "Our own EfficientNet-B0: held-out **word-crop** accuracy 0.9590 (748/780). "
            "Word-crop proof only — not whole-photo accuracy."
        )
        word_file = st.file_uploader("Upload one clear medicine word crop",
                                     type=["jpg", "jpeg", "png", "webp"], key="word_proof")
        if word_file:
            word_image = Image.open(word_file).convert("RGB")
            st.image(word_image, caption="CNN input", width=180)
            if st.button("Read this word with our CNN"):
                prediction = recognizer.predict_word(word_image, top_k=3)
                if prediction["top"]:
                    st.success(f"Top: **{prediction['brand']}** ({prediction['confidence']:.2f})")
                    st.caption("Other guesses: " + ", ".join(
                        f"{h['brand']} {h['confidence']:.2f}" for h in prediction["top"][1:]
                    ))
                else:
                    st.error("CNN checkpoint not available — nothing was guessed.")

    tab_upload, tab_camera = st.tabs(["Upload photo(s)", "Use camera"])
    with tab_upload:
        st.caption("১–৩টি প্রেসক্রিপশন ছবি দিন। Upload 1–3 photos; each gets its own crop box.")
        files = st.file_uploader(
            "Prescription image(s) (1–3)", type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key=f"multi_files_{st.session_state.multi_upload_seq}",
        )
        if files:
            if len(files) > 3:
                st.warning("সর্বোচ্চ ৩টি ছবি — প্রথম ৩টি ব্যবহার করা হয়েছে / "
                           "Maximum 3 images — only the first 3 were used.")
                files = files[:3]
            seen_multi = tuple((item.name, item.size) for item in files)
            images = [Image.open(item).convert("RGB") for item in files]
            if st.session_state.get("multi_seen") != seen_multi:
                st.session_state.multi_seen = seen_multi
                st.session_state.single_seen = None
                st.session_state.sources = [{"image": img} for img in images]
                st.session_state.multi_mode = len(images) > 1
                st.session_state.source = images[0] if len(images) == 1 else None
    with tab_camera:
        st.caption("Use the **rear camera** for prescriptions.")
        st.markdown("**Camera not working? Use the Upload photo(s) tab** — it works on every device.")
        photo = camera.capture()
        if photo is not None:
            st.session_state.source = photo
            st.session_state.multi_mode = False
            st.session_state.sources = [{"image": photo}]
            st.session_state.multi_upload_seq += 1  # camera stays single-image

    if st.session_state.multi_mode:
        multi_photo_screen()
        return

    if st.session_state.source is None:
        st.info("Choose a photo above, or click a demo card to load it into the reader.")
        return

    st.subheader("Select the medicine area")
    st.caption("বক্সে শুধু ওষুধের লাইন রাখুন — নাম, স্বাক্ষর বা তারিখ নয়।")
    sample = demo_dir / "crop_example.png"
    if sample.is_file():
        st.image(sample, width=150, caption="Cropping example")
    st.caption("ছবি সংরক্ষণ করা হয় না — শুধু এই সেশনে ব্যবহৃত হয়।")
    with st.expander("Advanced — crop margin", expanded=False):
        coverage = st.slider(
            "Medicine-area coverage (%)", 70, 98, 92, 2, key="coverage",
            help="Default 92% means a 4% margin on each side of the photo.",
        )
    st.session_state.crop, crop_box = crop_ui(
        st.session_state.source, coverage=coverage)
    if st.session_state.crop is None:
        st.warning("Crop is not ready yet — drag a box around the medicine lines, then try again.")
        return
    # The cropper itself is the only photo. Its green rectangle already shows
    # exactly what the readers see, so no second preview is rendered.
    st.caption("Green box = medicine area sent to the AI")
    if st.session_state.read_count >= 5:
        st.caption("Session reading limit reached — Gemini is paused, our CNN still works.")
    if st.button("🔍 Read with both AI models →", type="primary",
                 disabled=st.session_state.reading_lock):
        if not claim_read(st.session_state):
            st.info("একটি পড়া চলছে — শেষ হলে আবার চেষ্টা করুন।")
        else:
            skip_vlm = st.session_state.read_count >= 5
            loader = st.empty()
            loader.markdown(ui.loading_html(st.session_state.theme),
                            unsafe_allow_html=True)
            try:
                st.session_state.analysis = pipeline.analyse(
                    st.session_state.crop, full_image=st.session_state.source,
                    skip_vlm=skip_vlm)
                st.session_state.analysis.pop("images", None)
                st.session_state.read_count += 1
                st.session_state.page = 2
                loader.empty()
                st.rerun()
            except Exception as exc:
                loader.empty()
                st.error(f"Reading failed: {vlm.friendly_error(exc)}")
            finally:
                release_read(st.session_state)


def _closest_hint_html(item):
    """Show DGDA verification status and suggestion-only closest names."""
    name = str(item.get("name") or "").strip()
    if not name or name == "(unreadable)":
        return ""
    brands = load_brands()
    v = verify_name(name, brands)
    colour = str(item.get("colour") or "").upper()

    if colour == "GREEN" and v.get("dar_backed") and v.get("exact"):
        return ""

    if v.get("exact") and v.get("dar_backed"):
        status = "DGDA-registered in snapshot"
    elif v.get("exact") and v.get("in_dgda"):
        status = "In DGDA snapshot, but not DAR-backed/confirmed"
    else:
        status = "Not in DGDA snapshot"

    suggestions = [s.get("brand") for s in (v.get("suggestions") or item.get("suggestions") or []) if s.get("brand")]
    suggestions = [s for s in suggestions if str(s).casefold() != name.casefold()]
    hint = ""
    if suggestions and colour in ("UNVERIFIED", "YELLOW", "RED"):
        hint_names = ", ".join(escape(str(s)) for s in suggestions[:2])
        hint = (
            " · Closest DGDA: "
            f"<span style='color:var(--rx-text);font-weight:700;'>{hint_names}</span>"
            " <span style='color:var(--rx-muted);'>(suggestion only)</span>"
        )
    confirm_note = ""
    if colour != "GREEN":
        confirm_note = " · If not confirmed, ask pharmacist/doctor."
    return (
        f"<div style='color:var(--rx-muted);font-size:0.85rem;margin-top:4px;'>"
        f"{escape(status)}{hint}{escape(confirm_note)}</div>"
    )


def _render_status(analysis):
    """One short status strip and honest reader-failure notes (shared)."""
    cnn_ok = bool(analysis.get("cnn_available"))
    vlm_error = analysis.get("vlm_error") or ""
    second_error = analysis.get("vlm2_error") or ""
    status = (
        f"<span class='rx-chip'>{analysis.get('line_count', len(analysis['items']))} lines</span>"
        f"<span class='rx-chip {'rx-chip-good' if cnn_ok else 'rx-chip-warn'}'>"
        f"CNN {'ready' if cnn_ok else 'offline'}</span>"
        f"<span class='rx-chip'>{escape(str(analysis.get('vlm_model') or 'Reader 1 offline'))}</span>"
        f"<span class='rx-chip'>{escape(str(analysis.get('vlm2_model') or 'Reader 2 offline'))}</span>"
    )
    items = analysis.get("items") or []
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0, "UNVERIFIED": 0}
    for item in items:
        colour = str(item.get("colour") or "").upper()
        if colour in counts:
            counts[colour] += 1
    summary = (
        f"{len(items)} lines: {counts['GREEN']} GREEN, {counts['YELLOW']} YELLOW, "
        f"{counts['RED']} RED, {counts['UNVERIFIED']} UNVERIFIED"
    )
    st.markdown(f"**{escape(summary)}**<br>{status}", unsafe_allow_html=True)
    r1_name = str(analysis.get("vlm_model") or "Reader 1")
    r2_name = str(analysis.get("vlm2_model") or "Reader 2")
    if vlm_error:
        st.warning(
            f"Reader 1 is busy; continuing with Reader 2 and CNN. "
            f"Single-reader lines stay YELLOW at most. ({vlm.friendly_error(vlm_error, r1_name)})"
        )
    if second_error:
        st.warning(
            f"Reader 2 is busy; continuing with Reader 1. "
            f"Single-reader lines stay YELLOW at most. ({vlm.friendly_error(second_error, r2_name)})"
        )


def _render_item_card(item, form_key, persist=None, label=None):
    """The exact single-image card, reused per prescription with a unique key."""
    with st.container(border=True):
        if label:
            st.caption(label)
        right, card = st.columns([3, 2])
        safe_name = escape(str(item.get("name") or "(unreadable)"))
        right.markdown(
            f"{colour_badge(item['colour'])} "
            f"<b style='color:var(--rx-text);font-size:1.08rem;'>{safe_name}</b>",
            unsafe_allow_html=True,
        )
        right.markdown(
            f"<div class='rx-status-line'>{escape(ui.status_line(item['colour']))}</div>"
            f"<div class='rx-reason'>{escape(str(item['reason']))}</div>"
            f"{_closest_hint_html(item)}",
            unsafe_allow_html=True,
        )
        cnn_display = escape(str(item.get("cnn_display") or "not used for this line"))
        # Streamlit Cloud can hot-reload app.py while keeping an older
        # rxbondhu.ui in sys.modules. Never let a stale helper crash the
        # review screen: show a neutral card until the app is rebooted.
        fallback_html = (
            "<div style='background:var(--rx-surface-alt);border:1px solid var(--rx-border);"
            "border-radius:14px;padding:10px 12px;'>"
            "<b style='color:var(--rx-text);'>DGDA তথ্য</b><br>"
            "এই সেশনে DGDA তথ্য দেখা যাচ্ছে না — ছবিটি আবার পড়ুন।</div>"
        )
        try:
            compact_html = ui.dgda_compact_html(item.get("dgda_record"))
        except (AttributeError, TypeError, ValueError):
            compact_html = fallback_html
        card.markdown(compact_html, unsafe_allow_html=True)
        with card.expander("More info", expanded=False):
            st.markdown(
                "<div class='rx-readings'>"
                f"<div><b>CNN:</b> {cnn_display}</div>"
                f"<div><b>Reader 1:</b> {escape(str(item.get('vlm_guess') or item.get('vlm_text') or '—'))}</div>"
                f"<div><b>Reader 2:</b> {escape(str(item.get('vlm2_guess') or item.get('vlm2_text') or '—'))}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            raw_cnn = str(item.get("cnn_brand") or "—")
            raw_conf = float(item.get("cnn_confidence") or 0.0)
            st.caption(f"CNN raw guess (word-crop model only): {raw_cnn} ({raw_conf:.2f})")
            if item.get("cnn_conflicts"):
                st.caption(
                    "This guess conflicts with the readable/verified name, so it is shown here only. "
                    "Our CNN has 78 training classes and was trained on clean word crops, not whole prescriptions."
                )
            try:
                full_html = ui.dgda_card_html(item.get("dgda_record"))
            except (AttributeError, TypeError, ValueError):
                full_html = fallback_html
            st.markdown(full_html, unsafe_allow_html=True)
        # A real form button keeps the current reading in session state;
        # its dedicated test id also lets CSS give it a danger style.
        with right.form(form_key):
            if st.form_submit_button("Not sure?"):
                item["colour"] = "RED"
                item["reason"] = (
                    str(item.get("reason") or "") + " User flagged this line as wrong."
                ).strip()
                if persist:
                    persist()
                st.rerun()


def _rows_from_items(items, prescription=None):
    """Review rows. Single-image rows are byte-for-byte the old shape."""
    rows = []
    for item in items:
        options = [s["brand"] for s in item["suggestions"]]
        if item["name"] and item["name"] not in options:
            options.insert(0, item["name"])
        options.append("— skip this line —")
        unverified = str(item["colour"]).upper() == "UNVERIFIED"
        if unverified:
            options = [item["name"] or "— skip this line —", "— skip this line —"]
        index = item["index"]
        if prescription is not None:
            index = prescription * 100 + int(index)
        row = {
            "index": index,
            "name": options[0] if options else "— skip this line —",
            "original_name": item["name"] or "",
            "options": options,
            "dose": item["dose_text"],
            "generic": item["generic"] or "",
            "colour": item["colour"],
            "editable": unverified,
            "raw_reading": item.get("vlm_guess") or item.get("vlm2_guess") or "",
            "dgda_record": item.get("dgda_record"),
        }
        if prescription is not None:
            row["prescription"] = prescription
        rows.append(row)
    return rows


def screen_2():
    ui.step_header(2, "২. দুই AI-র পড়া", "Compare with the paper — nothing becomes a schedule until you confirm.")
    st.markdown(DEMO_DISCLAIMER, unsafe_allow_html=True)
    if st.session_state.multi_mode:
        _screen_2_multi()
        return
    analysis = st.session_state.analysis
    if not analysis_is_current(analysis):
        if analysis:
            # An older app version stored word-level results in this session.
            st.error("This reading came from an older version of RxBondhu. "
                     "Please read the photo again — no data is lost.")
            if st.button("← Back to photo and re-read"):
                reset_reading()
        else:
            st.warning("Go back to Step 1 and read a photo first.")
        return

    _render_status(analysis)
    if not analysis["items"]:
        st.info("কিছু পাওয়া যায়নি — ওষুধের লাইনের চারপাশে টাইট ক্রপ করে আবার চেষ্টা করুন। "
                "Nothing found — try a tighter crop around the medicine lines.")
        if st.button("← Back to photo"):
            st.session_state.page = 1
            st.rerun()
        return
    for item in analysis["items"]:
        persist = lambda: st.session_state.update(analysis=analysis)
        _render_item_card(item, f"wrong_{item['index']}", persist)
    if st.button("✏️ Confirm / correct each line →", type="primary"):
        st.session_state.confirmed = _rows_from_items(analysis["items"])
        st.session_state.page = 3
        st.rerun()
    if st.button("← Back to photo"):
        st.session_state.page = 1
        st.rerun()


def _screen_2_multi():
    """Review each prescription separately; nothing is merged yet."""
    groups = st.session_state.multi_analyses or []
    if not groups:
        st.warning("Go back to Step 1 and read the photos first.")
        if st.button("← Back to photo"):
            st.session_state.page = 1
            st.rerun()
        return

    for group in groups:
        number = group["number"]
        st.subheader(f"প্রেসক্রিপশন {bangla.digits(number)} / Prescription {number}")
        if group.get("error"):
            st.warning(group["error"])
        if group.get("analysis"):
            _render_status(group["analysis"])
        for line, item in enumerate(group["items"], start=1):
            # Items live in st.session_state.multi_analyses, so the in-place
            # flag is already persisted; no self-assigning callback is needed.
            _render_item_card(
                item, f"wrong_m{number}_{item['index']}",
                label=f"Prescription {number} · line {line}",
            )

    if st.button("✏️ Confirm / correct each line →", type="primary"):
        rows = []
        for group in groups:
            rows.extend(_rows_from_items(group["items"], prescription=group["number"]))
        st.session_state.confirmed = rows
        st.session_state.page = 3
        st.rerun()
    if st.button("← Back to photo"):
        st.session_state.page = 1
        st.rerun()


def screen_3():
    ui.step_header(3, "৩. নিশ্চিত করুন ও সময়সূচি", "You confirm every line. Only then do we build the Bangla schedule.")
    st.markdown(DEMO_DISCLAIMER, unsafe_allow_html=True)
    if st.session_state.multi_mode:
        chosen_now = [row for row in (st.session_state.confirmed or [])
                      if not str(row.get("name") or "").startswith("—")]
        st.caption(multi.count_text(len(st.session_state.sources), len(chosen_now)))
    rows = st.session_state.confirmed or []
    if not confirmed_rows_are_current(rows):
        if rows:
            st.error("This review came from an older version of RxBondhu. "
                     "Please read the photo again.")
            if st.button("← Back to photo and re-read"):
                reset_reading()
        else:
            st.warning("Nothing to review yet.")
        return

    brands = load_brands()
    last_prescription = None
    for row in rows:
        number = row.get("prescription")
        if number is not None and number != last_prescription:
            st.markdown(f"**প্রেসক্রিপশন {bangla.digits(number)} / Prescription {number}**")
            last_prescription = number
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 3, 2], gap="small")
            # Build DGDA-backed suggestion options (never auto-applied).
            current_name = str(row.get("name") or "").strip()
            base_options = list(row.get("options") or [])
            v_now = verify_name(current_name, brands) if current_name else {"suggestions": []}
            dgda_suggestions = [s.get("brand") for s in (v_now.get("suggestions") or row.get("suggestions") or []) if s.get("brand")]
            if row.get("editable") or str(row.get("colour") or "").upper() in ("UNVERIFIED", "YELLOW", "RED"):
                for s in dgda_suggestions:
                    if s and s not in base_options:
                        base_options.append(s)
            row["options"] = base_options

            if row.get("editable"):
                row["name"] = c1.text_input(
                    "Brand — unverified, type the name from the paper",
                    row["name"], key=f"name_{row['index']}",
                )
                if dgda_suggestions:
                    pick = c1.selectbox(
                        "DGDA suggestion (optional, not auto-applied)",
                        ["(keep typed name)"] + dgda_suggestions[:5],
                        index=0,
                        key=f"dgda_pick_{row['index']}",
                    )
                    if pick != "(keep typed name)":
                        row["name"] = pick
            else:
                row["name"] = c1.selectbox("Brand (choose or correct)", row["options"],
                                           index=0, key=f"name_{row['index']}")
            row["dose"] = c2.text_input("Dose (e.g. 1+0+1, BD, সকাল ১ টি)",
                                        row["dose"], key=f"dose_{row['index']}")

            # A human correction/selection is high-trust input, but we still verify
            # against DGDA snapshot. Never auto-apply suggestions.
            name = str(row.get("name") or "").strip()
            v = verify_name(name, brands) if name else None
            if name and name != str(row.get("original_name") or ""):
                if v and v.get("dar_backed") and v.get("exact"):
                    exact = v.get("record") or {}
                    row["generic"] = exact.get("generic") or row.get("generic") or ""
                    row["dgda_record"] = exact
                    row["colour"] = "GREEN"
                    row["reason"] = (
                        "Corrected by you to an exact DGDA-registered brand "
                        "— still confirm with the prescriber."
                    )
                elif v and v.get("in_dgda"):
                    exact = v.get("record") or {}
                    row["generic"] = exact.get("generic") or row.get("generic") or ""
                    row["dgda_record"] = exact
                    row["colour"] = "YELLOW"
                    row["reason"] = (
                        "In DGDA snapshot but not DAR-backed/conflict-checked for GREEN — confirm on paper."
                    )
                else:
                    row["colour"] = "UNVERIFIED"
                    row["reason"] = "Not in DGDA snapshot — check the box/prescriber."
                    row["dgda_record"] = None
            elif v:
                # Keep provenance visible even when unchanged.
                if v.get("in_dgda") and v.get("record"):
                    row["dgda_record"] = row.get("dgda_record") or v.get("record")

            # Only show DGDA provenance when the current name is actually in DGDA.
            record_for_display = row.get("dgda_record") if (v and v.get("in_dgda")) else None
            provenance = ui.identity_provenance(record_for_display)
            in_list = "In DGDA" if (v and v.get("in_dgda")) else "Not in DGDA"
            confirm_note = "If not confirmed, ask pharmacist/doctor." if row.get("colour") != "GREEN" else ""
            c3.markdown(
                f"<div class='rx-review-badge'>{colour_badge(row['colour'])}"
                f"<b style='color:var(--rx-text);font-size:0.95rem;'>"
                f"{escape(str(row['generic'] or 'unknown'))}</b></div>"
                f"<div class='rx-status-line'>{escape(ui.status_line(row['colour']))} · {escape(in_list)}</div>"
                f"<div class='rx-review-meta'>{escape(provenance)}</div>"
                + (f"<div class='rx-review-meta'>{escape(confirm_note)}</div>" if confirm_note else ""),
                unsafe_allow_html=True,
            )

    if st.button("✅ Build my Bangla schedule", type="primary"):
        chosen = [r for r in rows if not r["name"].startswith("—")]
        st.session_state.schedule = pipeline.build_schedule(chosen)
        if st.session_state.multi_mode:
            # Existing duplicate-generic check already ran on the merged list;
            # this only names the prescriptions so a cross-script repeat is seen.
            st.session_state.schedule["warnings"].extend(
                multi.cross_prescription_warning(chosen))
        st.session_state.audio = None

    schedule = st.session_state.schedule
    if schedule:
        st.subheader("আপনার সময়সূচি / Your schedule")
        st.markdown(
            bangla.schedule_table_html(schedule["medicines"]),
            unsafe_allow_html=True,
        )
        if schedule["warnings"]:
            for warning in schedule["warnings"]:
                st.warning(warning)
        summary = bangla.summary_text(schedule)
        st.markdown("**Bangla summary**")
        st.markdown(
            "<div style='background:var(--rx-surface-alt);border:1px solid var(--rx-border);"
            "border-radius:14px;padding:12px 14px;white-space:pre-wrap;color:var(--rx-text);'>"
            f"{escape(summary)}</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔊 শুনুন Bangla audio"):
            with st.spinner("Generating speech (first run downloads the TTS model)…"):
                result = tts.speak_bangla(summary)
            if result["path"]:
                st.session_state.audio = result["path"]
                st.caption(f"Engine: {result['engine']}")
                st.audio(result["path"])
            else:
                st.error(f"Audio failed: {result['error']}")

        st.subheader("Calendar & sharing")
        first_day = st.date_input("First reminder date", value=date.today() + timedelta(days=1),
                                  key="first_day")
        reminder = reminders.make_ics(schedule, start_date=first_day)
        ics_col, all_col = st.columns([1, 1])
        with ics_col:
            st.download_button(
                "📅 Download reminders (.ics)",
                data=reminder["ics"].encode("utf-8"),
                file_name="rxbondhu-reminders.ics",
                mime="text/calendar",
            )
        with all_col:
            st.link_button(
                "📅 Add all medicines once (Google Calendar)",
                sharing.calendar_all_link(schedule, start_date=first_day),
            )
        links = sharing.calendar_links(schedule, start_date=first_day)
        for link in links:
            st.markdown(f"- [📅 {link['medicine']} — {link['slot']}]({link['url']})")
        st.caption("Links add one example day (Asia/Dhaka); the .ics repeats the course. "
                   "Confirm all times with the prescriber.")

        st.subheader("Reminders")
        st.link_button("📱 WhatsApp reminder", sharing.whatsapp_link(schedule))
        st.caption("WhatsApp opens a prepared Bangla message — the app never sends it for you.")

        st.markdown("**Per-medicine audio**")
        for index, med in enumerate(schedule["medicines"]):
            if st.button(f"🔊 {med['name']}", key=f"med_audio_{index}"):
                one = {"medicines": [med], "warnings": []}
                path = os.path.join(tempfile.gettempdir(), f"rxbondhu_med_{index}.wav")
                result = tts.speak_bangla(bangla.summary_text(one), output=path)
                if result["path"]:
                    st.audio(result["path"])
                else:
                    st.error(f"Audio failed: {result['error']}")

    if st.button("← Back to reading"):
        st.session_state.page = 2
        st.rerun()


def sidebar():
    theme = ui.theme_name(st.session_state.theme)
    info = recognizer.model_info()
    key_ok, _ = vlm.available()
    with st.sidebar:
        st.markdown(ui.sidebar_header_html(info, key_ok), unsafe_allow_html=True)
        # Disabled radio replaced by a compact one-line step indicator so the
        # full AI disclosure fits on one screen without scrolling.
        steps = {1: "photo", 2: "reading", 3: "schedule"}
        st.markdown(
            "<div class='rx-step-nav'>"
            + "".join(
                f"<span class='{'on' if number == st.session_state.page else ''}'>"
                f"{number} · {label}</span>" for number, label in steps.items()
            )
            + "</div>",
            unsafe_allow_html=True,
        )
        toggle_label = "☀️ Switch to light" if theme == "dark" else "🌙 Switch to dark"
        if st.button(toggle_label, key="theme_toggle", use_container_width=True,
                     help="Light is the default. Dark mode is remembered for this session."):
            st.session_state.theme = "Light" if theme == "dark" else "Dark"
            st.rerun()
        choices = ["Normal", "Large", "Extra large"]
        chosen = st.selectbox("Text size", choices,
                              index=choices.index(st.session_state.font_scale),
                              key="font_picker")
        st.session_state.font_scale = chosen
        with st.expander("Model info", expanded=False):
            st.markdown(ui.model_info_html(info, key_ok), unsafe_allow_html=True)
        st.markdown(
            "<div class='rx-sidebar-foot'>"
            "Built fresh for CoU AI Hackathon 2026. AI: OpenCode (Big Pickle) + "
            "Google Gemini (2 readers) + our own CNN. Groq and RxFusion were "
            "evaluated but not shipped.<br><b>Solo build</b></div>",
            unsafe_allow_html=True,
        )


def main():
    init_state()
    apply_query_actions()
    theme = ui.theme_name(st.session_state.theme)
    ui.inject_css(theme)
    scale = st.session_state.get("font_scale", "Normal")
    factor = {"Normal": 1.0, "Large": 1.1, "Extra large": 1.3}.get(str(scale), 1.1)
    st.markdown(
        f"<style>:root{{--rx-body:calc(18px * {factor})!important;}}</style>",
        unsafe_allow_html=True,
    )
    ui.hero(theme, compact=st.session_state.page in (2, 3))
    sidebar()
    if st.session_state.page == 1:
        screen_1()
    elif st.session_state.page == 2:
        screen_2()
    else:
        screen_3()


if __name__ == "__main__":
    main()

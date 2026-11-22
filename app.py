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

from rxbondhu import bangla, camera, pipeline, recognizer, reminders, sharing, tts, ui, vlm  # noqa: E402
from rxbondhu.lexicon import load_brands, lookup_exact, suggest_brands  # noqa: E402
from rxbondhu.state_guard import analysis_is_current, confirmed_rows_are_current  # noqa: E402

st.set_page_config(page_title="RxBondhu | রক্সবন্ধু", page_icon="💊", layout="wide")

DISCLAIMER_TEXT = (
    "এটি কেবল একটি পড়ার সহায়তা, ডাক্তারের পরামর্শ নয়। "
    "কোনো ওষুধ শুরু, বদল বা বন্ধ করার আগে ডাক্তার বা ফার্মাসিস্টের সাথে নিশ্চিত করুন।"
)
DEMO_DISCLAIMER = f'<div class="rx-disclaimer"><b>{DISCLAIMER_TEXT}</b></div>'


def init_state():
    defaults = {"page": 1, "source": None, "crop": None, "analysis": None,
                "confirmed": None, "schedule": None, "audio": None,
                "read_count": 0, "font_scale": "Normal", "theme": "Light"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_reading():
    """Drop stale/out-of-date results and return to the photo screen."""
    st.session_state.analysis = None
    st.session_state.confirmed = None
    st.session_state.schedule = None
    st.session_state.audio = None
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


def colour_badge(colour: str) -> str:
    """Kept as a thin wrapper so the rest of the app stays unchanged."""
    return ui.badge(colour)


def screen_1():
    ui.step_header(1, "১. ছবি দিন", "Upload a prescription photo or take one, then drag a box around the medicine lines only.")
    st.caption("Made by Team Zero-Shot · solo build for CoU AI Hackathon 2026")
    loaded = st.session_state.pop("demo_loaded", None)
    if loaded:
        st.success(f"Loaded {loaded} — drag the crop box, then read it.")

    info = recognizer.model_info()
    key_ok, _ = vlm.available()
    with st.expander("🤖 AI pipeline — what is trained, what is verified", expanded=False):
        st.markdown(ui.model_info_html(info, key_ok), unsafe_allow_html=True)

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

    with st.expander("🧪 Our CNN — proof demo (single word crop)"):
        st.caption(
            "Our own EfficientNet-B0, fine-tuned here: held-out **word-crop** accuracy "
            "0.9590 (748/780). That is a clean word image, NOT a whole prescription photo — "
            "real-photo results are measured separately and reported honestly."
        )
        word_file = st.file_uploader("Upload one clear medicine word crop",
                                     type=["jpg", "jpeg", "png", "webp"], key="word_proof")
        if word_file:
            word_image = Image.open(word_file).convert("RGB")
            st.image(word_image, caption="CNN input", width=180)
            if st.button("Read this word with our CNN"):
                prediction = recognizer.predict_word(word_image, top_k=3)
                if prediction["top"]:
                    st.success(
                        f"Top: **{prediction['brand']}** ({prediction['confidence']:.2f})"
                    )
                    st.caption("Other guesses: " + ", ".join(
                        f"{h['brand']} {h['confidence']:.2f}" for h in prediction["top"][1:]
                    ))
                else:
                    st.error("CNN checkpoint not available — nothing was guessed.")

    tab_upload, tab_camera = st.tabs(["Upload photo", "Use camera"])
    with tab_upload:
        uploaded = st.file_uploader("Prescription image", type=["jpg", "jpeg", "png", "webp"])
        if uploaded:
            st.session_state.source = Image.open(uploaded).convert("RGB")
    with tab_camera:
        st.caption("Rear camera preferred for prescriptions. Camera access is optional — "
                   "the upload tab works on every device.")
        photo = camera.capture()
        if photo is not None:
            st.session_state.source = photo

    if st.session_state.source is None:
        st.info("Choose a photo above, or use one of the demo images as a visual reference.")
        return

    st.subheader("Select the medicine area")
    coverage = st.slider(
        "Medicine-area coverage (%) — start wide, then trim", 70, 98, 92, 2,
        key="coverage", help="92% means a 4% margin on each side of the photo.",
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
    if st.button("🔍 Read with both AI models →", type="primary"):
        skip_vlm = st.session_state.read_count >= 5
        loader = st.empty()
        loader.markdown(ui.loading_html(st.session_state.theme), unsafe_allow_html=True)
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
            st.error(f"Reading failed: {exc}")


def screen_2():
    ui.step_header(2, "২. দুই AI-র পড়া", "Compare with the paper — nothing becomes a schedule until you confirm.")
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

    cnn_ok = bool(analysis.get("cnn_available"))
    vlm_error = analysis.get("vlm_error") or ""
    second_error = analysis.get("vlm2_error") or ""
    # One short status strip replaces the old four metrics and legend block.
    status = (
        f"<span class='rx-chip'>{analysis.get('line_count', len(analysis['items']))} lines</span>"
        f"<span class='rx-chip {'rx-chip-good' if cnn_ok else 'rx-chip-warn'}'>"
        f"CNN {'ready' if cnn_ok else 'offline'}</span>"
        f"<span class='rx-chip'>{escape(str(analysis.get('vlm_model') or 'Reader 1 offline'))}</span>"
        f"<span class='rx-chip'>{escape(str(analysis.get('vlm2_model') or 'Reader 2 offline'))}</span>"
    )
    st.markdown(status, unsafe_allow_html=True)
    if vlm_error:
        st.warning(f"Reader 1 unavailable: {vlm_error} — continuing with Reader 2 and CNN.")
    if second_error:
        st.warning(f"Reader 2 unavailable: {second_error} — continuing with Reader 1 and CNN.")
    if not analysis["items"]:
        st.error("No medicine lines detected. Try a tighter, better-lit crop.")
    for item in analysis["items"]:
        with st.container(border=True):
            right, card = st.columns([3, 2])
            safe_name = escape(str(item.get("name") or "(unreadable)"))
            right.markdown(
                f"{colour_badge(item['colour'])} "
                f"<b style='color:var(--rx-text);font-size:1.08rem;'>{safe_name}</b>",
                unsafe_allow_html=True,
            )
            right.caption(item["reason"])
            confidence = float(item.get("cnn_confidence") or 0.0)
            right.write(
                f"CNN: `{item.get('cnn_brand') or '—'}` ({confidence:.2f}) · "
                f"Reader 1: `{item.get('vlm_guess') or item.get('vlm_text') or '—'}` · "
                f"Reader 2: `{item.get('vlm2_guess') or item.get('vlm2_text') or '—'}`"
            )
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
                try:
                    full_html = ui.dgda_card_html(item.get("dgda_record"))
                except (AttributeError, TypeError, ValueError):
                    full_html = fallback_html
                st.markdown(full_html, unsafe_allow_html=True)
            # A real form button keeps the current reading in session state;
            # its dedicated test id also lets CSS give it a danger style.
            with right.form(f"wrong_{item['index']}"):
                if st.form_submit_button("🚩 Looks wrong — mark RED"):
                    item["colour"] = "RED"
                    item["reason"] = (
                        str(item.get("reason") or "") + " User flagged this line as wrong."
                    ).strip()
                    st.session_state.analysis = analysis
                    st.rerun()
    if st.button("✏️ Confirm / correct each line →", type="primary"):
        brands = load_brands()
        rows = []
        for item in analysis["items"]:
            options = [s["brand"] for s in item["suggestions"]]
            if item["name"] and item["name"] not in options:
                options.insert(0, item["name"])
            options.append("— skip this line —")
            unverified = str(item["colour"]).upper() == "UNVERIFIED"
            if unverified:
                options = [item["name"] or "— skip this line —", "— skip this line —"]
            rows.append({
                "index": item["index"],
                "name": options[0] if options else "— skip this line —",
                "original_name": item["name"] or "",
                "options": options,
                "dose": item["dose_text"],
                "generic": item["generic"] or "",
                "colour": item["colour"],
                "editable": unverified,
                "raw_reading": item.get("vlm_guess") or item.get("vlm2_guess") or "",
                "dgda_record": item.get("dgda_record"),
            })
        st.session_state.confirmed = rows
        st.session_state.page = 3
        st.rerun()
    if st.button("← Back to photo"):
        st.session_state.page = 1
        st.rerun()


def screen_3():
    ui.step_header(3, "৩. নিশ্চিত করুন ও সময়সূচি", "You confirm every line. Only then do we build the Bangla schedule.")
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
    st.markdown(DEMO_DISCLAIMER, unsafe_allow_html=True)

    brands = load_brands()
    for row in rows:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 3, 2], gap="small")
            if row.get("editable"):
                row["name"] = c1.text_input(
                    "Brand — unverified, type the name from the paper",
                    row["name"], key=f"name_{row['index']}",
                )
            else:
                row["name"] = c1.selectbox("Brand (choose or correct)", row["options"],
                                           index=0, key=f"name_{row['index']}")
            row["dose"] = c2.text_input("Dose (e.g. 1+0+1, BD, সকাল ১ টি)",
                                        row["dose"], key=f"dose_{row['index']}")
            # A human correction from the paper is the highest-trust signal.
            # Re-check the badge as well as the generic when the name changes,
            # otherwise a corrected brand would keep an old RED flag.
            name = str(row.get("name") or "").strip()
            if name and name != str(row.get("original_name") or ""):
                exact = lookup_exact(name, brands)
                if exact:
                    row["generic"] = exact.get("generic") or row.get("generic") or ""
                    row["dgda_record"] = exact
                    row["colour"] = "GREEN"
                    row["reason"] = (
                        "Corrected by you to an exact DGDA-registered brand "
                        "— still confirm with the prescriber."
                    )
                else:
                    row["colour"] = "UNVERIFIED"
                    row["reason"] = (
                        "Corrected by you; name not in the DGDA snapshot — check the box."
                    )
            record = row.get("dgda_record") or {}
            dar = str(record.get("dar_no") or "").strip()
            provenance = (f"DGDA-registered · DAR {dar}" if dar
                          else "DGDA DAR not matched — verify on the box")
            c3.markdown(
                f"<div class='rx-review-badge'>{colour_badge(row['colour'])}"
                f"<b style='color:var(--rx-text);font-size:0.95rem;'>"
                f"{escape(str(row['generic'] or 'unknown'))}</b></div>"
                f"<div class='rx-review-meta'>{escape(provenance)}</div>",
                unsafe_allow_html=True,
            )

    if st.button("✅ Build my Bangla schedule", type="primary"):
        chosen = [r for r in rows if not r["name"].startswith("—")]
        st.session_state.schedule = pipeline.build_schedule(chosen)
        st.session_state.audio = None

    schedule = st.session_state.schedule
    if schedule:
        st.subheader("আপনার সময়সূচি / Your schedule")
        st.dataframe(bangla.schedule_rows(schedule["medicines"]), width='stretch')
        if schedule["warnings"]:
            for warning in schedule["warnings"]:
                st.warning(warning)
        st.markdown(DEMO_DISCLAIMER, unsafe_allow_html=True)
        summary = bangla.summary_text(schedule)
        st.markdown("**Bangla summary**")
        st.markdown(
            "<div style='background:var(--rx-surface-alt);border:1px solid var(--rx-border);"
            "border-radius:14px;padding:12px 14px;white-space:pre-wrap;color:var(--rx-text);'>"
            f"{escape(summary)}</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔊 Bangla audio"):
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
        email_col, call_col, whatsapp_col = st.columns(3)
        email_col.button("📧 Email reminder — Coming soon", disabled=True)
        call_col.button("📞 Call reminder — Coming soon", disabled=True)
        whatsapp_col.link_button("📱 WhatsApp reminder", sharing.whatsapp_link(schedule))
        st.caption("WhatsApp opens a prepared Bangla message — the app never sends it for you. "
                   "Email and call reminders need a verified sender/number and user consent.")

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
            "evaluated but not shipped.<br><b>Made by Team Zero-Shot</b></div>",
            unsafe_allow_html=True,
        )


def main():
    init_state()
    apply_query_actions()
    theme = ui.theme_name(st.session_state.theme)
    ui.inject_css(theme)
    scale = st.session_state.get("font_scale", "Normal")
    factor = {"Normal": 1.0, "Large": 1.15, "Extra large": 1.3}.get(str(scale), 1.0)
    st.markdown(
        f"<style>.stMarkdown p,.stMarkdown li,.stCaption{{font-size:calc(0.95rem * {factor})!important;}}</style>",
        unsafe_allow_html=True,
    )
    ui.hero(theme)
    sidebar()
    if st.session_state.page == 1:
        screen_1()
    elif st.session_state.page == 2:
        screen_2()
    else:
        screen_3()


if __name__ == "__main__":
    main()

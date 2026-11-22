"""RxBondhu — Streamlit app (3 screens).

1) Photo + crop   2) Two-AI reading with GREEN/YELLOW/RED   3) Review + Bangla schedule + audio
Run:  streamlit run app.py
"""

import os
import sys
import tempfile
from datetime import date, timedelta

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
                "read_count": 0, "font_scale": "Normal"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_reading():
    """Drop stale/out-of-date results and return to the photo screen."""
    st.session_state.analysis = None
    st.session_state.analysis_images = []
    st.session_state.confirmed = None
    st.session_state.schedule = None
    st.session_state.audio = None
    st.session_state.page = 1
    st.rerun()


def crop_ui(image: Image.Image, coverage: int = 92, key: str = "crop") -> Image.Image:
    """Crop the medicine lines only, starting at ~92% of the photo by default."""
    already_cropped = st.checkbox(
        "Already cropped — use the full image (no crop box)",
        value=False, key=f"already_{key}",
    )
    if already_cropped:
        st.caption("Using the full image as the medicine area.")
        return image
    try:
        from streamlit_cropper import st_cropper
        inset_x = int(image.width * (100 - coverage) / 200)
        inset_y = int(image.height * (100 - coverage) / 200)
        default_coords = (inset_x, image.width - inset_x,
                          inset_y, image.height - inset_y)
        return st_cropper(
            image, realtime_update=True, default_coords=default_coords,
            box_color="#2E8B57", aspect_ratio=None, return_type="image",
            key=f"cropper_{key}_{coverage}",
        )
    except Exception as exc:
        st.info(f"Cropper unavailable ({exc}) — using the full image as the crop.")
        return image


def colour_badge(colour: str) -> str:
    """Kept as a thin wrapper so the rest of the app stays unchanged."""
    return ui.badge(colour)


def screen_1():
    ui.step_header(1, "১. ছবি দিন", "Upload a prescription photo or take one, then drag a box around the medicine lines only.")
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
            st.image(photo, caption="Captured photo — crop the medicine lines below", width='stretch')

    if st.session_state.source is None:
        st.info("No image yet. Demo without a photo? Add a sample in `samples/` and refresh.")
        return

    st.subheader("Crop the medicine area")
    coverage = st.slider(
        "Medicine-area coverage (%) — start wide, then trim", 70, 98, 92, 2,
        key="coverage", help="92% means a 4% margin on each side of the photo.",
    )
    st.session_state.crop = crop_ui(st.session_state.source, coverage=coverage)
    if st.session_state.crop is None:
        st.warning("Crop is not ready yet — drag a box around the medicine lines, then try again.")
        return
    st.image(st.session_state.crop, caption="Selected crop", width='stretch')
    if st.session_state.read_count >= 5:
        st.caption("Session reading limit reached — Gemini is paused, our CNN still works.")
    if st.button("🔍 Read with both AI models →", type="primary"):
        skip_vlm = st.session_state.read_count >= 5
        with st.spinner("Finding medicine lines, running our CNN"
                        + ("…" if skip_vlm else " and Gemini…")):
            try:
                st.session_state.analysis = pipeline.analyse(
                    st.session_state.crop, full_image=st.session_state.source,
                    skip_vlm=skip_vlm)
                st.session_state.analysis_images = st.session_state.analysis.pop("images", [])
                st.session_state.read_count += 1
                st.session_state.page = 2
                st.rerun()
            except Exception as exc:
                st.error(f"Reading failed: {exc}")


def screen_2():
    ui.step_header(2, "২. দুই AI-র পড়া", "Two independent readers, one safety decision — nothing becomes a schedule yet.")
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
    vlm_ok = not vlm_error
    second_error = analysis.get("vlm2_error") or ""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Medicine lines found", analysis.get("line_count", len(analysis["items"])))
    c2.metric("Our CNN", "ready" if cnn_ok else "not trained yet")
    c3.metric("Reader 1", (analysis.get("vlm_model") or "offline") if vlm_ok else "offline")
    c4.metric("Reader 2", (analysis.get("vlm2_model") or "offline") if not second_error else "offline")
    if not vlm_ok:
        st.warning(f"Reader 1 unavailable: {vlm_error} — continuing with Reader 2 and CNN.")
    if second_error:
        st.warning(f"Reader 2 unavailable: {second_error} — continuing with Reader 1 and CNN.")
    st.caption("🟢 both readers agree on a verified brand · 🟡 one reader confident · "
               "🔍 readable but unverified (edit the name) · 🔴 disagreement or low confidence. "
               "Nothing is a schedule until you confirm it.")

    if not analysis["items"]:
        st.error("No medicine lines detected. Try a tighter, better-lit crop.")
    st.caption("Line crop on the left, both readings on the right — compare them with the paper.")
    for item in analysis["items"]:
        with st.container(border=True):
            left, right = st.columns([1, 4])
            left.image(item_image(item), width='stretch')
            right.markdown(
                f"{colour_badge(item['colour'])} "
                f"<b style='color:#0B4B2A;font-size:1.05rem;'>{item['name'] or '(unreadable)'}</b>",
                unsafe_allow_html=True,
            )
            right.caption(item["reason"])
            confidence = float(item.get("cnn_confidence") or 0.0)
            right.write(
                f"CNN: `{item.get('cnn_brand') or '—'}` ({confidence:.2f}) · "
                f"Reader 1: `{item.get('vlm_guess') or item.get('vlm_text') or '—'}` · "
                f"Reader 2: `{item.get('vlm2_guess') or item.get('vlm2_text') or '—'}`"
            )
            if right.button("🚩 Looks wrong — mark RED", key=f"wrong_{item['index']}"):
                item["colour"] = "RED"
                item["reason"] = (str(item.get("reason") or "")
                                  + " User flagged this crop as wrong.").strip()
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
                "options": options,
                "dose": item["dose_text"],
                "generic": item["generic"] or "",
                "colour": item["colour"],
                "editable": unverified,
                "raw_reading": item.get("vlm_guess") or item.get("vlm2_guess") or "",
            })
        st.session_state.confirmed = rows
        st.session_state.page = 3
        st.rerun()
    if st.button("← Back to photo"):
        st.session_state.page = 1
        st.rerun()


def item_image(item):
    """Image crops are kept in memory in analysis, not in the dict sent to UI."""
    images = st.session_state.get("analysis_images") or []
    index = item.get("index", -1)
    if isinstance(index, int) and 0 <= index < len(images):
        return images[index]
    return Image.new("RGB", (8, 8), "white")


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
            c1, c2, c3 = st.columns([3, 3, 2])
            if row.get("editable"):
                row["name"] = c1.text_input(
                    "Brand — unverified, type the name from the paper",
                    row["name"], key=f"name_{row['index']}",
                )
                c1.caption(f"Reader saw: {row.get('raw_reading') or '—'}")
            else:
                row["name"] = c1.selectbox("Brand (choose or correct)", row["options"],
                                           index=0, key=f"name_{row['index']}")
            row["dose"] = c2.text_input("Dose (e.g. 1+0+1, BD, সকাল ১ টি)",
                                        row["dose"], key=f"dose_{row['index']}")
            exact = lookup_exact(row["name"], brands)
            row["generic"] = exact["generic"] if exact else row["generic"]
            c3.markdown(
                f"{colour_badge(row['colour'])}<br><br>"
                f"Generic: <b>{row['generic'] or 'unknown'}</b>",
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
        with st.expander("Bangla summary text"):
            st.write(summary)
        if st.button("🔊 Bangla audio"):
            with st.spinner("Generating speech (first run downloads the TTS model)…"):
                result = tts.speak_bangla(summary)
            if result["path"]:
                st.session_state.audio = result["path"]
                st.caption(f"Engine: {result['engine']}")
                st.audio(result["path"])
            else:
                st.error(f"Audio failed: {result['error']}")

        reminder = reminders.make_ics(schedule)
        st.download_button(
            "📅 Download reminders (.ics)",
            data=reminder["ics"].encode("utf-8"),
            file_name="rxbondhu-reminders.ics",
            mime="text/calendar",
        )
        st.caption(
            f"{len(reminder['events'])} calendar events generated. "
            "Times 08:00 / 13:00 / 21:00 are examples — please confirm with the prescriber."
        )
        for warning in reminder["warnings"]:
            st.caption(warning)

        st.subheader("Calendar & sharing")
        first_day = st.date_input("First reminder date", value=date.today() + timedelta(days=1),
                                  key="first_day")
        links = sharing.calendar_links(schedule, start_date=first_day)
        for link in links:
            st.markdown(f"- [📅 {link['medicine']} — {link['slot']}]({link['url']})")
        st.caption("Each link adds one example day to Google Calendar (Asia/Dhaka); "
                   "the .ics above repeats for the full course. Times 08:00 / 13:00 / 21:00 "
                   "are examples — confirm with the prescriber. Use the .ics for all medicines at once.")
        st.markdown(f"[📱 Prepare WhatsApp message]({sharing.whatsapp_link(schedule)})")
        st.caption("Opens WhatsApp with a prepared Bangla message — the app never sends it for you.")
        with st.expander("Roadmap / future work"):
            st.caption("Voice-call reminders and email reminders are future work: they need a "
                       "verified sender/number, user consent and a paid service. They are not built here.")

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
    with st.sidebar:
        st.title("💊 RxBondhu")
        st.caption("Handwritten prescription → Bangla schedule")
        st.radio("Step", [1, 2, 3], index=st.session_state.page - 1,
                 format_func=lambda n: {1: "1 · photo", 2: "2 · reading", 3: "3 · schedule"}[n],
                 key="nav", disabled=True)
        info = recognizer.model_info()
        if info.get("available"):
            st.success(f"CNN ready · test acc {info.get('test_accuracy', '?')}")
        else:
            st.warning("CNN checkpoint not found — Gemini-only mode")
        key_ok, _ = vlm.available()
        st.info(f"Gemini key: {'yes' if key_ok else 'no'}")
        choices = ["Normal", "Large", "Extra large"]
        chosen = st.selectbox("Text size", choices,
                              index=choices.index(st.session_state.font_scale),
                              key="font_picker")
        st.session_state.font_scale = chosen
        st.caption("Built fresh for CoU AI Hackathon 2026. AI tools: OpenCode + Google Gemini.")


def main():
    init_state()
    # Keep PIL crops for display; they are not serialisable into a dataframe.
    if "analysis_images" not in st.session_state:
        st.session_state.analysis_images = []
    ui.inject_css()
    scale = st.session_state.get("font_scale", "Normal")
    factor = {"Normal": 1.0, "Large": 1.15, "Extra large": 1.3}.get(str(scale), 1.0)
    st.markdown(
        f"<style>.stMarkdown p,.stMarkdown li,.stCaption{{font-size:calc(0.95rem * {factor})!important;}}</style>",
        unsafe_allow_html=True,
    )
    ui.hero()
    sidebar()
    if st.session_state.page == 1:
        screen_1()
    elif st.session_state.page == 2:
        screen_2()
    else:
        screen_3()


if __name__ == "__main__":
    main()

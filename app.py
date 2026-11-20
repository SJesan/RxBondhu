"""RxBondhu — Streamlit app (3 screens).

1) Photo + crop   2) Two-AI reading with GREEN/YELLOW/RED   3) Review + Bangla schedule + audio
Run:  streamlit run app.py
"""

import io
import os
import sys

import streamlit as st
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rxbondhu import bangla, pipeline, recognizer, tts, vlm  # noqa: E402
from rxbondhu.lexicon import load_brands, lookup_exact, suggest_brands  # noqa: E402

st.set_page_config(page_title="RxBondhu | রক্সবন্ধু", page_icon="💊", layout="wide")

DEMO_DISCLAIMER = (
    "**এটি কেবল একটি পড়ার সহায়তা, ডাক্তারের পরামর্শ নয়।** "
    "কোনো ওষুধ শুরু, বদল বা বন্ধ করার আগে ডাক্তার বা ফার্মাসিস্টের সাথে নিশ্চিত করুন।"
)


def init_state():
    defaults = {"page": 1, "source": None, "crop": None, "analysis": None,
                "confirmed": None, "schedule": None, "audio": None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def crop_ui(image: Image.Image) -> Image.Image:
    """Use streamlit-cropper when available, otherwise a simple full image."""
    try:
        from streamlit_cropper import st_cropper
        return st_cropper(image, realtime_update=True, box_color="#2E8B57",
                          aspect_ratio=None, return_type="image")
    except Exception:
        st.info("Cropper add-on unavailable — using the full image as the crop.")
        return image


def colour_badge(colour: str) -> str:
    return {"GREEN": "🟢 GREEN", "YELLOW": "🟡 YELLOW", "RED": "🔴 RED"}.get(colour, colour)


def screen_1():
    st.header("১. ছবি দিন / Step 1 — Photo and crop")
    st.caption("Upload a prescription photo or take one. Then drag a box around the medicine lines only.")
    tab_upload, tab_camera = st.tabs(["Upload photo", "Use camera"])
    with tab_upload:
        uploaded = st.file_uploader("Prescription image", type=["jpg", "jpeg", "png", "webp"])
        if uploaded:
            st.session_state.source = Image.open(uploaded).convert("RGB")
    with tab_camera:
        camera = st.camera_input("Take a photo")
        if camera:
            st.session_state.source = Image.open(io.BytesIO(camera.getvalue())).convert("RGB")

    if st.session_state.source is None:
        st.info("No image yet. Demo without a photo? Add a sample in `samples/` and refresh.")
        return

    st.subheader("Crop the medicine area")
    st.session_state.crop = crop_ui(st.session_state.source)
    st.image(st.session_state.crop, caption="Selected crop", width='stretch')
    if st.button("🔍 Read with both AI models →", type="primary"):
        with st.spinner("Segmenting words, running our CNN and Gemini…"):
            try:
                st.session_state.analysis = pipeline.analyse(
                    st.session_state.crop, full_image=st.session_state.source)
                st.session_state.analysis_images = st.session_state.analysis.pop("images", [])
                st.session_state.page = 2
                st.rerun()
            except Exception as exc:
                st.error(f"Reading failed: {exc}")


def screen_2():
    st.header("২. দুই AI-র পড়া / Step 2 — Two readers")
    analysis = st.session_state.analysis
    if not analysis:
        st.warning("Go back to Step 1 and read a photo first.")
        return

    cnn_ok = analysis["cnn_available"]
    vlm_ok = not analysis["vlm_error"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Word crops found", analysis["word_count"])
    c2.metric("Our CNN", "ready" if cnn_ok else "not trained yet")
    c3.metric("Gemini", analysis["vlm_model"] if vlm_ok else "offline")
    if not vlm_ok:
        st.warning(f"Gemini unavailable: {analysis['vlm_error']} — showing CNN-only results.")
    st.caption("🟢 both agree · 🟡 one is unsure · 🔴 disagree or low confidence — always confirm these.")

    if not analysis["items"]:
        st.error("No words detected. Try a tighter, better-lit crop.")
    for item in analysis["items"]:
        with st.container(border=True):
            left, right = st.columns([1, 4])
            left.image(item_image(item), width='stretch')
            right.markdown(f"**{colour_badge(item['colour'])} — {item['name'] or '(unreadable)'}**")
            right.caption(item["reason"])
            right.write(
                f"CNN: `{item['cnn_brand'] or '—'}` ({item['cnn_confidence']:.2f}) · "
                f"Gemini: `{item['vlm_guess'] or item['vlm_text'] or '—'}`"
            )
    if st.button("✏️ Confirm / correct each line →", type="primary"):
        brands = load_brands()
        rows = []
        for item in analysis["items"]:
            options = [s["brand"] for s in item["suggestions"]]
            if item["name"] and item["name"] not in options:
                options.insert(0, item["name"])
            options.append("— skip this line —")
            rows.append({
                "index": item["index"],
                "name": options[0] if options else "— skip this line —",
                "options": options,
                "dose": item["dose_text"],
                "generic": item["generic"] or "",
                "colour": item["colour"],
            })
        st.session_state.confirmed = rows
        st.session_state.page = 3
        st.rerun()
    if st.button("← Back to photo"):
        st.session_state.page = 1
        st.rerun()


def item_image(item):
    """Image crops are kept in memory in analysis, not in the dict sent to UI."""
    return st.session_state.analysis_images[item["index"]]


def screen_3():
    st.header("৩. নিশ্চিত করুন ও সময়সূচি / Step 3 — Review and schedule")
    rows = st.session_state.confirmed or []
    if not rows:
        st.warning("Nothing to review yet.")
        return
    st.markdown(DEMO_DISCLAIMER)

    brands = load_brands()
    for row in rows:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 3, 2])
            row["name"] = c1.selectbox("Brand (choose or correct)", row["options"],
                                       index=0, key=f"name_{row['index']}")
            row["dose"] = c2.text_input("Dose (e.g. 1+0+1, BD, সকাল ১ টি)",
                                        row["dose"], key=f"dose_{row['index']}")
            exact = lookup_exact(row["name"], brands)
            row["generic"] = exact["generic"] if exact else row["generic"]
            c3.markdown(f"{colour_badge(row['colour'])}\n\nGeneric: **{row['generic'] or 'unknown'}**")

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
        st.info(DEMO_DISCLAIMER)
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
        st.caption("Built fresh for CoU AI Hackathon 2026. AI tools: OpenCode + Google Gemini.")


def main():
    init_state()
    # Keep PIL crops for display; they are not serialisable into a dataframe.
    if "analysis_images" not in st.session_state:
        st.session_state.analysis_images = []
    sidebar()
    if st.session_state.page == 1:
        screen_1()
    elif st.session_state.page == 2:
        screen_2()
    else:
        screen_3()


if __name__ == "__main__":
    main()

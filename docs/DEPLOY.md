# Live link vs demo video (Hugging Face update, 2026)

The rulebook accepts a live link **or** a ≤3-minute demo video. We are using the
**video** route.

Hugging Face removed the built-in Streamlit SDK in 2025. In 2026 a new Space
offers only **Static**, **Gradio** and **Docker**; Gradio/Docker on CPU require a
PRO/Team plan, so a free new account cannot host our Streamlit app. Therefore no
HF Space push is part of the submission. The judged code stays on GitHub:
**https://github.com/SJesan/RxBondhu**.

## What to submit instead
1. Run the app locally:
   ```powershell
   .\venv\Scripts\streamlit.exe run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
   ```
   Open `http://localhost:8501`.
2. Record a **≤3-minute** walkthrough following [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).
3. Put the final MP4 link/file in the submission form, and rehearse once so the
   backup video is ready.

## Key handling
`.env` is git-ignored and never committed. There is no HF secret to set because
there is no Space. If the key was ever pasted into a chat, rotate it in Google AI
Studio and update the local `.env` before the final demo.

## Important
Do not commit `.env` or any API key. The checkpoint `models/rx_cnn.pt` is ours
and is committed.

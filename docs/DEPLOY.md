# Live link and demo video

The rulebook accepts a live link **or** a ≤3-minute demo video. We can do both:
a **free** live link on Streamlit Community Cloud (great for a CV) and the local
prototype for the on-site final.

## 1. Free live link — Streamlit Community Cloud (no payment)

1. Go to **https://share.streamlit.io** and sign in with **GitHub**.
2. Click **Create app** → **Yup, I have an app**.
3. Fill in:
   - Repository: `SJesan/RxBondhu`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: e.g. `rxbondhu` → `https://rxbondhu.streamlit.app`
4. Click **Advanced settings**:
   - Python version: **3.11**
   - Secrets field:
     ```toml
     GEMINI_API_KEY = "your-real-key"
     RX_VLM_MODEL = "gemini-2.5-flash"
     ```
   The key is stored in Streamlit's secret store, **never in the repo**.
5. Click **Deploy**. First boot takes a few minutes because `torch` is installed.
6. Verify: sidebar shows `Gemini key: yes` and `CNN ready · test acc 0.9590`.

Notes:
- Free apps sleep after 12 hours without traffic; opening the link wakes them.
  That is fine for a CV link.
- `requirements.txt` uses PyTorch's CPU wheel index, so no CUDA packages are
  downloaded on the free container.
- Our `vlm.py` reads `st.secrets` first and falls back to local `.env`.

## 2. Why not Hugging Face?

Hugging Face removed the built-in Streamlit SDK in 2025. In 2026 a new Space
offers only Static, Gradio and Docker; Gradio/Docker on CPU need PRO/Team. So a
free new account cannot host this Streamlit app. Streamlit Community Cloud is
the correct free host.

## 3. Local prototype (on-site final)

The 24 Nov final requires a fully working local prototype, no hosting needed:

```powershell
.\venv\Scripts\streamlit.exe run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Open `http://localhost:8501`. Judges may ask for changes on-site, so keep the
GitHub repo and this runbook handy.

## 4. Demo video (backup)

Record a ≤3-minute walkthrough following [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md),
export MP4, and keep an unlisted link ready.

## 5. Key handling

`.env` and `.streamlit/secrets.toml` are git-ignored. Never commit either. If the
key was pasted into a chat, rotate it in Google AI Studio and update both the
local `.env` and the Streamlit Cloud secret before the final demo.

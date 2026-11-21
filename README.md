---
title: RxBondhu
emoji: 💊
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.67.0
app_file: app.py
pinned: false
---

# RxBondhu (রক্সবন্ধু)

**Handwritten prescription photo → clear Bangla medicine schedule + audio**, with GREEN / YELLOW / RED confidence colours and a duplicate-medicine warning.

> **Reading aid, not a doctor.** No diagnosis, no prescribing, no drug-interaction checking. The user always confirms before a schedule appears.

**Hackathon:** CoU AI Hackathon 2026 · Healthcare & Wellbeing  
**Team:** Solo · **Member:** M M Sadikul Islam Jesan  
**Status (22 Nov 2026):** Fresh build from zero. All three screens, dose parser, brand lexicon, fusion, segmentation, Gemini reader and CNN inference are working. Our CNN was trained on Kaggle T4: **validation 0.9577, test 0.9590 (748/780)** across 78 brands. Full log: [`results/kaggle_training_log.txt`](results/kaggle_training_log.txt) · proof: [`docs/EVALUATION.md`](docs/EVALUATION.md) · demo script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

---

## 1. Problem and solution summary

In Bangladesh many prescriptions are handwritten and hard to read. Patients and caregivers can misread a brand name, a dose notation (`1+0+1`, BD, `রাতে ১ টি`), or miss that two brands contain the same generic drug — causing a double dose.

RxBondhu reads the medicine area with **two AI models**, checks every name against a list of **real Bangladeshi brands**, shows a confidence colour, asks the user to **confirm or correct** everything, then produces a **Bangla morning/noon/night schedule with audio** and warns about duplicate generics.

## 2. Features and how the AI works

1. **Photo + crop** — upload/photograph a prescription, drag a box around the medicine section.
2. **Find lines** — OpenCV groups handwritten words into lines.
3. **Two readers** — our own trained handwriting CNN **and** Google Gemini read the crop.
4. **Real-brand matching** — fuzzy matching (RapidFuzz) against a verified brand→generic list, so invented names are blocked.
5. **Fusion colours** — GREEN = both agree; YELLOW = one unsure; RED = disagreement/low confidence → "confirm with your pharmacist".
6. **Review screen** — user confirms/fixes every name and dose. Nothing becomes a schedule before this.
7. **Dose parser** — `1+0+1`, `BD`, `TDS`, `HS`, Bangla dose notes → schedule.
8. **Safety check** — two brands with the same generic trigger a duplicate warning.
9. **Clean white + Bangla green UI** — 3 guided screens, cards with subtle CSS 3D tilt, and a small locally bundled Three.js capsule hero (`static/three.min.js`).
10. **Bangla schedule + audio** — Bangla table and spoken summary (MMS-TTS, gTTS backup).

Flow: `photo → crop → segment.py → (recognizer.py CNN + vlm.py Gemini) → lexicon.py → fusion.py → review → dose_parser.py → safety.py → bangla.py/tts.py`.

## 3. Tech stack, models, APIs, datasets

- **Language:** Python 3.11 (recommended)
- **App:** Streamlit, streamlit-cropper
- **Vision / matching:** OpenCV, NumPy, Pillow, RapidFuzz
- **Our model:** EfficientNet-B0 (torchvision, ImageNet weights), fine-tuned by us on the public **Doctor's Handwritten Prescription BD** dataset (Kaggle: `mamun1113`) — 4,680 word images, 78 brands, split 3,120 / 780 / 780, **test accuracy 0.9590 (748/780)**, validation 0.9577, 128×384 letterbox input, 12 epochs, seed 42
- **Second reader:** Google Gemini via Google AI Studio (`google-genai`, model in `RX_VLM_MODEL`)
- **Speech:** `facebook/mms-tts-ben` (CC-BY-NC-4.0), gTTS fallback
- **Training:** Kaggle T4 GPU · **Deployment:** Hugging Face Spaces (planned)
- Full credits and licences: [`RESOURCES.md`](RESOURCES.md)

## 4. AI tools used and for what (disclosure)

- **OpenCode** (AI coding agent, model Big Pickle) — planning, writing and debugging the code, README and presentation drafts; created the full plan in `docs/PLAN.md`.
- **Google Gemini** (Google AI Studio, model set in `RX_VLM_MODEL`) — the in-app AI reader that produces medicine names and dose text from the image.
- *Add one honest line here for any other assistant you actually used (Claude, ChatGPT, Copilot, etc.), with the task it performed.*

All models/APIs above are real and run live; no output is hard-coded or faked.

## 5. Third-party code and assets credited

Public datasets, pretrained model weights, libraries and fonts are listed in [`RESOURCES.md`](RESOURCES.md). Our test prescriptions are handwritten by the team, with no real patient data.

## 6. Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # then paste GEMINI_API_KEY into .env (never commit it)
streamlit run app.py
```

Without a Gemini key the app runs CNN-only. Without the CNN file it runs with the reader only.

Tests (no network needed):

```bash
.\venv\Scripts\python.exe tests\test_core.py
.\venv\Scripts\python.exe tests\test_pipeline.py
.\venv\Scripts\python.exe tests\test_segmentation.py
```

Evaluation table and judge proof: [`docs/EVALUATION.md`](docs/EVALUATION.md).

The CNN was trained on Kaggle: GPU T4 + Internet On, dataset added as Input, `training/train_cnn_kaggle.py` run with seed 42. The four outputs — `rx_cnn.pt`, `labels.json`, `test_report.csv`, `training_summary.txt` — live in `models/`; the raw training log is in `results/kaggle_training_log.txt`.

## 7. Live link and demo video

- Code (public repo): **https://github.com/SJesan/RxBondhu** ✅
- Live app: **TBD** (Hugging Face Spaces)
- Demo video (max 3 min): **TBD**

## Safety and limits

RED items say "please confirm with your pharmacist". Only brands in our verified list are shown. The app covers a limited brand list and handwriting styles — that is why human confirmation is built in.

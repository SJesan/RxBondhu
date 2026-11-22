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

[![tests](https://github.com/SJesan/RxBondhu/actions/workflows/tests.yml/badge.svg)](https://github.com/SJesan/RxBondhu/actions/workflows/tests.yml)

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
- **Second reader:** Google Gemini via Google AI Studio (`google-genai`, serial fallback chain in `RX_VLM_MODELS`)
- **Speech:** `facebook/mms-tts-ben` (CC-BY-NC-4.0), gTTS fallback
- **Training:** Kaggle T4 GPU · **Submission proof:** public live link (demo video kept as optional backup)
- Full credits and licences: [`RESOURCES.md`](RESOURCES.md)

## 4. AI tools used and for what (disclosure)

- **OpenCode** (AI coding agent, model Big Pickle) — planning, writing and debugging the code, README and presentation drafts; created the full plan in `docs/PLAN.md`.
- **Google Gemini** (Google AI Studio) — the in-app AI reader that produces medicine names and dose text from the image. Primary `gemini-2.5-flash`, then automatic fallbacks `gemini-3.5-flash-lite` → `gemini-3.1-flash-lite` (one key, no hard-coded output).

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

Tests (no network needed, 53 tests across 8 files):

```bash
.\venv\Scripts\python.exe tests\test_core.py
.\venv\Scripts\python.exe tests\test_pipeline.py
.\venv\Scripts\python.exe tests\test_segmentation.py
.\venv\Scripts\python.exe tests\test_evaluation.py
.\venv\Scripts\python.exe tests\test_reminders.py
.\venv\Scripts\python.exe tests\test_preprocess.py
.\venv\Scripts\python.exe tests\test_localization.py
```

These also run automatically on every push via GitHub Actions (badge above).

Real-handwriting evaluation runner (needs your answer key + Rx photos; never invents results):

```bash
.\venv\Scripts\python.exe tools\evaluate_handwritten.py --answers results\answer_key.csv --images results\rx
```

It writes `results/handwritten_test_log.csv` and a JSON summary with **name accuracy (CNN / Gemini / Combined), dose accuracy, unsafe-GREEN rate, catch rate and over-flag rate**. Template: [`results/answer_key_template.csv`](results/answer_key_template.csv).

External localization check on 200 real handwritten prescriptions (positions only, **not** name accuracy):

```bash
.\venv\Scripts\python.exe tools\evaluate_localization.py --zip "<dataset.zip>"
```

Evaluation table and judge proof: [`docs/EVALUATION.md`](docs/EVALUATION.md).  
Detailed 10-page project report (architecture, training, evaluation, rule compliance, demo script, Q&A): [`docs/RxBondhu_Project_Report.pdf`](docs/RxBondhu_Project_Report.pdf).

The CNN was trained on Kaggle: GPU T4 + Internet On, dataset added as Input, `training/train_cnn_kaggle.py` run with seed 42. The four outputs — `rx_cnn.pt`, `labels.json`, `test_report.csv`, `training_summary.txt` — live in `models/`; the raw training log is in `results/kaggle_training_log.txt`.

## 7. Live link and demo video

- Code (public repo): **https://github.com/SJesan/RxBondhu** ✅
- Live app (free, Streamlit Community Cloud): **https://rxbondhu.streamlit.app** ✅ — see [`docs/DEPLOY.md`](docs/DEPLOY.md)
- Demo video (optional backup, max 3 min): script ready in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)
- No login in the app — **no test credentials needed**. The live link is public and will stay up until results.

## Safety and limits

RED items say "please confirm with your pharmacist". Only brands in our verified list are shown. The app covers a limited brand list and handwriting styles — that is why human confirmation is built in.

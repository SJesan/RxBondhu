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

**Handwritten prescription photo → clear Bangla medicine schedule + audio**, with GREEN / YELLOW / UNVERIFIED / RED confidence colours and a duplicate-medicine warning.

> **Reading aid, not a doctor.** No diagnosis, no prescribing, no drug-interaction checking. The user always confirms before a schedule appears.

**Hackathon:** CoU AI Hackathon 2026 · Healthcare & Wellbeing  
**Team:** Solo · **Member:** M M Sadikul Islam Jesan  
**Status (23 Nov 2026):** Fresh build from zero. Three screens, two independent Gemini photo readers, our own fine-tuned CNN as safety veto, soft UNVERIFIED badge, rear-camera capture, 92% crop default, calendar links, .ics and prepared WhatsApp text all work. Our CNN was trained on Kaggle T4: **validation 0.9577, test 0.9590 (748/780)** across 78 brands (clean word crops — real-photo numbers are reported separately). Full log: [`results/kaggle_training_log.txt`](results/kaggle_training_log.txt) · proof: [`docs/EVALUATION.md`](docs/EVALUATION.md) · demo script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

---

## 1. Problem and solution summary

In Bangladesh many prescriptions are handwritten and hard to read. Patients and caregivers can misread a brand name, a dose notation (`1+0+1`, BD, `রাতে ১ টি`), or miss that two brands contain the same generic drug — causing a double dose.

RxBondhu reads the medicine area with **two AI models**, checks every name against a list of **real Bangladeshi brands**, shows a confidence colour, asks the user to **confirm or correct** everything, then produces a **Bangla morning/noon/night schedule with audio** and warns about duplicate generics.

## 2. Features and how the AI works

1. **Photo + crop** — upload or use the phone rear camera; default crop covers 92% of the photo with a coverage slider and an "already cropped" option.
2. **Find lines** — OpenCV groups handwritten words into lines; each review row is one medicine line.
3. **Three readings** — two independent Gemini models read the photo; our own fine-tuned CNN reads word crops as a safety veto and proof of an own model.
4. **Real-brand matching** — fuzzy matching (RapidFuzz) against a verified brand→generic list, so invented names are blocked.
5. **Fusion colours** — GREEN = both readers agree on a verified brand; YELLOW = one reader confident; 🔍 UNVERIFIED = readable but not in the checked list (editable, never GREEN); RED = direct disagreement / low confidence / user flag.
6. **Review screen** — user confirms/fixes every name and dose. Nothing becomes a schedule before this.
7. **Dose parser** — `1+0+1`, `BD`, `TDS`, `HS`, Bangla dose notes → schedule.
8. **Safety check** — two brands with the same generic trigger a duplicate warning.
9. **Clean white + Bangla green UI** — 3 guided screens, cards with subtle CSS 3D tilt, and a small locally bundled Three.js capsule hero (`static/three.min.js`).
10. **Bangla schedule + audio** — Bangla table and spoken summary (MMS-TTS, gTTS backup).
11. **Calendar & sharing** — one-click Google Calendar links (Asia/Dhaka, example 08:00/13:00/21:00), a repeating `.ics`, and prepared WhatsApp text. The app never sends messages or books events for you.

Flow: `photo → crop → segment.py → (vlm.py reader 1 + vlm.py reader 2 + recognizer.py CNN veto) → lexicon.py → fusion.py → review → dose_parser.py → safety.py → bangla.py/tts.py`.

## 3. Tech stack, models, APIs, datasets

- **Language:** Python 3.11 (recommended)
- **App:** Streamlit, streamlit-cropper
- **Vision / matching:** OpenCV, NumPy, Pillow, RapidFuzz
- **Our model:** EfficientNet-B0 (torchvision, ImageNet weights), fine-tuned by us on the public **Doctor's Handwritten Prescription BD** dataset (Kaggle: `mamun1113`) — 4,680 word images, 78 brands, split 3,120 / 780 / 780, **test accuracy 0.9590 (748/780)**, validation 0.9577, 128×384 letterbox input, 12 epochs, seed 42
- **Two readers:** Google Gemini via Google AI Studio — primary `gemini-3.5-flash-lite`, independent second `gemini-3.1-flash-lite`; `gemini-2.5-flash` remains only in the serial fallback chain because its free quota was exhausted in testing.
- **Evaluated but not shipped:** Groq `qwen/qwen3.8-27b` was tested on the same 10 images; it failed the 30% name-accuracy / 10 s gate, so it is disclosed as a bake-off only and is not an app dependency.
- **Speech:** `facebook/mms-tts-ben` (CC-BY-NC-4.0), gTTS fallback
- **Training:** Kaggle T4 GPU · **Submission proof:** public live link (demo video kept as optional backup)
- Full credits and licences: [`RESOURCES.md`](RESOURCES.md)

## 4. AI tools used and for what (disclosure)

- **OpenCode** (AI coding agent, model Big Pickle) — planning, writing and debugging the code, README and presentation drafts; created the full plan in `docs/PLAN.md`.
- **Google Gemini** (Google AI Studio) — the two in-app photo readers that produce medicine names and dose text from the image: `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` (one key, no hard-coded output). `gemini-2.5-flash` was also used during v1 testing and hit its daily quota.
- **Groq + `qwen/qwen3.8-27b`** — used only for a 10-image, 48-line second-reader bake-off on 22–23 Nov. It failed the locked gate, so it is **not** in the app and no Groq key is needed to run it.
- **Rakin** — recorded the demo video (3-minute backup) for the submission.
- **Other AI tools used outside this project are not part of this build and are not claimed here.**

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

`GROQ_API_KEY` in `.env.example` is a placeholder for the rejected bake-off only — the app never calls Groq. Without a Gemini key the app runs CNN-only. Without the CNN file it runs with the readers only.

Tests (no network needed, 65 tests across 12 files):

```bash
.\venv\Scripts\python.exe -m unittest discover -s tests -q
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

RED items say "please confirm with your pharmacist". UNVERIFIED names are shown as editable defaults, never GREEN and never auto-accepted. The app covers a limited verified brand list and handwriting styles — that is why human confirmation is built in. See [`docs/EVALUATION.md`](docs/EVALUATION.md) for the 0.9590 word-crop accuracy and the separate real-photo numbers.

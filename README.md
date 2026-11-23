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
**Status (23 Nov 2026):** Three guided screens, **Large text by default**, light (default) / dark themes, one-line hero on screens 2–3, two independent Gemini photo readers, our own fine-tuned CNN as a safety veto (set aside only for an exact 100/100 dual match to the same **DAR-backed** DGDA brand), rear-camera capture with an obvious upload fallback, 92% crop default hidden under **Advanced**, one-sentence crop help plus a sample image, six **click-to-use** fictional demo Rx thumbnails, `দুটি AI পড়ছে…` loader, compact DGDA cards with **More info**, Bangla-first schedule table with big ✓ and Bangla digits, one main `শুনুন` button, and working .ics / Google Calendar / prepared WhatsApp text. Brand identity is checked against a **committed DGDA Allopathic snapshot** (41,655 source rows → 23,804 verified entries; 888 conflicting keys quarantined). **GREEN needs both readers to agree at ≥95 on a DGDA row with a DAR No**; a box-checked-only identity (Napa, Fexo, Ace) is YELLOW with explicit wording, and fuzzy-only is YELLOW at most. Our CNN was trained on Kaggle T4: **validation 0.9577, word-crop test 0.9590 (748/780)** across 78 brands — real-photo numbers are reported separately. Proof: [`docs/EVALUATION.md`](docs/EVALUATION.md) · demo script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

---

## 1. Problem and solution summary

In Bangladesh many prescriptions are handwritten and hard to read. Patients and caregivers can misread a brand name, a dose notation (`1+0+1`, BD, `রাতে ১ টি`), or miss that two brands contain the same generic drug — causing a double dose.

RxBondhu reads the medicine area with **two AI models**, checks every name against a list of **real Bangladeshi brands**, shows a confidence colour, asks the user to **confirm or correct** everything, then produces a **Bangla morning/noon/night schedule with audio** and warns about duplicate generics.

## 2. Features and how the AI works

1. **Photo + crop** — upload or use the phone rear camera; crop help plus a small sample image show how to box only the medicine lines. The 92% default margin is under **Advanced**, and the cropper is the only photo preview. Photos are session-only: `ছবি সংরক্ষণ করা হয় না`.
2. **Find lines** — OpenCV groups handwritten words into lines; each review row is one medicine line.
3. **Three readings** — two independent Gemini models read the photo; our own fine-tuned CNN reads word crops as a safety veto and proof of an own model. A conflicting CNN guess is not shown as a reading in the main view (`CNN: not applicable to this name`); its raw score stays in **More info**. An exact 100/100 dual match to a DAR-backed DGDA brand may set aside an out-of-distribution CNN guess, and the reason says so; spelling disagreements stay RED.
4. **DGDA-registered brand matching** — a committed snapshot of the official DGDA Allopathic export (`data/dgda_brands.csv`, 23,804 verified brand→generic entries with DAR No, source URL and access date) plus 10 box/pharmacy-checked rows. Bulk/API rows and 888 conflicting generic identities are quarantined in `data/dgda_conflicts.csv`. No runtime network call; `data/dgda_source.json` records the sha256 and access date.
   **Wording limit:** “DGDA-registered” is an identity check against that export — it is not dose advice and not a medical approval. A name missing from the export is **UNVERIFIED, never “not approved”**.
5. **Fusion colours** — GREEN = both readers agree on the same **DGDA row with a DAR No** at ≥95 normalised match, with no unhandled CNN contradiction; an exact 100 dual match may override an out-of-distribution CNN guess; YELLOW = one reader offline/confident, fuzzy agreement (85–94.9), or a **box-checked-only identity** (Napa/Fexo/Ace — “Verified by box check, not found in DGDA snapshot”); 🔍 UNVERIFIED = readable with no verified candidate (editable, never GREEN); RED = direct disagreement / close spelling disagreement / CNN contradiction / low confidence / user flag. Fuzzy-only never reaches GREEN.
6. **Review screen** — user confirms/fixes every name and dose. Nothing becomes a schedule before this.
7. **Dose parser** — `1+0+1`, `BD`, `TDS`, `HS`, Bangla dose notes → schedule.
8. **Safety check** — two brands with the same generic trigger a non-blocking duplicate-generic warning; ingredient order in combinations is canonicalised so `Amlodipine + Atenolol` and `Atenolol + Amlodipine` match. No mg ceiling is claimed.
8b. **Identity card** — Screen 2 shows a compact generic / DAR No / strength / form card beside each line and a **More info** expander with company, source, access date, conflict detail and the raw CNN guess. Screen 3 uses `DGDA-registered (DAR No …)` or `Verified by box check, not found in DGDA snapshot`. Every card says **identity only, not dose advice**; no “approved”, “not approved”, price, indication or clock time.
9. **Readable light + dark UI** — Large text by default (18px minimum), every button ≥48px, bigger 1/2/3 step indicator, high-contrast light theme, one card per medicine with more padding, one-line hero on screens 2–3, ≤2 sidebar chips (`Groq not shipped` moved into Model info), neutral grey `Not sure?` instead of a red flag button, `Team Zero-Shot` credit, click-to-use fictional demo images, and a locally bundled Three.js capsule hero on screen 1.
10. **Bangla-first schedule + audio** — Bangla labels first with small English, big ✓ and Bangla digits, `দিন লেখা নেই — নিশ্চিত করুন` when days are missing, plain status lines under badges, Bangla summary + table before calendar/WhatsApp, one main `শুনুন` button above per-medicine audio (MMS-TTS, gTTS backup).
11. **Calendar & sharing** — one-click Google Calendar links (Asia/Dhaka), a repeating `.ics`, **Add all medicines once**, and prepared WhatsApp text. No “Coming soon” Email/Call buttons; the app never sends messages or books events for you.
12. **Multi-prescription mode (branch `multi-image`, not merged)** — the single-photo flow is unchanged; a separate “Multiple prescriptions (2–3 photos)” uploader accepts 1–3 images (extra files are capped at 3 with a friendly warning). Each image has its own crop box and stays a separate group until confirmation. Reads are sequential (`Prescription 1 of 3…`), the button is locked for the whole loop, and each result is cached in-session by `sha256(image bytes + crop box)` so the same crop never spends quota twice. A failed or empty image shows a Bangla+English warning on that image only; the others still work. Screen 2 labels each line `Prescription N · line M`, and Screen 3 merges **only user-confirmed** rows, re-running the existing duplicate-generic check plus a non-blocking cross-prescription warning (`একাধিক প্রেসক্রিপশনে একই জেনেরিক আছে …`). No fusion, lexicon, DGDA or threshold logic was changed.

Flow: `photo → crop → segment.py → (vlm.py reader 1 + reader 2 + recognizer.py CNN veto, overridden only by an exact 100/100 dual match on a DAR-backed row) → lexicon.py → fusion.py → review → dose_parser.py → safety.py → bangla.py/tts.py`.

## Results at a glance

| Measure | Result | Meaning / limit |
|---|---|---|
| CNN **word-crop test accuracy** | **0.9590 (748/780)** | Clean single-word images from our Kaggle split. **Not** whole-photo accuracy. |
| CNN on our real prescription photos | **0/47 (0%)** | Its 78 classes do not cover these brands; used as veto/proof, not general reader. |
| Reader 1 `gemini-3.5-flash-lite` | 27/47 (57.4%) | Names matched to the answer key. |
| Reader 2 `gemini-3.1-flash-lite` | 32/47 (68.1%) | Names matched to the answer key. |
| Combined name shown | 24/47 (51.1%) | Fusion output without human correction. |
| Dose notation | 8/48 (16.7%) | `1+0+1`, BD, TDS, Bangla notes. |
| Unsafe-GREEN **before** DGDA import | **1/7 = 0.1429** | 25-brand box list, legacy 70 score. |
| Unsafe-GREEN **after** DGDA import | **0/12 = 0.0000** | DGDA snapshot, candidate 90, GREEN ≥95. |
| Unsafe-GREEN after exact-dual override | 0/19 = 0.0000 | Override kept unsafe-GREEN at zero. |
| Unsafe-GREEN **after DAR-gate** | **0/14 = 0.0000** | Box-only identities capped at YELLOW (shipped). |
| Catch rate | **1.0** (23/23) | Every wrong reading was flagged, never GREEN. |
| Over-flag rate | 3/24 = 0.1250 | Correct names shown RED; conservative by design. |

**Method note.** The real-photo test uses **10 handwritten prescriptions from one writer** (48 review lines), so it is a same-writer safety check, not a population accuracy claim. The 5-image dev / 5-image holdout split was fixed before scoring: candidate threshold 90 was picked on dev rows 1–5 and reported once on rows 6–10; `GREEN_SCORE = 95` is a safety policy, not tuned. Before/after runs reuse the same cached real Gemini responses, so only the lexicon/rule changed. Gemini output varies slightly between runs; these numbers come from the committed cache run. Full logs: [`docs/EVALUATION.md`](docs/EVALUATION.md) and `results/handwritten_boxcap_*`.

## 3. Tech stack, models, APIs, datasets

- **Language:** Python 3.11 (recommended)
- **App:** Streamlit, streamlit-cropper
- **Vision / matching:** OpenCV, NumPy, Pillow, RapidFuzz
- **Our model:** EfficientNet-B0 (torchvision, ImageNet weights), fine-tuned by us on the public **Doctor's Handwritten Prescription BD** dataset (Kaggle: `mamun1113`) — 4,680 word images, 78 brands, split 3,120 / 780 / 780, **test accuracy 0.9590 (748/780)**, validation 0.9577, 128×384 letterbox input, 12 epochs, seed 42
- **Two readers:** Google Gemini via Google AI Studio — primary `gemini-3.5-flash-lite`, independent second `gemini-3.1-flash-lite`; `gemini-2.5-flash` remains only in the serial fallback chain because its free quota was exhausted in testing.
- **Verified reference:** DGDA (Directorate General of Drug Administration, Bangladesh) Allopathic *Medicine Information* export, `http://180.211.137.202:9310/Allopathic/`, accessed 23 Nov 2026, 41,655 rows, sha256 `7569a475c565c9b18bc1dba8a4725ea418d74ad0049258b3f122149473d317fc`. Downloaded once; filtered snapshot committed; no runtime fetch. This is Allopathic only — do not claim “all Bangladesh approved medicines”.
- **Evaluated but not shipped:** Groq `qwen/qwen3.8-27b` was tested on the same 10 images; it failed the 30% name-accuracy / 10 s gate, so it is disclosed as a bake-off only and is not an app dependency. The Kaggle/MedEx “Assorted Medicine Dataset of Bangladesh” (CC0) was also evaluated as a lexicon source and **superseded** by DGDA; it is not used for verification or CNN training.
- **Speech:** `facebook/mms-tts-ben` (CC-BY-NC-4.0), gTTS fallback
- **Training:** Kaggle T4 GPU · **Submission proof:** public live link (demo video kept as optional backup)
- Full credits and licences: [`RESOURCES.md`](RESOURCES.md)

## 4. AI tools used and for what (disclosure)

- **OpenCode** (AI coding agent, **Big Pickle**) — planning, coding, debugging and drafting all project docs.
- **Google Gemini / Google AI Studio** — in-app photo readers `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite`; `gemini-2.5-flash` was used in v1 testing and hit its free quota. No output is hard-coded.
- **Groq + `qwen/qwen3.8-27b`** — 10-image second-reader bake-off only; failed the locked gate, **not shipped** and no Groq key is needed.
- **RxFusion char-CNN** — our own failed experiment, disclosed in `docs/EVALUATION.md`, **not shipped**.
- **Our own EfficientNet-B0 CNN** — fine-tuned by us on the Kaggle *Doctor's Handwritten Prescription BD* dataset; used as a safety veto and proof of a trained model.
- **External data sources** — official **DGDA Allopathic Medicine Information export** (23 Nov 2026, identity reference only) and the **Kaggle/MedEx “Assorted Medicine Dataset of Bangladesh” (~25k rows)**, which was evaluated as a lexicon source and **superseded**; neither is used for dose advice. The 200-prescription public localization set was used for position-only evaluation.
- **Speech/3D assets** — `facebook/mms-tts-ben`, gTTS fallback, and locally bundled Three.js (no CDN call).
- **Rakin** — recorded the ≤3-minute unlisted backup demo video (pending on 23 Nov).

All models/APIs above are real; no output is hard-coded or faked.

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

Tests (no network needed, 137 tests across 19 files):

```bash
.\venv\Scripts\python.exe -m unittest discover -s tests -q
```

These also run automatically on every push via GitHub Actions (badge above).

Real-handwriting evaluation runner (needs your answer key + Rx photos; never invents results):

```bash
.\venv\Scripts\python.exe tools\evaluate_handwritten.py --answers results\answer_key.csv --images results\rx --cache results\vlm_cache.jsonl --out results\handwritten_boxcap_log.csv --summary results\handwritten_boxcap_summary.json
```

It writes the named log/summary with **name accuracy (CNN / reader 1 / reader 2 / Combined), dose accuracy, unsafe-GREEN rate, catch rate and over-flag rate**. Template: [`results/answer_key_template.csv`](results/answer_key_template.csv). The answer key and photos stay local/private (gitignored); only derived metrics are committed.

External localization check on 200 real handwritten prescriptions (positions only, **not** name accuracy):

```bash
.\venv\Scripts\python.exe tools\evaluate_localization.py --zip "<dataset.zip>"
```

Evaluation table and judge proof: [`docs/EVALUATION.md`](docs/EVALUATION.md).  
Detailed 10-page project report (architecture, training, evaluation, rule compliance, demo script, Q&A): [`docs/RxBondhu_Project_Report.pdf`](docs/RxBondhu_Project_Report.pdf).

The CNN was trained on Kaggle: GPU T4 + Internet On, dataset added as Input, `training/train_cnn_kaggle.py` run with seed 42. The four outputs — `rx_cnn.pt`, `labels.json`, `test_report.csv`, `training_summary.txt` — live in `models/`; the raw training log is in `results/kaggle_training_log.txt`.

## 7. Live link and demo video

- Code (public repo): **https://github.com/SJesan/RxBondhu** ✅
- Live app (free, Streamlit Community Cloud): **https://rxbondhu.streamlit.app** — see [`docs/DEPLOY.md`](docs/DEPLOY.md). **Verified public (23 Nov):** the Cloud dashboard says “This app is public and searchable”; its auth gateway performs a 303 → cookie → 200 handshake (real browsers do this automatically), and `curl -L -c/-b cookies https://rxbondhu.streamlit.app/_stcore/health` returns **200**. There is no app-level login and no test credentials. Local demo remains primary in case the venue blocks the domain.
- Demo video (optional backup, max 3 min): script ready in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md); Rakin's recording still pending.
- No login in the app code — **no test credentials needed**.

## Safety and limits

RED says `ফার্মাসিস্টকে জিজ্ঞাসা করুন`. UNVERIFIED is editable, never GREEN and never auto-accepted; it means **“not in our verified reference”**, never “not approved”. Cards give recorded identity fields only and say **identity only, not dose advice**. GREEN needs both readers at ≥95 on a **DGDA row with a DAR No**; a box-checked-only identity is YELLOW with `Verified by box check, not found in DGDA snapshot`, and fuzzy-only is YELLOW at most. A CNN contradiction blocks GREEN unless both readers make an exact 100/100 match on a DAR-backed row; the raw CNN guess then lives in More info while the main view says `CNN: not applicable to this name`. Human confirmation is mandatory on Screen 3. See [`docs/EVALUATION.md`](docs/EVALUATION.md) for the separate word-crop and real-photo numbers.

### Known limits (honest)
- 10 real prescriptions from **one writer**; thresholds tuned on 5 dev rows and reported once on 5 holdout rows. Not a population-level accuracy claim.
- The 0.9590 number is **word-crop test accuracy**, not whole-photo accuracy; our CNN scored 0/47 on these real photos.
- A brand not in the DGDA snapshot is **UNVERIFIED** (or box-check YELLOW), never a regulatory judgement.
- No dose advice, no interaction database, no indication/price claims, and **no clinical validation**.
- Multi-prescription mode is session-only: the crop cache lives in memory and is keyed on exact pixels + exact box, so a 1px crop change re-reads; three images can use up to six reader calls and the existing 5-read CNN-only guard may engage mid-set. It is on a review branch, not merged to `main`.

### Next steps
- Larger multi-writer study with pharmacist review.
- Offline mode and wider handwriting styles.
- Clinical validation before any real-world use.

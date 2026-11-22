# Demo script (max 3 minutes)

Practice this exact flow. Keep the video/voice calm — judges care about safety and honesty.

**Delivery plan (confirmed 22 Nov):** primary = local `streamlit run app.py`;
secondary = live link `https://rxbondhu.streamlit.app` if the venue network allows
(it redirected to a Streamlit sign-in page for anonymous checks on 23 Nov, so do
not rely on it); backup = this exact ≤3-min run recorded as an unlisted MP4
by Rakin (still pending). Clean primary sample:
`samples/sample_ui_smoke.png`. Stress sample: `images.jpg`.

## 0:00–0:20 — Problem
"Many Bangladeshi prescriptions are handwritten. A caregiver can misread `1+0+1` or miss that Napa and Ace are both Paracetamol — a double dose. RxBondhu is a reading aid, not a doctor."

## 0:20–0:50 — Screen 1 (clean primary demo)
Upload a medicine-line photo (or use the rear-camera tab on a phone). The crop box starts at **92% coverage**; drag to trim or tick "already cropped". Say:
"We crop first so both readers see only medicines — no name, no signature, no patient data."
For the CNN proof, open the expander and read one clean word crop: held-out word-crop accuracy 95.90%, shown separately from real-photo numbers.

## 0:50–1:30 — Screen 2 (the AI core)
Press **Read with both AI models**. Point to:
- **one review row per medicine line** (not per word), with the line crop on the left,
- **Reader 1 `gemini-3.5-flash-lite`** and **Reader 2 `gemini-3.1-flash-lite`** reading the photo independently,
- our own EfficientNet-B0 CNN reading word crops as a **safety veto**, trained by us on 4,680 labelled word images,
- the GREEN / YELLOW / UNVERIFIED / RED badge and the one-line reason.

Honest line: "GREEN means both readers agree on a verified brand. On real phone photos our CNN is often unsure and most brands are outside the checked list, so the app shows an editable UNVERIFIED name instead of approving it. That is the safety guarantee."

## 1:30–2:10 — Screen 3 + safety warning
Pick/correct each brand, type the dose (`1+0+1`), press **Build my Bangla schedule**. Show the Bangla morning/noon/night table.
Keep Napa + Ace in the demo and say: "Two brands, same generic — we warn instead of silently adding doses."
Trigger **🔊 Bangla audio**, show the **📅 .ics** download and one Google Calendar link, then the **📱 Prepare WhatsApp message** link. Say: "These open prefilled reminders — the app never sends anything for you."

## 2:10–2:35 — Safety stress test (the Amdocal photo)
Upload `images.jpg` (Amdocal / Eltroxin / Paricel / Vave). Show the result: **exactly 4 rows with the correct names**, each 🔍 UNVERIFIED with "could not be verified — please check" and an editable name field.
Say: "Unknown brands are never auto-approved or shown GREEN. We display what the readers saw, but a pharmacist or caregiver must confirm before any schedule is built."

## 2:35–3:00 — Limits and close
"Brand list and handwriting styles are limited. We do not diagnose, prescribe, or run a drug-interaction database — always ask a pharmacist. Evidence: our CNN's held-out word-crop test is 95.90%, separate from real-photo accuracy; two-reader bake-off and honest limits are in `docs/EVALUATION.md`. Built fresh for the hackathon with OpenCode, Gemini and our own trained CNN; Rakin recorded the backup video. Live link here."

## Backup if a model is down
- No internet / Gemini key: app clearly says both readers offline and shows CNN-only lines — keep going.
- One reader offline: the other reader still supplies the rows, but never a fake GREEN — keep going.
- No CNN file: app clearly says CNN not trained and shows reader-only lines — keep going.
- Audio fails: explain gTTS/MMS fallback and show the Bangla text table instead.
- A photo produces messy doses: correct them on screen 3 — that is exactly the human-in-the-loop step.

Record with phone + OBS or any screen recorder. Keep total under 3:00. Export MP4 and upload to YouTube (unlisted) or Loom; paste link in submission.

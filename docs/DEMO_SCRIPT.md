# Demo script (max 3 minutes)

Practice this exact flow. Keep the video/voice calm — judges care about safety and honesty.

## 0:00–0:20 — Problem
"Many Bangladeshi prescriptions are handwritten. A caregiver can misread `1+0+1` or miss that Napa and Ace are both Paracetamol — a double dose. RxBondhu is a reading aid, not a doctor."

## 0:20–0:50 — Screen 1 (clean primary demo)
Use a tight crop around **only the medicine lines** (2–3 lines). Upload it, drag the crop box, say:
"We crop first so both readers see only medicines — no name, no signature, no patient data."

## 0:50–1:30 — Screen 2 (the AI core)
Press **Read with both AI models**. Point to:
- **one review row per medicine line** (not per word),
- the small word crops that feed **our own EfficientNet-B0 CNN**, trained by us on 4,680 labelled word images,
- **Google Gemini Flash** reading the same crop independently,
- the GREEN / YELLOW / RED badge and the reason line.

Honest line: "GREEN means both readers agree. On real phone photos our CNN is often unsure, so the app refuses GREEN and asks a human to confirm. That is the safety guarantee."

## 1:30–2:10 — Screen 3 + safety warning
Pick/correct each brand, type the dose (`1+0+1`), press **Build my Bangla schedule**. Show the Bangla morning/noon/night table.
Keep Napa + Ace in the demo and say: "Two brands, same generic — we warn instead of silently adding doses."
Trigger **🔊 Bangla audio** and show the **📅 .ics** download.

## 2:10–2:35 — Safety stress test (the Amdocal photo)
Upload `images.jpg` (Amdocal / Eltroxin / Paricel / Vave). Show the result: **exactly 4 rows with the correct names**, each 🔴 RED with "not in the verified list — please confirm".
Say: "Unknown brands are never auto-approved. We display what Gemini read, but a pharmacist or caregiver must confirm before any schedule is built."

## 2:35–3:00 — Limits and close
"Brand list and handwriting styles are limited. We do not diagnose, prescribe, or run a drug-interaction database — always ask a pharmacist. Evidence: our CNN's held-out word-crop test is 95.90%, separate from real-photo accuracy; honest logs are in `docs/EVALUATION.md`. Built fresh for the hackathon with OpenCode + Gemini. Live link here."

## Backup if a model is down
- No internet / Gemini key: app clearly says Gemini offline and shows CNN-only lines — keep going.
- No CNN file: app clearly says CNN not trained and shows Gemini-only lines — keep going.
- Audio fails: explain gTTS/MMS fallback and show the Bangla text table instead.
- A photo produces messy doses: correct them on screen 3 — that is exactly the human-in-the-loop step.

Record with phone + OBS or any screen recorder. Keep total under 3:00. Export MP4 and upload to YouTube (unlisted) or Loom; paste link in submission.

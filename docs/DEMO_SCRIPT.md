# Demo script (max 3 minutes)

Practice this exact flow. Keep the video/voice calm — judges care about safety and honesty.

## 0:00–0:20 — Problem
"Many Bangladeshi prescriptions are handwritten. A caregiver can misread `1+0+1` or miss that Napa and Ace are both Paracetamol — a double dose. RxBondhu is a reading aid, not a doctor."

## 0:20–0:50 — Screen 1
Show a volunteer's handwritten sample (no real patient data). Upload it. Drag the crop around only the medicine lines. Say: "We crop first so the readers see only medicines."

## 0:50–1:30 — Screen 2 (the AI core)
Press **Read with both AI models**. Point to:
- the small word crops (OpenCV),
- **our own EfficientNet-B0 CNN**, trained on 4,680 labelled word images,
- **Google Gemini Flash** reading the same crop independently,
- the GREEN / YELLOW / RED badges and the reason line.

Honest line: "GREEN means both readers agree. Anything else demands human confirmation."

## 1:30–2:10 — Screen 3
Pick the right brand from suggestions, type/correct the dose (`1+0+1`). Press **Build my Bangla schedule**. Show the Bangla morning/noon/night table. Trigger the duplicate warning by keeping Napa + Ace in the demo.

Say: "Two brands, same generic — we warn instead of silently adding doses."

## 2:10–2:35 — Audio + proof
Press **Bangla audio**. Let it speak 8–10 seconds. Then show `models/labels.json` test accuracy and the CNN/Gemini/Combined comparison in `docs/EVALUATION.md`.

## 2:35–3:00 — Limits and close
"Limited brand list and handwriting styles; that is why every line is confirmed. We don't diagnose, prescribe, or check interactions. Live app / video link here. Built fresh for the hackathon with OpenCode + Gemini."

## Backup if a model is down
- No internet / Gemini key: app clearly says Gemini offline and shows CNN-only results — keep going.
- No CNN file: app clearly says CNN not trained and shows Gemini-only — keep going.
- Audio fails: explain gTTS/MMS fallback and show the Bangla text table instead.

Record with phone + OBS or any screen recorder. Keep total under 3:00. Export MP4 and upload to YouTube (unlisted) or Loom; paste link in submission.

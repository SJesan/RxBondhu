# Demo script (max 3 minutes)

Practice this exact flow. Keep the video/voice calm — judges care about safety and honesty.

**Delivery plan (confirmed 22 Nov):** primary = local `streamlit run app.py`;
secondary = live link `https://rxbondhu.streamlit.app` if the venue network allows
(**verified public 23 Nov**: Cloud dashboard says “public and searchable” and the
health endpoint returns 200 after the normal auth-cookie handshake; a plain
no-cookie checker loops on 303, which is Streamlit platform behaviour, not a
private app); backup = this exact ≤3-min run
recorded as an unlisted MP4 by Rakin (still pending). Clean primary sample:
`samples/sample_ui_smoke.png`. Stress sample: `images.jpg`.

## 0:00–0:20 — Problem
"Many Bangladeshi prescriptions are handwritten. A caregiver can misread `1+0+1` or miss that Napa and Ace are both Paracetamol — a double dose. RxBondhu is a reading aid, not a doctor."

## 0:20–0:50 — Screen 1 (clean primary demo)
Briefly show the light hero, the six small fictional demo Rx thumbnails and the sidebar 🌙/☀️ toggle (light is default); switch to dark and back once if time allows. **Click a demo thumbnail once** — it loads exactly like an upload. You can also upload your own photo or use the rear-camera tab on a phone. The crop box starts at **92% coverage**; drag to trim or tick "already cropped". The cropper is the **only** photo preview — its green rectangle shows exactly what the AI reads; the crop itself still feeds the pipeline. Say:
"We crop first so both readers see only medicines — no name, no signature, no patient data."
For the CNN proof, open the expander and read one clean word crop: held-out word-crop accuracy 95.90%, shown separately from real-photo numbers.

## 0:50–1:30 — Screen 2 (the AI core)
Press **Read with both AI models** — the two-tone **capsule animation** plays while the models work. Point to:
- **one review row per medicine line** (not per word), with both readings side by side and no unreliable line-crop thumbnail,
- one short status strip: **Reader 1 `gemini-3.5-flash-lite`** and **Reader 2 `gemini-3.1-flash-lite`** reading the photo independently (the old four metrics and long legend are gone),
- our own EfficientNet-B0 CNN reading word crops as a **safety veto**, trained by us on 4,680 labelled word images; an exact dual-DGDA match overrides its out-of-distribution guess and the reason says so,
- the GREEN / YELLOW / UNVERIFIED / RED badge and the one-line reason,
- the compact **DGDA তথ্য card** on the right: generic, **DAR No**, strength and form; press **More info** to reveal brand, company, source and access date. Say “DGDA-registered means this identity is in the official Allopathic export we checked on 23 Nov — it is not dose advice, and a missing name is only UNVERIFIED, never ‘not approved’. The export has no indication field, so we do not guess what it works for.”

Honest line: "GREEN needs both readers to agree with a 95+ match on a DGDA-registered brand. A fuzzy-only match stops at YELLOW. If both readers match the brand exactly, the CNN's guess is shown but ignored because its 78 training classes do not include these real-photo brands — the reason text says that. Everything still needs human confirmation before a schedule appears."

## 1:30–2:10 — Screen 3 + safety warning
Pick/correct each brand, type the dose (`1+0+1`), press **Build my Bangla schedule**. If you correct a brand, show that its **generic and badge update together** (a manual exact DGDA match clears a stale RED; an unknown typed name becomes neutral UNVERIFIED). Show the Bangla morning/noon/night table (no colour column) and the always-visible Bangla summary.
Keep Napa + Ace in the demo and say: "Two brands, same generic — we warn instead of silently adding doses."
Trigger **🔊 Bangla audio**, show the **📅 Download reminders (.ics)** button and the new **📅 Add all medicines once (Google Calendar)** button. Say: "The .ics imports every dose as a separate event; the new button opens one overview event with all medicines in the description." Then show **📱 WhatsApp reminder** (opens prepared text) and the disabled **Email / Call reminder — Coming soon** placeholders. Say: "These open prefilled reminders — the app never sends anything for you."

## 2:10–2:35 — Safety stress test (the Amdocal photo)
Upload `images.jpg` (Amdocal / Eltroxin / Paricel / Vave). Show the result: **exactly 4 rows with the correct names**. Names outside the DGDA snapshot stay editable UNVERIFIED; a name that is in the snapshot shows its DGDA card, and `Panicel` vs `Paricel` spelling disagreement is RED.
Say: "Unknown brands are never auto-approved or shown GREEN, and a fuzzy match cannot become GREEN. We display what the readers saw plus the DGDA record when it exists — a pharmacist or caregiver must confirm before any schedule is built."

## 2:35–3:00 — Limits and close
"Brand list and handwriting styles are limited. We do not diagnose, prescribe, or run a drug-interaction database — always ask a pharmacist. Evidence: our CNN's held-out word-crop test is 95.90%, separate from real-photo accuracy; two-reader bake-off and honest limits are in `docs/EVALUATION.md`. Built fresh for the hackathon with OpenCode, Gemini and our own trained CNN; Rakin recorded the backup video. Live link here."

## Backup if a model is down
- No internet / Gemini key: app clearly says both readers offline and shows CNN-only lines — keep going.
- One reader offline: the other reader still supplies the rows, but never a fake GREEN — keep going.
- No CNN file: app clearly says CNN not trained and shows reader-only lines — keep going.
- Audio fails: explain gTTS/MMS fallback and show the Bangla text table instead.
- A photo produces messy doses: correct them on screen 3 — that is exactly the human-in-the-loop step.

Record with phone + OBS or any screen recorder. Keep total under 3:00. Export MP4 and upload to YouTube (unlisted) or Loom; paste link in submission.

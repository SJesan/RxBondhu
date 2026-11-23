# Demo script (hard stop at 3:00)

Practice this exact flow three times, timed. Judges care about **safety and honesty** more
than speed — never say "approved", never claim whole-photo accuracy, never hide a reader
failure. Every screen starts with the same Bangla disclaimer, once, at the top.

## Delivery plan (confirmed 23 Nov)

1. **Primary:** local `streamlit run app.py` on the laptop (offline-safe apart from the two
   Gemini readers; .env key already loaded).
2. **Secondary:** live link <https://rxbondhu.streamlit.app> if the venue network allows.
   Verified public 23 Nov: Cloud dashboard says "public and searchable"; the health endpoint
   returns 200 after Streamlit's standard 303 → cookie → 200 handshake (a no-cookie checker
   loops on 303 for *all* public Streamlit apps).
3. **Backup:** this same ≤3-min run as an **unlisted MP4 recorded by Rakin** (still pending —
   must be ready before check-in). Three offline screenshots in `docs/screenshots/` are a
   last-resort visual fallback (see "Offline backup" below).

## The six demo images (`assets/demo/`, fictional, click-to-use)

| # | File | Verified fusion result | Purpose |
|---|---|---|---|
| 01 | `demo_rx_01.png` | GREEN / GREEN / GREEN | **Clean primary** — Pantonix, Maxpro, Lysivin (all DAR-backed) |
| 02 | `demo_rx_02.png` | GREEN / GREEN / GREEN | Second clean — Seclo, Losar, Zyrtec |
| 03 | `demo_rx_03.png` | YELLOW / GREEN / YELLOW | **YELLOW fixed live** — Napa + Fexo are box-check-only, Maxpro is DAR-backed |
| 04 | `demo_rx_04.png` | GREEN / GREEN / GREEN | **Deliberate RED** — clean base, then flag one line "Not sure?" on Screen 2 |
| 05 | `demo_rx_05.png` | UNVERIFIED ×3 | Off-list stress — Amsocal, Eltroxin, Panicel |
| 06 | `demo_rx_06.png` | YELLOW / GREEN / UNVERIFIED | Mixed stress — Napa, Alafree, Zinc |

Colours were **verified with `tests/test_demo_sets.py`** (two exact readers through real
fusion), not guessed. Gemini may spell a name slightly differently on the day — the safety
story holds either way: only DAR-backed exact dual matches reach GREEN.

## 0:00–0:20 — Problem

"Many Bangladeshi prescriptions are handwritten. A caregiver can misread `1+0+1`, or miss that
two brands are the same generic — a double dose. RxBondhu is a **reading aid**, not a doctor."

## 0:20–0:45 — Screen 1: photo + crop

- Point to the single Bangla disclaimer at the top, then the **Large text default** (sidebar
  Text size) and the light/dark toggle. One-line hero on this screen is the full 3D card.
- Click **Demo 01** once — it loads exactly like an upload. Mention upload and rear-camera tabs;
  the camera tab says plainly "Camera not working? Use the Upload photo tab".
- Show the one-sentence crop help, the small **crop example** image, and
  `ছবি সংরক্ষণ করা হয় না` (session-only photos). The 92% margin is hidden under **Advanced** —
  do not open it unless asked. The green crop box is the only photo preview.
- Say: "We crop first so both readers see only medicine lines — no name, no signature, no date."
- Press **🔍 Read with both AI models →**; the loader says `দুটি AI পড়ছে…`.

## 0:45–1:25 — Screen 2: the AI core (Demo 01, all GREEN)

Point to, in order:

- **One card per medicine line**, large padding, one-line hero, one disclaimer at top.
- The plain Bangla status line **`দুটি AI একমত`** under each GREEN badge (YELLOW = `আবার দেখুন`,
  RED = `ফার্মাসিস্টকে জিজ্ঞাসা করুন`).
- The short status strip: Reader 1 `gemini-3.5-flash-lite`, Reader 2 `gemini-3.1-flash-lite`
  reading independently. Our own EfficientNet-B0 CNN reads word crops as a **safety veto**,
  trained by us on 4,680 public word images.
- The readings block: main view shows `CNN: not applicable to this name` for an
  out-of-distribution guess; **More info** holds the raw `CNN: Az (0.62)` and the note that the
  78-class model saw clean word crops, not whole prescriptions.
- The compact **DGDA তথ্য** card: generic, DAR No, strength, form; **More info** adds company,
  source, access date, conflict detail and the raw CNN guess.

Say exactly:
> "GREEN needs both readers to agree at 95+ on a DGDA row **with a DAR No** — this is an
> identity check against the official Allopathic export we checked on 23 Nov, **identity only,
> not dose advice**. A name missing from the export is UNVERIFIED, never 'not approved'. A
> fuzzy-only match stops at YELLOW. Fuzzy-only never reaches GREEN."

## 1:25–2:00 — Screen 3: confirm + Bangla schedule (Demo 01)

- Show each line: pick/correct the brand, type the dose (`1+0+1`). Correct one brand to an
  exact DGDA row and show its **generic and badge update together**; a wrong typed name becomes
  neutral UNVERIFIED, never GREEN.
- Press **✅ Build my Bangla schedule**. The **Bangla-first table** comes first: `ওষুধ / জেনেরিক /
  ডোজ / সকাল / দুপুর / রাত / দিন` with small English, big ✓ and Bangla digits. A missing day
  says `দিন লেখা নেই — নিশ্চিত করুন`, never a bare dash.
- Show the always-visible Bangla summary, then one main **🔊 শুনুন Bangla audio** button
  (per-medicine audio is below). Then **📅 Download reminders (.ics)**, **📅 Add all medicines
  once (Google Calendar)** and **📱 WhatsApp reminder**. Say: "These open prepared reminders —
  the app never sends anything or books anything for you." No "Coming soon" buttons remain.

## 2:00–2:25 — YELLOW fixed live (Demo 03)

Go back to Screen 1, click **Demo 03**. Screen 2 shows:

- Napa and Fexo = **YELLOW**, reason `Verified by box check, not found in DGDA snapshot —
  confirm on paper`. Maxpro = GREEN (it has a DAR No).
- Open **More info** on Napa: the card names the conflict (DGDA also maps `Napa` to caffeine +
  paracetamol) and says **identity only, not dose advice**. Never say "approved" or "not
  approved".

Say:
> "Napa and Fexo are real medicines we checked on the box, but our DGDA snapshot has no clean
> matching row — so they stop at YELLOW with honest wording, not a fake GREEN."

**Fix live:** on Screen 3, select a DAR-backed exact brand for the line where the paper and
box support it (or confirm the box-only identity with the caregiver). Show the badge/generic
update, then build the schedule. This is the whole point: **a human resolves every YELLOW
before it becomes a schedule.**

## 2:25–2:45 — Deliberate RED + off-list stress (Demos 04 & 05)

- Demo 04 is clean GREEN; press the small neutral grey **"Not sure?"** button on one line and
  show it flip to **RED** with `ফার্মাসিস্টকে জিজ্ঞাসা করুন`. Say: "Any caregiver can downgrade a
  line; the flag is deliberate and the reason is recorded."
- Demo 05 shows three off-list brands as **UNVERIFIED** (editable, never GREEN). Say: "Unknown
  names are never auto-approved. We show what the readers saw and ask a pharmacist."

## 2:45–3:00 — Limits and close

> "Ten real prescriptions from one writer — this is a same-writer safety check, not a
> population accuracy claim. Our 95.90% is **word-crop test accuracy**, separate from real-photo
> accuracy (our CNN scored 0/47 there). We do not diagnose, prescribe, run interactions, or give
> dose advice. Built fresh for the hackathon, solo, with OpenCode (Big Pickle), two Gemini
> readers and our own trained CNN. Evidence in `docs/EVALUATION.md`. Live link here."

## Backup if something fails on the day

- **Both readers offline / quota:** the app names each failed reader, continues with CNN only,
  and never invents a reading. Keep going — this is an intended, tested path.
- **One reader offline:** other reader continues; single-reader lines cap at YELLOW.
- **No CNN file / audio fails:** app says so plainly; show the Bangla text table instead.
- **Messy dose:** correct it on Screen 3 — that is the human-in-the-loop step.
- **Network completely down:** use local Streamlit, then the offline screenshots in
  `docs/screenshots/`, then Rakin's unlisted video.

## Rehearsal checklist (three timed runs before 24 Nov 09:00)

- [ ] Run 1 ≤ 3:00, Run 2 ≤ 3:00, Run 3 ≤ 3:00 (record the times here: ___ / ___ / ___).
- [ ] Demo 01 → all GREEN; Demo 03 → YELLOW wording + live fix; Demo 04 → "Not sure?" RED.
- [ ] Say "identity only, not dose advice" and "word-crop test accuracy" verbatim.
- [ ] Never say "approved", "not approved", or claim whole-photo accuracy.
- [ ] Judge's own photo end-to-end: upload → crop → read → confirm → schedule → audio.
- [ ] Rear camera tested on a real phone; upload fallback confirmed.
- [ ] Rakin's ≤3-min unlisted video uploaded and link pasted in the submission.
- [ ] Offline screenshots current after the final code push.
- [ ] `git status` clean, CI green, secret scan clean, live health 200.

## Offline backup

`docs/screenshots/` holds PNGs of the three screens (light theme, Large text):
`screen1_photo.png`, `screen2_reading.png` (YELLOW box-check demo), `screen3_schedule.png`
(Bangla-first table). They are a visual fallback only — the live app and Rakin's video are the
primary evidence. Re-capture after any further UI change.

Record with phone + OBS or any screen recorder. Keep total under 3:00. Export MP4, upload to
YouTube (unlisted) or Loom, and paste the link in the submission.

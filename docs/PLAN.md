# RxBondhu — Full Winning Plan (Zero → Final)
**Hackathon:** CoU AI Hackathon 2026 · Healthcare & Wellbeing  
**Track:** Team Zero-Shot · **Build window:** 21–23 Nov 2026 · **Final:** 24 Nov 2026 (5 hours on-site)
**Plan version:** 21 Nov 2026 · **Owner:** `[CERTIFICATE_NAME]` (confirm exact spelling from registration form)  
**Language:** Bangla + English mix, deliberately simple.

---

## 0. Current reality (read this first)

- Payment **done** ✅ — seat confirmed.
- Kaggle phone verification **possible** ✅ — primary training path is Kaggle T4 GPU (fallback: Colab T4 → local RTX 3050 with small batch).
- Final-day check-in / start / deadline time is **still TBC** by organisers. Keep checking email + website. Two non-negotiable rules anyway: **submit ≥10 minutes early** and **commit at least hourly during the final**.
- `RxBondhu_code.zip` exists in Downloads, but **you did not write it**. Rule 8 forbids old / someone else's project code. **Decision: DO NOT copy that code.** Use only the Roadmap's Section 3 & 6 as a *specification* and the library list as reference. We write **fresh code starting 21 Nov** with AI assistance. This also means you can genuinely explain every line — which judges score.
- You are starting from near-zero knowledge. That is fine: the AI writes code **with** you, step by step, and you verify + explain. Understanding beats code volume.

---

## 1. Source documents

| File | Original location | What it gave us |
|---|---|---|
| `rulebook.pdf` | `C:\Users\sadik_gabesu6\Downloads\rulebook.pdf` | Official rules, deadlines, disqualification triggers |
| `RxBondhu_Roadmap (2).docx` | same Downloads folder | Architecture, flow, module list, 8-slide outline, judge Q&A |
| `RxBondhu 0 থেকে Final পর্যন্ত Winning Plan (Solo).docx` | same Downloads folder | Solo scope cutting (MUST / SHOULD / CUT), teach-back, risk list |
| `RxBondhu_code.zip` | same Downloads folder | **Reference only — do not copy code** |

**After switching to Build mode:** copy all four files into `D:\OpenCode\cu` together with this plan (MD + DOCX + PDF).

---

## 2. Rulebook hard limits (rule numbers inside)

| Rule | Meaning for us |
|---|---|
| **8.1–8.8** | Project-specific code may be written **only from 21 Nov**. Before that: research, planning, UI wireframes, choosing datasets, accounts/keys, learning. No old / previously submitted / someone else's project. Open-source libraries, public APIs, UI kits are allowed — **list them in README**. |
| **9.1–9.11** | Coding assistants allowed (ChatGPT, Claude, Gemini, Copilot, Cursor, similar) — **disclose each one and what it did**. Models/APIs must be named. Hard-coded / pre-recorded / human-faked AI output = **disqualification**. Bare prompt-forwarding wrapper scores low. Judges score what you designed and can explain. Public/licensed/own data only, credited. Bring your own keys. |
| **10.1–10.10** | One public repo, **created on/after 21 Nov**; **first commit on/after 21 Nov**; commit regularly from your own account, **at least hourly during the final**; no force-push, squash or back-dating; **last commit before deadline is judged**; never commit keys, include `.env.example`. README must contain: project/team/member names; problem+solution; features+how AI works; tech stack/models/APIs/datasets; AI tools used and for what; third-party code/assets credited; setup steps, live link, demo video. |
| **11.1–11.8** | Deploy publicly from the repo (free tiers OK, stay live until results). If login exists: give test credentials. Can't deploy? Demo video **max 3 minutes** showing the real project. Live demo must run the real project; slides/recordings only as network backup; keep local copy + recording. |
| **12.1–12.6** | Submission by leader, one per team, before final ends: title + description **max 150 words**, public GitHub link, live link **or** demo video, credentials if login, AI tools + models disclosure. **Submit ≥10 min early**; broken/private link counts as missing. |
| **6.1–6.9** | Tk 1,350 payment deadline **23 Nov 11:59 PM** (already paid). Never share PIN/OTP/password. |
| **7.1–7.10** | Original student ID at check-in; >30 min late may be refused; 5 continuous hours, organiser clock only; bring own laptop/charger/extension/hotspot; no outside help; mentors guide but never write code. |
| **13.1–13.8** | Disqualification: code before 21 Nov, old project, plagiarism, outside help, faked demo/AI, rewritten history, post-deadline changes, false info. Lesser breaches (missing README item, undisclosed AI tool) = point deduction or warning. |
| **Phase 1 criteria** | Rulebook says: **problem clarity, AI relevance, feasibility, originality**. The Roadmap's 20/25/25/15/15 split differs — follow the **rulebook**. |

---

## 3. Winning strategy — do less, prove more

### MUST (never cut)
1. Your **own trained CNN** + honest held-out test accuracy.
2. App running locally: **Photo → Review → Schedule**.
3. **Gemini reader** as second model + fusion colours.
4. Public GitHub with a **first commit on 21 Nov** and regular commits.
5. README with **all 7 required sections** + AI tool/model/dataset disclosure.
6. Live link **or** ≤3-min real demo video + demo script + backup video.

### SHOULD
- Bangla audio (MMS-TTS, gTTS backup).
- 10–12 own handwritten test prescriptions + **CNN / Gemini / Combined** table.
- 3–5 volunteer usability test (3 volunteers is acceptable).

### CUT (protect your sleep)
- docTR detector, 20 prescriptions, 10 volunteers, phone-link polish, extra brand entries, FreeLLMAPI proxy setup (OpenCode is the coding assistant).

### Never do
Hard-code output · rewrite old commits · commit a key · quote an unmeasured number.

### Why this wins
- **Real AI, live:** two models, one trained by you.
- **Safety by design:** RED/YELLOW, user confirm before schedule, duplicate-generic warning.
- **Proof:** one small table (CNN only / Gemini only / combined) + two separate accuracy numbers.
- **Explainability:** you can teach back all 8 key terms.
- Solo advantage: no teammate can say "I didn't see that part."

---

## 4. Build order — no clock, just sequence

Each step: say "Step N" → AI writes + explains → you run it → paste full error if any → commit.

### Step 1 — Repo + first commit (TODAY)
AI: create repo structure, `.gitignore`, `.env.example`, skeleton README.  
You: GitHub → **New repository → Public → `RxBondhu`**, commit everything **on 21 Nov**.  
Done: public repo, first commit today, no `.env`, no key anywhere.

### Step 2 — Python environment
AI: give exact commands for venv + `pip install -r requirements.txt` + smoke test.  
You: install **Python 3.11** with "Add python.exe to PATH" ticked, Git + GitHub Desktop.  
Done: venv activates, smoke test runs, errors decoded.

### Step 3 — `dose_parser.py` (first quick win)
AI: write parser for `1+0+1`, `1+1+1`, `0+0+1`, `BD`, `TDS`, `HS`, `রাতে ১ টি`, `সকাল ১ টি` → morning/noon/night + days.  
You: invent 5 dose strings and check output.  
Done: you can say in Bangla what the module does.

### Step 4 — `lexicon.py` + `safety.py`
AI: 10 verified brand→generic rows, RapidFuzz fuzzy match, duplicate-generic warning.  
You: verify each generic from a medicine box / trusted drug index; mark `verified = yes`.  
Done: "Maxpo" → "Maxpro" matches; two paracetamol brands trigger warning.

### Step 5 — `fusion.py`
AI: GREEN = both agree, YELLOW = one confident, RED = disagree/unsure.  
You: create 3 test cases manually.  
Done: RED always means "confirm with pharmacist", never a guess.

### Step 6 — Train CNN on Kaggle (start early; runs while you do Steps 3–5)
AI: write/review `training/train_cnn_kaggle.py`, explain metrics.  
You: Kaggle → New Notebook → **GPU T4 + Internet On** → Add Input "Doctor's Handwritten Prescription BD" → paste script → Run (~30–40 min). Download `rx_cnn.pt`, `labels.json`, `test_report.csv`. Save Version → Save & Run All.  
Done: files in `models/`, metrics screenshot saved. If `device: cuda` and ~3120/780/780 don't appear → stop and ask AI.

### Step 7 — `segment.py` + `recognizer.py`
AI: OpenCV word/line grouping; load CNN, 128×384 input, top-1/top-3 + confidence.  
You: upload one of your Rx photos, crop medicine area.  
Done: sidebar shows "Handwriting model: loaded" + test accuracy.

### Step 8 — `vlm.py` (Gemini)
AI: read key from `.env`, 25 s timeout, never crash the app, JSON output.  
You: Google AI Studio → free key → paste into `.env` only. If model-name error, set `RX_VLM_MODEL`.  
Done: review screen says "AI reader found N line(s)".

### Step 9 — `pipeline.py` + `app.py`
AI: wire all modules; 3 screens **Photo → Review → Schedule**; user confirm gate.  
You: run `streamlit run app.py`, upload Rx, crop, review, fix, make schedule.  
Done: **no schedule appears before user confirms**.

### Step 10 — `bangla.py` + `tts.py`
AI: Bangla morning/noon/night table + speech (MMS-TTS, gTTS backup).  
You: open schedule screen once online so voice model (~150 MB) downloads; then **Wi-Fi off → restart → run again**.  
Done: offline CNN + matching + dose + safety + audio all work; only Gemini is unavailable offline.

### Step 11 — Test prescriptions + log
AI: test log template, bug categories.  
You: hand-write 10–12 "doctor-style" prescriptions. Two must contain two brands with the same generic; 1–2 use brands outside the 78. Photograph straight from above in good light. Save answer keys. No real patient data.  
Done: 10–12 log rows; 3 demo Rx chosen: all-GREEN / duplicate warning / RED being corrected.

### Step 12 — Evaluation (your proof)
AI: `tools/make_results.py`, charts, comparison table.  
You: count correct names three ways — CNN only (reader off), Gemini only ("AI reader saw" text), combined. Keep **dataset test accuracy** separate from **your own Rx accuracy**.  
Done: small honest table + charts on results slide.

### Step 13 — Deploy + README + slides + video
AI: HF Space files (Streamlit SDK), README with all 7 sections, 8-slide deck, 150-word description, demo script.  
You: Hugging Face Space → add `GEMINI_API_KEY` as **Secret** → open link on phone. Record ≤3-min backup video with Win+G/OBS (real app, audio). 3–5 volunteers: 3 Rx without app, 3 different Rx with app, time + correctness + one quote. Rehearse twice aloud.  
Done: live link **or** valid video; slides ready; README complete; 2 rehearsals. **Feature freeze** when this gate passes.

### Step 14 — Final day (relative to official clock)
Hour 1 setup + tests + demo Rx + phone link → Hour 2 small fixes, update README links/numbers, **commit + push** → Hour 3 submit form ≥10 min early → Hour 4 two rehearsals + 10 judge questions aloud → Hour 5 present + **final commit before deadline**. Hourly commits throughout.

---

## 5. Gates (state, not time)

| Gate | Condition |
|---|---|
| **Gate 1** | Repo + first commit on 21 Nov; env works; dose/lexicon/safety/fusion tested; CNN trained and in `models/`; 3 Rx photos + answer keys. |
| **Gate 2** | Gemini reader; Bangla audio offline; 3-screen app; 10–12 Rx logged; live link or video; **feature freeze** (only bug fixes after this). |
| **Gate 3** | Comparison table + charts; 3 demo Rx; backup video; 3–5 volunteers; 8 slides; final README + 150 words; 2 rehearsals; **code freeze** (crash fixes only). |
| **Gate 4** | Submit early, present, last commit pushed before deadline. |

---

## 6. How to work with AI (zero-knowledge workflow)

**AI does:** unzip/setup, venv, installs, code, error decoding, metrics explanation, bug fixes, commit messages, README/slides/draft, quizzes.  
**You do:** accounts, phone verify, write Rx on paper, verify generics, payment (done), ID at check-in, record video, rehearse aloud, honest disclosure.

**Prompt templates (copy-paste):**
```
Step 1 শুরু করি। Public RxBondhu repo-র structure, .gitignore, .env.example বানাও।
জিপের কোড কপি করব না — Roadmap section 3/6 থেকে নতুন করে লিখব।
আজই first commit-এর জন্য files প্রস্তুত করো।
```
```
Debug:
Phase: (Step 8, Gemini)
কী করছিলাম: ...
কী হলো: (পুরো লাল error / screenshot)
কী চেষ্টা করেছি: ...
OS: Windows 11, Python 3.11
```
```
Training শেষ। METRICS: (paste metrics)। Top-1/Top-3 কত?
threshold ঠিক আছে কি? পরের ২টা কাজ বলো।
```

**Rule:** after every bug fix → one commit with a clear message (`Fix dose parser for BD notation`). No force-push. No key in chat/code/screenshot.

---

## 7. Teach-back — 8 terms you must explain

| Term | One-line answer |
|---|---|
| Transfer learning | ImageNet-এ আগে শেখা EfficientNet-B0 নিয়ে আমার handwriting-এ আবার শেখালাম — কম data-তেই কাজ করে। |
| CNN | ছবি চেনার standard model; শব্দের ছবি → ৭৮টি brand-এর একটি + confidence। |
| Train / Val / Test | Train থেকে শেখে, Val দিয়ে setting ঠিক করি, Test কখনো দেখেনি → সৎ স্কোর (3,120 / 780 / 780)। |
| Top-1 / Top-3 | প্রথম অনুমান ঠিক কতবার / সঠিক উত্তর প্রথম ৩টির ভেতর কতবার (Top-3 → suggestion list)। |
| Confidence + calibration | ০.৯ মানে সত্যিই ~৯০% ঠিক হওয়া — স্কোরকে সৎ করা। |
| Threshold | যে cut-off-এর ওপরের reading ≥৯৫% ঠিক; নিচে হলে user-কে confirm। |
| VLM + hallucination | Gemini ছবি দেখে লেখে, কিন্তু না-থাকা নাম বানাতে পারে — brand list দিয়ে আটকাই। |
| Lexicon + fuzzy matching | Real brand list; "Maxpo" → "Maxpro" ধরা (edit distance, RapidFuzz)। |

**Nightly drill (10 min):** explain these aloud to AI; AI corrects you. AI can also generate an exam-style quiz.

---

## 8. Judge Q&A bank (short answers)

| Question | Core answer |
|---|---|
| Why not just Gemini/ChatGPT? | General model invents names and has no honest confidence. Our own CNN + brand list + fusion + RED flag. Measured all three. |
| What data? | Public "Doctor's Handwritten Prescription BD" (Kaggle, mamun1113): 4,680 word images, 78 brands, 15 generics. Credited in README. |
| Why EfficientNet-B0? | Small, fast on laptop CPU, strong transfer learning; wide words → 128×384 input. |
| How do you know it works? | Held-out test accuracy + our own prescriptions + small usability test. Two numbers reported separately. |
| What if AI is wrong? | User always reviews; RED says ask pharmacist; reading aid, not a doctor. No diagnosis/interaction checking. |
| Brands outside 78? | Gemini reads them; verified manual list matches; YELLOW because only one model read them. |
| Offline? | Yes except Gemini. Voice model downloaded beforehand. Phone hotspot as backup. |
| Solo — how? | Phases separated: data, train, app, test, deploy. AI coding tools used and disclosed. I designed safety, chose scope, trained, measured, tested. |
| AI wrote code — what did you do? | Scope cutting, safety design, dataset choice, training/eval, handwriting Rx, and I can open `fusion.py`/`dose_parser.py` and explain line by line. |
| What other AI tools? | Truthfully read the README list (OpenCode; Gemini in-app; any other assistant actually used). |
| Privacy? | Session-only images; volunteer-written Rx only, no patient data. |
| Claim "97.1% handwritten (Scientific Reports 2022)"? | Verify paper title/number/link before using it; otherwise use safer wording "many prescriptions are handwritten". |
| Next? | 2–3 pharmacy pilot, more brands/data with consent, reminder feature. |

---

## 9. Templates

### Test log (one row per Rx)
`ID | True medicines (answer key) | Found | Correct names | Correct doses | Time (s) | Problems`

### Model comparison (fill honestly)
`System | Correct names | Total names | Accuracy`
Rows: CNN only (reader off) · Gemini only ("AI reader saw") · Combined (RxBondhu)

### Usability (3–5 volunteers)
`Volunteer | Correct without app | Time without | Correct with app | Time with | One quote`
Swap which Rx set is used with/without app between volunteers.

---

## 10. Risks & fallbacks

| Risk | Fallback |
|---|---|
| Fresh build slower than expected | Cut order: 5→3 volunteers → 12→10 Rx → Bangla audio (text schedule stays) → live link (video). Never cut: own CNN, honest numbers, README disclosure, commit history. |
| Kaggle GPU fails | Colab T4 → local RTX 3050 (batch ~16) |
| Accuracy low | Report honestly; tune epochs/size; RED flag + review screen keep it safe |
| Line detection fails on real handwriting | Tighter crop; Gemini reads whole image; user adds missed medicine manually |
| HF deploy stuck | Local demo + ≤3-min real project video (allowed by rule 11.4) |
| Gemini quota / model name error | CNN-only mode (already built); fix `RX_VLM_MODEL` |
| Key leaked | Delete key at provider immediately, create new one |
| No internet at venue | Everything but Gemini offline; hotspot; backup video only as network backup |
| Sleep loss | Minimum 6–7 hours; tired debugging costs double time |

---

## 11. Final submission checklist

- [ ] Title + description ≤150 words
- [ ] Public GitHub link; **no key**; `.env.example` present
- [ ] Commits on 21–24 Nov, hourly during final; no force-push/squash/back-date
- [ ] Live link **or** demo video ≤3 min
- [ ] README: member name (`[CERTIFICATE_NAME]`), problem/solution, features + how AI works, tech stack/models/APIs/datasets, AI tools + for what, credits, setup, live link, video
- [ ] Live demo runs the real project; backup video only for network failure
- [ ] Final commit pushed before deadline; submitted ≥10 min early

---

## 12. Disclosure list (write exactly what is true)

- **OpenCode** (AI coding agent, model Big Pickle) — wrote/debugged code, docs, this plan.
- **Google Gemini** (Google AI Studio, model in `RX_VLM_MODEL`) — in-app AI reader.
- Add one line each if you also used Claude / ChatGPT / Copilot / other assistant, with the actual task.
- Datasets, model weights, libraries and assets credited in `RESOURCES.md` / README.

---

## 13. First actions after switching to Build mode

1. Create `D:\OpenCode\cu` if missing.
2. Copy this plan (`.md`, `.docx`, `.pdf`) + `rulebook.pdf` + both `.docx` files + `RxBondhu_code.zip` from Downloads into `D:\OpenCode\cu`.
3. Start **Step 1** — repo structure + today's first commit.
4. Set the working directory to `D:\OpenCode\cu` for the rest of the build.

> Reminder: Plan mode cannot write to `D:\OpenCode\cu`. That is why the files are generated here first and copied there immediately after you switch.

# Submission text (draft — review before pasting)

**Title (≤100 chars):**

> RxBondhu — Two-AI Handwritten Prescription Reader with Bangla Safety Schedule

**Short description (≤150 words):**

> RxBondhu turns a photo of a handwritten Bangladeshi prescription into a clear Bangla morning/noon/night schedule with audio. It combines two independent readers — an EfficientNet-B0 handwriting CNN trained by me on 4,680 public word images (held-out test 95.90%, 748/780) and live Google Gemini — then merges them with an explainable GREEN / YELLOW / RED rule. A verified brand–generic lexicon blocks invented names and flags duplicate generics. Users must confirm every line before any schedule appears. Built solo in Python and Streamlit with a public repo, 53 automated tests, a free live demo and honest evaluation logs. Reading aid only; not medical advice.

**Word count of description:** 116 (limit 150).

**Live link:** https://rxbondhu.streamlit.app
**Repo:** https://github.com/SJesan/RxBondhu

**Demo plan (confirmed 22 Nov):** local `streamlit run app.py` as primary, ≤3-min unlisted backup video, plus the live link above if the venue network allows.

**Event facts (official site `coutechnova.xyz` + rule book, checked 22 Nov 2026):**
- 24 November 2026 · Faculty of Engineering, Comilla University, Cumilla · five-hour on-site final
- Bring laptop, charger and student ID for check-in; no extra time for late arrival
- Strict submission deadline — submit at least 10 minutes early
- Exact reporting/check-in time is **still "Time to be announced"** on `coutechnova.xyz/schedule`; check the confirmation email or call the helpline before leaving
- Helpline: coutechnova2026@gmail.com (numbers on the official site)

**Before submitting, confirm:**
- [x] Certificate name: `M. M. Sadikul Islam` (confirmed 22 Nov)
- [x] Venue and date from official website + rule book (see above)
- [ ] Exact reporting/check-in time from organiser email or helpline
- [x] Real-handwriting table filled from 10 samples / 48 lines (no invented numbers) — see [`docs/EVALUATION.md`](EVALUATION.md) and [`docs/HANDWRITTEN_TEST_GUIDE.md`](HANDWRITTEN_TEST_GUIDE.md)
- [x] GitHub Actions badge green on README (run #16, commit `f394a3a`)
- [ ] Backup video recorded (≤3 min, unlisted)
- [ ] Submit at least 10 minutes early

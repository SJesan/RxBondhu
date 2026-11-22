# Submission text (draft — review before pasting)

**Title (≤100 chars):**

> RxBondhu — Two-AI Handwritten Prescription Reader with Bangla Safety Schedule

**Short description (≤150 words):**

> RxBondhu turns a handwritten Bangladeshi prescription photo into a clear Bangla morning/noon/night schedule with audio. Two independent Gemini models read the photo, while my own EfficientNet-B0 handwriting CNN (trained on 4,680 public word images; held-out test 95.90%, 748/780) acts as a safety veto. Explainable GREEN / YELLOW / UNVERIFIED / RED badges, a verified brand–generic lexicon and duplicate-generic warnings keep the user in control: every line must be confirmed before a schedule appears. Built solo in Python and Streamlit with a public repo, 68 automated tests, a free live demo and honest evaluation logs. Calendar links, .ics and prepared WhatsApp text are included. Reading aid only; not medical advice.

**Word count of description:** 109 (limit 150).

**Live link:** https://rxbondhu.streamlit.app
**Repo:** https://github.com/SJesan/RxBondhu

**Demo plan (confirmed 22 Nov, updated 23 Nov):** local `streamlit run app.py` as primary, ≤3-min unlisted backup video by **Rakin** (pending), plus the live link above if the venue network allows (it redirected to Streamlit sign-in for anonymous checks on 23 Nov — local demo is primary).

**Organiser update (22 Nov 6:07 PM):**
- GitHub account collection form (team leader, once): https://docs.google.com/forms/d/e/1FAIpQLSeot5-TccNHNZ-HWqXcYFNZQmAF2iNT7lumJ3JgCG510sKXLg/viewform — deadline **23 Nov 2026, 11:00 PM**. Fields: official team name, GitHub-linked email, contact phone. No project content.
- 24 Nov schedule: 8:45–9:00 check-in · 9:00 start · 12:00–2:00 judging · **repo deadline 1:00 PM** · minor pushes 1:00–2:00 PM only · 2:45 closing. Submit ≥10 min early.

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
- [x] Organiser GitHub account form submitted (confirmed 23 Nov)
- [x] Real-handwriting table filled from 10 samples / 48 lines (no invented numbers) — see [`docs/EVALUATION.md`](EVALUATION.md) and [`docs/HANDWRITTEN_TEST_GUIDE.md`](HANDWRITTEN_TEST_GUIDE.md)
- [ ] GitHub Actions badge green on README after the final v2 push (check the latest run)
- [ ] Backup video recorded by **Rakin** (≤3 min, unlisted — still pending 23 Nov)
- [ ] Rear-camera tab tested on a real phone (not yet tested; upload fallback remains)
- [ ] Fresh Gemini key in Streamlit Secrets (owner chose to keep the existing key — accepted risk)
- [ ] Submit at least 10 minutes early

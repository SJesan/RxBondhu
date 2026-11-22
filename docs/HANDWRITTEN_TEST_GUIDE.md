# Real-handwriting test guide (10–12 Rx) — completed 22 Nov 2026

Status: section 2 of `docs/EVALUATION.md` is now filled from 10 real medicine-line
crops handwritten by a doctor contacted online. This file stays as the repeatable
recipe. No invented numbers.

## 1. Safety first
- Use **fake patient names** only (e.g. "Test Case 01"). No real patient data, no real prescriptions.
- Write on plain white A4 paper with a **blue or black pen**. No printed text for the medicine lines.
- Ask **3–5 volunteers** if available (classmates/friends). Different handwriting = stronger proof. If nobody is available, you can write all 12 yourself with varied styles, but say so honestly in the notes.
- **What we actually did (22 Nov):** one doctor contacted online wrote all 10 samples. Only the medicine lines were cropped — no patient name, phone or address. Writer variety is therefore limited; say so if asked.

## 2. What to write on each sheet
Each sheet is one fake prescription with:
- Header: `Rx`, fake serial, date, fake patient name.
- **2 medicine lines** in handwriting. Use this mix (all names are in our 78-class CNN or verified lexicon):

| Sheet | Line 1 | Line 2 | Dose notation to include |
|---|---|---|---|
| 01 | Napa | Maxpro | `1+0+1` / `BD` |
| 02 | Ace | Azithral | `BD` / `1+0+1` |
| 03 | Maxpro | Cetiriz | `1+1+1` / `HS` |
| 04 | Napa | Omez | `1+0+1 7 days` / `OD` |
| 05 | Azithral | Flagyl | `BD 5 days` / `TDS` |
| 06 | Ace | Ventolin | `1+1+1` / `BD` |
| 07 | Napa | Losar | `1+0+1` / `OD 10 days` |
| 08 | Maxpro | Pantocid | `BD` / `1+0+1` |
| 09 | Cetiriz | Napa | `HS` / `1+1+1` |
| 10 | Azithral | Maxpro | `1+0+1 3 days` / `BD` |
| 11 | Omez | Ace | `OD` / `1+0+1` |
| 12 | Flagyl | Cetiriz | `TDS 5 days` / `HS` |

- Add **one deliberate trap** on sheets 07 and 12: write a made-up name like `Zzqqx` as a third line. Our lexicon must show it RED. This demonstrates the catch rate.
- Vary the writing: some lines slightly slanted, one sheet with a shadow (phone flashlight at an angle), one sheet photographed at a small tilt. That is realistic and tests preprocessing.

## 3. Photograph
- Phone camera, decent light, whole sheet visible.
- **For the evaluator images, crop to the medicine-lines block only** and save as `results/rx/rx01.jpg` … `rx12.jpg`. Include all 2–3 medicine lines with a small white margin; do not cut off letters, do not crop individual words, no filters/deskew.
  - Why: `tools/evaluate_handwritten.py` does **not** use the app's cropper — it segments every word in the file. Header text (`Rx`, serial, date, fake patient name) would be fed to the CNN as fake medicines and would break the line-by-line dose scoring.
  - If you want a realistic full-sheet original as evidence, save it separately (e.g. `results/rx_full/rx01.jpg`); do not use it in the answer key.
- In the **live app demo**, the opposite is correct: upload the full photo and drag the crop box on screen 1 — that is what the app is designed for.

## 4. Answer key
Create `results/answer_key.csv` (UTF-8) using the template:

```csv
image,true_brands,true_dose
rx01.jpg,Napa|Maxpro,1+0+1|BD
rx02.jpg,Ace|Azithral,BD|1+0+1
...
rx07.jpg,Napa|Losar|Zzqqx,1+0+1|OD 10 days|
```

Rules:
- `true_brands` and `true_dose` are pipe-separated and **aligned by line**.
- For the fake `Zzqqx` trap, leave its dose blank (trailing `|` is fine).
- If a line in the photo is genuinely unreadable to you too, omit it from the key and note it in `notes`.

## 5. Run the evaluator
```bash
.\venv\Scripts\python.exe tools\evaluate_handwritten.py --answers results\answer_key.csv --images results\rx
```
It writes:
- `results/handwritten_test_log.csv` — per-sample predictions and badges
- `results/handwritten_evaluation_summary.json` — name accuracy (CNN/Gemini/Combined), dose accuracy, unsafe-GREEN rate, catch rate, over-flag rate

If you want to measure preprocessing:
```bash
.\venv\Scripts\python.exe tools\evaluate_handwritten.py --answers results\answer_key.csv --images results\rx --preprocess --out results\handwritten_preprocessed.csv
```
Compare the two JSON summaries and fill the ablation table in `docs/EVALUATION.md` section 5.

## 6. Report honestly
Copy the real numbers into `docs/EVALUATION.md` section 2. Never claim the 0.9590 CNN dataset score applies to these photos — it does not. The domain-gap note is already written there.

Commit and push normally when done.

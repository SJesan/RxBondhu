# Evaluation proof — real results

Numbers below come from **our own** Kaggle training run and `models/labels.json`.
Nothing is copied from another person's checkpoint or report. The real-handwriting
test in §2 was written by a doctor contacted online on 22 Nov 2026; only the
medicine-line crops were kept, so no patient identifier appears in any evaluated
image.

## 1. Our CNN (trained by us)

| Item | Value |
|---|---|
| Dataset | Doctor's Handwritten Prescription BD (Kaggle, `mamun1113`) |
| Samples | 4,680 word images · 78 brands |
| Split | 3,120 train / 780 val / 780 test (our own stratified split, seed 42) |
| Base model | EfficientNet-B0, ImageNet pretrained (torchvision) |
| Input | 128×384 letterbox — identical transform in training and inference |
| Epochs / batch / LR | 12 / 32 / 3e-4 (AdamW, cosine schedule) |
| Device | Kaggle GPU T4 (`torch 2.11.0+cu130`) |
| **Validation accuracy** | **0.9577** |
| **Test accuracy** | **0.9590 (748/780)** |
| Artifacts | `models/rx_cnn.pt`, `models/labels.json`, `models/test_report.csv`, `models/training_summary.txt` |
| Full training log | `results/kaggle_training_log.txt` |

The CSVs used were `training_labels.csv`, `validation_labels.csv` and
`testing_labels.csv`, joined by the `MEDICINE_NAME` column; bare image filenames
were resolved against the matching `*_words` folders.

## 1b. Live integration check (21–22 Nov 2026)

`vlm.read(samples/sample_ui_smoke.png)` with `gemini-2.5-flash` returned
`Napa — 1+0+1` and `Maxpro — BD`.

After copying our checkpoint into `models/`, `tools/verify_model.py` reported:

- CNN metadata loaded: 78 classes, `img_size = [128, 384]`, `test_accuracy = 0.9590`
- 5 word crops produced by `segmentation.segment()` (CNN evidence only)
- After the 22 Nov line-level fix, fusion output is `Napa — RED (cnn 0.434)`
  and `Maxpro — RED (cnn 0.384)`: Gemini's names are shown, but the CNN's
  top class is outside the verified lexicon, so GREEN is never allowed.

The public Streamlit Cloud deployment
**https://rxbondhu.streamlit.app** was also verified on 22 Nov 2026: the sidebar
showed `CNN ready · test acc 0.959` and `Gemini key: yes`.

This proves both AI readers run live together. It is **not** an accuracy claim;
the accuracy claim is only the held-out test number in section 1.

## 1c. External localization test on 200 real prescriptions (22 Nov 2026)

Public dataset: *A Curated Bangladesh-Based Dataset of Handwritten* — 200
prescription photos with **1,086 YOLO boxes** marking medicine-line positions
(single class `medicine`). The boxes contain **positions, not medicine names**,
so this is a **localization** result, never a name-accuracy result.

`tools/evaluate_localization.py` reads the dataset ZIP directly (no network,
no training). A ground-truth box counts as found when a detected line box
overlaps it with IoU ≥ 0.3.

| Variant | Medicine-line recall | Precision | Reading |
|---|---|---|---|
| none (app default) | **0.6259** | 0.2016 | baseline |
| shadow removal | 0.6361 | 0.2015 | +0.010 recall, no precision gain |
| + CLAHE | 0.6152 | 0.1881 | worse |
| + deskew | 0.6141 | 0.1861 | worse |

Raw per-image output: `results/localization_test_log.csv` and
`results/localization_summary.json`.

**Honest reading:** about 63% of annotated medicine lines are found on unseen
real handwriting, and the detector also picks up header/test-name lines
(precision ≈ 0.20). This is why screen 1 asks the user to drag a crop box around
the medicine lines, and why preprocessing stays off by default — it did not
help on this external set. This measured domain gap is *not* a claim that the
CNN reads these whole photos at 0.9590.

## 1d. Line-level review fix (22 Nov 2026)

A full-page phone photo previously produced one review row per segmented word
(30 rows, mostly `Az`) because word crops were paired by index with Gemini's
four lines. `pipeline.analyse()` now produces **one row per medicine line**;
word crops still feed our CNN, and the highest-confidence CNN reading inside a
line is kept. In v2 that case is a 🔍 UNVERIFIED badge: the reader's name is an
editable default and is never GREEN (v1 used RED; both refused auto-approval).

Live integration check on `images.jpg` (Amdocal / Eltroxin / Paricel / Vave):
`word_count = 30`, `line_count = 4`, four correctly named rows, all RED, read by
`gemini-2.5-flash` with no API error. On `samples/sample_ui_smoke.png`:
`word_count = 10`, `line_count = 2`, `Napa — 1+0+1` and `Maxpro — BD`.
These are presentation/integration checks, **not** accuracy measurements.

## 2. Handwritten prescription test (10 samples, 22 Nov 2026) — done

Ten real-handwriting medicine-line crops were read with the **same pipeline as
the app**. They were handwritten by **a doctor contacted online** (not typed or
AI-generated), and only the medicine lines were cropped — no patient name, phone
or address is present in any evaluated image. The answer key was typed from the
paper and then corrected by hand on 22 Nov 2026 (six corrections: Renova 5→3 days,
Loetril 3→6 months, Lorno 12→21 days, Frenxit 2→1 month, Napa Rapid 3m→3 months,
Flacort 6→10 mg). The photos and verified key stay local for privacy
(`results/rx/` and `results/answer_key.csv` are gitignored); only derived metrics
are committed.

`gemini-2.5-flash` reached its free-tier limit of 20 requests/day, so the
documented fallback **`gemini-3.5-flash-lite`** served all 10 images. Every
image returned lines; no VLM errors were recorded.

```bash
.\venv\Scripts\python.exe tools\evaluate_handwritten.py --answers results\answer_key.csv --images results\rx
```

Raw log: `results/handwritten_test_log.csv` · summary:
`results/handwritten_evaluation_summary.json`.

| Reader | Correct / total | Accuracy |
|---|---|---|
| CNN only (best crop per line) | 0 / 48 | 0.0% |
| Gemini only (`3.5-flash-lite` fallback) | 24 / 48 | 50.0% |
| Combined (fusion) | 2 / 48 | 4.2% |
| Dose notation | 7 / 48 | 14.6% |

Safety metrics (the numbers judges should probe first):

| Metric | Definition | Target | Result |
|---|---|---|---|
| Unsafe-GREEN rate | wrong names shown GREEN ÷ all GREEN lines | **0** | **0 wrong GREEN; 0 GREEN lines → rate n/a** |
| Catch rate | wrong readings flagged YELLOW/RED ÷ all wrong readings | high | **1.0 (45/45)** |
| Over-flag rate | correct names shown RED ÷ all correct names | low | **1.0 (2/2)** — conservative, see below |

**Honest reading.** Gemini alone found half of the 48 brand lines. Fusion is
deliberately stricter: most of these brands were outside the then-18-brand
verified lexicon (now 25 after the 23 Nov box check), so the displayed name came
from Gemini but the badge stayed 🔴 RED.
That is why combined accuracy is low and over-flag rate is 1.0 — the system
refuses to auto-approve unverified names. Every wrong combined reading was
flagged (catch rate 1.0), and **not a single wrong name was shown GREEN**.

**Limitation:** all 10 samples were written by one person (the doctor contacted
online), so writer variety is limited — this is a same-writer safety check, not a
population-level accuracy claim.

**Domain-gap note (honest answer to the 0.9590 question).** The 0.9590 figure is
accuracy on **cropped word images from the public dataset**, not on real
prescription photos. On our phone-photo smoke test, `Napa` scored 0.411 and
`Maxpro` 0.076 CNN confidence. `Maxpro` **is** one of our 78 classes
(`models/labels.json`); the low score is a photo-vs-clean-dataset gap, not a
missing class. That is why real photos usually produce RED and require human
confirmation, and why the real-handwriting table above is reported separately.

No number in this table is invented; all values come from the linked log.

## 2b. Second-reader bake-off and v2 gates (22–23 Nov 2026)

Same 10 real images and 48 verified lines as §2. Every number below comes from
`tools/bakeoff_groq.py --reader <gemini|groq>` using the local, gitignored answer
key; the per-image logs stay local for privacy and only derived numbers are
committed. Gate (locked before running): **valid JSON ≥90%, mean <10 s/image,
name accuracy ≥30%/48 lines**.

| Reader / model | Valid JSON | Name correct | Dose correct | Mean time | Images with API error | Gate |
|---|---|---|---|---|---|---|
| Gemini `gemini-2.5-flash` | 4/10 (40%) | 6/48 (12.5%) | 0/48 | 6.8 s | 6 (429 quota) | ❌ |
| Gemini `gemini-3.5-flash-lite` (v1 fallback) | 10/10 (100%) | **23/48 (47.9%)** | 4/48 (8.3%) | 10.8 s | 0 | latency only |
| Gemini `gemini-3.1-flash-lite` | 10/10 (100%) | **24/48 (50.0%)** | 5/48 (10.4%) | 4.7 s | 0 | ✅ **shipped as reader 2** |
| Groq `qwen/qwen3.8-27b` | 10/10 (100%) | 10/48 (20.8%) | 2/48 (4.2%) | 16.4 s¹ | 0 | ❌ **not shipped** |

¹ Groq inference itself was ~1–2 s; 16.4 s includes honest 20 s backoffs for
HTTP 429 (7,000 input tokens/minute on the free tier). It still failed the
name-accuracy gate, so no Groq key is needed to run the app.

**Decision:** two independent Gemini models are the photo readers.
`gemini-3.5-flash-lite` is reader 1, `gemini-3.1-flash-lite` is reader 2, and our
EfficientNet-B0 stays as a safety veto. If reader 1 is offline, reader 2's lines
are used for the row count but are **never copied into both readers' opinions** —
a unit test proves this cannot fabricate a GREEN.

### Prompt experiment (reverted)

Adding the 18-brand list, dose-notation examples and an explicit "?" rule to the
reader prompt made names **worse**: `3.1-flash-lite` 24/48 → 18/48, and
out-of-list lines wrongly promoted to a listed brand 4/48 → 8/48 for
`3.5-flash-lite`. The gate rejected it; the plain prompt remains the default
(`RX_VLM_PROMPT_HINTS=0`). Raw logs: `results/hints_lite_log.csv`,
`results/hints_31_log.csv` (local only).

### RxFusion char-CNN (experiment, not shipped)

A small char-CNN was trained on **synthetic noisy spellings of verified brand
names only** (seed 42, 3,344 train / 836 test pairs; no image or answer-key line
used for training). Against the RapidFuzz baseline:

| Slice | RapidFuzz | char-CNN |
|---|---|---|
| Held-out synthetic pairs | 449/836 (53.7%) | **832/836 (99.5%)** |
| Read-only real-line probe (4 reader logs × 48 lines) | 11/192 (5.7%) | 11/192 (5.7%) |

The real-line probe ties because most truth brands are outside the 18-row
verified lexicon; the gate required a win on **both** slices, so it failed.
The rule-based fusion stays in the app; the checkpoint is gitignored and the
metrics are committed at `results/rx_fusion_metrics.json`. Training script:
`tools/train_rx_fusion.py`.

### Crop diagnosis (why the CNN scored 0/48 on real photos)

`tools/dump_crops.py` saved every word/line crop for the 10 local images:
**549 word crops for 48 real lines** (~11 crops per line), many only 14–20 px
fragments, repeated boxes, and at least one 498×1557 whole-column blob. The
segmentation step breaks handwriting into fragments before the CNN sees it;
this is a measured pipeline gap, not a claim that the 0.9590 word-crop number
transfers to photos. Contact sheets are in gitignored `results/crop_dump/`.

## 2c. v2 end-to-end on the same 10 images (23 Nov 2026)

Full pipeline (`tools/evaluate_handwritten.py`), two Gemini readers + CNN veto +
lexicon + fusion, no human correction applied. Logs:
`results/handwritten_v2_test_log.csv` and `results/handwritten_v2_summary.json`.

| Metric | v1 (one reader) | v2 (two readers) |
|---|---|---|
| CNN name accuracy (real photo) | 0/48 | 0/47 |
| Reader 1 (`3.5-flash-lite`) | 24/48 (50.0%) | **30/47 (63.8%)** |
| Reader 2 (`3.1-flash-lite`) | — | 21/47 (44.7%) |
| Combined name shown | 2/48 (4.2%) | 26/47 (55.3%) |
| Default-correct rate (shown lines) | — | 27/48 (56.3%) |
| Dose accuracy | 7/48 (14.6%) | 8/48 (16.7%) |
| Unverified lines | — | 36/48 |
| Unsafe GREEN | 0 | **0 of 4 GREEN lines** |
| Catch rate (wrong lines not GREEN) | 1.0 | 1.0 |
| Over-flag rate (correct lines shown RED) | 1.0 | 0.0385 (1 line) |

**Lexicon provenance (23 Nov 2026):** ten rows were checked against medicine
boxes / a pharmacist and added to `data/manual_brands.csv` with `checked_by` and
`source`; the verified lexicon now has 25 unique brands (3 of the 10 rows
overlapped the seed list). That check also corrected
`Maxpro` from the old `Meloxicam` label to **Esomeprazole**. These are brand →
generic identity facts, not dose advice.

**Badge fix (23 Nov):** off-lexicon names that a reader could see (`Amsocal plus`,
`Eltroxin`, `Panicel`, `Vare`) were incorrectly showing RED because the low-CNN
branch ran before readable names were considered. They now show editable
UNVERIFIED; RED is reserved for no readable name, direct reader disagreement,
or an explicit user flag. Gemini output varies slightly between runs, so the
numbers above are the committed log from this run, not a promise of identical
per-model scores next time.

The totals are 47 rather than 48 because the answer key's `Syp. Napa` and
`Supp. Napa` normalise to the same brand and are counted once as a set; 48 review
lines were still shown. The first v2 run appeared to show 4 unsafe GREEN lines;
that was a **scorer bug**, not a fusion bug — `norm()` did not strip `Syp.`,
`Supp.` or strength text, so the correct `Napa` default did not compare equal to
`Syp. Napa (120mg/5ml)`. After fixing `norm()` (and preserving Bangla vowel
marks in `clean_display_name()`) the unsafe-GREEN count is 0. The safety
invariant itself is unchanged: GREEN only when both readers map to the same
verified brand.

## 2d. Controlled DGDA import comparison (23 Nov 2026)

The 10 images / 47 unique brands in the verified answer key were re-scored with
**identical real Gemini responses** (cached by image bytes + model in the
gitignored `results/vlm_cache.jsonl`). Only the lexicon / threshold changed, so
this is a controlled before/after, not a comparison between two different API runs.

| Configuration | Unsafe-GREEN | GREEN lines | Combined name accuracy | Catch rate |
|---|---|---|---|---|
| **Before import** — 25-brand box list, legacy 70 score | **1/7 = 0.1429** | 7 | 26/47 (0.5532) | 0.9524 |
| **After import** — DGDA snapshot, candidate 90, GREEN ≥95 | **0/12 = 0.0000** | 12 | 24/47 (0.5106) | **1.0** |

**Gate result:** unsafe-GREEN **fell** from 0.1429 to 0, so the kill switch was
**not** triggered. Combined accuracy dropped by 2/47 because fuzzy matches no
longer silently become an approved brand — the intended trade-off. Every wrong
name was still caught (1.0); over-flag rose to 0.4167, which is conservative and
safe.

Logs: `results/handwritten_before_dgda_log.csv` /
`results/handwritten_before_dgda_summary.json` and
`results/handwritten_v2_test_log.csv` / `results/handwritten_v2_summary.json`.

### Threshold selection — no test-set tuning

The 5/5 split was fixed by answer-key row order before looking at scores.
`GREEN_SCORE = 95` is a safety policy, not tuned. Only the candidate threshold
was chosen on the dev split:

| Split | Candidate score | Combined accuracy | Unsafe-GREEN | Decision |
|---|---|---|---|---|
| Dev rows 1–5 | 85 | 13/25 (0.52) | 0 | |
| Dev rows 1–5 | **90** | **15/25 (0.60)** | 0 | **selected** |
| Holdout rows 6–10 (reported once) | 90 | 13/22 (0.5909) | 0 | final |

Logs: `results/threshold85_dev_summary.json`, `results/threshold90_dev_summary.json`,
`results/threshold90_holdout_summary.json`.

### DGDA source and provenance

- Portal verified as **Directorate General of Drug Administration** (`<title>`
  and `Medicine Information` menu), design/development by Doel e-Services.
- Export endpoint: `http://180.211.137.202:9310/Allopathic/Medicine_Information_Ajax.php?action=export`
- Downloaded once on 23 Nov 2026: 41,655 rows, 4,364,654 bytes,
  sha256 `7569a475c565c9b18bc1dba8a4725ea418d74ad0049258b3f122149473d317fc`.
- Filtering: 856 bulk/API/empty rows dropped; 888 brand keys with conflicting
  generic identities quarantined; 23,801 DGDA keys + 3 box-only brands =
  **23,804 verified entries**.
- Source metadata: `data/dgda_source.json`; conflicts: `data/dgda_conflicts.csv`.
- Spot-check conflicts flagged for the owner, **no silent override**:
  `Napa` / `Ace` — DGDA also has `Caffeine + Paracetamol` rows while the box
  check says `Paracetamol`; `Fexo` — DGDA says `Fexofenadine Hydrochloride`,
  box note says `Fexofenadine`. The manual box row wins in the shipped lexicon
  and every case remains in the conflict log.
- **Claim limit:** “DGDA-registered (DAR No …)” in an Allopathic export as of
  the access date. Not “all approved medicines in Bangladesh”, not dose advice,
  and **a missing name is UNVERIFIED, not “not approved”**. Kaggle/MedEx was
  evaluated and superseded; the CNN training data is a separate dataset.

Note: the CNN's 0/47 on these real photos is genuine — its 78 classes are the
Kaggle word-crop brands and none of the answer-key brands fall in that set. It
is used as a veto/proof, not as the general reader.

## 3. Safety checks demonstrated

| Check | How shown in demo |
|---|---|
| Duplicate generic | Napa + Ace → warning (both Paracetamol) |
| Unknown/invented name | `Zzqqx` rejected by lexicon (unit test) |
| Unknown brand a reader saw | Amsocal plus / Eltroxin / Amdocal plus → editable name, badge UNVERIFIED (never GREEN) |
| Close spelling disagreement | Panicel vs Paricel → RED, user confirms |
| DGDA identity card | Screen 2 shows DAR No / form / company; no price, indication or dose advice |
| Duplicate generic in combinations | `Amlodipine + Atenolol` vs `Atenolol + Amlodipine` → one warning (unit test) |
| Low confidence | RED badge + "confirm with pharmacist" |
| Line-level reading | One review row per medicine line, not per word fragment |
| Human-in-the-loop | No schedule until Review button is pressed |

## 4. Reproduce locally

```bash
.\venv\Scripts\python.exe -m unittest discover -s tests -q   # 84 tests, no network
.\venv\Scripts\python.exe tools\verify_model.py
.\venv\Scripts\python.exe tools\evaluate_localization.py --zip "<dataset.zip>"
```

The full v2 real-photo run itself needs a `GEMINI_API_KEY` and the local answer
key: `.\venv\Scripts\python.exe tools\evaluate_handwritten.py --answers results/answer_key.csv --images results/rx --out results/handwritten_v2_test_log.csv --summary results/handwritten_v2_summary.json`.

## 5. Optional preprocessing ablation — pending

`rxbondhu/preprocess.py` provides switchable shadow removal → CLAHE → deskew →
auto-crop. It is **off by default** until measured on real handwriting. The
external 200-image localization ablation is already reported in section 1c.
The name/dose ablation below uses the 10 verified handwritten samples; only
the default variant was measured so far (no extra Gemini quota was spent on
preprocessed variants). Run `tools/evaluate_handwritten.py --preprocess` to add
the other rows later — fill them only from real output:

| Variant | CNN name acc. | Combined acc. | Unsafe-GREEN | Notes |
|---|---|---|---|---|
| none (default) | 0.0% | 51.1% | 0 | measured 23 Nov 2026, 10 samples, two readers + DGDA snapshot, GREEN ≥95 (see §2d for the controlled baseline) |
| shadow + CLAHE | _fill_ | _fill_ | _fill_ | |
| + deskew + auto-crop (all) | _fill_ | _fill_ | _fill_ | |

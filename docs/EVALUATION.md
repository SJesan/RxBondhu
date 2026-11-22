# Evaluation proof — real results

Numbers below come from **our own** Kaggle training run and `models/labels.json`.
Nothing is copied from another person's checkpoint or report. The volunteer
handwritten-test table at the end is still pending and must stay blank until the
real test is done.

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
line is kept. When that CNN class is outside the verified lexicon, the name
shown comes from Gemini while the badge stays 🔴 RED — never GREEN.

Live integration check on `images.jpg` (Amdocal / Eltroxin / Paricel / Vave):
`word_count = 30`, `line_count = 4`, four correctly named rows, all RED, read by
`gemini-2.5-flash` with no API error. On `samples/sample_ui_smoke.png`:
`word_count = 10`, `line_count = 2`, `Napa — 1+0+1` and `Maxpro — BD`.
These are presentation/integration checks, **not** accuracy measurements.

## 2. Handwritten prescription test (10–12 samples) — pending

Every row must be a fresh prescription handwritten by a volunteer, with an
answer key. The runner `tools/evaluate_handwritten.py` calls the **same pipeline
as the app** and writes `results/handwritten_test_log.csv`. Template answer key:
`results/answer_key_template.csv`.

```bash
.\venv\Scripts\python.exe tools\evaluate_handwritten.py --answers results\answer_key.csv --images results\rx
```

| Reader | Correct / total | Accuracy |
|---|---|---|
| CNN only | _fill after real test_ | _fill_ |
| Gemini only | _fill after real test_ | _fill_ |
| Combined (fusion) | _fill after real test_ | _fill_ |
| Dose notation | _fill after real test_ | _fill_ |

Safety metrics (the numbers judges should probe first):

| Metric | Definition | Target | Result |
|---|---|---|---|
| Unsafe-GREEN rate | wrong names shown GREEN ÷ all GREEN lines | **0** | _fill_ |
| Catch rate | wrong readings flagged YELLOW/RED ÷ all wrong readings | high | _fill_ |
| Over-flag rate | correct names shown RED ÷ all correct names | low | _fill_ |

**Domain-gap note (honest answer to the 0.9590 question).** The 0.9590 figure is
accuracy on **cropped word images from the public dataset**, not on real
prescription photos. On our phone-photo smoke test, `Napa` scored 0.411 and
`Maxpro` 0.076 CNN confidence. `Maxpro` **is** one of our 78 classes
(`models/labels.json`); the low score is a photo-vs-clean-dataset gap, not a
missing class. That is why fusion shows YELLOW and requires confirmation, and
why the real-handwriting table above is reported separately.

Results must stay blank until the real test is run. No number is invented.

## 3. Safety checks demonstrated

| Check | How shown in demo |
|---|---|
| Duplicate generic | Napa + Ace → warning (both Paracetamol) |
| Unknown/invented name | `Zzqqx` rejected by lexicon (unit test) |
| Low confidence | RED badge + "confirm with pharmacist" |
| Human-in-the-loop | No schedule until Review button is pressed |

## 4. Reproduce locally

```bash
.\venv\Scripts\python.exe tests\test_core.py
.\venv\Scripts\python.exe tests\test_pipeline.py
.\venv\Scripts\python.exe tests\test_segmentation.py
.\venv\Scripts\python.exe tests\test_evaluation.py
.\venv\Scripts\python.exe tests\test_reminders.py
.\venv\Scripts\python.exe tests\test_preprocess.py
tests\test_localization.py
.\venv\Scripts\python.exe tools\verify_model.py
.\venv\Scripts\python.exe tools\evaluate_localization.py --zip "<dataset.zip>"
```

## 5. Optional preprocessing ablation — pending

`rxbondhu/preprocess.py` provides switchable shadow removal → CLAHE → deskew →
auto-crop. It is **off by default** until measured on real handwriting. The
external 200-image localization ablation is already reported in section 1c;
the name/dose ablation below still needs the 12 handwritten samples. Run
`tools/evaluate_handwritten.py --preprocess` and fill this table only from real
output:

| Variant | CNN name acc. | Combined acc. | Unsafe-GREEN | Notes |
|---|---|---|---|---|
| none (default) | _fill_ | _fill_ | _fill_ | baseline |
| shadow + CLAHE | _fill_ | _fill_ | _fill_ | |
| + deskew + auto-crop (all) | _fill_ | _fill_ | _fill_ | |

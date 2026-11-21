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
- 5 word crops produced by `segmentation.segment()`
- Fusion output: `Napa — YELLOW (cnn 0.411)`, `Maxpro — YELLOW (cnn 0.076)`,
  extra crops `RED` because CNN/Gemini disagreed

This proves both AI readers run live together. It is **not** an accuracy claim;
the accuracy claim is only the held-out test number in section 1.

## 2. Handwritten prescription test (10–12 samples) — pending

Every row must be a fresh prescription handwritten by a volunteer, with an
answer key. Log results in `results/handwritten_test_log.csv` with columns:
`sample_id, true_medicine, cnn_pred, gemini_pred, combined_pred, cnn_correct, gemini_correct, combined_correct, colour`.

| Reader | Correct / total | Accuracy |
|---|---|---|
| CNN only | _fill after real test_ | _fill_ |
| Gemini only | _fill after real test_ | _fill_ |
| Combined (fusion) | _fill after real test_ | _fill_ |

The combined system counts a line as correct only when the confirmed name
matches the answer key; GREEN lines are accepted, YELLOW/RED lines are counted
after user confirmation.

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
.\venv\Scripts\python.exe tools\verify_model.py
```

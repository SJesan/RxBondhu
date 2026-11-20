# Evaluation proof — fill with REAL results

Do not invent numbers. Put the actual content of `models/labels.json` and
`results/handwritten_test_log.csv` here before submission.

## 1. Our CNN (trained by us)

| Item | Value |
|---|---|
| Dataset | Doctor's Handwritten Prescription BD (Kaggle, mamun1113) |
| Samples | 4,680 word images · 78 brands · 15 generics |
| Split | 3,120 train / 780 val / 780 test (adjust to actual script output) |
| Base model | EfficientNet-B0, ImageNet pretrained |
| Epochs / batch / LR | 12 / 32 / 3e-4 |
| **Validation accuracy** | _from labels.json_ |
| **Test accuracy** | _from labels.json_ |
| Artifacts | `models/rx_cnn.pt`, `models/labels.json`, `models/test_report.csv`, `models/training_summary.txt` |

Screenshot of the Kaggle training output: `results/kaggle_training.png` (add file).

## 1b. Live Gemini check (21 Nov 2026)
`vlm.read(samples/sample_ui_smoke.png)` with `gemini-2.5-flash` returned
`Napa — 1+0+1` and `Maxpro — BD`. The Streamlit screen showed both as YELLOW
because the CNN checkpoint was not present yet. Keep this as a real integration
check, not as an accuracy claim.

## 2. Handwritten prescription test (10–12 samples)

Every row is a fresh prescription handwritten by a volunteer, with an answer
key. Log results in `results/handwritten_test_log.csv` with columns:
`sample_id, true_medicine, cnn_pred, gemini_pred, combined_pred, cnn_correct, gemini_correct, combined_correct, colour`.

| Reader | Correct / total | Accuracy |
|---|---|---|
| CNN only | _fill_ | _fill_ |
| Gemini only | _fill_ | _fill_ |
| Combined (fusion) | _fill_ | _fill_ |

Fill after the real test. The combined system counts a line as correct only
when the confirmed name matches the answer key; GREEN lines are accepted,
YELLOW/RED lines are counted after user confirmation.

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
```

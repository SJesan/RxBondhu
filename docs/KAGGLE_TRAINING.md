# Train the CNN on Kaggle (free T4 GPU)

This is the only step that needs a GPU. Do it after the GitHub repo is public.

## Before you start
- Verify your Kaggle account with your phone (Kaggle asks for this on new accounts).
- Create a Kaggle API token if you want to download the dataset locally: Account → Create New API Token → put `kaggle.json` in `C:\Users\<you>\.kaggle\`.
- In Kaggle: **New Notebook** → Settings → **Accelerator: GPU T4** → **Internet: On**.

## Steps in the notebook

Cell 1 — get our fresh code:

```python
!git clone https://github.com/SJesan/RxBondhu.git /kaggle/working/RxBondhu
```

Cell 2 — add the dataset:
- Click **Add Data** → search `Doctor's Handwritten Prescription BD` (user `mamun1113`) → Add.
- Note the input path shown, e.g. `/kaggle/input/doctors-handwritten-prescription-bd`.

Cell 3 — inspect what the script can see:

```python
!python /kaggle/working/RxBondhu/training/train_cnn_kaggle.py --input /kaggle/input --list-only
```

If it prints `Samples: 4680` and `Classes: 78` (or similar), continue. If not, copy the exact input path from the Add Data panel and pass it with `--input`. The script also prints which CSV/folder layout it detected.

Cell 4 — train:

```python
!python /kaggle/working/RxBondhu/training/train_cnn_kaggle.py --input /kaggle/input --output /kaggle/working --epochs 12 --batch-size 32
```

Kaggle T4 should finish this quickly. The last lines print `TEST ACCURACY: 0.xxxx`.

Cell 5 — download these files from the notebook's Output panel:
- `rx_cnn.pt`
- `labels.json`
- `test_report.csv`
- `training_summary.txt`

Put all four in this repo's `models/` folder on your computer. Then update `docs/EVALUATION.md` with the real numbers and commit (model `.pt` is allowed; it is our trained artifact).

## If the dataset layout is unexpected

The script tries CSV annotations first, then a folder-per-class tree. `--list-only` tells you which one it used. If it finds fewer than 20 samples, open the dataset page and note the actual CSV column names, then tell the coding assistant — the `--input` path and column handling can be adjusted without changing the model design.

## Honesty note

If ImageNet weights cannot download, the script still trains a real CNN from random initialisation and says so in the log. Report the actual accuracy either way — never type a number you did not measure.

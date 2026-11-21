# ML Pipeline (generic, data-agnostic)

A reusable training pipeline that works on **any** dataset laid out as:

```
<data_root>/
  <label_1>/*.csv
  <label_2>/*.csv
  ...
```

Each **sub-folder name is a class label**; every `.csv` inside is one recording
belonging to that label. The pipeline auto-discovers labels, counts samples,
selects numeric features automatically, chops recordings into sliding windows,
trains a classifier, and saves the model. Nothing is hardcoded to air quality.

## Install

```powershell
pip install -r ml/requirements.txt
```

## Quick start (with synthetic data)

```powershell
# 1. Generate dummy data (folder-per-label CSVs) to verify the pipeline
python -m ml.src.make_dummy_data --out data/dummy --labels good moderate poor

# 2. Run the full pipeline end-to-end
python ml/run_pipeline.py --data-root data/dummy
```

## Run on your real data

Your recordings live in `data/raw/<label>/` (`good`, `moderate`, `poor`):

```powershell
python ml/run_pipeline.py --data-root data/raw
```

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--data-root` | `data/raw` | Folder containing `<label>/` sub-folders |
| `--output-dir` | `ml/artifacts` | Where model + metadata are saved |
| `--window-size` | `50` | Rows per window (use `0` = whole file as one sample) |
| `--stride` | `50` | Step between windows (smaller = more overlapping samples) |
| `--model` | `random_forest` | `random_forest` \| `logistic_regression` \| `svm` |
| `--test-size` | `0.25` | Fraction held out for evaluation |

## How it works

1. **Discover** (`src/dataset.py`) — scans `data_root`, one label per sub-folder,
   counts files + rows per label, reads headers without loading everything.
2. **Preprocess** (`src/preprocess.py`) —
   - Replaces sentinel values (`-999`, `-1`) with NaN, imputes per-recording median.
   - Selects features = **all numeric columns minus `drop_columns`** (e.g. timestamp).
   - Slices each recording into sliding windows (approach B) so windows never span
     two files; flattens each `window_size × n_features` window into one vector.
3. **Train** (`src/train.py`) — train/test split, `StandardScaler` + estimator,
   saves `model.joblib` plus metadata (feature order, class names, window params).
4. **Evaluate** — prints accuracy, classification report, and confusion matrix.

## Genericity check

Run on labels that are *not* air-quality to confirm the code is data-agnostic:

```powershell
python -m ml.src.make_dummy_data --out data/dummy_x --labels apple orange banana
python ml/run_pipeline.py --data-root data/dummy_x
```

It discovers `apple/orange/banana`, windows, trains, and evaluates with no code
changes. (The toy generator gives these labels no distinct signal, so accuracy
≈ chance — which is exactly the honest result.)

## Config

Default settings live in `src/config.py` (`PipelineConfig`). Command-line flags
override them. For programmatic use:

```python
from ml.src.config import PipelineConfig
cfg = PipelineConfig(data_root="data/raw", window_size=50, model_type="svm")
cfg.resolve()
```

## Notes

- `window_size: null` (or `--window-size 0`) = whole-recording classification.
- Models/artifacts are git-ignored (`ml/artifacts/`); regenerate anytime.
- The saved metadata keeps feature order + window size for consistent inference.

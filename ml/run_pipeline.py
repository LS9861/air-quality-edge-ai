"""End-to-end generic ML pipeline.

Steps:
  1. Discover data (each sub-folder of data_root = a label)
  2. Print a summary table (files + rows per label)
  3. Preprocess (clean -> auto numeric features -> sliding windows)
  4. Train + evaluate
  5. Save model + print report

Works on ANY dataset laid out as  <data_root>/<label>/*.csv.

Usage:
    python ml/run_pipeline.py --data-root data/dummy
    python ml/run_pipeline.py --data-root data/raw --window-size 50 --stride 25
    python ml/run_pipeline.py --data-root data/dummy --model logistic_regression
"""
from __future__ import annotations

import argparse
import sys
import os

# Allow running as a script: make repo root importable and use package imports.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from ml.src.config import PipelineConfig
from ml.src.dataset import discover, load_all
from ml.src.preprocess import select_feature_columns, clean, build_windows
from ml.src.train import train


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generic ML pipeline (data-agnostic).")
    p.add_argument("--data-root", default=None, help="Folder: <root>/<label>/*.csv")
    p.add_argument("--output-dir", default=None, help="Where to write model artifacts")
    p.add_argument("--window-size", type=int, default=None, help="Rows per window (0 = whole file)")
    p.add_argument("--stride", type=int, default=None, help="Window step")
    p.add_argument("--model", default=None, help="random_forest | logistic_regression | svm")
    p.add_argument("--test-size", type=float, default=None, help="Fraction for test split")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg = PipelineConfig()
    if args.data_root:
        cfg.data_root = args.data_root
    if args.output_dir:
        cfg.output_dir = args.output_dir
    if args.window_size is not None:
        cfg.window_size = None if args.window_size == 0 else args.window_size
    if args.stride is not None:
        cfg.window_stride = args.stride
    if args.model:
        cfg.model_type = args.model
    if args.test_size is not None:
        cfg.test_size = args.test_size
    cfg.resolve()

    print("=" * 60)
    print(" STEP 1/4  Discovering data")
    print("=" * 60)
    summary = discover(cfg.data_root)
    print(summary.to_table())
    print()

    if summary.total_files == 0:
        print("ERROR: no CSV files found. Generate dummy data first:")
        print("  python -m ml.src.make_dummy_data --out data/dummy")
        return 1

    print("=" * 60)
    print(" STEP 2/4  Preprocessing")
    print("=" * 60)
    combined, labels = load_all(cfg.data_root, cfg.label_map)
    combined = clean(combined, cfg)
    feature_cols = select_feature_columns(combined, cfg)
    print(f"Classes ({len(labels)}): {labels}")
    print(f"Feature columns ({len(feature_cols)}): {feature_cols}")
    print(f"Window size: {cfg.window_size}  stride: {cfg.window_stride}")
    print()

    X, y, class_names = build_windows(combined, feature_cols, cfg)
    print(f"Built {X.shape[0]} windows, each {X.shape[1]} features")
    per_class = {name: int((y == i).sum()) for i, name in enumerate(class_names)}
    print(f"Windows per class: {per_class}")
    print()

    print("=" * 60)
    print(" STEP 3/4  Training")
    print("=" * 60)
    result = train(X, y, class_names, feature_cols, cfg)
    print(f"Model: {cfg.model_type}  -> {result.model_path}")
    print(f"Train samples: {result.n_samples}  Features/sample: {result.n_features}")
    print()

    print("=" * 60)
    print(" STEP 4/4  Evaluation")
    print("=" * 60)
    print(f"Accuracy: {result.accuracy:.4f}")
    print()
    print("Classification report:")
    print(result.report)
    print("Confusion matrix (rows=true, cols=pred):")
    print(f"  labels: {result.class_names}")
    print(result.confusion)
    print()
    print("Pipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

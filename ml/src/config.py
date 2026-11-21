"""Global pipeline configuration.

This is deliberately a plain Python dataclass (not YAML) so the pipeline is
self-contained and easy to import/override from any project.

Point `data_root` at ANY folder laid out as:  <data_root>/<label>/*.csv
and the pipeline discovers classes, counts samples, and trains — no code change.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


# Resolved from this file: ml/src/config.py -> repo root is two levels up from ml/
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _abspath(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(_REPO_ROOT, p)


@dataclass
class PipelineConfig:
    # ---- Paths ----
    # Root folder containing one sub-folder per class label.
    data_root: str = "data/raw"
    # Where processed windows, models, and reports are written.
    output_dir: str = "ml/artifacts"

    # ---- Feature selection ----
    # Columns dropped from features (non-numeric bookkeeping).
    drop_columns: List[str] = field(default_factory=lambda: ["timestamp_ms"])
    # If non-empty, use ONLY these as features (still minusing drop_columns).
    feature_columns: List[str] = field(default_factory=list)

    # ---- Preprocessing ----
    # Values treated as "missing" (replaced by NaN, then imputed).
    na_sentinels: List[float] = field(default_factory=lambda: [-999.0, -1])
    # Per-column median imputation after sentinel removal.
    impute: bool = True
    # Drop any column that is entirely NaN after cleaning.
    drop_all_nan_columns: bool = True

    # ---- Windowing (approach B: sliding window) ----
    # Each recording is chopped into windows of `window_size` consecutive rows.
    # Set window_size=None to use each whole file as a single sample (approach A).
    window_size: Optional[int] = 50
    # Step between consecutive windows (<= window_size). window_size => no overlap.
    window_stride: int = 50

    # ---- Labeling ----
    # Label = parent folder name, optionally renamed via this map.
    label_map: dict = field(default_factory=dict)

    # ---- Train / test split ----
    test_size: float = 0.25
    random_state: int = 42

    # ---- Model ----
    # Supported types: random_forest, logistic_regression, svm
    model_type: str = "random_forest"
    # Default params per model type. `model_params` (if non-empty) overrides
    # the selected type's defaults.
    model_params: dict = field(default_factory=dict)
    default_params: dict = field(
        default_factory=lambda: {
            "random_forest": {
                "n_estimators": 200,
            "max_depth": None,
            "random_state": 42,
            },
            "logistic_regression": {"max_iter": 2000},
            "svm": {"probability": True},
        }
    )

    model_name: str = "air_quality_model"

    # ---- Derived (do not set) ----
    def resolve(self) -> "PipelineConfig":
        """Resolve relative paths against repo root and return self."""
        self.data_root = _abspath(self.data_root)
        self.output_dir = _abspath(self.output_dir)
        return self


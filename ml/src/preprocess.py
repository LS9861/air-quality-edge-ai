"""Preprocessing: cleaning, auto feature selection, and sliding-window generation.

Data-agnostic: features are chosen automatically = all numeric columns
minus `drop_columns` (and intersected with `feature_columns` if provided).
Windowing (approach B) chops each recording into fixed-size windows so the
number of training samples grows, mirroring on-device rolling-window inference.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

from .config import PipelineConfig


def select_feature_columns(df: pd.DataFrame, cfg: PipelineConfig) -> List[str]:
    """Return the feature column names: numeric, minus drops (respect allowlist)."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Optionally restrict to an explicit allowlist.
    if cfg.feature_columns:
        numeric_cols = [c for c in numeric_cols if c in cfg.feature_columns]

    drop = set(cfg.drop_columns) | {"label", "__source__"}
    features = [c for c in numeric_cols if c not in drop]
    if not features:
        raise ValueError(
            "No numeric feature columns remain after applying drop_columns/"
            "feature_columns. Check your data and config."
        )
    return features


def clean(df: pd.DataFrame, cfg: PipelineConfig) -> pd.DataFrame:
    """Replace sentinel values with NaN and optionally drop all-NaN columns."""
    df = df.copy()
    if cfg.na_sentinels:
        df[df.isin(cfg.na_sentinels)] = np.nan
    if cfg.drop_all_nan_columns:
        all_nan = [c for c in df.columns if df[c].isna().all()]
        if all_nan:
            df = df.drop(columns=all_nan)
    return df


def build_windows(
    df: pd.DataFrame,
    feature_cols: List[str],
    cfg: PipelineConfig,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Turn per-recording data into (X, y, labels).

    For each recording (grouped by label + __source__) we slide a window of
    `window_size` rows with step `window_stride`, flattening each window into a
    single feature vector: [w0_f0, w0_f1, ..., w0_fN, w1_f0, ...].

    Returns:
        X: float array (n_samples, window_size * n_features)
        y: int array (n_samples,) class indices
        class_names: list mapping class index -> label string
    """
    window_size = cfg.window_size
    stride = cfg.window_stride or window_size or 1

    class_names = sorted(df["label"].unique().tolist())
    label_to_idx = {name: i for i, name in enumerate(class_names)}

    X_list: List[np.ndarray] = []
    y_list: List[int] = []

    # Group by recording so windows never span two different files.
    for (label, _src), group in df.groupby(["label", "__source__"], sort=False):
        group = group.reset_index(drop=True)

        # Per-recording imputation (median of this recording's values).
        if cfg.impute:
            group[feature_cols] = group[feature_cols].apply(
                lambda col: col.fillna(col.median())
            )
        # Any remaining NaN (e.g. all-NaN column): fill with 0 as a safe default.
        group[feature_cols] = group[feature_cols].fillna(0)

        values = group[feature_cols].to_numpy(dtype=np.float64)
        n = len(values)

        if window_size is None:
            # Approach A: whole recording = one sample.
            X_list.append(values.reshape(-1))
            y_list.append(label_to_idx[label])
            continue

        if n < window_size:
            # Pad short recordings by repeating the last row.
            pad = window_size - n
            values = np.vstack([values, np.repeat(values[-1:], pad, axis=0)])
            n = window_size

        for start in range(0, n - window_size + 1, stride):
            window = values[start:start + window_size]
            X_list.append(window.reshape(-1))
            y_list.append(label_to_idx[label])

    if not X_list:
        raise ValueError(
            "No windows were produced. Check window_size/stride vs. data length."
        )

    return np.vstack(X_list), np.array(y_list, dtype=int), class_names

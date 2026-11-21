"""Data-agnostic dataset discovery and loading.

Convention:  <data_root>/<label>/*.csv
  - each immediate sub-folder of data_root is a class label
  - every .csv inside a label folder is one recording ("sample source")

This module knows nothing about air quality. Point it anywhere and it works.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class RecordingInfo:
    """Metadata about a single CSV file."""
    path: str
    label: str
    rows: int = 0
    columns: Optional[List[str]] = None


@dataclass
class LabelSummary:
    """Per-label aggregated statistics."""
    label: str
    files: int = 0
    rows: int = 0


@dataclass
class DatasetSummary:
    """Whole-dataset statistics produced by discovery."""
    data_root: str
    labels: List[str] = field(default_factory=list)
    per_label: Dict[str, LabelSummary] = field(default_factory=dict)
    recordings: List[RecordingInfo] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return sum(s.files for s in self.per_label.values())

    @property
    def total_rows(self) -> int:
        return sum(s.rows for s in self.per_label.values())

    def to_table(self) -> str:
        """Return a human-readable summary table."""
        lines = []
        lines.append(f"Dataset root: {self.data_root}")
        lines.append(f"Labels ({len(self.labels)}): {', '.join(self.labels) or '(none)'}")
        lines.append("")
        header = f"{'Label':<20} {'Files':>8} {'Rows':>10}"
        lines.append(header)
        lines.append("-" * len(header))
        for label in self.labels:
            s = self.per_label[label]
            lines.append(f"{label:<20} {s.files:>8} {s.rows:>10}")
        lines.append("-" * len(header))
        lines.append(f"{'TOTAL':<20} {self.total_files:>8} {self.total_rows:>10}")
        return "\n".join(lines)


def discover(data_root: str) -> DatasetSummary:
    """Scan data_root: each sub-folder = a label; each .csv = a recording.

    CSV headers are read and row counts computed without loading full data
    into memory (fast, works for many/large files).
    """
    if not os.path.isdir(data_root):
        raise FileNotFoundError(f"data_root not found: {data_root}")

    summary = DatasetSummary(data_root=data_root)

    for entry in sorted(os.listdir(data_root)):
        label_dir = os.path.join(data_root, entry)
        if not os.path.isdir(label_dir):
            continue
        # Skip hidden / placeholder-only folders.
        if entry.startswith("."):
            continue

        csv_files = sorted(
            f for f in os.listdir(label_dir) if f.lower().endswith(".csv")
        )
        if not csv_files:
            # Keep the label listed even if empty (helps spot missing data).
            summary.labels.append(entry)
            summary.per_label[entry] = LabelSummary(label=entry, files=0, rows=0)
            continue

        summary.labels.append(entry)
        label_sum = LabelSummary(label=entry)

        for fname in csv_files:
            fpath = os.path.join(label_dir, fname)
            try:
                df = pd.read_csv(fpath)
            except Exception as exc:  # noqa: BLE001 - report and continue
                print(f"[warn] could not read {fpath}: {exc}")
                continue
            info = RecordingInfo(
                path=fpath,
                label=entry,
                rows=len(df),
                columns=list(df.columns),
            )
            summary.recordings.append(info)
            label_sum.files += 1
            label_sum.rows += info.rows

        summary.per_label[entry] = label_sum

    return summary


def load_all(data_root: str, label_map: Optional[dict] = None) -> Tuple[pd.DataFrame, List[str]]:
    """Load every CSV and return (concatenated DataFrame with 'label' column, labels).

    A `label` column is added per file from its parent folder name (optionally
    renamed via label_map). Used by preprocess for all numeric-feature logic.
    """
    label_map = label_map or {}
    frames = []

    for entry in sorted(os.listdir(data_root)):
        label_dir = os.path.join(data_root, entry)
        if not os.path.isdir(label_dir) or entry.startswith("."):
            continue
        label = label_map.get(entry, entry)

        for fname in sorted(os.listdir(label_dir)):
            if not fname.lower().endswith(".csv"):
                continue
            fpath = os.path.join(label_dir, fname)
            try:
                df = pd.read_csv(fpath)
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] could not read {fpath}: {exc}")
                continue
            if df.empty:
                continue
            df = df.copy()
            df["label"] = label
            df["__source__"] = fname
            frames.append(df)

    if not frames:
        raise ValueError(f"No CSV data found under {data_root}")

    combined = pd.concat(frames, ignore_index=True)
    labels = sorted(combined["label"].unique().tolist())
    return combined, labels

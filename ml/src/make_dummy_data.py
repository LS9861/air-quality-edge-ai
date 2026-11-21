"""Generate synthetic CSV data to test the pipeline end-to-end.

Creates a folder-per-label structure with N CSV files per label, each containing
M rows of synthetic sensor-like data with class-dependent signal so a model can
actually learn something. This proves the pipeline is data-agnostic and works
before real sensor data exists.

Usage:
    python -m ml.src.make_dummy_data --out data/dummy --labels good moderate poor \
        --files-per-label 3 --rows 200
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

# Feature columns mirroring the real firmware CSV (minus timestamp/ label).
FEATURES = [
    "pm1_cf1", "pm25_cf1", "pm10_cf1",
    "pm1_atm", "pm25_atm", "pm10_atm",
    "n03", "n05", "n10", "n25", "n50", "n100",
    "mq135_raw", "temp_c", "hum_pct",
]

# Class "centers" so classes are separable but noisy. Keys = label names.
# Any label not listed gets a generic mild center.
CLASS_CENTERS = {
    "good":     dict(mq=340, n03=60, n05=50, temp=23.0, hum=55.0),
    "moderate": dict(mq=400, n03=150, n05=120, temp=24.0, hum=58.0),
    "poor":     dict(mq=470, n03=320, n05=240, temp=25.0, hum=62.0),
}


def _make_file(label: str, rows: int, rng: np.random.Generator) -> pd.DataFrame:
    center = CLASS_CENTERS.get(
        label, dict(mq=380, n03=120, n05=90, temp=24.0, hum=57.0)
    )
    mq = center["mq"] + rng.normal(0, 8, rows)
    n03 = np.clip(center["n03"] + rng.normal(0, 10, rows), 0, None)
    n05 = np.clip(center["n05"] + rng.normal(0, 8, rows), 0, None)
    n10 = np.clip(n05 + rng.normal(0, 3, rows), 0, None)
    n25 = np.clip(n10 * 0.2 + rng.normal(0, 1, rows), 0, None)
    n50 = np.clip(n25 * 0.3 + rng.normal(0, 1, rows), 0, None)
    n100 = np.clip(n50 * 0.3, 0, None)
    temp = center["temp"] + rng.normal(0, 0.5, rows)
    hum = np.clip(center["hum"] + rng.normal(0, 1.5, rows), 0, 100)

    # Mass fields: emulate the PMS clone (mostly zero) + tiny noise.
    pm25_atm = np.clip(rng.normal(0, 1, rows), 0, None).round().astype(int)
    pm10_atm = np.clip(pm25_atm + rng.normal(0, 1, rows), 0, None).round().astype(int)

    df = pd.DataFrame({
        "timestamp_ms": np.arange(rows) * 2000,
        "pm1_cf1": pm25_atm,
        "pm25_cf1": pm25_atm,
        "pm10_cf1": pm10_atm,
        "pm1_atm": pm25_atm,
        "pm25_atm": pm25_atm,
        "pm10_atm": pm10_atm,
        "n03": n03.round().astype(int),
        "n05": n05.round().astype(int),
        "n10": n10.round().astype(int),
        "n25": n25.round().astype(int),
        "n50": n50.round().astype(int),
        "n100": n100.round().astype(int),
        "mq135_raw": mq.round().astype(int),
        "temp_c": temp.round(2),
        "hum_pct": hum.round(2),
    })
    return df[FEATURES + ["timestamp_ms"]]


def generate(
    out_dir: str,
    labels: list[str],
    files_per_label: int = 3,
    rows: int = 200,
    seed: int = 0,
) -> str:
    rng = np.random.default_rng(seed)
    for label in labels:
        label_dir = os.path.join(out_dir, label)
        os.makedirs(label_dir, exist_ok=True)
        for i in range(files_per_label):
            df = _make_file(label, rows, rng)
            fname = f"{label}_{i:02d}.csv"
            df.to_csv(os.path.join(label_dir, fname), index=False)
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic test data.")
    parser.add_argument("--out", default="data/dummy")
    parser.add_argument("--labels", nargs="+", default=["good", "moderate", "poor"])
    parser.add_argument("--files-per-label", type=int, default=3)
    parser.add_argument("--rows", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    path = generate(
        args.out, args.labels, args.files_per_label, args.rows, args.seed
    )
    print(f"Dummy data written to: {path}")
    total = len(args.labels) * args.files_per_label
    print(f"  {len(args.labels)} labels x {args.files_per_label} files = {total} CSVs, {args.rows} rows each")


if __name__ == "__main__":
    main()

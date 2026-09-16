"""Clean CICIDS2017 and save as a single Parquet file.

Pipeline:
  1. Read all 8 CSVs (latin-1 encoding to fix mojibake labels).
  2. Strip whitespace from column names.
  3. Replace inf / -inf with NaN.
  4. Drop rows with NaN.
  5. Drop exact duplicate rows.
  6. Map original labels -> grouped labels.
  7. Save as Parquet.

Usage:
    python ml/training/clean_dataset.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "datasets" / "cicids2017"
OUT_FILE = Path(__file__).resolve().parent.parent / "datasets" / "cicids2017_clean.parquet"

# Mapping from original CICIDS2017 labels to grouped labels.
# Note: the original CSVs contain a non-ASCII dash in "Web Attack - X".
# After reading with latin-1 the character comes through as "\x96",
# so the keys below use that exact byte.
LABEL_MAP = {
    "BENIGN": "BENIGN",
    "DoS Hulk": "DoS",
    "DoS GoldenEye": "DoS",
    "DoS slowloris": "DoS",
    "DoS Slowhttptest": "DoS",
    "DDoS": "DDoS",
    "PortScan": "PortScan",
    "FTP-Patator": "BruteForce",
    "SSH-Patator": "BruteForce",
    "Web Attack \x96 Brute Force": "BruteForce",
    "Web Attack \x96 XSS": "WebAttack",
    "Web Attack \x96 Sql Injection": "WebAttack",
    "Bot": "Bot",
    "Infiltration": "Infiltration",
    "Heartbleed": "Heartbleed",
}


def load_one(path: Path) -> pd.DataFrame:
    """Read a single CSV with the correct encoding and cleaned columns."""
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    df.columns = df.columns.str.strip()
    return df


def main() -> None:
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        print(f"No CSVs found in {RAW_DIR}")
        return

    print(f"Found {len(csv_files)} CSV files in {RAW_DIR}\n")

    frames = []
    for path in csv_files:
        df = load_one(path)
        print(f"  {path.name:60s} {len(df):>9,} rows")
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    print(f"\nConcatenated: {len(df):,} rows")

    # Replace inf / -inf with NaN (they break scalers and stats).
    df = df.replace([np.inf, -np.inf], np.nan)

    # Drop rows with any NaN.
    before = len(df)
    df = df.dropna().reset_index(drop=True)
    print(f"Dropped {before - len(df):,} rows with NaN -> {len(df):,} rows")

    # Drop exact duplicate rows.
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Dropped {before - len(df):,} duplicate rows -> {len(df):,} rows")

    # Map labels -> grouped labels.
    df["Label"] = df["Label"].astype(str).str.strip()
    unmapped = set(df["Label"].unique()) - set(LABEL_MAP.keys())
    if unmapped:
        print(f"\nWARNING: {len(unmapped)} unmapped label(s):")
        for label in sorted(unmapped):
            print(f"  {label!r}")
        print("Rows with these labels will be dropped.")
        df = df[df["Label"].isin(LABEL_MAP.keys())].reset_index(drop=True)

    df["Label"] = df["Label"].map(LABEL_MAP)
    print(f"After label mapping: {len(df):,} rows")

    # Summary.
    print("\nFinal label distribution:")
    counts = df["Label"].value_counts()
    for label, count in counts.items():
        pct = 100 * count / len(df)
        print(f"  {label:<15s} {count:>10,}  ({pct:5.2f}%)")

    # Save.
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_FILE, index=False)
    size_mb = OUT_FILE.stat().st_size / (1024 * 1024)
    print(f"\nSaved: {OUT_FILE}  ({size_mb:.1f} MB)")
    print(f"Final shape: {df.shape[0]:,} rows x {df.shape[1]} columns")


if __name__ == "__main__":
    main()

"""Clean CICIDS2017 and save as a single Parquet file.

Pipeline:
  1. Read all 8 CSVs (latin-1 encoding).
  2. Strip whitespace from column names.
  3. Replace inf / -inf with NaN.
  4. Drop rows with NaN.
  5. Drop exact duplicate rows.
  6. Map original labels -> grouped labels via normalize_label().
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

# Canonical grouped labels, in fixed order (useful for reports and confusion matrices).
GROUP_ORDER = [
    "BENIGN",
    "DoS",
    "DDoS",
    "PortScan",
    "BruteForce",
    "WebAttack",
    "Bot",
    "Infiltration",
    "Heartbleed",
]


def normalize_label(label: str) -> str:
    """Map an original CICIDS2017 label to a grouped label.

    Uses substring matching so it is robust to encoding differences in the
    Web Attack labels (the original CSVs contain a non-ASCII dash that
    decodes differently depending on encoding).
    """
    label = label.strip()

    # Web attacks: "Web Attack <dash> XSS", "... Sql Injection", "... Brute Force".
    # Match by substring so the dash encoding doesn't matter.
    if label.startswith("Web Attack"):
        if "Brute Force" in label:
            return "BruteForce"
        if "XSS" in label or "Sql Injection" in label:
            return "WebAttack"
        return "WebAttack"  # fallback for any other Web Attack variant

    # DoS family.
    if label in {"DoS Hulk", "DoS GoldenEye", "DoS slowloris", "DoS Slowhttptest"}:
        return "DoS"

    # Brute force family.
    if label in {"FTP-Patator", "SSH-Patator"}:
        return "BruteForce"

    # Already-canonical labels.
    if label in {"BENIGN", "DDoS", "PortScan", "Bot", "Infiltration", "Heartbleed"}:
        return label

    return "UNKNOWN"


def load_one(path: Path) -> pd.DataFrame:
    """Read a single CSV with cleaned column names."""
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

    # Show original labels BEFORE mapping (so we can see what's really there).
    print("\nOriginal label counts (before grouping):")
    orig_counts = df["Label"].astype(str).str.strip().value_counts()
    for label, count in orig_counts.items():
        print(f"  {label!r:50s} {count:>10,}")

    # Map labels -> grouped labels.
    df["Label"] = df["Label"].astype(str).str.strip().map(normalize_label)

    unknown_count = int((df["Label"] == "UNKNOWN").sum())
    if unknown_count:
        print(f"\nWARNING: {unknown_count:,} rows with UNKNOWN label will be dropped.")
        df = df[df["Label"] != "UNKNOWN"].reset_index(drop=True)

    print(f"\nAfter label grouping: {len(df):,} rows")

    # Summary (ordered).
    print("\nFinal label distribution:")
    counts = df["Label"].value_counts()
    for label in GROUP_ORDER:
        if label in counts:
            count = counts[label]
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

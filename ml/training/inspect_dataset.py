"""Inspect the CICIDS2017 CSVs before any ML.

Prints, for each CSV:
  - shape (rows x columns)
  - column dtypes summary
  - missing value count
  - label distribution
Also prints the union of all columns across files to detect schema drift.

Usage:
    python ml/training/inspect_dataset.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "datasets" / "cicids2017"

CSV_FILES = sorted(DATA_DIR.glob("*.csv"))


def inspect_one(path: Path) -> dict:
    """Load one CSV and return a summary dict."""
    # low_memory=False: CICIDS files have mixed types in some columns;
    # the default chunked inference can produce wrong dtypes.
    df = pd.read_csv(path, low_memory=False)

    # Strip leading spaces from column names — the original CSVs have
    # inconsistent spacing (e.g. " Destination Port" vs "Destination Port").
    df.columns = df.columns.str.strip()

    return {
        "path": path,
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.value_counts().to_dict(),
        "missing": int(df.isna().sum().sum()),
        "labels": df["Label"].value_counts().to_dict() if "Label" in df.columns else {},
    }


def main() -> None:
    if not CSV_FILES:
        print(f"No CSVs found in {DATA_DIR}")
        return

    all_columns: set[str] = set()

    for path in CSV_FILES:
        summary = inspect_one(path)
        all_columns.update(summary["columns"])

        print(f"\n=== {path.name} ===")
        print(f"Shape:   {summary['shape'][0]:>7} rows x {summary['shape'][1]} columns")
        print(f"Missing: {summary['missing']}")
        print(f"Dtypes:  {summary['dtypes']}")
        print("Labels:")
        for label, count in sorted(summary["labels"].items(), key=lambda x: -x[1]):
            print(f"  {label:>30}  {count:>9}")

    print(f"\n=== Union of all columns: {len(all_columns)} ===")


if __name__ == "__main__":
    main()
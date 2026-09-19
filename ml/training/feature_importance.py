"""Inspect feature importances from the trained Random Forest.

Loads the saved model, extracts feature_importances_, and prints:
  - top 20 features ranked
  - cumulative importance (how many features for 90/95/99%)
  - a markdown table saved to docs/feature_importance.md

Usage:
    python ml/training/feature_importance.py
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

MODEL_FILE = Path(__file__).resolve().parent.parent / "models" / "random_forest_v1.joblib"
DOCS_FILE = Path(__file__).resolve().parent.parent.parent / "docs" / "feature_importance.md"

TOP_N = 20


def main() -> None:
    print(f"Loading model: {MODEL_FILE}")
    bundle = joblib.load(MODEL_FILE)

    model = bundle["model"]
    feature_names = bundle["feature_names"]

    importances = model.feature_importances_
    if len(importances) != len(feature_names):
        raise ValueError(
            f"Mismatch: {len(importances)} importances vs {len(feature_names)} features"
        )

    df = pd.DataFrame(
        {"feature": feature_names, "importance": importances}
    ).sort_values("importance", ascending=False, ignore_index=True)

    # --- Top N ---
    print(f"\nTop {TOP_N} features by importance:")
    print("-" * 50)
    for i, row in df.head(TOP_N).iterrows():
        print(f"  {i + 1:>2}.  {row['feature']:<40s} {row['importance']:.6f}")

    # --- Cumulative ---
    df["cumulative"] = df["importance"].cumsum()
    total = df["importance"].sum()

    print("\nCumulative importance thresholds:")
    print("-" * 50)
    for threshold in (0.90, 0.95, 0.99):
        target = total * threshold
        n_needed = int((df["cumulative"] < target).sum()) + 1
        print(f"  {int(threshold * 100)}% of importance -> {n_needed:>3} features")

    # --- Save markdown ---
    DOCS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DOCS_FILE.open("w", encoding="utf-8") as f:
        f.write("# Random Forest — Feature Importance\n\n")
        f.write(f"Model: `{MODEL_FILE.name}`\n\n")
        f.write(f"Total features: {len(df)}\n\n")
        f.write("## Top 20 features\n\n")
        f.write("| Rank | Feature | Importance | Cumulative |\n")
        f.write("|---:|---|---:|---:|\n")
        for i, row in df.head(TOP_N).iterrows():
            f.write(
                f"| {i + 1} | `{row['feature']}` | "
                f"{row['importance']:.6f} | {row['cumulative']:.6f} |\n"
            )
        f.write("\n## Cumulative thresholds\n\n")
        for threshold in (0.90, 0.95, 0.99):
            target = total * threshold
            n_needed = int((df["cumulative"] < target).sum()) + 1
            f.write(f"- **{int(threshold * 100)}%** of importance: {n_needed} features\n")

    print(f"\nSaved: {DOCS_FILE}")


if __name__ == "__main__":
    main()

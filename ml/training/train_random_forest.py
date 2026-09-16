"""Train a baseline Random Forest on cleaned CICIDS2017.

Design decisions (Phase 4, Step 1):
  - 9-class grouped labels.
  - Stratified 80/20 train/test split.
  - class_weight='balanced' to counter severe imbalance.
  - All 78 features (no feature selection yet).
  - No hyperparameter tuning yet — this is the baseline.

Usage:
    python ml/training/train_random_forest.py
"""

from __future__ import annotations

import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split

DATA_FILE = Path(__file__).resolve().parent.parent / "datasets" / "cicids2017_clean.parquet"
MODEL_FILE = Path(__file__).resolve().parent.parent / "models" / "random_forest_v1.joblib"

RANDOM_STATE = 42
TEST_SIZE = 0.20


def main() -> None:
    print(f"Loading {DATA_FILE} ...")
    t0 = time.time()
    df = pd.read_parquet(DATA_FILE)
    print(f"Loaded {len(df):,} rows x {df.shape[1]} columns in {time.time() - t0:.1f}s\n")

    # Split features and labels.
    X = df.drop(columns=["Label"])
    y = df["Label"]

    print(f"Features: {X.shape[1]} columns")
    print(f"Classes:  {sorted(y.unique())}\n")

    # Stratified split preserves class proportions in both halves.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    print(f"Train: {len(X_train):,} rows")
    print(f"Test:  {len(X_test):,} rows\n")

    # Baseline Random Forest.
    # - n_estimators=100: standard starting point.
    # - class_weight='balanced': weights each class by inverse frequency.
    # - n_jobs=-1: use all CPU cores.
    # - random_state: reproducibility.
    print("Training Random Forest ...")
    t0 = time.time()
    clf = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
        verbose=1,
    )
    clf.fit(X_train, y_train)
    print(f"Trained in {time.time() - t0:.1f}s\n")

    # Predict.
    print("Predicting on test set ...")
    y_pred = clf.predict(X_test)

    # --- Metrics ---
    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Accuracy:     {acc:.4f}")
    print(f"Macro F1:     {macro_f1:.4f}   <- primary metric")
    print(f"Weighted F1:  {weighted_f1:.4f}")

    print("\nPer-class report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Confusion matrix with label order from the data.
    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    print("Confusion matrix (rows = true, cols = predicted):")
    print(cm_df.to_string())

    # --- Save model ---
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": clf,
            "feature_names": list(X.columns),
            "classes": list(clf.classes_),
        },
        MODEL_FILE,
    )
    size_mb = MODEL_FILE.stat().st_size / (1024 * 1024)
    print(f"\nSaved model: {MODEL_FILE}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()

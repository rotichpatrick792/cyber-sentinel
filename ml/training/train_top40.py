"""Train a Random Forest on the top 40 features (by importance).

Loads the full model to get the feature ranking, then trains a new model
on the reduced feature set with identical hyperparameters. Saves as
random_forest_v2_top40.joblib. Compares metrics against the full model.

Usage:
    python ml/training/train_top40.py
"""

from __future__ import annotations

import time
from pathlib import Path

import joblib
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
FULL_MODEL_FILE = Path(__file__).resolve().parent.parent / "models" / "random_forest_v1.joblib"
REDUCED_MODEL_FILE = Path(__file__).resolve().parent.parent / "models" / "random_forest_v2_top40.joblib"

RANDOM_STATE = 42
TEST_SIZE = 0.20
TOP_N = 40


def main() -> None:
    # --- Step 1: get the top N features from the full model ---
    print(f"Loading full model: {FULL_MODEL_FILE}")
    bundle = joblib.load(FULL_MODEL_FILE)
    full_model = bundle["model"]
    feature_names = bundle["feature_names"]

    ranking = pd.DataFrame(
        {"feature": feature_names, "importance": full_model.feature_importances_}
    ).sort_values("importance", ascending=False, ignore_index=True)

    top_features = ranking.head(TOP_N)["feature"].tolist()
    print(f"Selected top {TOP_N} features (out of {len(feature_names)})\n")

    # --- Step 2: load data, keep only those columns ---
    print(f"Loading {DATA_FILE} ...")
    df = pd.read_parquet(DATA_FILE)
    print(f"Loaded {len(df):,} rows x {df.shape[1]} columns")

    X = df[top_features]
    y = df["Label"]
    print(f"Reduced feature set: {X.shape[1]} columns\n")

    # --- Step 3: same split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    print(f"Train: {len(X_train):,} rows")
    print(f"Test:  {len(X_test):,} rows\n")

    # --- Step 4: train (identical hyperparameters) ---
    print("Training Random Forest (top 40) ...")
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

    # --- Step 5: evaluate ---
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    print("\n" + "=" * 70)
    print("RESULTS — top 40 features")
    print("=" * 70)
    print(f"Accuracy:     {acc:.4f}")
    print(f"Macro F1:     {macro_f1:.4f}   <- primary metric")
    print(f"Weighted F1:  {weighted_f1:.4f}")

    print("\nPer-class report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    print("Confusion matrix (rows = true, cols = predicted):")
    print(cm_df.to_string())

    # --- Step 6: save ---
    REDUCED_MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": clf,
            "feature_names": top_features,
            "classes": list(clf.classes_),
        },
        REDUCED_MODEL_FILE,
    )
    size_mb = REDUCED_MODEL_FILE.stat().st_size / (1024 * 1024)
    print(f"\nSaved model: {REDUCED_MODEL_FILE}  ({size_mb:.1f} MB)")

    # --- Step 7: side-by-side summary ---
    full_size_mb = FULL_MODEL_FILE.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'':<20} {'Full (78)':<15} {'Top 40':<15}")
    print(f"{'Accuracy':<20} {0.9985:<15.4f} {acc:<15.4f}")
    print(f"{'Macro F1':<20} {0.9320:<15.4f} {macro_f1:<15.4f}")
    print(f"{'Weighted F1':<20} {0.9984:<15.4f} {weighted_f1:<15.4f}")
    print(f"{'Model size (MB)':<20} {full_size_mb:<15.1f} {size_mb:<15.1f}")
    print("\n(Full model numbers hardcoded from the previous run.)")


if __name__ == "__main__":
    main()

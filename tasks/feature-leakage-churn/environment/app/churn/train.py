"""Train and validate the churn model: python -m churn.train --features <file.parquet> --data <dir> [--l2 1.0]

Time-based split: train on predictions before 2025-09-01, validate on 2025-09-01 .. 2025-11-30. Every column of the
feature table other than customer_id and as_of is a model input: numeric columns as they are (a null is a missing
value), string columns one-hot encoded. A column that holds no value at all is skipped.
"""
import argparse
import os

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

KEYS = ["customer_id", "as_of"]
LABEL = "churned_30d"
TRAIN_END = pd.Timestamp("2025-09-01", tz="UTC")
VALID_END = pd.Timestamp("2025-12-01", tz="UTC")


def inputs(feats):
    return [c for c in feats.columns if c not in KEYS and c != LABEL]


def categories(feats):
    """Sorted values of each string column (one indicator column per value)."""
    return {c: sorted(feats[c].dropna().astype(str).unique()) for c in inputs(feats)
            if not pd.api.types.is_numeric_dtype(feats[c])}


def design_matrix(feats, cats):
    X = feats[[c for c in inputs(feats) if c not in cats]].astype("float64").copy()
    for c, values in cats.items():
        for v in values:
            X[f"{c}_{v}"] = (feats[c] == v).astype("float64")
    return X


def make_model(l2=1.0, max_depth=4):
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_depth=max_depth,
                                          l2_regularization=l2, early_stopping=False, random_state=0)


def train_validate(feats, labels, l2=1.0, max_depth=4):
    """Fit on labelled predictions before TRAIN_END, validate on TRAIN_END .. VALID_END."""
    df = feats.merge(labels[KEYS + [LABEL]], on=KEYS, how="inner").dropna(axis=1, how="all")  # no value: no input
    cats = categories(df)
    tr = df[df["as_of"] < TRAIN_END]
    va = df[(df["as_of"] >= TRAIN_END) & (df["as_of"] < VALID_END)]
    model = make_model(l2, max_depth).fit(design_matrix(tr, cats), tr[LABEL])
    auc = roc_auc_score(va[LABEL], model.predict_proba(design_matrix(va, cats))[:, 1])
    return model, cats, auc, tr, va


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--features", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--l2", type=float, default=1.0, help="L2 regularization")
    ap.add_argument("--max-depth", type=int, default=4)
    a = ap.parse_args()
    feats = pd.read_parquet(a.features)
    feats["as_of"] = pd.to_datetime(feats["as_of"], utc=True)
    labels = pd.read_csv(os.path.join(a.data, "labels.csv"))
    labels["as_of"] = pd.to_datetime(labels["as_of"], utc=True)
    model, cats, auc, tr, va = train_validate(feats, labels, a.l2, a.max_depth)
    print(f"train rows {len(tr)}, validation rows {len(va)}, validation churn rate {va['churned_30d'].mean():.3f}")
    print(f"offline validation AUC: {auc:.3f}")


if __name__ == "__main__":
    main()

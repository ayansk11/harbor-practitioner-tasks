"""Train and validate the churn model: python -m churn.train --features <file.parquet> --data <dir> [--l2 1.0]

Time-based split: train on predictions before 2025-09-01, validate on 2025-09-01 .. 2025-11-30.
"""
import argparse
import os

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from churn.build_features import FEATURE_COLUMNS

TRAIN_END = pd.Timestamp("2025-09-01", tz="UTC")
VALID_END = pd.Timestamp("2025-12-01", tz="UTC")
STATUSES = ["active", "paused", "payment_failed", "cancelled"]


def design_matrix(feats):
    X = feats[[c for c in FEATURE_COLUMNS if c != "status"]].astype("float64").copy()
    for s in STATUSES:
        X[f"status_{s}"] = (feats["status"] == s).astype("float64")
    return X


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
    df = feats.merge(labels[["customer_id", "as_of", "churned_30d"]], on=["customer_id", "as_of"], how="inner")
    tr, va = df[df["as_of"] < TRAIN_END], df[(df["as_of"] >= TRAIN_END) & (df["as_of"] < VALID_END)]
    model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_depth=a.max_depth,
                                           l2_regularization=a.l2, early_stopping=False, random_state=0)
    model.fit(design_matrix(tr), tr["churned_30d"])
    auc = roc_auc_score(va["churned_30d"], model.predict_proba(design_matrix(va))[:, 1])
    print(f"train rows {len(tr)}, validation rows {len(va)}, validation churn rate {va['churned_30d'].mean():.3f}")
    print(f"offline validation AUC: {auc:.3f}")


if __name__ == "__main__":
    main()

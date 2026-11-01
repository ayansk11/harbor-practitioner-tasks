"""churn-hgb-v3 as shipped (authoring only): the starting pipeline's features and its model, imported from the task's
environment/app/churn, so the AUC calibration and the scores in the live log sample use exactly the code an agent
starts from (`python -m churn.build_features`, then `python -m churn.train`).

offline(data_dir) -> the model train.py fits on v3's features of that extract (predictions before 2025-09-01), with
                     its validation AUC (2025-09-01 .. 2025-11-30), as `python -m churn.train` prints it.
score(fit, rows)  -> that model's scores for rows that carry v3's 11 feature columns (for example ref_truth's live
                     values).
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "feature-leakage-churn", "environment", "app"))
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def _churn():
    if APP not in sys.path:
        sys.path.insert(0, APP)
    from churn import build_features, train
    return build_features, train


def features(data_dir):
    """v3's feature table (as_of a UTC timestamp, as the CLI writes it)."""
    bf, _ = _churn()
    return bf.build(data_dir)


def seconds(ts):
    return ((pd.to_datetime(ts, utc=True) - EPOCH) // pd.Timedelta(seconds=1)).astype("int64")


def offline(data_dir, feats=None):
    bf, tr = _churn()
    feats = bf.build(data_dir) if feats is None else feats
    labels = pd.read_csv(os.path.join(data_dir, "labels.csv"))
    labels["as_of"] = pd.to_datetime(labels["as_of"], utc=True)
    model, cats, auc, trn, val = tr.train_validate(feats, labels)
    return {"model": model, "cats": cats, "auc": float(auc), "columns": list(feats.columns), "n_train": len(trn),
            "n_valid": len(val), "valid_churn_rate": float(val["churned_30d"].mean()),
            "train_columns": list(tr.design_matrix(trn, cats).columns)}


def score(fit, rows):
    _, tr = _churn()
    X = tr.design_matrix(rows[fit["columns"]], fit["cats"])
    assert list(X.columns) == fit["train_columns"], "design matrix columns differ from training"
    return fit["model"].predict_proba(X)[:, 1]


def auc(y, s):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(np.asarray(y), np.asarray(s)))

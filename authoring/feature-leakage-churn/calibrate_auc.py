"""AUC calibration for feature-leakage-churn (authoring only).

Offline AUC   = model trained on the original (leaky) features, validated on leaky features (what train.py prints).
Leak-free AUC = model trained and validated on reference (point-in-time) features.
Live AUC      = the leaky-trained model (trained on everything before 2025-12-01) scored on point-in-time features of
                January 2026 predictions (simulated past the extract; in production only the past exists, so live
                features equal point-in-time features; approximation noted in DESIGN.md).
Ablations: offline AUC with exactly one leak left in, and with exactly one leak fixed.
python calibrate_auc.py [seed]
"""
import os, sys, tempfile
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_data, dataset_io, ref_vectorized  # noqa: E402
sys.path.insert(0, os.path.join(gen_data.TASK, "environment", "app"))
from churn import build_features  # noqa: E402  (the original, leaky pipeline)

FEAT = build_features.FEATURE_COLUMNS
GROUPS = {"windows": ["orders_7d", "orders_30d", "spend_30d_cents", "tickets_30d"], "target_encoding": ["te_district"],
          "status": ["status"], "imputation": ["app_minutes_7d"]}
TRAIN_END = int(pd.Timestamp("2025-09-01", tz="UTC").timestamp())
VALID_END = int(pd.Timestamp("2025-12-01", tz="UTC").timestamp())
JAN, FEB = int(pd.Timestamp("2026-01-01", tz="UTC").timestamp()), int(pd.Timestamp("2026-02-01", tz="UTC").timestamp())


def X(df):
    out = df[[c for c in FEAT if c != "status"]].astype("float64").copy()
    for s in ["active", "paused", "payment_failed", "cancelled"]:
        out[f"status_{s}"] = (df["status"] == s).astype("float64")
    return out


def model():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_depth=4, l2_regularization=1.0,
                                          early_stopping=False, random_state=0)


def keyed(df):
    d = df.copy()
    if not pd.api.types.is_integer_dtype(d["as_of"]):
        d["as_of"] = dataset_io.to_seconds(d["as_of"])
    d["status"] = d["status"].astype(object).where(d["status"].notna(), None)
    return d.sort_values(["customer_id", "as_of"]).reset_index(drop=True)


def auc_split(feats, labels, train_end=TRAIN_END, valid_end=VALID_END):
    df = feats.merge(labels[["customer_id", "as_of", "churned_30d"]], on=["customer_id", "as_of"])
    tr, va = df[df.as_of < train_end], df[(df.as_of >= train_end) & (df.as_of < valid_end)]
    m = model().fit(X(tr), tr.churned_30d)
    if len(va) == 0:
        return None, m
    return roc_auc_score(va.churned_30d, m.predict_proba(X(va))[:, 1]), m


def main(seed=1):
    full = gen_data.simulate(seed)
    vis = gen_data.extract(full)
    late = gen_data.extract(full, end=gen_data.HORIZON)
    with tempfile.TemporaryDirectory() as tmp:
        dataset_io.write_dataset(vis, os.path.join(tmp, "V"))
        dataset_io.write_dataset(late, os.path.join(tmp, "L"))
        leaky = keyed(build_features.build(os.path.join(tmp, "V")))
        clean = keyed(ref_vectorized.compute(os.path.join(tmp, "V")))
        live_feats = keyed(ref_vectorized.compute(os.path.join(tmp, "L")))
    lab = vis["labels"]
    off, _ = auc_split(leaky, lab)
    free, _ = auc_split(clean, lab)
    _, deployed = auc_split(leaky, lab, train_end=VALID_END)
    lv = live_feats[(live_feats.as_of >= JAN) & (live_feats.as_of < FEB)].merge(
        late["labels"][["customer_id", "as_of", "churned_30d"]], on=["customer_id", "as_of"])
    live = roc_auc_score(lv.churned_30d, deployed.predict_proba(X(lv))[:, 1])
    print(f"seed {seed}: offline AUC (leaky) {off:.3f} | leak-free AUC {free:.3f} | live AUC (Jan 2026) {live:.3f}"
          f" | live rows {len(lv)}, live churn rate {lv.churned_30d.mean():.3f}")
    for g, cols in GROUPS.items():
        only = clean.copy(); only[cols] = leaky[cols]
        fixed = leaky.copy(); fixed[cols] = clean[cols]
        print(f"  {g:16s} only this leak: {auc_split(only, lab)[0]:.3f} | all but this leak fixed... "
              f"this one fixed, others left: {auc_split(fixed, lab)[0]:.3f}")
    diff = {c: int((~np.isclose(leaky[c].astype('float64'), clean[c].astype('float64'), equal_nan=True)).sum())
            for c in FEAT if c != "status"}
    diff["status"] = int((leaky.status.fillna("<null>") != clean.status.fillna("<null>")).sum())
    print("  rows where leaky != point-in-time:", diff, "of", len(clean))


if __name__ == "__main__":
    # python calibrate_auc.py [seed] [knob=value ...]  (knobs override gen_data.P for an experiment)
    args = sys.argv[1:]
    seed = int(args.pop(0)) if args and args[0].isdigit() else 1
    for kv in args:
        k, v = kv.split("=")
        gen_data.P[k] = type(gen_data.P[k])(float(v)) if not isinstance(gen_data.P[k], tuple) else eval(v)
    main(seed)

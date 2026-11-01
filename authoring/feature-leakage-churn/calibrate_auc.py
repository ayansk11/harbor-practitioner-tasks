"""AUC calibration for feature-leakage-churn (authoring only).

AUC_OFF  = what `python -m churn.train` prints for churn-hgb-v3 on the visible extract: train.py's model fitted on v3's
           own features (the starting pipeline in environment/app/churn) of the labelled predictions before 2025-09-01,
           validated on those of 2025-09-01 .. 2025-11-30 (labels of the extract).
AUC_LIVE = the same fitted model scored on the live service's values (ref_truth: what the warehouse held at each
           prediction) for every prediction of the first live month, January 2026, against its true 30-day outcome.
AUC_TRUE = for context only: the same model class fitted and validated like AUC_OFF, but on ref_truth's values of the
           10 kept features (what a v4 trained on a table that matches live would see offline).
TARGET (design section 9 step 6): AUC_OFF - AUC_LIVE >= 0.10, reached through the knobs downgrade_p (the downgrade
share of churners) and login_decline (how fast logins fall with disengagement), both in gen_data.P.

python calibrate_auc.py [knob=value ...] [--write]
  --write: auc_calibration.json (both AUCs to 3 decimals, the gap, the knobs, the row counts) next to this file.
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_data, extract_io, ref_truth, v3_model  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

TRAIN_END, VALID_END = gen_data.ts("2025-09-01"), gen_data.ts("2025-12-01")
KNOBS = ["downgrade_p", "login_decline", "login_rate"]


def true_auc(truth, labels):
    """AUC of train.py's model class fitted and validated on ref_truth's 10 kept features (context only)."""
    df = truth.merge(labels[["customer_id", "as_of", "churned_30d"]], on=["customer_id", "as_of"])
    X = df[[c for c in ref_truth.KEPT if c not in ("status", "plan")]].astype("float64")
    for c, vals in (("status", ["active", "cancelled", "paused", "payment_failed"]), ("plan", gen_data.PLANS)):
        for v in vals:
            X[f"{c}_{v}"] = (df[c] == v).astype("float64")
    tr, va = (df["as_of"] < TRAIN_END).to_numpy(), ((df["as_of"] >= TRAIN_END) & (df["as_of"] < VALID_END)).to_numpy()
    m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_depth=4, l2_regularization=1.0,
                                       early_stopping=False, random_state=0).fit(X[tr], df["churned_30d"][tr])
    return float(roc_auc_score(df["churned_30d"][va], m.predict_proba(X[va])[:, 1]))


def measure(p=None, world=None, ext=None):
    w = gen_data.brand_world("visible", p=p) if world is None else world
    ext = gen_data.extract_tables(w) if ext is None else ext
    with tempfile.TemporaryDirectory() as tmp:
        extract_io.write_dataset(ext, tmp)
        fit = v3_model.offline(tmp)
    sp = ext["scoring_points"]
    jan = sp[(sp["as_of"] >= gen_data.LIVE_FROM) & (sp["as_of"] < gen_data.LIVE_TO)]
    live = ref_truth.compute(w, jan)
    y = live[["customer_id", "as_of"]].merge(w["labels"][["customer_id", "as_of", "churned_30d"]],
                                             on=["customer_id", "as_of"], how="left")["churned_30d"]
    assert y.notna().all()
    s = v3_model.score(fit, live)
    truth_all = ref_truth.compute(w, sp)
    return {"AUC_OFF": round(fit["auc"], 3), "AUC_LIVE": round(v3_model.auc(y, s), 3),
            "gap": round(fit["auc"] - v3_model.auc(y, s), 3),
            "AUC_TRUE_context": round(true_auc(truth_all, ext["labels"]), 3),
            "offline_rows": {"train": fit["n_train"], "valid": fit["n_valid"],
                             "valid_churn_rate": round(fit["valid_churn_rate"], 4)},
            "live_rows": int(len(live)), "live_churn_rate": round(float(y.mean()), 4),
            "knobs": {k: (gen_data.P if p is None else p)[k] for k in KNOBS}}


def main(args):
    p = dict(gen_data.P)
    write = "--write" in args
    for kv in [a for a in args if "=" in a]:
        k, v = kv.split("=")
        assert k in p, k
        p[k] = float(v)
    res = measure(p)
    print(json.dumps(res, indent=1))
    if write:
        assert p == gen_data.P, "--write records the knobs gen_data.py uses; set them there first"
        assert res["gap"] >= 0.10, "TARGET gap >= 0.10 not met"
        with open(os.path.join(HERE, "auc_calibration.json"), "w") as f:
            json.dump(res, f, indent=1, sort_keys=True)
            f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])

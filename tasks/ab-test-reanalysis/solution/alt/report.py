"""EXP-2291 readout (alt solution): python -m abtest.report --data <folder> --out <result.json>

Per-user sums with numpy (bincount over a user index) and a user-level bootstrap interval.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .filters import exclude_bots
from .load import load_assignments, load_pageviews, load_users
from .stats import RESAMPLES, SRM_ALPHA, bootstrap_diff_ci, srm_pvalue


def build_readout(data_dir):
    assignments = exclude_bots(load_assignments(data_dir), load_users(data_dir))
    pageviews = load_pageviews(data_dir, assignments)
    index = pd.Index(assignments["user_id"])
    pos = index.get_indexer(pageviews["user_id"])
    clicks = np.bincount(pos, weights=pageviews["clicked"].to_numpy(float), minlength=len(index))
    views = np.bincount(pos, minlength=len(index)).astype(float)
    in_b = (assignments["variant"] == "B").to_numpy()
    c_a, v_a, c_b, v_b = clicks[~in_b], views[~in_b], clicks[in_b], views[in_b]
    ctr_a, ctr_b = c_a.sum() / v_a.sum(), c_b.sum() / v_b.sum()
    lo, hi = bootstrap_diff_ci(c_a, v_a, c_b, v_b)
    n_a, n_b = int((~in_b).sum()), int(in_b.sum())
    srm_p = srm_pvalue(n_a, n_b)
    srm_flag = srm_p < SRM_ALPHA
    if srm_flag:
        decision = "invalid"
    elif lo > 0:
        decision = "ship"
    else:
        decision = "no_ship"
    return {
        "n_users": {"A": n_a, "B": n_b},
        "pageviews": {"A": int(v_a.sum()), "B": int(v_b.sum())},
        "clicks": {"A": int(c_a.sum()), "B": int(c_b.sum())},
        "ctr": {"A": float(ctr_a), "B": float(ctr_b)},
        "diff": float(ctr_b - ctr_a),
        "ci_95": [lo, hi],
        "ci_method": f"user-level bootstrap, {RESAMPLES} resamples, percentile",
        "srm_p": srm_p,
        "srm_flag": bool(srm_flag),
        "decision": decision,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="EXP-2291 CTR readout")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    readout = build_readout(args.data)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(readout, indent=2) + "\n")
    print(f"wrote {args.out}: decision={readout['decision']}")


if __name__ == "__main__":
    main()

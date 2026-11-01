"""Readout (alt_recount solution): python -m abtest.report --data <folder> --out <result.json>

Standard-library readers (load.py), the exclusions recounted from the events (filters.py), per-user sums by
numpy.bincount over integer user codes, and a CR1 cluster-robust interval (stats.py).
"""
import argparse
import json
from pathlib import Path

import numpy as np

from .filters import recount_velocity
from .load import rows, seconds
from .stats import CI_METHOD, SRM_ALPHA, cr1_ci, srm_pvalue


def build_readout(data_dir):
    seen, assigned = set(), {}
    for rec in rows(data_dir, "assignments", ("user_id", "variant", "assigned_at", "method")):
        if rec in seen:                                    # an exact repeat of a row counts once
            continue
        seen.add(rec)
        user, variant, at, method = rec
        if user in assigned or variant not in ("A", "B"):
            raise ValueError(f"conflicting or unknown assignment row {rec}")
        assigned[user] = (variant, seconds(at), method)
    hashed = [u for u, (_v, _t, m) in assigned.items() if m == "hash"]
    code = {u: i for i, u in enumerate(hashed)}
    arm_b = np.array([assigned[u][0] == "B" for u in hashed])
    start = [assigned[u][1] for u in hashed]

    crawler = {u for u, rule in rows(data_dir, "bot_flags", ("user_id", "rule")) if rule == "ua_crawler"}
    item_pageviews, ev_user, ev_t = set(), [], []
    for pid, user, ts, target in rows(data_dir, "module_clicks", ("pageview_id", "user_id", "ts", "target")):
        if target.startswith("item:"):
            item_pageviews.add(pid)
            if user in code:
                ev_user.append(code[user])
                ev_t.append(seconds(ts))
    excluded = np.zeros(len(hashed), dtype=bool)
    excluded[[code[u] for u in crawler if u in code]] = True
    excluded[sorted(recount_velocity(ev_user, ev_t))] = True

    pv_user, pv_clicked, ids = [], [], set()
    for pid, user, ts in rows(data_dir, "pageviews", ("pageview_id", "user_id", "ts")):
        if pid in ids:
            raise ValueError(f"pageview_id {pid} repeated")
        ids.add(pid)
        i = code.get(user)
        if i is None or excluded[i] or seconds(ts) < start[i]:
            continue
        pv_user.append(i)
        pv_clicked.append(pid in item_pageviews)
    views = np.bincount(np.asarray(pv_user, dtype=np.int64), minlength=len(hashed))
    clicks = np.bincount(np.asarray(pv_user, dtype=np.int64), weights=np.asarray(pv_clicked, dtype=float),
                         minlength=len(hashed)).round().astype(np.int64)

    keep = ~excluded
    sel = {"A": keep & ~arm_b, "B": keep & arm_b}
    n_users = {arm: int(m.sum()) for arm, m in sel.items()}
    total_views = {arm: int(views[m].sum()) for arm, m in sel.items()}
    total_clicks = {arm: int(clicks[m].sum()) for arm, m in sel.items()}
    ctr = {arm: total_clicks[arm] / total_views[arm] for arm in ("A", "B")}
    _d, lo, hi = cr1_ci(clicks[sel["A"]], views[sel["A"]], clicks[sel["B"]], views[sel["B"]])
    srm_p = srm_pvalue(n_users["A"], n_users["B"])
    srm_flag = srm_p < SRM_ALPHA
    decision = "invalid" if srm_flag else ("ship" if lo > 0 else "no_ship")
    return {
        "n_users": n_users,
        "pageviews": total_views,
        "clicks": total_clicks,
        "ctr": ctr,
        "diff": ctr["B"] - ctr["A"],
        "ci_95": [lo, hi],
        "ci_method": CI_METHOD,
        "srm_p": srm_p,
        "srm_flag": bool(srm_flag),
        "decision": decision,
        "notes": [
            f"Population: {len(hashed)} hash-assigned users, minus {int(excluded.sum())} excluded as ua_crawler or by "
            "the velocity rule recounted on item: events; override accounts are not randomized and are left out.",
            "A counted pageview is clicked when a related product was opened from the module on it (an item: event).",
            f"Decision {decision}: SRM p = {srm_p:.3g}; 95% CI of the CTR difference [{lo:+.5f}, {hi:+.5f}].",
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="CTR readout of one experiment export")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    readout = build_readout(args.data)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(readout, indent=2) + "\n")
    print(f"wrote {args.out}: decision={readout['decision']}")


if __name__ == "__main__":
    main()

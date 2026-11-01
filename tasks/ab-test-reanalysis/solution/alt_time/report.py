"""Readout (alt_time solution): python -m abtest.report --data <folder> --out <result.json>

Population by time (filters.py), counted pageviews joined to the item: events, per-user sums by a pandas groupby,
and a user-level bootstrap interval (stats.py).
"""
import argparse
import json
from pathlib import Path

from .filters import experiment_users
from .load import read_all
from .stats import CI_METHOD, SRM_ALPHA, bootstrap_ci, srm_pvalue


def per_user(data):
    """users, with clicks and views per user over the counted pageviews (zero for users with none)."""
    users = experiment_users(data["assignments"], data["bot_flags"])
    pv = data["pageviews"][["pageview_id", "user_id", "ts"]].merge(users, on="user_id", how="inner")
    pv = pv[pv["ts"] >= pv["assigned_at"]]
    mc = data["module_clicks"]
    opened = mc.loc[mc["target"].str.startswith("item:"), ["pageview_id"]].drop_duplicates()
    opened["opened"] = 1
    pv = pv.merge(opened, on="pageview_id", how="left")              # left join: a pageview row is never dropped
    pv["opened"] = pv["opened"].fillna(0).astype("int64")
    sums = pv.groupby("user_id").agg(clicks=("opened", "sum"), views=("opened", "count")).reset_index()
    out = users.merge(sums, on="user_id", how="left")
    out[["clicks", "views"]] = out[["clicks", "views"]].fillna(0).astype("int64")
    return out


def build_readout(data_dir):
    data = read_all(data_dir)
    users = per_user(data)
    by_arm = users.groupby("variant").agg(n=("user_id", "size"), clicks=("clicks", "sum"), views=("views", "sum"))
    n_users = {arm: int(by_arm.loc[arm, "n"]) for arm in ("A", "B")}
    views = {arm: int(by_arm.loc[arm, "views"]) for arm in ("A", "B")}
    clicks = {arm: int(by_arm.loc[arm, "clicks"]) for arm in ("A", "B")}
    ctr = {arm: clicks[arm] / views[arm] for arm in ("A", "B")}
    a = users[users["variant"] == "A"]
    b = users[users["variant"] == "B"]
    lo, hi = bootstrap_ci(a["clicks"], a["views"], b["clicks"], b["views"])
    srm_p = srm_pvalue(n_users["A"], n_users["B"])
    srm_flag = srm_p < SRM_ALPHA
    decision = "invalid" if srm_flag else ("ship" if lo > 0 else "no_ship")
    return {
        "n_users": n_users,
        "pageviews": views,
        "clicks": clicks,
        "ctr": ctr,
        "diff": ctr["B"] - ctr["A"],
        "ci_95": [lo, hi],
        "ci_method": CI_METHOD,
        "srm_p": srm_p,
        "srm_flag": bool(srm_flag),
        "decision": decision,
        "notes": [
            "Population: hash-assigned users without a bot flag raised at or before the user's assignment "
            "(flags raised later read in-experiment behaviour); override accounts are not randomized and are left out.",
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

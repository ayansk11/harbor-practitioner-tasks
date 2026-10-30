"""EXP-2291 readout: python -m abtest.report --data <folder> --out <result.json>"""
import argparse
import json
from pathlib import Path

from .filters import exclude_bots
from .load import load_assignments, load_pageviews, load_users
from .stats import CI_METHOD, SRM_ALPHA, diff_ci, srm_pvalue

ARMS = ("A", "B")


def per_user_counts(assignments, pageviews):
    """One row per counted user (users with no pageview included): user_id, variant, clicks, views."""
    g = pageviews.groupby("user_id").agg(clicks=("clicked", "sum"), views=("clicked", "size"))
    per_user = assignments[["user_id", "variant"]].join(g, on="user_id")
    return per_user.fillna({"clicks": 0, "views": 0})


def decide(srm_flag, ci_low):
    """EXPERIMENT.md section 7, in this order."""
    if srm_flag:
        return "invalid"
    return "ship" if ci_low > 0 else "no_ship"


def build_readout(data_dir):
    assignments = exclude_bots(load_assignments(data_dir), load_users(data_dir))
    pageviews = load_pageviews(data_dir, assignments)
    per_user = per_user_counts(assignments, pageviews)
    arms = {arm: per_user[per_user["variant"] == arm] for arm in ARMS}

    n_users = {arm: int(len(arms[arm])) for arm in ARMS}
    views = {arm: int(arms[arm]["views"].sum()) for arm in ARMS}
    clicks = {arm: int(arms[arm]["clicks"].sum()) for arm in ARMS}
    ctr = {arm: clicks[arm] / views[arm] for arm in ARMS}
    diff, (ci_low, ci_high) = diff_ci(arms["A"], arms["B"])
    srm_p = srm_pvalue(n_users["A"], n_users["B"])
    srm_flag = bool(srm_p < SRM_ALPHA)
    return {
        "experiment": "EXP-2291",
        "n_users": n_users,
        "pageviews": views,
        "clicks": clicks,
        "ctr": ctr,
        "diff": float(diff),
        "rel_lift": float(diff / ctr["A"]),
        "ci_95": [float(ci_low), float(ci_high)],
        "ci_method": CI_METHOD,
        "srm_p": srm_p,
        "srm_flag": srm_flag,
        "decision": decide(srm_flag, ci_low),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="EXP-2291 CTR readout")
    ap.add_argument("--data", required=True, help="folder with assignments.csv, users.csv, pageviews.csv")
    ap.add_argument("--out", required=True, help="path of the result.json to write")
    args = ap.parse_args(argv)
    readout = build_readout(args.data)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(readout, indent=2) + "\n")
    print(f"wrote {out}: decision={readout['decision']} diff={readout['diff']:+.5f} "
          f"ci=[{readout['ci_95'][0]:+.5f}, {readout['ci_95'][1]:+.5f}] srm_p={readout['srm_p']:.3g}")


if __name__ == "__main__":
    main()

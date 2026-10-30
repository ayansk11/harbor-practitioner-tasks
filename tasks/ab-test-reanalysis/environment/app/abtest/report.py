"""EXP-2291 readout: python -m abtest.report --data <folder> --out <result.json>"""
import argparse
import json
from pathlib import Path

from .filters import exclude_bots
from .load import load_assignments, load_pageviews, load_users
from .stats import ctr_ztest


def build_readout(data_dir):
    assignments = load_assignments(data_dir)
    users = load_users(data_dir)
    assignments = exclude_bots(assignments, users)
    pageviews = load_pageviews(data_dir, assignments)

    n_users = assignments.groupby("variant")["user_id"].nunique()
    views = pageviews.groupby("variant").size()
    clicks = pageviews.groupby("variant")["clicked"].sum()
    test = ctr_ztest(int(clicks["A"]), int(views["A"]), int(clicks["B"]), int(views["B"]))
    ctr = {arm: float(clicks[arm] / views[arm]) for arm in ("A", "B")}

    decision = "ship" if (test.p_value < 0.05 and test.diff > 0) else "no_ship"
    return {
        "experiment": "EXP-2291",
        "n_users": {arm: int(n_users[arm]) for arm in ("A", "B")},
        "pageviews": {arm: int(views[arm]) for arm in ("A", "B")},
        "clicks": {arm: int(clicks[arm]) for arm in ("A", "B")},
        "ctr": ctr,
        "diff": float(test.diff),
        "rel_lift": float(test.diff / ctr["A"]),
        "ci_95": [float(test.ci_low), float(test.ci_high)],
        "p_value": float(test.p_value),
        "decision": decision,
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
    print(f"wrote {out}: decision={readout['decision']} diff={readout['diff']:+.5f} p={readout['p_value']:.2g}")


if __name__ == "__main__":
    main()

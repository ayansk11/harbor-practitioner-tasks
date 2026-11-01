"""Readout of one experiment export: python -m abtest.report --data <folder> --out <result.json>"""
import argparse
import json
from pathlib import Path

from .filters import BEHAVIOUR_RULES, CLIENT_RULES, experiment_users
from .load import load_assignments, load_bot_flags, load_counted_pageviews, load_item_pageviews
from .stats import CI_METHOD, SRM_ALPHA, diff_ci, srm_pvalue

ARMS = ("A", "B")


def per_user_counts(users, pageviews):
    """One row per experiment user (users with no counted pageview included): user_id, variant, clicks, views."""
    g = pageviews.groupby("user_id").agg(clicks=("clicked", "sum"), views=("clicked", "size"))
    per_user = users[["user_id", "variant"]].join(g, on="user_id")
    return per_user.fillna({"clicks": 0, "views": 0})


def decide(srm_flag, ci_low):
    """EXPERIMENT.md section 7, in this order."""
    if srm_flag:
        return "invalid"
    return "ship" if ci_low > 0 else "no_ship"


def _by_arm(frame):
    counts = frame["variant"].value_counts()
    return {arm: int(counts.get(arm, 0)) for arm in ARMS}


def notes_for_pm(assignments, bot_flags, pageviews, r):
    """Plain-words account of the readout, every figure computed from this export."""
    randomized = assignments[assignments["method"] == "hash"]
    override = _by_arm(assignments[assignments["method"] != "hash"])
    client = set(bot_flags.loc[bot_flags["rule"].isin(CLIENT_RULES), "user_id"])
    behaviour = set(bot_flags.loc[bot_flags["rule"].isin(BEHAVIOUR_RULES), "user_id"]) - client
    out = _by_arm(randomized[randomized["user_id"].isin(client)])
    kept = _by_arm(randomized[randomized["user_id"].isin(behaviour)])
    platform = {arm: int(pageviews.loc[pageviews["variant"] == arm, "platform_clicked"].sum()) for arm in ARMS}
    lo, hi = r["ci_95"]
    if r["decision"] == "invalid":
        verdict = ("The user counts fail the sample ratio check after the plan's exclusions, so the assignment itself "
                   "is unbalanced and the experiment cannot be read: investigate the assignment before any decision.")
    elif r["decision"] == "ship":
        verdict = "The whole 95% interval is above 0: B raises click-through, ship."
    else:
        verdict = "The 95% interval does not lie above 0: no evidence that B raises click-through, do not ship."
    return [
        f"Population (plan section 3): {len(randomized)} users randomized by the hash. {sum(override.values())} "
        f"accounts placed by hand (method = override; A {override['A']}, B {override['B']}) are not in the experiment.",
        f"Bots: users with a ua_crawler flag are excluded (A {out['A']}, B {out['B']}). Users whose only flags are "
        f"velocity stay in (A {kept['A']}, B {kept['B']}): that rule counts module clicks made during the experiment, "
        "and the plan excludes no one for what was done in it.",
        "Clicks (plan section 4): a counted pageview is clicked when a related product was opened from the module on "
        f"it (an item: event). The export's clicked flag marks any module click, arrows and See all included, and "
        f"would give A {platform['A']} and B {platform['B']} clicked pageviews instead of A {r['clicks']['A']} and "
        f"B {r['clicks']['B']}.",
        f"Result: CTR A {r['ctr']['A']:.5f}, B {r['ctr']['B']:.5f}, diff {r['diff']:+.5f}, 95% CI "
        f"[{lo:+.5f}, {hi:+.5f}] ({CI_METHOD}); SRM p = {r['srm_p']:.3g} on {r['n_users']['A']} and "
        f"{r['n_users']['B']} users. {verdict}",
    ]


def build_readout(data_dir):
    assignments = load_assignments(data_dir)
    bot_flags = load_bot_flags(data_dir)
    users = experiment_users(assignments, bot_flags)
    pageviews = load_counted_pageviews(data_dir, users)
    pageviews["clicked"] = pageviews["pageview_id"].isin(load_item_pageviews(data_dir)).astype("int64")
    per_user = per_user_counts(users, pageviews)
    arms = {arm: per_user[per_user["variant"] == arm] for arm in ARMS}

    n_users = {arm: int(len(arms[arm])) for arm in ARMS}
    views = {arm: int(arms[arm]["views"].sum()) for arm in ARMS}
    clicks = {arm: int(arms[arm]["clicks"].sum()) for arm in ARMS}
    ctr = {arm: clicks[arm] / views[arm] for arm in ARMS}
    diff = ctr["B"] - ctr["A"]
    _diff, (ci_low, ci_high) = diff_ci(arms["A"], arms["B"])
    srm_p = srm_pvalue(n_users["A"], n_users["B"])
    srm_flag = bool(srm_p < SRM_ALPHA)
    readout = {
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
    readout["notes"] = notes_for_pm(assignments, bot_flags, pageviews, readout)
    return readout


def main(argv=None):
    ap = argparse.ArgumentParser(description="CTR readout of one experiment export")
    ap.add_argument("--data", required=True, help="folder with the four export files (.csv.gz or .csv)")
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

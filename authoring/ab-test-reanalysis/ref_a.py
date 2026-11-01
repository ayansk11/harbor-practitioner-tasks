"""Reference A for ab-test-reanalysis: the plan's readout of one export, standard library only (the rule route).

Independent of the shipped code, the solutions and ref_b: csv + gzip + datetime.fromisoformat, dict bookkeeping.
  population  every user the assignment service randomized (assignments.method = "hash"; an exact repeat of an
              assignment row counts once), minus the users with a ua_crawler row in bot_flags (a rule that looks only
              at the client; velocity reads in-experiment behaviour, so its users stay); n_users counts users with no
              counted pageview too;
  pageviews   that population's rows with ts at or after the user's assigned_at (instants, not text);
  clicks      counted pageviews whose pageview_id has at least one module_clicks row with an item:<product> target
              (a related product opened; two opened from one pageview is one clicked pageview);
  CTR         sum(clicks) / sum(pageviews) per arm; diff = CTR_B - CTR_A;
  CI          delta method for each arm's ratio of per-user sums, arms independent:
                Var(CTR) = N / (N - 1) * sum_i (c_i - CTR * n_i)^2 / (sum_i n_i)^2,  diff +/- z_0.975 sqrt(VarA + VarB);
  SRM         Pearson chi-square of n_users against 50/50, 1 df, no continuity correction: p = erfc(sqrt(chi2 / 2));
  decision    "invalid" if p < 0.001, else "ship" if the lower bound > 0, else "no_ship".
Reads <folder>/<file>.csv.gz (or the plain .csv) for assignments, bot_flags, pageviews, module_clicks. Used by
gen_data.py for tests/expected/. Run alone: python ref_a.py <folder>  (prints the JSON).
"""
import csv, gzip, json, math, os, sys
from datetime import datetime
from statistics import NormalDist

Z975 = NormalDist().inv_cdf(0.975)
SRM_ALPHA = 0.001
RULES = ("ua_crawler", "velocity")


def _open(folder, name):
    p = os.path.join(folder, name + ".gz")
    if os.path.exists(p):
        return gzip.open(p, "rt", newline="", encoding="utf-8")
    return open(os.path.join(folder, name), newline="", encoding="utf-8")


def _instant(text):
    t = datetime.fromisoformat(text.strip())
    if t.tzinfo is None:
        raise ValueError(f"timestamp without offset: {text!r}")
    return t


def analyse(folder):
    seen, assign = set(), {}
    with _open(folder, "assignments.csv") as f:
        for r in csv.DictReader(f):
            key = (r["user_id"], r["variant"], r["assigned_at"], r["method"])
            if key in seen:                        # an exact repeat of a row counts once
                continue
            seen.add(key)
            if r["user_id"] in assign:
                raise ValueError(f"user {r['user_id']} has two different assignment rows")
            if r["variant"] not in ("A", "B") or r["method"] not in ("hash", "override"):
                raise ValueError(f"unknown variant or method in {r}")
            assign[r["user_id"]] = (r["variant"], _instant(r["assigned_at"]), r["method"])
    crawlers = set()
    with _open(folder, "bot_flags.csv") as f:
        for r in csv.DictReader(f):
            if r["rule"] not in RULES:
                raise ValueError(f"unknown rule {r['rule']!r}")
            _instant(r["flagged_at"])
            if r["rule"] == "ua_crawler":
                crawlers.add(r["user_id"])
    users = {u: (v, t) for u, (v, t, m) in assign.items() if m == "hash" and u not in crawlers}
    views = dict.fromkeys(users, 0)
    counted = {}                                   # pageview_id -> user, counted pageviews only
    ids = set()
    with _open(folder, "pageviews.csv") as f:
        for r in csv.DictReader(f):
            pid = r["pageview_id"]
            if pid in ids:
                raise ValueError(f"pageview_id {pid} repeated")
            ids.add(pid)
            u = r["user_id"]
            if u not in users or _instant(r["ts"]) < users[u][1]:    # strictly before assignment: dropped
                continue
            views[u] += 1
            counted[pid] = u
    clicked = set()
    with _open(folder, "module_clicks.csv") as f:
        for r in csv.DictReader(f):
            if r["target"].startswith("item:") and r["pageview_id"] in counted:
                clicked.add(r["pageview_id"])
    clicks = dict.fromkeys(users, 0)
    for pid in clicked:
        clicks[counted[pid]] += 1
    out = {"n_users": {}, "pageviews": {}, "clicks": {}, "ctr": {}}
    var = {}
    for arm in ("A", "B"):
        us = [u for u, (v, _t) in users.items() if v == arm]
        N = len(us)
        C = sum(clicks[u] for u in us)
        V = sum(views[u] for u in us)
        R = C / V
        ss = math.fsum((clicks[u] - R * views[u]) ** 2 for u in us)
        var[arm] = N / (N - 1) * ss / (V * V)
        out["n_users"][arm], out["pageviews"][arm], out["clicks"][arm], out["ctr"][arm] = N, V, C, R
    diff = out["ctr"]["B"] - out["ctr"]["A"]
    hw = Z975 * math.sqrt(var["A"] + var["B"])
    na, nb = out["n_users"]["A"], out["n_users"]["B"]
    e = (na + nb) / 2
    chi2 = ((na - e) ** 2 + (nb - e) ** 2) / e
    srm_p = math.erfc(math.sqrt(chi2 / 2))
    srm_flag = srm_p < SRM_ALPHA
    lo, hi = diff - hw, diff + hw
    decision = "invalid" if srm_flag else ("ship" if lo > 0 else "no_ship")
    out.update(diff=diff, ci_95=[lo, hi], half_width=hw, srm_p=srm_p, srm_flag=srm_flag, decision=decision,
               method="delta method, sample-variance form, z=%.15f" % Z975)
    return out


if __name__ == "__main__":
    print(json.dumps(analyse(sys.argv[1]), indent=1, sort_keys=True))

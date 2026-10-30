"""Reference A for ab-test-reanalysis: the analysis as /app/EXPERIMENT.md states it, standard library only.

Independent of the shipped code and of the solutions: csv + datetime.fromisoformat parsing, dict bookkeeping, and the
delta method for each arm's ratio CTR = sum(clicks) / sum(pageviews) over users:
    Var(CTR) = N / (N - 1) * sum_i (c_i - CTR * n_i)^2 / (sum_i n_i)^2      (sample-variance form)
    CI_95(diff) = diff +/- z_0.975 * sqrt(Var_A + Var_B),  diff = CTR_B - CTR_A
SRM: Pearson chi-square of the user counts against 50/50, 1 df, no continuity correction: p = erfc(sqrt(chi2 / 2)).
Decision: "invalid" if p < 0.001, else "ship" if the lower bound > 0, else "no_ship".
Reads a folder with assignments.csv, users.csv, pageviews.csv (plain or .gz). Used by gen_data.py for tests/expected/.
Run alone: python ref_a.py <folder>  (prints the JSON).
"""
import csv, gzip, json, math, os, sys
from datetime import datetime
from statistics import NormalDist

Z975 = NormalDist().inv_cdf(0.975)
SRM_ALPHA = 0.001


def _open(folder, name):
    p = os.path.join(folder, name)
    if os.path.exists(p):
        return open(p, newline="", encoding="utf-8")
    return gzip.open(p + ".gz", "rt", newline="", encoding="utf-8")


def _instant(text):
    t = datetime.fromisoformat(text.strip())
    if t.tzinfo is None:
        raise ValueError(f"timestamp without offset: {text!r}")
    return t


def analyse(folder):
    seen, assign = set(), {}
    with _open(folder, "assignments.csv") as f:
        for r in csv.DictReader(f):
            key = (r["user_id"], r["variant"], r["assigned_at"])
            if key in seen:            # an exact repeat of a row counts once
                continue
            seen.add(key)
            if r["user_id"] in assign:
                raise ValueError(f"user {r['user_id']} has two different assignment rows")
            if r["variant"] not in ("A", "B"):
                raise ValueError(f"unknown variant {r['variant']!r}")
            assign[r["user_id"]] = (r["variant"], _instant(r["assigned_at"]))
    with _open(folder, "users.csv") as f:
        bots = {r["user_id"] for r in csv.DictReader(f) if r["is_bot"].strip() == "1"}
    users = {u: v for u, v in assign.items() if u not in bots}       # bots out of both arms
    clicks = dict.fromkeys(users, 0)
    views = dict.fromkeys(users, 0)
    with _open(folder, "pageviews.csv") as f:
        for r in csv.DictReader(f):
            u = r["user_id"]
            if u not in users:
                continue
            if _instant(r["ts"]) < users[u][1]:                      # strictly before assignment: dropped
                continue
            views[u] += 1
            clicks[u] += int(r["clicked"])
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

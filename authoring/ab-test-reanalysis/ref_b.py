"""Reference B for ab-test-reanalysis: a second, independent reading of an export (pandas + numpy; the time route).

Own loader (pandas, not the shipped code, not ref_a) and a different population rule that the generator makes
coincide with ref_a's rule route (data_checks.py assertion e):
  population  hash-assigned users (exact repeats once) with no bot_flags row of any rule flagged at or before their
              assigned_at (flags raised later read what the user did during the experiment);
  clicks      a counted pageview is clicked if its pageview_id is among the pageview_ids of item:<product> events
              (set membership, so pageviews without events count as unclicked and two events count once).
Interval methods (used by calibration_study.py):
  delta(...)     delta method for each arm's ratio of sums (numpy), with the N/(N-1) factor or without it;
  cr1(...)       pageview-level OLS of clicked on a B indicator with CR1 cluster-robust errors by user (2x2 algebra);
  bootstrap(...) user-level bootstrap, users resampled with replacement within each arm (or pooled), any B and seed.
readout(folder) gives the full readout with the delta interval (gen_data.py compares it with ref_a's).
`python ref_b.py <folder>` prints its delta and CR1 readouts.
"""
import json, math, os, sys

import numpy as np
import pandas as pd

Z975 = 1.959963984540054
SRM_ALPHA = 0.001


def _read(folder, name, **kw):
    p = os.path.join(folder, name + ".gz")
    return pd.read_csv(p if os.path.exists(p) else os.path.join(folder, name), **kw)


def _utc(col):
    return pd.to_datetime(col, utc=True, format="ISO8601")


def per_user(folder):
    """-> dict arm -> (clicks per user, pageviews per user) as float arrays, every counted user (zeros included)."""
    a = _read(folder, "assignments.csv", dtype=str).drop_duplicates()
    if a["user_id"].duplicated().any():
        raise ValueError("conflicting assignment rows")
    a = a[a["method"] == "hash"].copy()
    a["t0"] = _utc(a["assigned_at"])
    f = _read(folder, "bot_flags.csv", dtype=str)
    f["t"] = _utc(f["flagged_at"])
    early = f.merge(a[["user_id", "t0"]], on="user_id", how="inner")
    early = early.loc[early["t"] <= early["t0"], "user_id"]
    a = a[~a["user_id"].isin(early)]
    pv = _read(folder, "pageviews.csv", dtype={"pageview_id": str, "user_id": str, "ts": str, "clicked": "int64"})
    pv["t"] = _utc(pv["ts"])
    pv = pv.merge(a[["user_id", "t0"]], on="user_id", how="inner")
    pv = pv[pv["t"] >= pv["t0"]]
    mc = _read(folder, "module_clicks.csv", dtype=str)
    items = mc.loc[mc["target"].str.startswith("item:"), "pageview_id"].unique()
    pv = pv.assign(c=pv["pageview_id"].isin(items).astype("int64"))
    g = pv.groupby("user_id").agg(c=("c", "sum"), n=("c", "size"))
    a = a.join(g, on="user_id").fillna({"c": 0, "n": 0})
    return {arm: (a.loc[a["variant"] == arm, "c"].to_numpy(float), a.loc[a["variant"] == arm, "n"].to_numpy(float))
            for arm in ("A", "B")}


def delta(arms, small_sample=True):
    out = {}
    for arm, (c, n) in arms.items():
        N = len(c)
        R = c.sum() / n.sum()
        v = float(((c - R * n) ** 2).sum()) / float(n.sum()) ** 2
        out[arm] = (R, v * (N / (N - 1) if small_sample else 1.0))
    diff = out["B"][0] - out["A"][0]
    se = math.sqrt(out["A"][1] + out["B"][1])
    return diff, diff - Z975 * se, diff + Z975 * se


def readout(folder):
    """The full readout (delta interval) in ref_a's keys."""
    arms = per_user(folder)
    out = {"n_users": {}, "pageviews": {}, "clicks": {}, "ctr": {}}
    for arm, (c, n) in arms.items():
        out["n_users"][arm] = int(len(c))
        out["pageviews"][arm] = int(n.sum())
        out["clicks"][arm] = int(c.sum())
        out["ctr"][arm] = float(c.sum() / n.sum())
    diff, lo, hi = delta(arms)
    na, nb = out["n_users"]["A"], out["n_users"]["B"]
    e = (na + nb) / 2
    chi2 = ((na - e) ** 2 + (nb - e) ** 2) / e
    srm_p = math.erfc(math.sqrt(chi2 / 2))
    srm_flag = srm_p < SRM_ALPHA
    out.update(diff=float(diff), ci_95=[float(lo), float(hi)], half_width=float((hi - lo) / 2), srm_p=srm_p,
               srm_flag=srm_flag, decision="invalid" if srm_flag else ("ship" if lo > 0 else "no_ship"))
    return out


def cr1(arms):
    """OLS y = b0 + b1*B on pageviews, CR1 by user: V = (X'X)^-1 M (X'X)^-1 * G/(G-1) * (n-1)/(n-k)."""
    ca, na = arms["A"]
    cb, nb = arms["B"]
    Va, Vb = na.sum(), nb.sum()
    XtX = np.array([[Va + Vb, Vb], [Vb, Vb]])
    XtY = np.array([ca.sum() + cb.sum(), cb.sum()])
    b = np.linalg.solve(XtX, XtY)
    fit_a, fit_b = b[0], b[0] + b[1]
    da = ca - fit_a * na                 # each user's summed residual
    db = cb - fit_b * nb
    meat = np.zeros((2, 2))
    meat[0, 0] = (da ** 2).sum() + (db ** 2).sum()
    meat[0, 1] = meat[1, 0] = (db ** 2).sum()
    meat[1, 1] = (db ** 2).sum()
    inv = np.linalg.inv(XtX)
    G = len(ca) + len(cb)
    nobs = Va + Vb
    V = inv @ meat @ inv * (G / (G - 1)) * ((nobs - 1) / (nobs - 2))
    se = math.sqrt(V[1, 1])
    return float(b[1]), float(b[1] - Z975 * se), float(b[1] + Z975 * se)


def bootstrap_draws(arms, B, seed, pooled=False, chunk=250):
    """B bootstrap replicates of diff. Within-arm resampling by default; pooled = resample all users together."""
    rng = np.random.default_rng(seed)
    out = np.empty(B)
    if not pooled:
        ca, na = arms["A"]
        cb, nb = arms["B"]
        for s in range(0, B, chunk):
            k = min(chunk, B - s)
            ia = rng.integers(0, len(ca), size=(k, len(ca)), dtype=np.int32)
            ib = rng.integers(0, len(cb), size=(k, len(cb)), dtype=np.int32)
            out[s:s + k] = cb[ib].sum(1) / nb[ib].sum(1) - ca[ia].sum(1) / na[ia].sum(1)
        return out
    c = np.r_[arms["A"][0], arms["B"][0]]
    n = np.r_[arms["A"][1], arms["B"][1]]
    isb = np.r_[np.zeros(len(arms["A"][0])), np.ones(len(arms["B"][0]))]
    cb_, nb_ = c * isb, n * isb
    for s in range(0, B, chunk):
        k = min(chunk, B - s)
        i = rng.integers(0, len(c), size=(k, len(c)), dtype=np.int32)
        sb_c, sb_n = cb_[i].sum(1), nb_[i].sum(1)
        out[s:s + k] = sb_c / sb_n - (c[i].sum(1) - sb_c) / (n[i].sum(1) - sb_n)
    return out


def bootstrap_cis(diff, draws):
    """percentile, basic and normal 95% intervals from one set of replicates."""
    q_lo, q_hi = np.quantile(draws, [0.025, 0.975])
    sd = float(draws.std(ddof=1))
    return {"percentile": (float(q_lo), float(q_hi)), "basic": (2 * diff - float(q_hi), 2 * diff - float(q_lo)),
            "normal": (diff - Z975 * sd, diff + Z975 * sd)}


if __name__ == "__main__":
    arms = per_user(sys.argv[1])
    print(json.dumps({"n_users": {k: len(v[0]) for k, v in arms.items()}, "delta": delta(arms), "cr1": cr1(arms)},
                     indent=1))

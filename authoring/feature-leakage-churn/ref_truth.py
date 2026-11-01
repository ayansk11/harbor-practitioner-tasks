"""The live scoring service's feature values, from the simulator's TRUE warehouse state (authoring only).

For every scoring point (customer c, time t) this returns what `live/features.py` computes when it queries the
warehouse at t. Each table holds exactly the rows committed before t, where the commit time of every row is the
simulator's own record of the loader run that wrote it (`visible_at` in the world built by gen_data.brand_world); the
customer record is what the last CRM sync committed before t wrote (plan and last login, from the simulated CRM state
at that sync's start), or the sign-up row if no sync has written it yet. It never reads an extract's audit columns
(`_loaded_at`, `_updated_at`, `_load_job`) or its records in `_ops/`, so a value that an extract-only pipeline
matches is a value the extract determines.

The live queries, applied literally (both the visibility and each query's own time condition):
  orders_7d, orders_30d    count of visible orders with t - 7 (30) days <= ordered_at < t
  spend_30d_cents          sum of amount_cents over the 30-day rows (0 if none)
  days_since_last_order    (t - max ordered_at of visible orders with ordered_at < t) / 86400, null if none
  tickets_30d              count of visible tickets with t - 30 days <= opened_at < t
  tenure_days              (t - signup_at) / 86400
  status                   status of the visible snapshot with the greatest snapshot_date, null if none
  plan                     customers.plan as held at t
  days_since_last_login    (t - customers.last_login_at as held at t) / 86400, null if that is null
  app_minutes_7d           the request's own reading, else that of the customer's latest earlier scoring point with
                           one, else null
  te_district              (s + 20 p) / (n + 20); p = mean churned_30d of all visible labels (0.05 if none); n, s =
                           count and sum over the visible labels of customers in c's postcode district

compute(world, points=None) -> DataFrame with customer_id, as_of (int64 epoch seconds) and the 11 features.
The *_lists helpers and the feature functions take plain per-customer lists, so mechanisms.py can swap one input for
what a wrong rule would read and keep every other input true.
"""
import bisect
from collections import defaultdict

import numpy as np
import pandas as pd

DAY = 86400
M, P0 = 20, 0.05
FEATURES = ["orders_7d", "orders_30d", "spend_30d_cents", "tickets_30d", "days_since_last_order", "tenure_days",
            "status", "plan", "days_since_last_login", "app_minutes_7d", "te_district"]
KEPT = [f for f in FEATURES if f != "days_since_last_login"]
INT_FEATS = ["orders_7d", "orders_30d", "spend_30d_cents", "tickets_30d"]
STR_FEATS = ["status", "plan"]


def order_lists(cust, ordered_at, visible_at, amount, window_at=None):
    """Per customer: (ordered_at, visible_at, amount_cents, window time); the window time is ordered_at unless a
    variant says otherwise."""
    window_at = ordered_at if window_at is None else window_at
    out = defaultdict(list)
    for c, oa, va, amt, wt in zip(cust.tolist(), ordered_at.tolist(), visible_at.tolist(), amount.tolist(),
                                  window_at.tolist()):
        out[c].append((oa, va, amt, wt))
    return out


def ticket_lists(cust, opened_at, visible_at):
    out = defaultdict(list)
    for c, op, va in zip(cust.tolist(), opened_at.tolist(), visible_at.tolist()):
        out[c].append((op, va))
    return out


def snapshot_lists(cust, snapshot_date, visible_at, status):
    out = defaultdict(list)
    for c, sd, va, st in zip(cust.tolist(), snapshot_date.tolist(), visible_at.tolist(), status.tolist()):
        out[c].append((sd, va, st))
    return out


def order_features(pc, pt, lists):
    n = len(pc)
    o7, o30, s30 = np.zeros(n, np.int64), np.zeros(n, np.int64), np.zeros(n, np.int64)
    dso = np.full(n, np.nan)
    for i in range(n):
        c, t = pc[i], pt[i]
        lo7, lo30 = t - 7 * DAY, t - 30 * DAY
        a7 = a30 = s = 0
        last = None
        for (oa, va, amt, wt) in lists.get(c, ()):
            if va < t and oa < t:
                if lo7 <= wt < t:
                    a7 += 1
                if lo30 <= wt < t:
                    a30 += 1
                    s += amt
                if last is None or oa > last:
                    last = oa
        o7[i], o30[i], s30[i] = a7, a30, s
        if last is not None:
            dso[i] = (t - last) / DAY
    return {"orders_7d": o7, "orders_30d": o30, "spend_30d_cents": s30, "days_since_last_order": dso}


def ticket_features(pc, pt, lists):
    n = len(pc)
    k30 = np.zeros(n, np.int64)
    for i in range(n):
        c, t = pc[i], pt[i]
        lo30 = t - 30 * DAY
        k30[i] = sum(1 for (op, va) in lists.get(c, ()) if va < t and lo30 <= op < t)
    return {"tickets_30d": k30}


def status_feature(pc, pt, lists, pick="date"):
    """Status of the visible snapshot with the greatest snapshot_date (pick='date', the live query); a variant may
    pick the most recently loaded one (pick='loaded')."""
    out = [None] * len(pc)
    for i in range(len(pc)):
        c, t = pc[i], pt[i]
        best_key, best = None, None
        for (sd, va, st) in lists.get(c, ()):
            if va < t:
                key = sd if pick == "date" else va
                if best_key is None or key > best_key:
                    best_key, best = key, st
        out[i] = best
    return {"status": np.array(out, dtype=object)}


def customer_record_features(pc, pt, writes, signup_plan):
    """plan and days_since_last_login from the customer record as held at t: the last CRM write committed before t,
    else the sign-up row (the signup plan, no last login)."""
    plan = [None] * len(pc)
    dsl = np.full(len(pc), np.nan)
    for i in range(len(pc)):
        c, t = pc[i], pt[i]
        commits, plans, logins = writes.get(c, ((), (), ()))
        j = bisect.bisect_left(commits, t) - 1
        if j >= 0:
            plan[i] = plans[j]
            if logins[j] is not None:
                dsl[i] = (t - logins[j]) / DAY
        else:
            plan[i] = signup_plan[c]
    return {"plan": np.array(plan, dtype=object), "days_since_last_login": dsl}


def te_feature(pc, pt, district, lab_cust, lab_visible, lab_y):
    """Smoothed district churn rate over the labels visible at t (whole extract for p, the district for n and s)."""
    order = np.argsort(lab_visible, kind="stable")
    g_vis = lab_visible[order].tolist()
    g_pref = [0]
    for y in lab_y[order].tolist():
        g_pref.append(g_pref[-1] + y)
    d_vis, d_pref = defaultdict(list), defaultdict(lambda: [0])
    for c, va, y in zip(lab_cust[order].tolist(), g_vis, lab_y[order].tolist()):
        k = district[c]
        d_vis[k].append(va)
        d_pref[k].append(d_pref[k][-1] + y)
    te = np.zeros(len(pc))
    for i in range(len(pc)):
        c, t = pc[i], pt[i]
        N = bisect.bisect_left(g_vis, t)
        p = g_pref[N] / N if N > 0 else P0
        k = district[c]
        n = bisect.bisect_left(d_vis.get(k, []), t)
        s = d_pref[k][n] if k in d_pref else 0
        te[i] = (s + M * p) / (n + M)
    return {"te_district": te}


def app_feature(points):
    """Own reading, else the customer's latest earlier reading (the scoring_points rows written before t)."""
    df = points[["customer_id", "as_of", "app_minutes_7d"]].reset_index(drop=True)
    order = np.lexsort((df["as_of"].to_numpy(), df["customer_id"].to_numpy()))
    out = np.full(len(df), np.nan)
    cust, vals = df["customer_id"].to_numpy()[order], df["app_minutes_7d"].to_numpy(dtype="float64")[order]
    last_c, last_v = None, np.nan
    for j, i in enumerate(order):
        if cust[j] != last_c:
            last_c, last_v = cust[j], np.nan
        if not np.isnan(vals[j]):
            last_v = vals[j]
        out[i] = last_v
    return {"app_minutes_7d": out}


def crm_lists(writes):
    """Per customer: (commit times, plans, last logins) of the true CRM writes, in commit order."""
    w = writes.sort_values(["customer_id", "commit"], kind="mergesort")
    out = {}
    for c, g in w.groupby("customer_id", sort=False):
        ll = [None if pd.isna(v) else int(v) for v in g["last_login_at"].tolist()]
        out[c] = (g["commit"].tolist(), g["plan"].tolist(), ll)
    return out


def compute(world, points=None):
    pts = world["points"] if points is None else points
    pts = pts[["customer_id", "as_of", "app_minutes_7d"]].reset_index(drop=True)
    pc, pt = pts["customer_id"].tolist(), pts["as_of"].tolist()
    cu = world["customers"]
    signup = dict(zip(cu["customer_id"].tolist(), cu["signup_at"].tolist()))
    district = dict(zip(cu["customer_id"].tolist(), cu["postcode_district"].tolist()))
    signup_plan = dict(zip(cu["customer_id"].tolist(), cu["plan0"].tolist()))
    o, k, s, lb = world["orders"], world["tickets"], world["snapshots"], world["labels"]
    feats = {}
    feats.update(order_features(pc, pt, order_lists(o["customer_id"].to_numpy(), o["ordered_at"].to_numpy(),
                                                    o["visible_at"].to_numpy(), o["amount_cents"].to_numpy())))
    feats.update(ticket_features(pc, pt, ticket_lists(k["customer_id"].to_numpy(), k["opened_at"].to_numpy(),
                                                      k["visible_at"].to_numpy())))
    feats["tenure_days"] = np.array([(t - signup[c]) / DAY for c, t in zip(pc, pt)])
    feats.update(status_feature(pc, pt, snapshot_lists(s["customer_id"].to_numpy(), s["snapshot_date"].to_numpy(),
                                                       s["visible_at"].to_numpy(), s["status"].to_numpy())))
    feats.update(customer_record_features(pc, pt, crm_lists(world["crm_writes"]), signup_plan))
    wp = world["points"].reset_index(drop=True)
    app_all = app_feature(wp)["app_minutes_7d"].tolist()
    app = dict(zip(zip(wp["customer_id"].tolist(), wp["as_of"].tolist()), app_all))
    feats["app_minutes_7d"] = np.array([app[(c, t)] for c, t in zip(pc, pt)], dtype="float64")
    feats.update(te_feature(pc, pt, district, lb["customer_id"].to_numpy(), lb["visible_at"].to_numpy(),
                            lb["churned_30d"].to_numpy()))
    out = pd.DataFrame({"customer_id": np.array(pc, dtype=np.int64), "as_of": np.array(pt, dtype=np.int64)})
    for f in FEATURES:
        out[f] = feats[f]
    return out

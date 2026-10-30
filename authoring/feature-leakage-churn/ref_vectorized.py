"""Reference 1 (vectorized, pandas merge_asof on cumulative counts), written from churn/FEATURES.md alone.

compute(data_dir) -> DataFrame with customer_id (int64), as_of (int64 epoch seconds) and the nine features.
Every number is exact integer arithmetic followed by at most one division chain, so reference 2 (ref_loop.py) can
agree bit for bit.
"""
import os
import numpy as np
import pandas as pd

DAY = 86400
M, P0 = 20, 0.05
FEATURES = ["orders_7d", "orders_30d", "spend_30d_cents", "tickets_30d", "days_since_last_order", "tenure_days",
            "status", "app_minutes_7d", "te_district"]
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def _sec(s):
    return ((pd.to_datetime(s, utc=True) - EPOCH) // pd.Timedelta(seconds=1)).astype("int64")


def load(d):
    r = lambda n: pd.read_csv(os.path.join(d, n + ".csv"), dtype={"postcode_district": "str"})
    cu, sp, od, tk, sn, lb = (r(n) for n in ("customers", "scoring_points", "orders", "tickets", "status_snapshots",
                                              "labels"))
    cu["signup_at"] = _sec(cu["signup_at"])
    sp["as_of"] = _sec(sp["as_of"])
    od["ordered_at"] = _sec(od["ordered_at"])
    tk["opened_at"] = _sec(tk["opened_at"])
    sn["snapshot_date"] = _sec(sn["snapshot_date"])
    lb["label_available_at"] = _sec(lb["label_available_at"])
    return cu, sp, od, tk, sn, lb


def _cum_before(pts, key_col, ev, ev_t, by="customer_id", value=None):
    """For each point: count (and sum of `value`) of events of the same `by` group with ev_t < pts[key_col]."""
    e = ev.sort_values([by, ev_t], kind="mergesort").copy()
    e["_c"] = e.groupby(by).cumcount() + 1
    if value is not None:
        e["_s"] = e.groupby(by)[value].cumsum().astype("int64")
    e = e.sort_values(ev_t, kind="mergesort")
    left = pts[["_row", by, key_col]].sort_values(key_col, kind="mergesort")
    cols = [by, ev_t, "_c"] + (["_s"] if value is not None else [])
    m = pd.merge_asof(left, e[cols], left_on=key_col, right_on=ev_t, by=by, allow_exact_matches=False,
                      direction="backward").set_index("_row").sort_index()
    c = m["_c"].fillna(0).astype("int64").to_numpy()
    s = m["_s"].fillna(0).astype("int64").to_numpy() if value is not None else None
    return c, s


def compute(data_dir):
    cu, sp, od, tk, sn, lb = load(data_dir)
    pts = sp[["customer_id", "as_of", "app_minutes_7d"]].reset_index(drop=True).copy()
    pts["_row"] = np.arange(len(pts))
    t = pts["as_of"].to_numpy()
    out = pd.DataFrame({"customer_id": pts["customer_id"].astype("int64"), "as_of": pts["as_of"].astype("int64")})

    for W in (7, 30):
        pts[f"_t{W}"] = pts["as_of"] - W * DAY
    c_now, s_now = _cum_before(pts, "as_of", od, "ordered_at", value="amount_cents")
    c7, _ = _cum_before(pts, "_t7", od, "ordered_at")
    c30, s30 = _cum_before(pts, "_t30", od, "ordered_at", value="amount_cents")
    out["orders_7d"] = c_now - c7
    out["orders_30d"] = c_now - c30
    out["spend_30d_cents"] = s_now - s30
    k_now, _ = _cum_before(pts, "as_of", tk, "opened_at")
    k30, _ = _cum_before(pts, "_t30", tk, "opened_at")
    out["tickets_30d"] = k_now - k30

    o = od.sort_values("ordered_at", kind="mergesort")[["customer_id", "ordered_at"]]
    left = pts[["_row", "customer_id", "as_of"]].sort_values("as_of", kind="mergesort")
    last = pd.merge_asof(left, o, left_on="as_of", right_on="ordered_at", by="customer_id",
                         allow_exact_matches=False).set_index("_row").sort_index()["ordered_at"]
    lastv = last.to_numpy(dtype="float64")
    gap = np.where(np.isnan(lastv), np.nan, 0.0)
    ok = ~np.isnan(lastv)
    gap[ok] = (t[ok] - lastv[ok].astype("int64")) / DAY
    out["days_since_last_order"] = gap

    signup = pts["customer_id"].map(cu.set_index("customer_id")["signup_at"]).astype("int64").to_numpy()
    out["tenure_days"] = (t - signup) / DAY

    pts["_day0"] = (pts["as_of"] // DAY) * DAY
    s = sn.sort_values("snapshot_date", kind="mergesort")[["customer_id", "snapshot_date", "status"]]
    left = pts[["_row", "customer_id", "_day0"]].sort_values("_day0", kind="mergesort")
    st = pd.merge_asof(left, s, left_on="_day0", right_on="snapshot_date", by="customer_id",
                       allow_exact_matches=False).set_index("_row").sort_index()["status"]
    out["status"] = [None if (isinstance(v, float) or v is None or pd.isna(v)) else str(v) for v in st.tolist()]

    a = pts[["_row", "customer_id", "as_of", "app_minutes_7d"]].sort_values(["customer_id", "as_of"], kind="mergesort")
    a["_f"] = a.groupby("customer_id")["app_minutes_7d"].ffill()
    out["app_minutes_7d"] = a.set_index("_row").sort_index()["_f"].to_numpy(dtype="float64")

    dist = cu.set_index("customer_id")["postcode_district"]
    L = lb[["customer_id", "churned_30d", "label_available_at"]].copy()
    L["district"] = L["customer_id"].map(dist)
    L["churned_30d"] = L["churned_30d"].astype("int64")
    L = L.sort_values("label_available_at", kind="mergesort").reset_index(drop=True)
    L["_N"] = np.arange(1, len(L) + 1)
    L["_S"] = L["churned_30d"].cumsum()
    L["_n"] = L.groupby("district").cumcount() + 1
    L["_s"] = L.groupby("district")["churned_30d"].cumsum()
    pts["district"] = pts["customer_id"].map(dist)
    left = pts[["_row", "district", "as_of"]].sort_values("as_of", kind="mergesort")
    g = pd.merge_asof(left, L[["label_available_at", "_N", "_S"]], left_on="as_of", right_on="label_available_at",
                      allow_exact_matches=False).set_index("_row").sort_index()
    k = pd.merge_asof(left, L[["district", "label_available_at", "_n", "_s"]], left_on="as_of",
                      right_on="label_available_at", by="district",
                      allow_exact_matches=False).set_index("_row").sort_index()
    N = g["_N"].fillna(0).astype("int64").to_numpy()
    S = g["_S"].fillna(0).astype("int64").to_numpy()
    n = k["_n"].fillna(0).astype("int64").to_numpy()
    s_ = k["_s"].fillna(0).astype("int64").to_numpy()
    p = np.full(len(pts), P0)
    nz = N > 0
    p[nz] = S[nz] / N[nz]
    out["te_district"] = (s_ + M * p) / (n + M)
    return out


if __name__ == "__main__":
    import sys
    print(compute(sys.argv[1]).head())

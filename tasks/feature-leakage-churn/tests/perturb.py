"""Check B's perturbed extracts: change everything that becomes known at or after a cut time, keep the rest.

Under FEATURES.md, a prediction at t <= cut only uses rows stamped before t, so its features must not change:
- orders and tickets stamped at or after the cut: amounts changed, 30% dropped, new ones added (some exactly at the
  cut, for customers who signed up before it, and one after the cut on the cut's own day for every customer scored
  earlier that day); every ticket-trigger point at or after the cut keeps a ticket at its as_of, as in the extract;
- status snapshots dated on or after the cut's UTC date (a snapshot dated D describes the end of day D): statuses
  rewritten, 20% dropped, new ones added;
- labels whose label_available_at is at or after the cut: 50% flipped, 20% dropped;
- scoring points after the cut: app_minutes_7d rewritten or blanked, 20% dropped with their labels, new ones added;
- 60 new customers who sign up at or after the cut, with activity only after it.
Deterministic for a given (extract, cut, seed): numpy PCG64 with a fixed seed, pinned numpy and pandas.
"""
import numpy as np
import pandas as pd

DAY = 86400
END = 1767225600  # 2026-01-01T00:00:00Z, the extract time
STATUSES = np.array(["active", "paused", "payment_failed", "cancelled"])
TOPICS = np.array(["delivery", "quality", "account", "billing"])


def perturb(d, cut, seed):
    rng = np.random.default_rng(seed)
    day_cut = cut - cut % DAY
    cust = d["customers"]
    signup = dict(zip(cust.customer_id.tolist(), cust.signup_at.tolist()))

    n_new = 60
    new_ids = int(cust.customer_id.max()) + 1 + np.arange(n_new)
    new_signup = rng.integers(cut, END - 30 * DAY, n_new)
    new_cust = pd.DataFrame({"customer_id": new_ids, "signup_at": new_signup,
                             "plan": rng.choice(["basic", "plus", "family"], n_new),
                             "postcode_district": rng.choice(cust.postcode_district.unique(), n_new)})
    signup.update(zip(new_ids.tolist(), new_signup.tolist()))
    customers = pd.concat([cust, new_cust], ignore_index=True)
    ids = customers.customer_id.to_numpy()

    def times_after(cids, lo=cut):
        lo_c = np.maximum(lo, np.array([signup[c] + 1 for c in cids], dtype="int64"))
        return np.array([rng.integers(a, END) for a in lo_c], dtype="int64")

    sp = d["scoring_points"]
    scored_today = sp[(sp.as_of >= day_cut) & (sp.as_of <= cut)].customer_id.unique()
    at_cut = rng.choice(cust[cust.signup_at < cut].customer_id.to_numpy(), 40, replace=False)  # signed up before

    def events(df, ts, id_col, extra):
        late = df[ts] >= cut
        keep_early = df[~late]
        lt = df[late].copy()
        lt = lt[rng.random(len(lt)) >= 0.3]
        add_c = rng.choice(ids, len(lt) // 3 + 1)
        same_day = np.array([rng.integers(cut, day_cut + DAY) for _ in scored_today], dtype="int64")
        cids = np.concatenate([add_c, scored_today, at_cut]).astype("int64")
        t = np.concatenate([times_after(add_c), same_day, np.full(len(at_cut), cut, dtype="int64")])
        new = pd.DataFrame({"customer_id": cids, ts: t})
        new = new[new[ts] < END]
        for col, fn in extra.items():
            new[col] = fn(len(new))
        new.insert(0, id_col, int(df[id_col].max()) + 1 + np.arange(len(new)))
        return lt, pd.concat([keep_early, lt, new[df.columns]], ignore_index=True)

    o = d["orders"]
    o_late, orders = events(o, "ordered_at", "order_id",
                            {"kind": lambda n: rng.choice(["box", "addon"], n),
                             "amount_cents": lambda n: rng.integers(499, 9000, n)})
    late = orders.ordered_at >= cut
    orders.loc[late, "amount_cents"] = np.maximum(
        1, np.round(orders.loc[late, "amount_cents"].to_numpy() * rng.uniform(0.2, 3.0, int(late.sum())))
    ).astype("int64")
    _, tickets = events(d["tickets"], "opened_at", "ticket_id", {"topic": lambda n: rng.choice(TOPICS, n)})
    # (every ticket-trigger point at or after the cut gets its ticket back below, once the points are final)

    s = d["status_snapshots"]
    late = s.snapshot_date >= day_cut
    s_late = s[late].copy()
    flip = rng.random(len(s_late)) < 0.6
    s_late.loc[flip, "status"] = rng.choice(STATUSES, int(flip.sum()))
    s_late = s_late[rng.random(len(s_late)) >= 0.2]
    add_c = rng.choice(ids, len(ids) // 3)
    add_day = np.array([rng.integers(max(day_cut, signup[c] - signup[c] % DAY), END) for c in add_c], dtype="int64")
    s_new = pd.DataFrame({"customer_id": add_c, "snapshot_date": add_day - add_day % DAY,
                          "status": rng.choice(STATUSES, len(add_c))})
    snaps = pd.concat([s[~late], s_late, s_new], ignore_index=True).drop_duplicates(
        ["customer_id", "snapshot_date"], keep="first")

    late = sp.as_of > cut
    p_late = sp[late].copy()
    redo = rng.random(len(p_late)) < 0.6
    vals = rng.integers(0, 400, int(redo.sum())).astype("float64")
    vals[rng.random(len(vals)) < 0.4] = np.nan
    p_late.loc[redo, "app_minutes_7d"] = vals
    dropped = p_late[rng.random(len(p_late)) < 0.2][["customer_id", "as_of"]]
    p_late = p_late.merge(dropped.assign(_drop=1), on=["customer_id", "as_of"], how="left")
    p_late = p_late[p_late._drop.isna()].drop(columns="_drop")
    add_c = rng.choice(ids, len(p_late) // 6 + 1)
    t = times_after(add_c, cut + 1)
    batch = rng.random(len(t)) < 0.5
    t[batch] = t[batch] - t[batch] % DAY + 6 * 3600
    p_new = pd.DataFrame({"customer_id": add_c, "as_of": t, "trigger": np.where(batch, "batch", "ticket"),
                          "app_minutes_7d": np.where(rng.random(len(t)) < 0.3, np.nan,
                                                     rng.integers(0, 400, len(t)).astype("float64"))})
    p_new = p_new[(p_new.as_of > cut) & (p_new.as_of < END)
                  & (p_new.as_of > p_new.customer_id.map(signup))]
    points = pd.concat([sp[~late], p_late, p_new], ignore_index=True).drop_duplicates(
        ["customer_id", "as_of"], keep="first")

    # Same layout as the extract: a ticket-trigger point is scored at its ticket's opened_at. Kept, new and at-cut
    # ticket points whose ticket was dropped above (or never existed) get one, stamped at their as_of (>= the cut).
    tp = points[(points.trigger == "ticket") & (points.as_of >= cut)][["customer_id", "as_of"]]
    has = tickets[["customer_id", "opened_at"]].rename(columns={"opened_at": "as_of"}).drop_duplicates()
    miss = tp.merge(has.assign(_has=1), on=["customer_id", "as_of"], how="left")
    miss = miss[miss._has.isna()]
    t_add = pd.DataFrame({"ticket_id": int(tickets.ticket_id.max()) + 1 + np.arange(len(miss)),
                          "customer_id": miss.customer_id.to_numpy(), "opened_at": miss.as_of.to_numpy(),
                          "topic": rng.choice(TOPICS, len(miss))})
    tickets = pd.concat([tickets, t_add], ignore_index=True)

    lb = d["labels"]
    lb = lb.merge(dropped.assign(_drop=1), on=["customer_id", "as_of"], how="left")
    lb = lb[lb._drop.isna()].drop(columns="_drop")
    late = lb.label_available_at >= cut
    l_late = lb[late].copy()
    flip = rng.random(len(l_late)) < 0.5
    l_late.loc[flip, "churned_30d"] = 1 - l_late.loc[flip, "churned_30d"]
    l_late = l_late[rng.random(len(l_late)) >= 0.2]
    new_pts = points.merge(lb[["customer_id", "as_of"]].assign(_has=1), on=["customer_id", "as_of"], how="left")
    new_pts = new_pts[new_pts._has.isna() & (new_pts.as_of > cut)]
    new_pts = new_pts[rng.random(len(new_pts)) < 0.7]
    l_new = pd.DataFrame({"customer_id": new_pts.customer_id.to_numpy(), "as_of": new_pts.as_of.to_numpy(),
                          "churned_30d": (rng.random(len(new_pts)) < 0.1).astype("int64"),
                          "label_available_at": new_pts.as_of.to_numpy() + rng.integers(3600, 40 * DAY, len(new_pts))})
    l_new = l_new[l_new.label_available_at < END]
    labels = pd.concat([lb[~late], l_late, l_new], ignore_index=True)

    return {"customers": customers, "scoring_points": points, "orders": orders, "tickets": tickets,
            "status_snapshots": snaps, "labels": labels}

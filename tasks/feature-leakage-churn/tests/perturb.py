"""Check B's perturbed extracts: change everything the warehouse did not yet hold at a cut time, keep the rest.

Rewritten 2026-10-31 for the scheduler's records in each extract's `_ops/` folder (ops_io.py reads and writes them).
A row is held at the cut iff the commit that made it visible is before the cut: for orders, order_visible_at below
(the records' rule: an order placed before the move day was read in the legacy table, from the commit of the
committed legacy_orders range holding it; a later order from its own load's commit, never before the rename that
made orders_new the table named `orders`); for every other table, its `_loaded_at`. A scoring point is kept iff its
`as_of` is at or before the cut. Every prediction with as_of <= cut reads only rows committed before its as_of
(live/features.py, docs/WAREHOUSE.md), so its ten kept features must not change.
A record is a scheduler.log line (dated by its time) or a commits.jsonl object (dated by its `at`). The copy's task
frames are edited per record time and its counts recomputed from its own tables (ops_io.recount), so no count is
stale: every record dated before the cut is unchanged; a task that sent its transaction before the cut is unchanged
in every field, and the rows it selected, copied or wrote keep their number (none dropped, added or moved; the values
of those not visible at the cut may change); a task that started before the cut and sent after it keeps its start.
Changed, with the loaders' rules kept for every row that is changed or added:
- legacy_orders tasks that sent at or after the cut, except the runs of the dual run's first day and of the move
  day: 30% of outcomes flipped, each commit re-timed (after the cut, the analyze and the end after it, before the
  next run's start), each range re-derived from the commits before it; never changed (times, outcomes): those two
  runs, the backfill, every orders_hourly task, dq_checks, schema_migrations, label_job and crm_sync;
- orders not yet visible: amounts changed, 25% dropped where no task that sent before the cut selected or copied
  them; added orders only where no such task had selected them (before the cut) and after the cut, for every customer
  with a kept prediction in that window and some others; each added order gets its loader's load (placed before the
  dual run's first day: legacy_backfill at the backfill's commit; later: orders_hourly at the first committed hourly
  task whose range ends above it, else it is left out);
- tickets loaded at or after the cut: 50% of topics changed, 25% dropped (never the ticket of a ticket point); added
  tickets open after the cut (so the 1 to 30 s capture lag never decides a kept value), and one at every new ticket
  point;
- status_snapshots partitions not landed at the cut: 60% of open statuses rewritten; where the export sent at or
  after the cut, 20% of rows dropped and rows added (at most one per customer and date, none after a customer's
  cancelled row); every export that started at or after the cut re-timed with its partition (sometimes hours or days
  late, after later partitions), and one that would end at or after END left out with its rows;
- labels loaded at or after the cut: 50% flipped, 20% dropped, 30% re-timed, labels added for unlabelled predictions;
  a re-timed or added label commits with a committed label_job task that started after its outcome was known and
  after the cut (the first such task, or one or two later), else it is left out;
- plan_changes applied at or after the cut: 50% of new plans changed, 25% dropped, changes added at crm_sync tasks
  that sent at or after the cut (some made before the cut and waiting for the next sync, for customers with a kept
  prediction since the previous sync's start), each made after the previous sync's start and before its own; then
  every customer's chain is re-derived (the first old_plan is the sign-up plan, each old_plan the plan before it,
  customers.plan the last new_plan) and _updated_at covers the last applied change;
- customers: last_login_at rewritten for half of the customers, each by a crm_sync that sent at or after the cut and
  started after the login; 60 new customers who sign up after the cut, with activity only after it;
- scoring points after the cut: 60% of app readings rewritten (40% of those blank), 20% dropped with their labels,
  new ones added (batch at 06:00:00 on the weekday of the customer's batch points, else a weekday drawn per point;
  ticket points with their ticket), none on a commit's second or between a transaction's sent line and its commit.
The tasks that sent at or after the cut get new transaction numbers after the kept ones, in (sent_at, job, run)
order. Never changed: every row visible before the cut, every scoring point at or before it, signup_at,
postcode_district and the sign-up plan of every customer. Every added or re-timed commit is after the cut, and every
task ends before END. invariants.py checks all of this on every copy.
Deterministic for a given (extract, cut, seed): numpy PCG64 with a fixed seed, pinned numpy and pandas.
"""
import numpy as np
import pandas as pd

import ops_io as OPS

DAY, HOUR, MINUTE = 86400, 3600, 60
END = 1772668800             # 2026-03-05T00:00:00Z: every extract is the warehouse at this moment
OPEN_STATUSES = np.array(["active", "paused", "payment_failed"])
PLANS = np.array(["basic", "plus", "family"])
TOPICS = np.array(["delivery", "quality", "account", "billing"])
N_NEW_CUSTOMERS = 60
LEGACY_FLIP = 0.3            # share of the re-timed legacy_orders tasks whose outcome is flipped
ANALYZE_LONG_P = 0.10        # share of re-timed legacy commits whose analyze runs 3 to 5 hours (as the build's)
WINDOW = 30 * DAY            # orders are added before the cut only in its last 30 days
RENAME_TO_ORDERS = "ALTER TABLE orders_new RENAME TO orders"
NA = np.iinfo(np.int64).max  # a missing time or count in the int64 arrays below
SELECTING_JOBS = ("legacy_orders", "orders_hourly", "legacy_backfill")


# ------------------------------------------------------------------ what the records say
def _int(col):
    """An int64 or Int64 column as an int64 array, missing values as NA."""
    return pd.array(col, dtype="Int64").to_numpy(dtype=np.int64, na_value=NA)


def _str(col):
    """A string column as an object array, missing values as ''."""
    return np.array(["" if (v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v))) else str(v)
                     for v in col.tolist()], dtype=object)


def _job(tasks, job):
    return tasks[(_str(tasks["job"]) == job)]


def ops_facts(tasks):
    """The migration's fixed points, read from the records (epoch seconds): d0, the dual run's first day (the bound of
    the backfill's copy); c, the move day (the bound of the last legacy_orders range); backfill_at, its commit;
    cutover_at and cutover_started, the committed schema_migrations task that renamed orders_new to orders;
    first_post_at, the first orders_hourly commit into `orders`."""
    leg, bf = _job(tasks, "legacy_orders"), _job(tasks, "legacy_backfill")
    if len(leg) == 0 or len(bf) != 1:
        raise ValueError(f"expected legacy_orders tasks and one legacy_backfill, found {len(leg)} and {len(bf)}")
    sm = _job(tasks, "schema_migrations")
    ren = [i for i, (stm, out) in enumerate(zip(_str(sm["statements"]).tolist(), _str(sm["outcome"]).tolist()))
           if out == "commit" and RENAME_TO_ORDERS in stm.split("; ")]
    if len(ren) != 1:
        raise ValueError(f"expected one committed rename of orders_new to orders, found {len(ren)}")
    x = sm.iloc[ren[0]]
    hr = _job(tasks, "orders_hourly")
    post = _int(hr["at"])[(_str(hr["table"]) == "orders") & (_str(hr["outcome"]) == "commit")]
    return {"d0": int(_int(bf["hi"])[0]), "c": int(_int(leg["hi"]).max()), "backfill_at": int(_int(bf["at"])[0]),
            "cutover_at": int(x["at"]), "cutover_started": int(x["started_at"]),
            "first_post_at": int(post.min()) if len(post) else None}


def committed_ats(tasks, job):
    """The sorted commit times of a job's committed transactions."""
    t = _job(tasks, job)
    return np.sort(_int(t["at"])[_str(t["outcome"]) == "commit"])


def order_visible_at(orders, tasks):
    """Per order: the commit that made it visible to a query on `orders` (epoch seconds), from the records."""
    f = ops_facts(tasks)
    leg = _job(tasks, "legacy_orders")
    ok = _str(leg["outcome"]) == "commit"
    lo, hi, at = _int(leg["lo"])[ok], _int(leg["hi"])[ok], _int(leg["at"])[ok]
    o = np.argsort(hi, kind="mergesort")
    lo, hi, at = lo[o], hi[o], at[o]
    x = orders["ordered_at"].to_numpy(dtype=np.int64)
    vis = np.maximum(orders["_loaded_at"].to_numpy(dtype=np.int64), np.int64(f["cutover_at"]))
    old = x < f["c"]
    j = np.searchsorted(hi, x[old], side="right")
    if len(hi) == 0 or (j >= len(hi)).any() or (lo[np.minimum(j, len(hi) - 1)] > x[old]).any():
        raise ValueError("an order placed before the move day lies in no committed legacy_orders range")
    vis[old] = at[j]
    return vis


def sync_commits(d):
    """The commit times of the crm_sync transactions the records show."""
    return committed_ats(d["_ops"]["tasks"], "crm_sync")


def signup_plans(customers, plan_changes):
    """customer_id -> the plan chosen at sign-up: the earliest change's old_plan, else the record's plan."""
    first = plan_changes.sort_values(["customer_id", "changed_at"], kind="mergesort").drop_duplicates("customer_id")
    p = customers["customer_id"].map(first.set_index("customer_id")["old_plan"])
    p = p.where(p.notna(), customers["plan"])
    return dict(zip(customers["customer_id"].tolist(), p.tolist()))


# ------------------------------------------------------------------ helpers
def _uniform(rng, lo, hi):
    """One integer in [lo, hi) per pair (lo < hi required)."""
    lo, hi = np.asarray(lo, dtype=np.int64), np.asarray(hi, dtype=np.int64)
    return lo + np.floor(rng.random(len(lo)) * (hi - lo)).astype(np.int64)


def _partition_commit(dates, rng):
    """A billing_export commit for partitions dated `dates`: mostly 06:27 to 06:45 on D+1, some hours later, some
    after the next day's partition."""
    dates = np.asarray(dates, dtype=np.int64)
    n = len(dates)
    u = rng.random(n)
    base = dates + DAY + 6 * HOUR + 27 * MINUTE + rng.integers(0, 18 * MINUTE + 1, n)
    late = dates + DAY + rng.integers(9 * HOUR, 29 * HOUR, n)
    ooo = dates + 2 * DAY + rng.integers(7 * HOUR, 36 * HOUR, n)
    return np.where(u < 0.9, base, np.where(u < 0.95, late, ooo))


def _covered(x, los, his):
    """Per value of x: inside one of the half-open ranges [los, his)."""
    x = np.asarray(x, dtype=np.int64)
    if len(los) == 0:
        return np.zeros(len(x), dtype=bool)
    o = np.argsort(los, kind="mergesort")
    a, reach = np.asarray(los, dtype=np.int64)[o], np.maximum.accumulate(np.asarray(his, dtype=np.int64)[o])
    j = np.searchsorted(a, x, side="right") - 1
    return (j >= 0) & (reach[np.maximum(j, 0)] > x)


def _free_spans(lo_w, hi_w, los, his):
    """[lo_w, hi_w) less the union of the ranges [los, his): the free spans, in time order."""
    spans, cur = [], int(lo_w)
    o = np.argsort(los, kind="mergesort")
    for a, b in zip(np.asarray(los, dtype=np.int64)[o].tolist(), np.asarray(his, dtype=np.int64)[o].tolist()):
        if b <= cur:
            continue
        if a >= hi_w:
            break
        if a > cur:
            spans.append((cur, min(a, int(hi_w))))
        cur = max(cur, b)
        if cur >= hi_w:
            break
    if cur < hi_w:
        spans.append((cur, int(hi_w)))
    return spans


def _away(t, pts):
    """Move commit times off the seconds of scoring points (one second later until none is on one)."""
    t = np.asarray(t, dtype=np.int64).copy()
    for _ in range(1000):
        bad = np.isin(t, pts)
        if not bad.any():
            return t
        t[bad] += 1
    raise ValueError("a commit could not be moved off the scoring seconds")


def _sent_for(at, s, pts):
    """The sent line of a transaction committed at `at`: s seconds before it, or the latest scoring point before it
    when that is later, so no scoring point lies between the sent line and the commit."""
    j = np.searchsorted(pts, at, side="left") - 1
    last = np.where(j >= 0, pts[np.maximum(j, 0)], np.int64(-1))
    return np.maximum(at - s, last)


def _nth_after(starts, ats, need, k):
    """For each need time: the commit of the (k+1)-th task (sorted by start) that started after it, or NA."""
    j = np.searchsorted(starts, need, side="right") + k
    return np.where(j < len(starts), ats[np.minimum(j, len(starts) - 1)], NA)


# ------------------------------------------------------------------ the perturbation
def perturb(d, cut, seed):
    rng = np.random.default_rng(seed)
    cut = int(cut)
    tasks, parity = d["_ops"]["tasks"], d["_ops"]["parity"]
    f = ops_facts(tasks)
    d0, move0 = f["d0"], f["c"]
    job, run = _str(tasks["job"]), _str(tasks["run"])
    started, ended = tasks["started_at"].to_numpy(dtype=np.int64), tasks["end_at"].to_numpy(dtype=np.int64)
    sent, at, lo, hi = _int(tasks["sent_at"]), _int(tasks["at"]), _int(tasks["lo"]), _int(tasks["hi"])
    analyze, txn = _int(tasks["analyze_at"]), _int(tasks["txn"])
    outcome, state = _str(tasks["outcome"]), _str(tasks["state"])
    has_txn = sent != NA
    pre = has_txn & (sent < cut)                          # sent before the cut: unchanged in every field
    committed = outcome == "commit"
    # every order a task that sent before the cut selected (LOAD) or copied (COPY); the dual run's orders are in two
    sel = pre & np.isin(job, SELECTING_JOBS)
    sel_lo = np.where(job[sel] == "legacy_backfill", np.int64(-(2 ** 62)), lo[sel])
    sel_hi = hi[sel]

    def tasks_of(name, commit_only=True):
        m = (job == name) & (committed if commit_only else True)
        i = np.flatnonzero(m)
        return i[np.argsort(started[i], kind="mergesort")]

    syncs = tasks_of("crm_sync")                          # every crm_sync task, by start
    post_syncs = syncs[~pre[syncs]]                       # those that sent at or after the cut
    cu = d["customers"]
    plan0 = signup_plans(cu, d["plan_changes"])
    signup = dict(zip(cu["customer_id"].tolist(), cu["signup_at"].tolist()))

    # ---- 60 new customers, signed up after the cut
    hi_su = END - 30 * DAY if END - 30 * DAY > cut + DAY else END - DAY
    n_new = N_NEW_CUSTOMERS if hi_su > cut + 1 else 0
    new_ids = int(cu["customer_id"].max()) + 1 + np.arange(n_new, dtype=np.int64)
    new_signup = rng.integers(cut + 1, max(hi_su, cut + 2), n_new).astype(np.int64)
    districts = np.array(sorted(cu["postcode_district"].unique().tolist()), dtype=object)
    new_cu = pd.DataFrame({"customer_id": new_ids, "signup_at": new_signup,
                           "plan": rng.choice(PLANS, n_new).astype(object),
                           "postcode_district": rng.choice(districts, n_new)})
    for c, s in zip(new_ids.tolist(), new_signup.tolist()):
        signup[c] = s
        plan0[c] = None
    plan0.update(zip(new_ids.tolist(), new_cu["plan"].tolist()))
    all_ids = np.concatenate([cu["customer_id"].to_numpy(dtype=np.int64), new_ids])

    def after_signup(cids, lo_, hi_):
        """For customers cids: one time in (max(lo_, signup), hi_), or -1 where that span is empty."""
        cids = np.asarray(cids, dtype=np.int64)
        lo_c = np.maximum(np.int64(lo_), np.array([signup[c] for c in cids.tolist()], dtype=np.int64)) + 1
        ok = lo_c < hi_
        t = np.full(len(cids), -1, dtype=np.int64)
        t[ok] = _uniform(rng, lo_c[ok], np.full(int(ok.sum()), hi_, dtype=np.int64))
        return t

    # a new scoring point never lies on a commit's second or between a sent line and its commit
    w_sent, w_at = sent[has_txn], at[has_txn]
    w_o = np.argsort(w_sent, kind="mergesort")
    w_sent, w_reach = w_sent[w_o], np.maximum.accumulate(w_at[w_o])

    def busy(t):
        j = np.searchsorted(w_sent, t, side="left") - 1
        return (j >= 0) & (w_reach[np.maximum(j, 0)] >= t)

    # ---- scoring points
    sp = d["scoring_points"]
    keep_p = sp[sp["as_of"] <= cut]
    late_p = sp[sp["as_of"] > cut].copy()
    redo = rng.random(len(late_p)) < 0.6
    vals = rng.integers(0, 400, int(redo.sum())).astype("float64")
    vals[rng.random(len(vals)) < 0.4] = np.nan
    late_p.loc[redo, "app_minutes_7d"] = vals
    drop = rng.random(len(late_p)) < 0.2
    dropped_keys = set(zip(late_p.loc[drop, "customer_id"].tolist(), late_p.loc[drop, "as_of"].tolist()))
    late_p = late_p[~drop]
    batch_rows = sp[sp["trigger"] == "batch"]
    weekday = dict(zip(batch_rows["customer_id"].tolist(), (batch_rows["as_of"] // DAY % 7).tolist()))
    add_c = rng.choice(all_ids, len(late_p) // 6 + 1)
    t = after_signup(add_c, cut, END - HOUR)
    is_batch = rng.random(len(add_c)) < 0.5
    wd = np.array([weekday.get(c, -1) for c in add_c.tolist()], dtype=np.int64)
    wd = np.where(wd < 0, rng.integers(0, 7, len(add_c)), wd)
    day = t // DAY
    day = day + (wd - day) % 7
    t = np.where(is_batch, day * DAY + 6 * HOUR, t)
    new_p = pd.DataFrame({"customer_id": add_c, "as_of": t, "trigger": np.where(is_batch, "batch", "ticket"),
                          "app_minutes_7d": np.where(rng.random(len(t)) < 0.3, np.nan,
                                                     rng.integers(0, 400, len(t)).astype("float64"))})
    su = new_p["customer_id"].map(signup)
    new_p = new_p[(t > 0) & (new_p["as_of"] > cut) & (new_p["as_of"] < END) & (new_p["as_of"] > su) & ~busy(t)]
    points = pd.concat([keep_p, late_p, new_p], ignore_index=True).drop_duplicates(["customer_id", "as_of"],
                                                                                  keep="first")
    points = points.reset_index(drop=True)
    kept_pts = points[points["as_of"] <= cut]
    pts = np.unique(points["as_of"].to_numpy(dtype=np.int64))

    # ---- legacy_orders tasks that sent at or after the cut (but the dual run's first day and the move day)
    L = np.flatnonzero(job == "legacy_orders")
    L = L[np.argsort(hi[L], kind="mergesort")]
    fixed = (hi[L] == d0) | (hi[L] == move0)
    change = ~pre[L] & ~fixed
    out_l = outcome[L].copy()
    flip = change & (rng.random(len(L)) < LEGACY_FLIP)
    out_l[flip] = np.where(out_l[flip] == "commit", "rollback", "commit")
    ci = L[change]
    k = len(ci)
    ok_new = out_l[change] == "commit"
    dur = np.where(~ok_new, rng.integers(4 * MINUTE, 40 * MINUTE + 1, k),
                   np.where(rng.random(k) < 0.1, rng.integers(int(3.6 * HOUR), 8 * HOUR + 1, k),
                            rng.integers(15 * MINUTE, 55 * MINUTE + 1, k)))
    l_at = _away(np.maximum(started[ci] + dur, cut + rng.integers(30, 601, k)), pts)
    l_sent = _sent_for(l_at, rng.integers(1, 21, k), pts)
    a_lag = rng.integers(1, 11, k)
    d_lag = np.where(rng.random(k) < ANALYZE_LONG_P, rng.integers(3 * HOUR, 5 * HOUR + 1, k),
                     rng.integers(5 * MINUTE, 40 * MINUTE + 1, k))
    l_an = np.where(ok_new, l_at + a_lag, NA)
    l_end = np.where(ok_new, l_at + a_lag + d_lag, l_at + rng.integers(1, 6, k))
    nxt = np.append(started[L][1:], END)[change]          # the next legacy run's start
    l_end = np.minimum(l_end, nxt - 1)
    if not ((l_sent > started[ci]) & (l_sent >= cut) & (l_end > np.where(ok_new, l_an, l_at))).all():
        raise ValueError("a re-timed legacy_orders task does not fit before the next run's start")
    outcome_new = tasks["outcome"].to_numpy(dtype=object).copy()   # untouched rows keep their exact values
    state_new = tasks["state"].to_numpy(dtype=object).copy()
    sent_new, at_new, an_new, end_new = sent.copy(), at.copy(), analyze.copy(), ended.copy()
    outcome_new[ci] = out_l[change]
    state_new[ci] = np.where(ok_new, "success", "failed")
    sent_new[ci], at_new[ci], an_new[ci], end_new[ci] = l_sent, l_at, l_an, l_end
    lo_new = lo.copy()
    last = lo[L[0]]                                       # the first range starts at the simulation's start
    for i, ti in enumerate(L.tolist()):                   # each range starts at the last committed bound before it
        lo_new[ti] = last
        if out_l[i] == "commit":
            last = hi[ti]
    if (lo_new[L][pre[L]] != lo[L][pre[L]]).any():
        raise ValueError("a legacy_orders task that sent before the cut changed its range")

    # ---- orders
    o = d["orders"]
    vis = order_visible_at(o, tasks)
    keep_o = o[vis < cut]
    late_o = o[vis >= cut].copy()
    late_o["amount_cents"] = np.maximum(1, np.round(late_o["amount_cents"].to_numpy(dtype="float64")
                                                    * rng.uniform(0.2, 3.0, len(late_o)))).astype(np.int64)
    held_sel = _covered(late_o["ordered_at"].to_numpy(dtype=np.int64), sel_lo, sel_hi)
    late_o = late_o[held_sel | (rng.random(len(late_o)) >= 0.25)]
    add_c = rng.choice(all_ids, len(late_o) // 3 + 1)
    ot = after_signup(add_c, cut, END - HOUR)
    box = rng.random(len(ot)) < 0.3
    charge = ot // DAY * DAY + 5 * HOUR + 30 * MINUTE                  # a box is charged at 05:30
    su_o = np.array([signup[c] for c in add_c.tolist()], dtype=np.int64)
    box &= (ot > 0) & (charge > cut) & (charge > su_o)
    ot = np.where(box, charge, ot)
    kinds = [np.where(box, "box", "addon")]
    amounts = [rng.integers(499, 9000, len(ot))]
    o_cust, o_time = [add_c], [ot]
    windows = []
    for a_, b_ in _free_spans(max(cut - WINDOW, 0), cut, sel_lo, sel_hi):
        for x0, x1, span in ((a_, min(b_, d0), DAY), (max(a_, d0), b_, HOUR)):
            if x0 < x1:
                windows.append((x0, x1, span))
    for lo_w, hi_w, span in windows:
        # every customer with a kept prediction inside the window: two orders placed before that prediction, one of
        # them in the window's first day (legacy loads) or hour (hourly loads), the earliest a schedule would expect
        w = kept_pts[(kept_pts["as_of"] > lo_w)].groupby("customer_id", sort=True)["as_of"].max()
        cids = w.index.to_numpy(dtype=np.int64)
        top = np.minimum(w.to_numpy(dtype=np.int64), hi_w)
        su_w = np.array([signup[c] for c in cids.tolist()], dtype=np.int64) + 1
        lo_c = np.maximum(lo_w, su_w)
        ok = lo_c < top
        cids, top, lo_c = cids[ok], top[ok], lo_c[ok]
        first = np.minimum(top, np.maximum(lo_c + 1, lo_w + span))
        o_cust += [cids, cids]
        o_time += [_uniform(rng, lo_c, top), _uniform(rng, lo_c, first)]
        rand_c = rng.choice(cu["customer_id"].to_numpy(dtype=np.int64), 40)
        rt = after_signup(rand_c, lo_w - 1, hi_w)
        o_cust.append(rand_c)
        o_time.append(rt)
        n_w = 2 * len(cids) + len(rand_c)
        kinds.append(np.full(n_w, "addon"))
        amounts.append(rng.integers(499, 3000, n_w))
    o_cust, o_time = np.concatenate(o_cust), np.concatenate(o_time)
    kinds, amounts = np.concatenate(kinds), np.concatenate(amounts).astype(np.int64)
    good = (o_time > 0) & ~_covered(o_time, sel_lo, sel_hi)
    o_cust, o_time, kinds, amounts = o_cust[good], o_time[good], kinds[good], amounts[good]
    hr_ok = tasks_of("orders_hourly")
    hr_ok = hr_ok[np.argsort(hi[hr_ok], kind="mergesort")]
    hr_hi, hr_at = hi[hr_ok], at[hr_ok]
    legacy = o_time < d0
    j = np.searchsorted(hr_hi, o_time, side="right")
    good = legacy | (j < len(hr_hi))
    loaded = np.where(legacy, f["backfill_at"], hr_at[np.minimum(j, len(hr_hi) - 1)])
    new_o = pd.DataFrame({"customer_id": o_cust, "ordered_at": o_time, "kind": kinds, "amount_cents": amounts,
                          "_load_job": np.where(legacy, "legacy_backfill", "orders_hourly"),
                          "_loaded_at": loaded})[good]
    new_o.insert(0, "order_id", int(o["order_id"].max()) + 1 + np.arange(len(new_o), dtype=np.int64))
    orders = pd.concat([keep_o, late_o, new_o], ignore_index=True)

    # ---- tickets
    k_ = d["tickets"]
    tp = points[points["trigger"] == "ticket"]
    tp_keys = set(zip(tp["customer_id"].tolist(), tp["as_of"].tolist()))
    tp_keys |= set(zip(sp.loc[sp["trigger"] == "ticket", "customer_id"].tolist(),
                       sp.loc[sp["trigger"] == "ticket", "as_of"].tolist()))
    keep_k = k_[k_["_loaded_at"] < cut]
    late_k = k_[k_["_loaded_at"] >= cut].copy()
    prot = np.array([(c, a) in tp_keys for c, a in zip(late_k["customer_id"].tolist(),
                                                         late_k["opened_at"].tolist())], dtype=bool)
    flip_k = rng.random(len(late_k)) < 0.5
    late_k.loc[flip_k, "topic"] = rng.choice(TOPICS, int(flip_k.sum()))
    late_k = late_k[prot | (rng.random(len(late_k)) >= 0.25)]
    add_c = rng.choice(all_ids, len(late_k) // 3 + 1)
    kt = after_signup(add_c, cut, END - MINUTE)
    new_k = pd.DataFrame({"customer_id": add_c, "opened_at": kt})[kt > 0]
    have = set(zip(pd.concat([keep_k, late_k])["customer_id"].tolist(),
                   pd.concat([keep_k, late_k])["opened_at"].tolist()))
    miss = [(c, a) for c, a in zip(tp["customer_id"].tolist(), tp["as_of"].tolist()) if (c, a) not in have]
    if miss:
        new_k = pd.concat([new_k, pd.DataFrame(miss, columns=["customer_id", "opened_at"])], ignore_index=True)
    new_k = new_k.drop_duplicates(["customer_id", "opened_at"])
    new_k = new_k[~np.array([(c, a) in have for c, a in zip(new_k["customer_id"].tolist(),
                                                              new_k["opened_at"].tolist())], dtype=bool)]
    new_k["topic"] = rng.choice(TOPICS, len(new_k))
    new_k["_loaded_at"] = new_k["opened_at"].to_numpy(dtype=np.int64) + rng.integers(1, 31, len(new_k))
    new_k.insert(0, "ticket_id", int(k_["ticket_id"].max()) + 1 + np.arange(len(new_k), dtype=np.int64))
    tickets = pd.concat([keep_k, late_k, new_k[k_.columns]], ignore_index=True)

    # ---- status snapshots: partitions not landed at the cut (one billing_export task per partition date)
    ex = np.flatnonzero(job == "billing_export")
    ex_date = np.array(run[ex].tolist(), dtype="datetime64[D]").astype(np.int64) * DAY
    free_dates = set(ex_date[~pre[ex]].tolist())          # exports that sent at or after the cut
    s = d["status_snapshots"]
    keep_s = s[s["_loaded_at"] < cut]
    late_s = s[s["_loaded_at"] >= cut].copy()
    open_row = (late_s["status"] != "cancelled").to_numpy()
    rew = open_row & (rng.random(len(late_s)) < 0.6)
    late_s.loc[rew, "status"] = rng.choice(OPEN_STATUSES, int(rew.sum()))
    in_free = late_s["snapshot_date"].isin(free_dates).to_numpy()
    late_s = late_s[~in_free | (rng.random(len(late_s)) >= 0.2)]
    dates = np.array(sorted(free_dates), dtype=np.int64)
    if len(dates):
        add_c = rng.choice(all_ids, len(all_ids) // 3)
        add_d = dates[rng.integers(0, len(dates), len(add_c))]
        su_day = np.array([signup[c] // DAY * DAY for c in add_c.tolist()], dtype=np.int64)
        okd = add_d >= su_day
        s_new = pd.DataFrame({"customer_id": add_c[okd], "snapshot_date": add_d[okd],
                              "status": rng.choice(OPEN_STATUSES, int(okd.sum()))})
    else:
        s_new = pd.DataFrame({"customer_id": [], "snapshot_date": [], "status": []})
    s_signup = pd.DataFrame({"customer_id": new_ids, "snapshot_date": new_signup // DAY * DAY,
                             "status": np.full(n_new, "active")})
    s_signup = s_signup[s_signup["snapshot_date"].isin(free_dates)]
    snaps = pd.concat([keep_s, late_s, s_new, s_signup], ignore_index=True)
    snaps["customer_id"] = snaps["customer_id"].astype(np.int64)
    snaps["snapshot_date"] = snaps["snapshot_date"].astype(np.int64)
    snaps = snaps.drop_duplicates(["customer_id", "snapshot_date"], keep="first")
    first_cancel = snaps[snaps["status"] == "cancelled"].groupby("customer_id")["snapshot_date"].min()
    fc = snaps["customer_id"].map(first_cancel).to_numpy(dtype="float64")
    is_pre = (snaps["_loaded_at"].notna() & (snaps["_loaded_at"].fillna(END) < cut)).to_numpy()
    snaps = snaps[is_pre | np.isnan(fc) | (snaps["snapshot_date"].to_numpy() <= fc)].copy()
    # the exports that started at or after the cut, re-timed with their partition; one past END goes with its rows
    rt = ex[(~pre[ex]) & (started[ex] >= cut)]
    rt_date = ex_date[(~pre[ex]) & (started[ex] >= cut)]
    new_at = _partition_commit(rt_date, rng)
    new_at = _away(np.maximum(new_at, cut + rng.integers(10 * MINUTE, 15 * MINUTE + 1, len(rt))), pts)
    shift = new_at - at[rt]
    started_new = started.copy()
    started_new[rt] = started[rt] + shift
    sent_new[rt] = _sent_for(new_at, at[rt] - sent[rt], pts)
    at_new[rt] = new_at
    end_new[rt] = ended[rt] + shift
    if not ((started_new[rt] >= cut) & (sent_new[rt] > started_new[rt])).all():
        raise ValueError("a re-timed billing_export task starts before the cut")
    keep_task = np.ones(len(tasks), dtype=bool)
    keep_task[rt[end_new[rt] >= END]] = False
    part_at = dict(zip(ex_date[keep_task[ex]].tolist(), at_new[ex][keep_task[ex]].tolist()))
    is_pre = (snaps["_loaded_at"].notna() & (snaps["_loaded_at"].fillna(END) < cut)).to_numpy()
    new_load = snaps["snapshot_date"].map(part_at).to_numpy(dtype="float64")
    loaded = np.where(is_pre, snaps["_loaded_at"].fillna(0).to_numpy(dtype="float64"), new_load)
    snaps = snaps[~np.isnan(loaded)].copy()
    snaps["_loaded_at"] = loaded[~np.isnan(loaded)].astype(np.int64)

    # ---- labels: each commits with a committed label_job task
    lt = tasks_of("label_job")
    lt_start, lt_at, lt_pre = started[lt], at[lt], pre[lt]
    task_of_at = {a: i for i, a in enumerate(lt_at.tolist())}
    lb = d["labels"]
    lb = lb[[(c, a) not in dropped_keys for c, a in zip(lb["customer_id"].tolist(), lb["as_of"].tolist())]]
    keep_l = lb[lb["_loaded_at"] < cut]
    late_l = lb[lb["_loaded_at"] >= cut].copy()
    ti = np.array([task_of_at[a] for a in late_l["_loaded_at"].tolist()], dtype=np.int64)
    y0 = late_l["churned_30d"].to_numpy(dtype=np.int64)
    a_l = late_l["as_of"].to_numpy(dtype=np.int64)

    def known(y, a):
        return np.where(y == 0, a + 30 * DAY, a + HOUR)

    flip_l = rng.random(len(late_l)) < 0.5
    y = np.where(flip_l, 1 - y0, y0)
    prot_l = lt_pre[ti]                                   # its task sent before the cut: kept, values may change
    y = np.where(prot_l & (lt_start[ti] <= known(y, a_l)), y0, y)
    keep = prot_l | (rng.random(len(late_l)) >= 0.2)
    late_l, y, ti, prot_l, a_l = late_l[keep], y[keep], ti[keep], prot_l[keep], a_l[keep]
    late_l["churned_30d"] = y
    retime = ~prot_l & ((rng.random(len(late_l)) < 0.3) | (lt_start[ti] <= known(y, a_l)))
    need = np.maximum(known(y, a_l), cut)
    cur = np.where(retime, _nth_after(lt_start, lt_at, need, rng.choice([0, 0, 0, 1, 2], len(late_l))),
                   late_l["_loaded_at"].to_numpy(dtype=np.int64))
    late_l["_loaded_at"] = cur
    late_l = late_l[cur != NA]
    have = set(zip(pd.concat([keep_l, late_l])["customer_id"].tolist(), pd.concat([keep_l, late_l])["as_of"].tolist()))
    cand = points[[(c, a_) not in have for c, a_ in zip(points["customer_id"].tolist(), points["as_of"].tolist())]]
    cand = cand[rng.random(len(cand)) < 0.7]
    ny = (rng.random(len(cand)) < 0.1).astype(np.int64)
    na_ = cand["as_of"].to_numpy(dtype=np.int64)
    nl = _nth_after(lt_start, lt_at, np.maximum(known(ny, na_), cut), rng.choice([0, 0, 0, 1, 2], len(cand)))
    l_new = pd.DataFrame({"customer_id": cand["customer_id"].to_numpy(dtype=np.int64), "as_of": na_,
                          "churned_30d": ny, "_loaded_at": nl})[nl != NA]
    labels = pd.concat([keep_l, late_l, l_new], ignore_index=True)

    # ---- plan changes applied at or after the cut, then the chains
    sy_start, sy_at = started[syncs], at[syncs]
    sy_of_at = {a: i for i, a in enumerate(sy_at.tolist())}
    pcg = d["plan_changes"]
    keep_c = pcg[pcg["_loaded_at"] < cut]
    late_c = pcg[pcg["_loaded_at"] >= cut].copy()
    prot_c = np.array([pre[syncs[sy_of_at[a]]] for a in late_c["_loaded_at"].tolist()], dtype=bool)
    late_c = late_c[prot_c | (rng.random(len(late_c)) >= 0.25)]
    chg = rng.random(len(late_c)) < 0.5
    late_c.loc[chg, "new_plan"] = rng.choice(PLANS, int(chg.sum()))
    add_rows = []
    if len(post_syncs):
        first = int(np.flatnonzero(syncs == post_syncs[0])[0])
        prev_start = int(sy_start[first - 1]) if first > 0 else cut - 7 * DAY
        s_first, a_first = int(sy_start[first]), int(sy_at[first])
        # changes made before the cut, waiting for the next sync, for customers with a kept prediction since the
        # previous sync's start: made before that prediction
        w = kept_pts[kept_pts["as_of"] > prev_start].groupby("customer_id", sort=True)["as_of"].max()
        for c, a_ in zip(w.index.tolist(), w.tolist()):
            lo_ = max(prev_start, signup[c]) + 1
            hi_ = min(a_, s_first)
            if lo_ < hi_ and rng.random() < 0.5:
                add_rows.append((c, int(rng.integers(lo_, hi_)), a_first))
        # and changes at later syncs, for random customers: made after the previous sync's start, before its own
        for c in rng.choice(all_ids, max(20, len(late_c) // 3)).tolist():
            i = first + int(rng.integers(0, len(post_syncs)))
            lo_ = max(int(sy_start[i - 1]) if i > 0 else cut - 7 * DAY, signup[c]) + 1
            hi_ = int(sy_start[i])
            if lo_ < hi_:
                add_rows.append((c, int(rng.integers(lo_, hi_)), int(sy_at[i])))
    add_ch = pd.DataFrame(add_rows, columns=["customer_id", "changed_at", "_loaded_at"])
    add_ch["old_plan"] = ""
    add_ch["new_plan"] = rng.choice(PLANS, len(add_ch))
    allc = pd.concat([keep_c.assign(_pre=True), late_c.assign(_pre=False), add_ch.assign(_pre=False)],
                     ignore_index=True).drop_duplicates(["customer_id", "changed_at"], keep="first")
    allc = allc.sort_values(["customer_id", "changed_at"], kind="mergesort").reset_index(drop=True)
    old, new = allc["old_plan"].to_numpy(dtype=object).copy(), allc["new_plan"].to_numpy(dtype=object).copy()
    pre_flag = allc["_pre"].to_numpy(dtype=bool)
    custs = allc["customer_id"].to_numpy(dtype=np.int64)
    prev_c, prev_plan = None, None
    for i in range(len(allc)):
        c = int(custs[i])
        if c != prev_c:
            prev_c, prev_plan = c, plan0[c]
        if not pre_flag[i]:
            old[i] = prev_plan
            if new[i] == old[i]:
                new[i] = rng.choice([p for p in PLANS.tolist() if p != old[i]])
        prev_plan = new[i]
    allc["old_plan"], allc["new_plan"] = old, new
    plan_changes = allc.drop(columns="_pre")
    last_new = plan_changes.groupby("customer_id", sort=False)["new_plan"].last()
    last_load = plan_changes.groupby("customer_id", sort=False)["_loaded_at"].max()

    # ---- customers: the record (plan, last login, _updated_at)
    cus = pd.concat([cu, new_cu.assign(last_login_at=pd.array([pd.NA] * n_new, dtype="Int64"),
                                       _updated_at=new_signup)], ignore_index=True)
    ids = cus["customer_id"].to_numpy(dtype=np.int64)
    plan = np.array([last_new.get(c, plan0[c]) for c in ids.tolist()], dtype=object)
    upd = cus["_updated_at"].to_numpy(dtype=np.int64).copy()
    login = cus["last_login_at"].astype("Int64").copy()
    login_v = login.to_numpy(dtype="float64", na_value=np.nan)
    is_new = np.isin(ids, new_ids)
    if len(post_syncs):
        # half of the existing customers: a login after the cut, written by the first later sync that started after
        # it; new customers: the sign-up session, written by the first sync after it (when there is one)
        ps_start, ps_at = started[post_syncs], at[post_syncs]
        pick = (~is_new) & (rng.random(len(ids)) < 0.5)
        pick |= is_new
        lo_g = np.where(is_new, cus["signup_at"].to_numpy(dtype=np.int64),
                        np.maximum(cut, cus["signup_at"].to_numpy(dtype=np.int64)) + 1)
        span = np.where(is_new, 3 * DAY, 30 * DAY)
        lg = lo_g + np.floor(rng.random(len(ids)) * span).astype(np.int64)
        js = np.searchsorted(ps_start, lg, side="right")
        pick &= js < len(ps_start)
        sk = ps_at[np.minimum(js, len(ps_start) - 1)]
        login_v = np.where(pick, lg.astype("float64"), login_v)
        upd = np.where(pick, np.maximum(np.where(is_new, 0, upd), sk), upd)
    ll = np.array([last_load.get(c, -1) for c in ids.tolist()], dtype=np.int64)
    upd = np.maximum(upd, ll)
    # a record a sync wrote holds a last login (the sign-up session counts as one)
    login_v = np.where(np.isnan(login_v) & (upd != cus["signup_at"].to_numpy(dtype=np.int64)),
                       cus["signup_at"].to_numpy(dtype="float64"), login_v)
    customers = pd.DataFrame({"customer_id": ids, "signup_at": cus["signup_at"].to_numpy(dtype=np.int64),
                              "plan": plan, "postcode_district": cus["postcode_district"].to_numpy(dtype=object),
                              "last_login_at": pd.array([pd.NA if np.isnan(v) else int(v) for v in login_v],
                                                        dtype="Int64"),
                              "_updated_at": upd.astype(np.int64)})
    # a new customer whose first change waits for a sync that never came stays without one (no change rows exist)
    tables = {"customers": customers, "plan_changes": plan_changes, "scoring_points": points, "orders": orders,
              "tickets": tickets, "status_snapshots": snaps, "labels": labels}

    # ---- the records: the edited task frame, new transaction numbers, every count from the copy's tables
    txn_new = txn.copy()
    renum = keep_task & has_txn & ~pre
    kept_txn = txn[keep_task & pre]
    base = int(kept_txn.max()) + 1 if len(kept_txn) else int(txn[has_txn].min())
    ri = np.flatnonzero(renum)
    order = pd.DataFrame({"s": sent_new[ri], "j": job[ri], "r": run[ri]}).sort_values(["s", "j", "r"],
                                                                                   kind="mergesort").index
    txn_new[ri[np.asarray(order)]] = base + np.arange(len(ri), dtype=np.int64)
    out = tasks.copy()
    for col, arr in (("lo", lo_new), ("sent_at", sent_new), ("at", at_new), ("analyze_at", an_new),
                     ("txn", txn_new)):
        v = pd.array(arr, dtype="Int64")
        v[arr == NA] = pd.NA
        out[col] = v
    out["started_at"], out["end_at"] = started_new, end_new
    out["outcome"] = pd.Series(outcome_new, index=out.index, dtype=object)
    out["state"] = pd.Series(state_new, index=out.index, dtype=object)
    out = out[keep_task]
    tables["_ops"] = OPS.recount({"tasks": out, "parity": parity.copy()}, tables)   # typed: dtypes, sort, index
    return tables

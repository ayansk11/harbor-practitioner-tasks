"""Invariants of check B's perturbed copies: check(h, p, cut) -> list of problems (empty when all hold).

h is the hidden extract H and p a copy perturb.perturb() made from it for the cut, both as dataset_io.read_dataset
returns them: the seven tables in int64 epoch seconds, and "_ops", the scheduler's records of the extract's `_ops/`
folder as two frames (ops_io.py): "tasks", one row per scheduled task run, and "parity", one row per dq_checks line.
grade.py runs this on every copy before the agent's CLI reads it; a problem means the perturbation, not the agent, is
wrong, and that cut's check then fails closed with the problems logged. The authoring proof (cut_check.py) runs it on
the graded cuts and on random cuts. Nothing here is taken from perturb.py: every rule is derived again from
docs/WAREHOUSE.md and the records, so a defect of the perturbation is not shared by its check. What it holds:
1. layout: the seven tables with their columns, no nulls but app_minutes_7d and last_login_at, known values, unique
   keys, every time before END, every row of a known customer and after that customer's sign-up; the records with
   known jobs, states, outcomes and targets, (job, run) and txn unique, txn rising in (sent_at, job, run) order, each
   task's times in order (start, send, commit, analyze, end), every record and every task end before END;
2. the records rules: the legacy_orders ranges nightly up to the move day C, each starting at the end of the last
   committed range, so the committed ranges hold every order before C once; the backfill after the committed D0 run,
   copying every order before D0; the hourly ranges from D0 on, chained the same way, into orders_new up to the
   cutover and into orders from the first hourly commit into orders on; dq_checks after C's legacy run, one parity
   line per order day D0 to C - 1 day, both of its counts the orders of that day; the cutover between dq_checks and
   the first hourly run into orders, the drop after it; a transaction committed iff its task succeeded, a failed
   label_job without one; every row count equal to the rows of the copy that its task selected, copied or wrote
   (counted here and by ops_io.recount); the rendered records parsing back to the same frames;
3. the loaders: each order loaded by the backfill (before D0) or by the first committed hourly range above it;
   tickets captured 1 to 30 s after opening; each status partition committed by its billing_export task, after 06:00
   on D+1, a cancelled row last; each label committed by a label_job run that started after its outcome became known;
   each plan change applied by the first crm_sync that started after the change; every customer record a sync wrote
   committed by that sync, with a last login from before the sync's start;
4. the plan chain: the first old_plan is the sign-up plan, each old_plan the plan before it, every change a change,
   customers.plan the last new_plan, _updated_at at or after the last applied change, a last login exactly when a
   sync wrote the record;
5. the move and the customers: the D0 and C legacy runs, the backfill, dq_checks, the cutover, the drop and every
   orders_hourly, label_job and crm_sync task as in H but rows and txn (the D0 and C runs also but lo, which follows
   the chain of item 2 when an earlier run's outcome changed); no task added, a task of H missing only if it is a
   billing_export task started at or after the cut; signup_at, postcode_district and the sign-up plan of every
   customer of H unchanged;
6. nothing visible before the cut changed: every record dated before the cut (a scheduler.log line by its time, a
   commits.jsonl object by its at) is the same in h and p; a task of H whose transaction was sent before the cut is
   unchanged in every field, and no row inside its range (a load), below its hi (the backfill) or at its commit (a
   write) is dropped, added or moved; a task started before the cut keeps its start; the rows of every table that
   were visible before the cut (orders by order_visible_at below, the other tables by _loaded_at, scoring points with
   as_of <= cut) are the same rows in h and p, no other row of p is visible before the cut, no commit lies at the
   cut, and a customer record differs from H's only if a sync after the cut wrote it.
Item 2's "committed iff succeeded" is the rule of the extracts as generated; a run that commits and then fails (an
analyze that fails after the commit) would need it relaxed.
"""
import json
import time

import numpy as np
import pandas as pd

import dataset_io as D
import ops_io as OPS

DAY, HOUR, MINUTE = 86400, 3600, 60
T0 = 1704067200              # 2024-01-01T00:00:00Z: the first legacy_orders range starts here
END = 1772668800             # 2026-03-05T00:00:00Z: every extract is the warehouse at this moment
PLANS = ["basic", "plus", "family"]
TOPICS = ["delivery", "quality", "account", "billing"]
STATUSES = ["active", "paused", "payment_failed", "cancelled"]
RENAME = "ALTER TABLE orders_new RENAME TO orders"       # the statement that gave orders_new the name orders
DROP = "DROP TABLE orders_legacy"
NULLABLE = {("scoring_points", "app_minutes_7d"), ("customers", "last_login_at")}
VALUES = {("customers", "plan"): PLANS, ("plan_changes", "old_plan"): PLANS, ("plan_changes", "new_plan"): PLANS,
          ("scoring_points", "trigger"): ["batch", "ticket"], ("orders", "kind"): ["box", "addon"],
          ("orders", "_load_job"): ["legacy_backfill", "orders_hourly"], ("tickets", "topic"): TOPICS,
          ("status_snapshots", "status"): STATUSES}
KEYS = {"customers": ["customer_id"], "plan_changes": ["customer_id", "changed_at"], "orders": ["order_id"],
        "scoring_points": ["customer_id", "as_of"], "tickets": ["ticket_id"],
        "status_snapshots": ["customer_id", "snapshot_date"], "labels": ["customer_id", "as_of"]}
# the table a job's transaction writes rows into ("" for a migration and for dq_checks, which writes none)
TARGET = {"legacy_orders": ("orders",), "legacy_backfill": ("orders_new",), "orders_hourly": ("orders_new", "orders"),
          "dq_checks": ("",), "schema_migrations": ("",), "label_job": ("labels",),
          "billing_export": ("status_snapshots",), "crm_sync": ("plan_changes",)}
WRITES = {"label_job": ("labels", ["customer_id", "as_of"]),
          "billing_export": ("status_snapshots", ["customer_id", "snapshot_date"]),
          "crm_sync": ("plan_changes", ["customer_id", "changed_at"])}
STR = ["job", "run", "state", "source", "statements", "table", "outcome"]
INT = ["started_at", "end_at", "lo", "hi", "rows", "txn", "sent_at", "at", "analyze_at"]
PARITY = ["run", "at", "day", "table_a", "rows_a", "table_b", "rows_b"]


# ------------------------------------------------------------------ what the records say
def _i64(col, na=-1):
    """A column as int64, na for a null (every real time, count and txn here is 0 or more)."""
    return pd.array(col, dtype="Int64").to_numpy(dtype=np.int64, na_value=na)


def _iso(sec):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(sec)))


def _date(sec):
    return time.strftime("%Y-%m-%d", time.gmtime(int(sec)))


def _day_seconds(text):
    return int(pd.Timestamp(text, tz="UTC").value // 10 ** 9)


def _view(tasks):
    """The tasks frame as plain arrays: text columns as str ("" for none), the others as int64 (-1 for none), and
    key = "<job> <run>"."""
    v = {c: tasks[c].astype(object).where(tasks[c].notna(), "").astype(str).to_numpy(dtype=object) for c in STR}
    v.update({c: _i64(tasks[c]) for c in INT})
    v["key"] = np.array([f"{a} {b}" for a, b in zip(v["job"].tolist(), v["run"].tolist())], dtype=object)
    return v


def _statements(text):
    return str(text).split("; ") if text else []


def cutover_at(tasks):
    """The commit of the transaction that renamed orders_new to orders: the committed schema_migrations task whose
    statements include that RENAME."""
    t = tasks[(tasks["job"] == "schema_migrations") & (tasks["outcome"] == "commit")]
    t = t[[RENAME in _statements(s) for s in t["statements"].tolist()]]
    if len(t) != 1:
        raise ValueError(f"{len(t)} committed transactions rename orders_new to orders, not one")
    return int(t["at"].iloc[0])


def order_visible_at(orders, tasks):
    """Per order: the commit that made it visible to a query on `orders` (epoch seconds). Up to the cutover the name
    meant the legacy table, which the committed legacy_orders ranges filled: an order placed before the end C of the
    last committed range became visible at the commit of the committed range holding it. Every later order is a row
    of the table renamed to `orders` at the cutover: visible from its own load's commit, and not before the cutover."""
    leg = tasks[(tasks["job"] == "legacy_orders") & (tasks["outcome"] == "commit")].sort_values("hi", kind="mergesort")
    if len(leg) == 0:
        raise ValueError("no committed legacy_orders range")
    hi, at = _i64(leg["hi"]), _i64(leg["at"])
    x = orders["ordered_at"].to_numpy(dtype=np.int64)
    vis = np.maximum(orders["_loaded_at"].to_numpy(dtype=np.int64), cutover_at(tasks))
    held = x < hi[-1]
    vis[held] = at[np.searchsorted(hi, x[held], side="right")]
    return vis


def signup_plans(customers, plan_changes):
    """customer_id -> the plan chosen at sign-up: the earliest change's old_plan, else the record's plan."""
    first = plan_changes.sort_values(["customer_id", "changed_at"], kind="mergesort").drop_duplicates("customer_id")
    p = customers["customer_id"].map(first.set_index("customer_id")["old_plan"])
    p = p.where(p.notna(), customers["plan"])
    return dict(zip(customers["customer_id"].tolist(), p.tolist()))


def _chained(lo, hi, committed, first):
    """Each range starts at the end of the last committed range before it (the first ones at `first`)."""
    if len(lo) == 0:
        return True
    prev = np.maximum.accumulate(np.where(committed, hi, first))
    want = np.concatenate([[first], prev[:-1]])
    return bool((lo == want).all())


def _union(lo, hi):
    """The union of the half-open ranges [lo, hi) as sorted, disjoint (starts, ends)."""
    o = np.argsort(lo, kind="mergesort")
    starts, ends = [], []
    for a, b in zip(lo[o].tolist(), hi[o].tolist()):
        if starts and a <= ends[-1]:
            ends[-1] = max(ends[-1], b)
        else:
            starts.append(a)
            ends.append(b)
    return np.array(starts, dtype=np.int64), np.array(ends, dtype=np.int64)


def _inside(x, starts, ends):
    if len(starts) == 0:
        return np.zeros(len(x), dtype=bool)
    i = np.searchsorted(starts, x, side="right") - 1
    return (i >= 0) & (x < ends[np.maximum(i, 0)])


def _before(files, cut):
    """The records dated before the cut: scheduler.log lines by their time, commits.jsonl objects by their at."""
    c = _iso(cut)
    log = [x for x in files["scheduler.log"].split("\n") if x and x[:20] < c]
    com = [x for x in files["commits.jsonl"].split("\n") if x and json.loads(x)["at"] < c]
    return log, com


def _canon(df, cols):
    """df[cols] as a sorted frame of plain values (strings as objects, nulls as None) for exact comparison."""
    out = pd.DataFrame(index=range(len(df)))
    for c in cols:
        v = df[c]
        if pd.api.types.is_integer_dtype(v) and not isinstance(v.dtype, pd.Int64Dtype):
            out[c] = v.to_numpy(dtype=np.int64)
        else:  # object dtype keeps None as None (a float NaN would never equal itself)
            out[c] = pd.Series([None if (x is None or x is pd.NA or (isinstance(x, float) and np.isnan(x))) else x
                                for x in v.astype(object).tolist()], dtype=object)
    key = [c for c in cols if out[c].dtype != object or not out[c].isna().any()]
    return out.sort_values(key, kind="mergesort").reset_index(drop=True)


def _same(a, b, cols):
    x, y = _canon(a, cols), _canon(b, cols)
    if len(x) != len(y):
        return False
    return all(x[c].tolist() == y[c].tolist() for c in cols)


def _frames_equal(a, b):
    try:
        pd.testing.assert_frame_equal(a, b, check_exact=True)
        return True
    except AssertionError:
        return False


# ------------------------------------------------------------------ the check
def check(h, p, cut):
    """The problems of the copy p of h for the cut, [] when every invariant holds. A copy so malformed that a rule
    cannot be evaluated is reported as a problem, never raised, so the cut fails closed with the reason logged."""
    try:
        return _check(h, p, cut)
    except Exception as e:
        return [f"invariants: the copy could not be checked ({type(e).__name__}: {str(e)[:300]})"]


def _check(h, p, cut):
    probs = []

    def need(ok, msg):
        if not bool(ok):
            probs.append(msg)

    cut = int(cut)
    # ---- 1. layout of the tables
    for name, key in KEYS.items():
        if name not in p or name not in D.TABLES:
            probs.append(f"{name}: table missing")
            continue
        df, cols = p[name], D.TABLES[name]
        miss = [c for c in cols if c not in df.columns]
        need(not miss, f"{name}: columns missing {miss}")
        if miss:
            continue
        for c in cols:
            if (name, c) not in NULLABLE:
                need(not df[c].isna().any(), f"{name}.{c}: nulls")
            if (name, c) in VALUES:
                need(df[c].dropna().isin(VALUES[(name, c)]).all(), f"{name}.{c}: unknown values")
        need(not df.duplicated(key).any(), f"{name}: duplicate keys {key}")
        for c in D.TS_COLS.get(name, []) + D.DATE_COLS.get(name, []):
            v = df[c].dropna().to_numpy(dtype=np.int64)
            need(((v > 0) & (v < END)).all(), f"{name}.{c}: a time outside (0, END)")
    need(set(D.TABLES) == set(KEYS), f"dataset_io tables {sorted(D.TABLES)} are not the seven this check holds")
    ops = p.get("_ops")
    if not isinstance(ops, dict) or not all(isinstance(ops.get(k), pd.DataFrame) for k in ("tasks", "parity")):
        probs.append("_ops: the records (tasks, parity) are missing")
        return probs
    miss = [c for c in STR + INT if c not in ops["tasks"].columns]
    miss += [c for c in PARITY if c not in ops["parity"].columns]
    need(not miss, f"_ops: columns missing {miss}")
    if probs:
        return probs
    cu, pc, sp, o = p["customers"], p["plan_changes"], p["scoring_points"], p["orders"]
    k, s, lb = p["tickets"], p["status_snapshots"], p["labels"]
    signup = cu.set_index("customer_id")["signup_at"]
    for name, col in (("orders", "ordered_at"), ("tickets", "opened_at"), ("scoring_points", "as_of"),
                      ("plan_changes", "changed_at"), ("labels", "as_of")):
        su = p[name]["customer_id"].map(signup)
        need(su.notna().all(), f"{name}: a row of an unknown customer")
        need((p[name][col] > su).all(), f"{name}: a row at or before sign-up")
    su = s["customer_id"].map(signup)
    need(su.notna().all() and (s["snapshot_date"] >= su // DAY * DAY).all(), "status_snapshots: before sign-up day")
    lk = lb.merge(sp[["customer_id", "as_of"]], on=["customer_id", "as_of"], how="left", indicator=True)
    need((lk["_merge"] == "both").all(), "labels: a label without its scoring point")
    tp = sp[sp["trigger"] == "ticket"][["customer_id", "as_of"]]
    tk = k[["customer_id", "opened_at"]].rename(columns={"opened_at": "as_of"}).drop_duplicates()
    need(len(tp.merge(tk, on=["customer_id", "as_of"])) == len(tp), "tickets: a ticket point without its ticket")

    # ---- 1. layout of the records
    t = ops["tasks"]
    v, hv = _view(t), _view(h["_ops"]["tasks"])
    job, state, out, run = v["job"], v["state"], v["outcome"], v["run"]
    st, se, at, an, en = v["started_at"], v["sent_at"], v["at"], v["analyze_at"], v["end_at"]
    lo, hi, rows = v["lo"], v["hi"], v["rows"]
    n = len(job)
    need(np.isin(job, list(TARGET)).all(), "_ops: a task of an unknown job")
    need(np.isin(state, ["success", "failed"]).all(), "_ops: a task state other than success or failed")
    need(len(set(v["key"].tolist())) == n, "_ops: a (job, run) twice")
    tx = v["txn"] >= 0
    need(len(np.unique(v["txn"][tx])) == int(tx.sum()), "_ops: a txn twice")
    srt = pd.DataFrame({"s": se[tx], "j": job[tx], "r": run[tx]}).sort_values(["s", "j", "r"], kind="mergesort")
    need((np.diff(v["txn"][tx][srt.index.to_numpy()]) > 0).all(),
         "_ops: txn does not rise in (sent_at, job, run) order")
    sends = ~((job == "dq_checks") | ((job == "label_job") & (state == "failed")))
    need((tx == sends).all(), "_ops: a transaction missing, or sent by dq_checks or a failed label_job run")
    need(np.isin(out[tx], ["commit", "rollback"]).all() and (out[~tx] == "").all(),
         "_ops: an outcome without a transaction, or a transaction without one")
    com = out == "commit"
    need(((out[tx] == "commit") == (state[tx] == "success")).all(),
         "_ops: a transaction committed by a failed task or rolled back by a successful one")
    need(all(tb in TARGET.get(j, ()) if sx else tb == ""
             for j, tb, sx in zip(job.tolist(), v["table"].tolist(), tx.tolist())),
         "_ops: a task writing into a table its job does not write, or a target without a transaction")
    need((v["source"] == np.where(job == "legacy_backfill", "orders", "")).all(), "_ops: a copy source other than the "
         "backfill's orders")
    need(((v["statements"] != "") == (job == "schema_migrations")).all(),
         "_ops: statements outside schema_migrations, or a migration without them")
    need(((se[tx] > st[tx]) & (at[tx] > se[tx]) & (en[tx] > at[tx])).all() and (se[~tx] < 0).all()
         and (at[~tx] < 0).all() and (en[~tx] > st[~tx]).all(),
         "_ops: a task's start, send, commit and end out of order")
    has_an = an >= 0
    need((has_an == ((job == "legacy_orders") & com)).all(),
         "_ops: an analyze missing, or on a task that is not a committed legacy_orders run")
    need(((an[has_an] > at[has_an]) & (an[has_an] < en[has_an])).all(), "_ops: an analyze outside its commit and end")
    times = np.concatenate([x[x >= 0] for x in (st, se, at, an, en)] + [_i64(ops["parity"]["at"])])
    need(((times > 0) & (times < END)).all(), "_ops: a record at or after END")
    need((en < END).all(), "_ops: a task ending at or after END")
    load = (job == "legacy_orders") | (job == "orders_hourly")
    need((lo[load] >= 0).all() and (hi[load] > lo[load]).all() and (lo[~load] < 0).all(),
         "_ops: a load range missing or empty, or a range start on a task that is not a load")
    need(((hi >= 0) == (load | (job == "legacy_backfill"))).all(),
         "_ops: a range end missing, or on a task without one")
    need(((rows >= 0) == (tx & (job != "schema_migrations"))).all(),
         "_ops: a row count missing, or on a task that writes no rows")
    if probs:
        return probs

    # ---- 2. the records rules
    L = np.flatnonzero(job == "legacy_orders")
    L = L[np.argsort(hi[L], kind="mergesort")]
    B = np.flatnonzero(job == "legacy_backfill")
    Q = np.flatnonzero(job == "dq_checks")
    Hh = np.flatnonzero(job == "orders_hourly")
    Hh = Hh[np.argsort(hi[Hh], kind="mergesort")]
    M = np.flatnonzero((job == "schema_migrations") & com)
    X = [m for m in M.tolist() if RENAME in _statements(v["statements"][m])]
    Dr = [m for m in M.tolist() if DROP in _statements(v["statements"][m])]
    if not (len(L) and len(B) == 1 and len(Q) == 1 and len(Hh) and len(X) == 1 and len(Dr) == 1):
        probs.append(f"_ops: the move's tasks are not all there once (legacy {len(L)}, backfill {len(B)}, dq_checks "
                     f"{len(Q)}, hourly {len(Hh)}, cutover {len(X)}, drop {len(Dr)})")
        return probs
    b, q, x, dr = int(B[0]), int(Q[0]), X[0], Dr[0]
    Lhi = hi[L]
    C, D0 = int(Lhi[-1]), int(hi[b])
    need((Lhi == T0 + DAY * np.arange(1, len(L) + 1)).all(),
         "legacy_orders: the ranges are not nightly from T0 + 1 day")
    need(all(r == _date(e) for r, e in zip(run[L].tolist(), Lhi.tolist())),
         "legacy_orders: a run is not named by its range's end")
    need(_chained(lo[L], Lhi, com[L], T0), "legacy_orders: a range does not start at the end of the last committed one")
    need(com[L[-1]], "legacy_orders: the last range (the move day C) is not committed")
    need((en[L[:-1]] < st[L[1:]]).all(), "legacy_orders: a run ends after the next run's start")
    ld0 = L[Lhi == D0]
    need(T0 < D0 < C and len(ld0) == 1 and com[ld0[0]] and st[b] > en[ld0[0]],
         "legacy_backfill: not after the committed legacy run of D0")
    need(com[b] and run[b] == _date(D0) and v["table"][b] == "orders_new", "legacy_backfill: not committed into "
         "orders_new, or not named by D0")
    need(all(r == _iso(e) for r, e in zip(run[Hh].tolist(), hi[Hh].tolist())),
         "orders_hourly: a run is not named by its range's end (the top of its hour)")
    need(_chained(lo[Hh], hi[Hh], com[Hh], D0),
         "orders_hourly: a range does not start at the end of the last committed one (the first ones at D0)")
    dual = v["table"][Hh] == "orders_new"
    first_post = int(np.argmax(~dual)) if (~dual).any() else -1
    need(dual.any() and first_post > 0 and not dual[first_post:].any(),
         "orders_hourly: not a dual run into orders_new followed by runs into orders")
    if probs:
        return probs
    fh = int(Hh[first_post])
    need(st[Hh[0]] > en[b], "orders_hourly: the dual run starts before the backfill ends")
    need(com[fh], "orders_hourly: the first run into orders is not committed")
    need(en[L[-1]] < st[q] and en[q] < st[x], "dq_checks: not between the move day's legacy run and the cutover")
    need(run[q] == _date(C), "dq_checks: its run is not the move day")
    need((en[Hh[dual]] < st[x]).all(), "orders_hourly: a dual run ends after the cutover starts")
    need(at[x] < st[fh], "schema_migrations: the cutover commits after the first hourly run into orders starts")
    need(en[x] < st[dr], "schema_migrations: the drop starts before the cutover ends")
    par = ops["parity"].sort_values("at", kind="mergesort")
    pday, pa, pb, pat = (_i64(par[c]) for c in ("day", "rows_a", "rows_b", "at"))
    want = np.arange(D0, C, DAY, dtype=np.int64)
    need(len(pday) == len(want) and (pday == want).all(), "parity: not one line per order day D0 to C - 1 day")
    xs = np.sort(o["ordered_at"].to_numpy(dtype=np.int64))
    per_day = np.searchsorted(xs, pday + DAY, side="left") - np.searchsorted(xs, pday, side="left")
    need((pa == pb).all() and (pa == per_day).all(), "parity: a line's counts are not both the orders of its day")
    need((par["table_a"] == "orders").all() and (par["table_b"] == "orders_new").all(),
         "parity: a line not comparing orders with orders_new")
    need(((pat > st[q]) & (pat < en[q])).all() and (par["run"] == run[q]).all(),
         "parity: a line outside its dq_checks task")
    cov = Hh[com[Hh] & (at[Hh] < st[q])]
    need(len(cov) and hi[cov].max() >= C, "orders_hourly: the dual ranges committed before dq_checks do not reach C")
    # each count, made here and by ops_io.recount
    nlo, nhi = np.searchsorted(xs, lo, side="left"), np.searchsorted(xs, hi, side="left")
    bad = load & (rows != nhi - nlo)
    need(not bad.any(), f"_ops: {int(bad.sum())} loads whose row count is not the orders in their range")
    need(rows[b] == nhi[b], "legacy_backfill: its row count is not the orders before D0")
    for wj, (tname, _keys) in WRITES.items():
        w = np.flatnonzero(tx & (job == wj))
        if wj == "billing_export":
            got = p[tname]["snapshot_date"].value_counts()
            ref = np.array([_day_seconds(r) for r in run[w].tolist()], dtype=np.int64)
        else:
            got = p[tname]["_loaded_at"].value_counts()
            ref = at[w]
        cnt = pd.Series(ref).map(got).fillna(0).to_numpy(dtype=np.int64)
        need((rows[w] == cnt).all(), f"{wj}: {int((rows[w] != cnt).sum())} row counts that are not the rows written")
    need(xs[0] >= T0 and rows[L][com[L]].sum() == np.searchsorted(xs, C, side="left"),
         "legacy_orders: the committed ranges do not hold every order before C once")
    need(rows[b] == rows[L][com[L] & (Lhi <= D0)].sum(), "legacy_backfill: its rows are not the committed legacy rows "
         "before D0")
    try:
        files = OPS.render(ops)
        back = OPS.parse(files)
        need(all(_frames_equal(back[f], ops[f]) for f in ("tasks", "parity")), "_ops: parse(render(x)) is not x")
        need(OPS.render(back) == files, "_ops: render(parse(render(x))) is not render(x)")
        rc = OPS.recount({f: ops[f].copy() for f in ("tasks", "parity")}, p)
        need(all(_frames_equal(rc[f], ops[f]) for f in ("tasks", "parity")), "_ops: recount(x) changed a count")
        bad_v = OPS.validate(ops)
        need(not bad_v, f"_ops: validate: {list(bad_v)[:3]}")
    except Exception as e:  # a copy whose records do not render or parse is the perturbation's defect
        probs.append(f"_ops: the records do not round trip ({type(e).__name__}: {str(e)[:300]})")
        return probs

    # ---- 3. the loaders
    pre = o["ordered_at"].to_numpy(dtype=np.int64) < D0
    need(((o["_load_job"] == "legacy_backfill").to_numpy() == pre).all(),
         "orders: _load_job legacy_backfill is not exactly the orders before D0")
    la = o["_loaded_at"].to_numpy(dtype=np.int64)
    need((la[pre] == at[b]).all(), "orders: an order before D0 not loaded by the backfill's commit")
    hc = Hh[com[Hh]]
    j = np.searchsorted(hi[hc], o["ordered_at"].to_numpy(dtype=np.int64)[~pre], side="right")
    need((j < len(hc)).all() and (at[hc][np.minimum(j, len(hc) - 1)] == la[~pre]).all(),
         "orders: an order from D0 on not loaded by the first committed hourly range above it")
    try:
        p_vis = order_visible_at(o, t)
    except ValueError as e:
        probs.append(f"orders: {e}")
        return probs
    need((p_vis > o["ordered_at"].to_numpy(dtype=np.int64)).all(), "orders: visible at or before ordered_at")
    lag = (k["_loaded_at"] - k["opened_at"]).to_numpy()
    need(((lag >= 1) & (lag <= 30)).all(), "tickets: capture lag outside 1 to 30 s")
    bx = np.flatnonzero(com & (job == "billing_export"))
    part_at = dict(zip([_day_seconds(r) for r in run[bx].tolist()], at[bx].tolist()))
    need((s["snapshot_date"].map(part_at) == s["_loaded_at"]).all(),
         "status_snapshots: a partition not committed by its billing_export task")
    need((s["_loaded_at"] > s["snapshot_date"] + DAY + 6 * HOUR).all(),
         "status_snapshots: a partition committed before 06:00 on D+1")
    last = s.sort_values(["customer_id", "snapshot_date"], kind="mergesort").groupby("customer_id").tail(1)
    canc = s[s["status"] == "cancelled"]
    need(len(canc.merge(last, on=["customer_id", "snapshot_date"])) == len(canc), "status_snapshots: a row after a "
         "cancelled one")
    y = lb["churned_30d"].to_numpy()
    need(np.isin(y, [0, 1]).all(), "labels: churned_30d not 0 or 1")
    lj = np.flatnonzero(com & (job == "label_job"))
    lstart = lb["_loaded_at"].map(dict(zip(at[lj].tolist(), st[lj].tolist())))
    need(lstart.notna().all(), "labels: a label not committed by a label_job run")
    known = np.where(y == 0, lb["as_of"].to_numpy(dtype=np.int64) + 30 * DAY, lb["as_of"].to_numpy(dtype=np.int64))
    need((lstart.fillna(0).to_numpy(dtype=np.int64) > known).all() and (lb["_loaded_at"] > lb["as_of"]).all(),
         "labels: committed by a run that started before the outcome was known")
    cs = np.flatnonzero(com & (job == "crm_sync"))
    cs = cs[np.argsort(st[cs], kind="mergesort")]
    s_start, s_at = st[cs], at[cs]
    sync_of = pd.Series(np.arange(len(cs)), index=s_at)
    ki = pc["_loaded_at"].map(sync_of)
    need(ki.notna().all(), "plan_changes: _loaded_at is not a crm_sync commit")
    ki = ki.fillna(0).to_numpy(dtype=np.int64)
    chg = pc["changed_at"].to_numpy(dtype=np.int64)
    prev_start = np.where(ki > 0, s_start[np.maximum(ki - 1, 0)], -1)
    need(((chg < s_start[ki]) & (chg >= prev_start)).all(),
         "plan_changes: a change not applied by the first crm_sync that started after it")

    # ---- 4. the plan chain and the customer record
    plan0 = signup_plans(h["customers"], h["plan_changes"])
    ch = pc.sort_values(["customer_id", "changed_at"], kind="mergesort")
    ok_chain, ok_first, ok_change = True, True, True
    last_new = {}
    for c, g in ch.groupby("customer_id", sort=False):
        old, new = g["old_plan"].tolist(), g["new_plan"].tolist()
        ok_chain &= all(old[i + 1] == new[i] for i in range(len(old) - 1))
        ok_change &= all(a != b_ for a, b_ in zip(old, new))
        if c in plan0:
            ok_first &= old[0] == plan0[c]
        last_new[c] = new[-1]
    need(ok_chain, "plan_changes: an old_plan is not the plan before it")
    need(ok_first, "plan_changes: the first old_plan is not the sign-up plan")
    need(ok_change, "plan_changes: a change with new_plan = old_plan")
    cur = dict(zip(cu["customer_id"].tolist(), cu["plan"].tolist()))
    need(all(cur[c] == val for c, val in last_new.items()), "customers.plan is not the last applied change's new_plan")
    need(all(cur[c] == plan0[c] for c in plan0 if c not in last_new and c in cur),
         "customers.plan of a customer without changes is not the sign-up plan")
    ml = ch.groupby("customer_id")["_loaded_at"].max()
    upd = cu.set_index("customer_id")["_updated_at"]
    need((upd.loc[ml.index] >= ml).all(), "customers._updated_at before the customer's last applied change")
    login = cu["last_login_at"]
    is_su = (cu["_updated_at"] == cu["signup_at"]).to_numpy()
    need((login.isna().to_numpy() == is_su).all(), "customers: a last login without a sync write, or the reverse")
    wstart = cu.loc[~is_su, "_updated_at"].map(dict(zip(s_at.tolist(), s_start.tolist())))
    need(wstart.notna().all(), "customers._updated_at is not a crm_sync commit")
    lv = login[~is_su].astype("Int64").fillna(0).to_numpy(dtype=np.int64)
    need((lv < wstart.fillna(0).to_numpy(dtype=np.int64)).all(), "customers: a last login after the sync's start")
    hc_ = h["customers"]
    m = hc_.merge(cu, on="customer_id", how="left", suffixes=("_h", "_p"), indicator=True)
    need((m["_merge"] == "both").all(), "customers: a customer of H is missing")
    need((m["signup_at_h"] == m["signup_at_p"]).all() and (m["postcode_district_h"] == m["postcode_district_p"]).all(),
         "customers: signup_at or postcode_district changed")
    p_plan0 = signup_plans(cu, pc)
    need(all(p_plan0.get(c) == val for c, val in plan0.items()), "customers: a sign-up plan changed")

    # ---- 5. the move and the task set, against H
    hjob = hv["job"]
    hpos = pd.Index(v["key"]).get_indexer(hv["key"])
    here = hpos >= 0
    gone = ~here
    need(((hjob[gone] == "billing_export") & (hv["started_at"][gone] >= cut)).all(),
         f"_ops: {int(gone.sum())} tasks of H missing (only a billing_export task started at or after the cut may go)")
    need((pd.Index(hv["key"]).get_indexer(v["key"]) >= 0).all(), "_ops: a task that H does not have")
    hL = hjob == "legacy_orders"
    h_C = int(hv["hi"][hL].max())
    h_D0 = int(hv["hi"][hjob == "legacy_backfill"].max())
    need(C == h_C and D0 == h_D0, "the move changed (D0 or C)")

    def differs(sel, cols):
        """Tasks of H (by mask) present in p with any of cols different."""
        i = np.flatnonzero(sel & here)
        bad_ = np.zeros(len(i), dtype=bool)
        for c in cols:
            bad_ |= hv[c][i] != v[c][hpos[i]]
        return i[bad_]

    keep_jobs = np.isin(hjob, ["orders_hourly", "label_job", "crm_sync", "legacy_backfill", "dq_checks",
                               "schema_migrations"])
    need(not (keep_jobs & gone).any(), "_ops: a task of the move, orders_hourly, label_job or crm_sync is missing")
    d1 = differs(keep_jobs, [c for c in STR + INT if c not in ("rows", "txn")])
    need(len(d1) == 0, f"_ops: {len(d1)} tasks of the move, orders_hourly, label_job or crm_sync changed (first: "
         f"{hv['key'][d1[0]] if len(d1) else ''})")
    edge = hL & np.isin(hv["hi"], [h_D0, h_C])
    d2 = differs(edge, [c for c in STR + INT if c not in ("rows", "txn", "lo")])
    need(len(d2) == 0 and not (edge & gone).any(), "legacy_orders: the run of D0 or of C changed")

    # ---- 6. nothing visible before the cut changed
    try:
        need(_before(OPS.render(h["_ops"]), cut) == _before(files, cut), "_ops: a record dated before the cut changed")
    except Exception as e:
        probs.append(f"_ops: H's records do not render ({type(e).__name__}: {str(e)[:300]})")
    hse = hv["sent_at"]
    sent_pre = (hse >= 0) & (hse < cut)
    need(not (sent_pre & gone).any(), "_ops: a task sent before the cut is missing")
    d3 = differs(sent_pre, STR + INT)
    need(len(d3) == 0, f"_ops: {len(d3)} tasks whose transaction was sent before the cut changed (first: "
         f"{hv['key'][d3[0]] if len(d3) else ''})")
    d4 = differs((hv["started_at"] < cut) & ~sent_pre, ["started_at"])
    need(len(d4) == 0, "_ops: a task started before the cut changed its start")
    rl = sent_pre & np.isin(hjob, ["legacy_orders", "orders_hourly", "legacy_backfill"])
    r_lo = np.where(hjob[rl] == "legacy_backfill", 0, hv["lo"][rl])
    ust, uen = _union(r_lo, hv["hi"][rl])
    ho = h["orders"]
    a_ = ho[_inside(ho["ordered_at"].to_numpy(dtype=np.int64), ust, uen)]
    b_ = o[_inside(o["ordered_at"].to_numpy(dtype=np.int64), ust, uen)]
    need(_same(a_, b_, ["order_id", "ordered_at"]),
         "orders: a row inside the range of a load sent before the cut was dropped, added or moved")
    for wj, (tname, keys) in WRITES.items():
        ats = hv["at"][sent_pre & (hjob == wj)]
        a_, b_ = h[tname], p[tname]
        need(_same(a_[a_["_loaded_at"].isin(ats)], b_[b_["_loaded_at"].isin(ats)], keys + ["_loaded_at"]),
             f"{tname}: a row written by a {wj} transaction sent before the cut was dropped, added or moved")
    h_vis = order_visible_at(h["orders"], h["_ops"]["tasks"])
    oc = D.TABLES["orders"]
    need(_same(h["orders"][h_vis < cut], o[p_vis < cut], oc), "orders: the rows visible before the cut changed")
    need(not (p_vis == cut).any(), "orders: a commit at the cut")
    need(not (at == cut).any(), "_ops: a transaction committed at the cut")
    for name in ("tickets", "status_snapshots", "labels", "plan_changes"):
        a_, b_ = h[name], p[name]
        need(_same(a_[a_["_loaded_at"] < cut], b_[b_["_loaded_at"] < cut], D.TABLES[name]),
             f"{name}: the rows loaded before the cut changed")
        need(not (b_["_loaded_at"] == cut).any(), f"{name}: a commit at the cut")
    hp = h["scoring_points"]
    need(_same(hp[hp["as_of"] <= cut], sp[sp["as_of"] <= cut], D.TABLES["scoring_points"]),
         "scoring_points: a point at or before the cut changed")
    pm = m[m["_updated_at_p"] < cut]
    same_rec = ((pm["plan_h"] == pm["plan_p"]) & (pm["_updated_at_h"] == pm["_updated_at_p"])
                & ((pm["last_login_at_h"].isna() & pm["last_login_at_p"].isna())
                   | (pm["last_login_at_h"] == pm["last_login_at_p"]).fillna(False)))
    need(bool(same_rec.all()), "customers: a record (plan, last_login_at, _updated_at) written before the cut changed")
    need(not (cu["_updated_at"] == cut).any(), "customers: a record written at the cut")
    return probs

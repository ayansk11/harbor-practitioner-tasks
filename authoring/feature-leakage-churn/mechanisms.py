"""Per-mechanism counts for feature-leakage-churn (authoring only; called by gen_data.py), and a check of an order
visibility table against the simulator's truth.

For each natural wrong choice of the design (one per rule-swap attempt in solution/attempts; the new attempts of the
operations-log revision carry the attempt's own name), this computes the values that an extract-only pipeline making
that one mistake (everything else right) gives an extract's scoring points, and counts the rows and cells that differ
from ref_truth. Each variant swaps exactly one input of ref_truth's loop for what the wrong rule reads from the
extract. Order visibility is read from the extract's scheduler records (ext["_ops"], ops_log.py) by the canonical
solution's rule (churn/visibility.py, order_visible_at): an order placed before the end of the last committed
legacy_orders range is visible from the commit of the committed range that holds it, any later order from the later of
its `_loaded_at` and the commit of the rename that gave orders_new the name `orders`. Every order variant is that rule
with the one edit its attempt makes (order_visibility). The `_derived_*` entries feed the right rules with inputs read
from the extract alone; they must equal ref_truth in every cell, the data-side proof that every graded value is
determined by the extract. assert_targets() holds that and the build's floors (>= 100 cells on both extracts for every
check-A kill, hourly_schedule > 0, the H targets); report() also states which of scheduler_end, v2_rule and min_commit
reach 300 cells. cut_candidates() lists check-B cut times on H.

python mechanisms.py --visibility <csv> --brand <visible|H>
  The csv holds order_id,visible_at (ISO 8601 UTC with a Z suffix), one row per order of that brand's extract. Prints
  the counts of (order, scoring point) pairs where (visible_at < as_of) differs from the simulator's truth, over every
  scoring point and over the order's own customer's points; exit status 0 only if the first is 0 and the table has
  exactly one row for every order and no other row.
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)  # the authoring modules next to this file (python -I leaves the script's folder out)
import ref_truth as R  # noqa: E402

DAY, HOUR = 86400, 3600
STRIDE = 10 ** 10                   # composite key customer_id * STRIDE + seconds
RENAME = "ALTER TABLE orders_new RENAME TO orders"
GROUPS = {"orders": ["orders_7d", "orders_30d", "spend_30d_cents", "days_since_last_order"], "tickets": ["tickets_30d"],
          "status": ["status"], "plan": ["plan"], "te": ["te_district"], "login": ["days_since_last_login"]}
A_KILLS = ["orders_event_time", "trust_loaded_at", "v2_rule", "min_commit", "scheduler_end", "scheduler_start",
           "rollback_as_commit", "backfill_event_time", "legacy_schedule", "window_on_loaded_at", "status_event_date",
           "status_latest_loaded", "current_plan", "plan_changed_at", "labels_matured"]
TARGET_300 = ["scheduler_end", "v2_rule", "min_commit"]
# order variants: name -> the edit of order_visibility's defaults that its attempt makes on the canonical lines
ORDER_EDITS = {
    "v2_rule": dict(base="loaded", held="backfill"),          # legacy commits for backfilled rows, `_loaded_at` else
    "min_commit": dict(base="loaded", assign="min"),          # the earlier of the legacy commit and `_loaded_at`
    "scheduler_end": dict(at="end_at"),                       # the legacy task's end (state=success) as its commit
    "scheduler_start": dict(at="started_at"),                 # the legacy task's start as its commit
    "rollback_as_commit": dict(committed="all"),              # rolled-back legacy ranges taken as committed
    "backfill_event_time": dict(assign="event"),              # ordered_at below the watermark
    "legacy_schedule": dict(assign="legacy_schedule"),        # 02:30 on the night after the order
    "hourly_schedule": dict(base="hourly_schedule"),          # :20 after the next top of the hour, above it
    # graft variants (built only with their records): state=success as the commit, the first rename as the cutover
    "failed_state_as_rollback": dict(committed="state"),
    "first_rename": dict(base="first_rename", assign="min"),
}


def differs(a, b, col):
    """Cell-wise difference with the grader's rule: integers and strings exactly, floats within 1e-6 + 1e-9 |b|,
    nulls alike."""
    if col in R.STR_FEATS:
        x = [None if (v is None or (isinstance(v, float) and np.isnan(v))) else v for v in list(a)]
        y = [None if (v is None or (isinstance(v, float) and np.isnan(v))) else v for v in list(b)]
        return np.array([p != q for p, q in zip(x, y)])
    x, y = np.asarray(a, dtype="float64"), np.asarray(b, dtype="float64")
    if col in R.INT_FEATS:
        return x != y
    nx, ny = np.isnan(x), np.isnan(y)
    close = np.abs(x - y) <= 1e-6 + 1e-9 * np.abs(y)
    return (nx != ny) | (~nx & ~ny & ~close)


# ------------------------------------------------------------------------------------------------ the records
def legacy_tasks(ops):
    """The legacy_orders tasks of the records (one per run night)."""
    t = ops["tasks"]
    return t[(t["job"] == "legacy_orders").to_numpy(dtype=bool)]


def _rename_tasks(ops):
    t = ops["tasks"]
    has = np.array([RENAME in s.split("; ") for s in t["statements"].tolist()], dtype=bool)
    return t[(t["job"] == "schema_migrations").to_numpy(dtype=bool) & has]


def cutover_at(ops):
    """The commit time of the schema_migrations transaction that renamed orders_new to `orders`."""
    x = _rename_tasks(ops)
    x = x[(x["outcome"] == "commit").to_numpy(dtype=bool)]
    assert len(x) == 1, ("committed renames of orders_new", len(x))
    return int(x["at"].iloc[0])


def order_visibility(ext, base="canonical", committed="commit", at="at", held="watermark", assign="commit"):
    """Per order of ext["orders"]: when it became visible to a query on `orders` (epoch seconds), by the canonical
    rule (the defaults) or by one attempt's edit of it (ORDER_EDITS). The lines follow order_visible_at:
      visible = max(_loaded_at, cutover)                          base: loaded = _loaded_at alone; hourly_schedule;
                                                                  first_rename = max(_loaded_at, the first rename's at)
      committed = committed legacy_orders tasks, sorted by hi     committed: all = every task; state = state success
      hi, at = their hi and `at`                                  at: end_at or started_at instead
      held = ordered_at < hi[-1]                                  held: backfill = `_load_job == legacy_backfill`
      visible[held] = at of the first committed task with hi > ordered_at
                                                                  assign: min (with visible), event (ordered_at),
                                                                  legacy_schedule (02:30 on the next night)"""
    o, ops = ext["orders"], ext["_ops"]
    loaded = np.asarray(o["_loaded_at"], dtype="int64")
    x = np.asarray(o["ordered_at"], dtype="int64")
    if base == "canonical":
        visible = np.maximum(loaded, cutover_at(ops))
    elif base == "loaded":
        visible = loaded.copy()
    elif base == "hourly_schedule":
        visible = (x // 3600 + 1) * 3600 + 20 * 60
    elif base == "first_rename":
        first = _rename_tasks(ops).sort_values(["started_at", "run"], kind="mergesort")
        visible = np.maximum(loaded, int(first["at"].iloc[0]))
    else:
        raise ValueError(base)
    leg = legacy_tasks(ops)
    if committed == "commit":
        leg = leg[(leg["outcome"] == "commit").to_numpy(dtype=bool)]
    elif committed == "state":
        leg = leg[(leg["state"] == "success").to_numpy(dtype=bool)]
    elif committed != "all":
        raise ValueError(committed)
    leg = leg.sort_values("hi", kind="mergesort")
    hi, ats = leg["hi"].to_numpy(dtype="int64"), leg[at].to_numpy(dtype="int64")
    if held == "watermark":
        h = x < hi[-1]
    elif held == "backfill":
        h = (o["_load_job"] == "legacy_backfill").to_numpy(dtype=bool)
    else:
        raise ValueError(held)
    a = ats[np.searchsorted(hi, x[h], side="right")]
    if assign == "commit":
        visible[h] = a
    elif assign == "min":
        visible[h] = np.minimum(a, visible[h])
    elif assign == "event":
        visible[h] = x[h]
    elif assign == "legacy_schedule":
        visible[h] = (x[h] // DAY + 1) * DAY + 2 * 3600 + 30 * 60
    else:
        raise ValueError(assign)
    return visible


def correct_order_visibility(ext):
    """The extract's own record of when each order became visible (gen_data asserts it equal to the truth), and the
    mask of the orders held by a legacy range (ordered_at below the last committed legacy watermark)."""
    leg = legacy_tasks(ext["_ops"])
    last = int(leg.loc[(leg["outcome"] == "commit").to_numpy(dtype=bool), "hi"].max())
    return order_visibility(ext), np.asarray(ext["orders"]["ordered_at"], dtype="int64") < last


# ------------------------------------------------------------------------------------------------ features
def _orders(pc, pt, ext, vis, window=None):
    o = ext["orders"]
    lists = R.order_lists(o["customer_id"].to_numpy(), o["ordered_at"].to_numpy(), np.asarray(vis, dtype=np.int64),
                          o["amount_cents"].to_numpy(), None if window is None else np.asarray(window, np.int64))
    return R.order_features(pc, pt, lists)


def _status(pc, pt, ext, vis, pick):
    s = ext["status_snapshots"]
    lists = R.snapshot_lists(s["customer_id"].to_numpy(), s["snapshot_date"].to_numpy(),
                             np.asarray(vis, dtype=np.int64), s["status"].to_numpy())
    return R.status_feature(pc, pt, lists, pick=pick)


def _te(pc, pt, ext, vis):
    cu = ext["customers"]
    district = dict(zip(cu["customer_id"].tolist(), cu["postcode_district"].tolist()))
    lb = ext["labels"]
    return R.te_feature(pc, pt, district, lb["customer_id"].to_numpy(), np.asarray(vis, dtype=np.int64),
                        lb["churned_30d"].to_numpy())


def _plan_by(ext, pc, pt, key):
    """Plan by the H4 fallbacks, with changes visible when `key` < t (key = changed_at for the wrong variant)."""
    pcg = ext["plan_changes"].sort_values(["customer_id", "changed_at"], kind="mergesort")
    by = {c: (g["changed_at"].tolist(), g[key].tolist(), g["old_plan"].tolist(), g["new_plan"].tolist())
          for c, g in pcg.groupby("customer_id", sort=False)}
    cur = dict(zip(ext["customers"]["customer_id"].tolist(), ext["customers"]["plan"].tolist()))
    out = []
    for c, t in zip(pc, pt):
        if c not in by:
            out.append(cur[c])
            continue
        ca, va, old, new = by[c]
        best, val = None, None
        for x, y, v in zip(ca, va, new):
            if y < t and (best is None or x > best):
                best, val = x, v
        out.append(val if best is not None else old[0])
    return {"plan": np.array(out, dtype=object)}


def variants(w, ext, pc, pt):
    """name -> (feature group, function returning that group's columns for the points)."""
    o = ext["orders"]
    oa = o["ordered_at"].to_numpy()
    vis = order_visibility(ext)
    cu = ext["customers"].set_index("customer_id")
    last_login = pd.Series(pc).map(cu["last_login_at"]).to_numpy(dtype="float64", na_value=np.nan)
    updated = pd.Series(pc).map(cu["_updated_at"]).to_numpy(dtype="float64")
    t = np.asarray(pt, dtype="float64")

    def order_variant(edit):
        return lambda: _orders(pc, pt, ext, order_visibility(ext, **edit))

    s = ext["status_snapshots"]
    lb = ext["labels"]
    k = ext["tickets"]
    out = {
        # the right rules on inputs read from the extract alone: each must equal ref_truth (0 cells; derivability)
        "_derived_orders": ("orders", lambda: _orders(pc, pt, ext, vis)),
        "_derived_tickets": ("tickets", lambda: R.ticket_features(pc, pt, R.ticket_lists(
            k["customer_id"].to_numpy(), k["opened_at"].to_numpy(), k["_loaded_at"].to_numpy()))),
        "_derived_status": ("status", lambda: _status(pc, pt, ext, s["_loaded_at"].to_numpy(), "date")),
        "_derived_plan": ("plan", lambda: _plan_by(ext, pc, pt, "_loaded_at")),
        "_derived_te": ("te", lambda: _te(pc, pt, ext, lb["_loaded_at"].to_numpy())),
        "orders_event_time": ("orders", lambda: _orders(pc, pt, ext, oa)),
        "trust_loaded_at": ("orders", lambda: _orders(pc, pt, ext, o["_loaded_at"].to_numpy())),
    }
    for name, edit in ORDER_EDITS.items():
        out[name] = ("orders", order_variant(edit))
    out.update({
        "window_on_loaded_at": ("orders", lambda: _orders(pc, pt, ext, vis, window=vis)),
        "tickets_event_time": ("tickets", lambda: R.ticket_features(pc, pt, R.ticket_lists(
            k["customer_id"].to_numpy(), k["opened_at"].to_numpy(), k["opened_at"].to_numpy()))),
        "status_event_date": ("status", lambda: _status(pc, pt, ext, s["snapshot_date"].to_numpy() + DAY - 1,
                                                        "date")),
        "status_latest_loaded": ("status", lambda: _status(pc, pt, ext, s["_loaded_at"].to_numpy(), "loaded")),
        "current_plan": ("plan", lambda: {"plan": pd.Series(pc).map(cu["plan"]).to_numpy(dtype=object)}),
        "plan_changed_at": ("plan", lambda: _plan_by(ext, pc, pt, "changed_at")),
        "labels_matured": ("te", lambda: _te(pc, pt, ext, lb["as_of"].to_numpy() + 30 * DAY)),
        "clip_last_login": ("login", lambda: {"days_since_last_login": np.where(
            last_login < t, (t - last_login) / DAY, np.nan)}),
        "last_login_where_known": ("login", lambda: {"days_since_last_login": np.where(
            t > updated, (t - last_login) / DAY, np.nan)}),
    })
    return out


def report(w, ext, truth):
    sp = ext["scoring_points"]
    pc, pt = sp["customer_id"].tolist(), sp["as_of"].tolist()
    assert (truth["customer_id"].tolist() == pc) and (truth["as_of"].tolist() == pt)
    batch = (sp["trigger"] == "batch").to_numpy()
    pre = (sp["as_of"] < w["move0"]).to_numpy()
    dual = ((sp["as_of"] >= w["d0"]) & (sp["as_of"] < w["move0"])).to_numpy()
    out = {"_points": len(sp), "_batch_points": int(batch.sum()), "_pre_move_points": int(pre.sum()),
           "_dual_run_points": int(dual.sum())}
    for name, (group, fn) in variants(w, ext, pc, pt).items():
        vals = fn()
        row = np.zeros(len(sp), bool)
        cells = 0
        per = {}
        for col in GROUPS[group]:
            d = differs(vals[col], truth[col].to_numpy(), col)
            per[col] = int(d.sum())
            cells += int(d.sum())
            row |= d
        rec = {"rows": int(row.sum()), "cells": cells, "batch_rows": int((row & batch).sum()),
               "pre_move_rows": int((row & pre).sum()), "dual_run_rows": int((row & dual).sum()), "per_feature": per}
        if group == "login":
            rec["non_null_rows"] = int((~np.isnan(np.asarray(vals["days_since_last_login"], "float64"))).sum())
        out[name] = rec
    out["_target_300"] = {n: {"cells": out[n]["cells"], "met": out[n]["cells"] >= 300} for n in TARGET_300}
    return out


def assert_targets(rep):
    """The build's floors. Check-A kills move >= 100 cells on both extracts (the design's fairness rule);
    hourly_schedule is the stated exception (> 0); the H targets of the design (TARGETs, asserted here)."""
    for b in ("visible", "H"):
        m = rep[b]["mechanisms"]
        for name in ("_derived_orders", "_derived_tickets", "_derived_status", "_derived_plan", "_derived_te"):
            assert m[name]["cells"] == 0, (b, name, m[name]["cells"], "a value the extract does not determine")
        for name in A_KILLS:
            assert m[name]["cells"] >= 100, (b, name, m[name]["cells"], "under the 100-cell floor")
        assert m["hourly_schedule"]["cells"] > 0, (b, "hourly_schedule never differs")
        assert m["orders_event_time"]["batch_rows"] >= 0.5 * m["_batch_points"], (b, "H1 orders on most batch rows")
        assert m["labels_matured"]["rows"] >= 0.5 * m["_points"], (b, "H6 on most rows")
        assert m["clip_last_login"]["rows"] >= 0.5 * m["_points"], (b, "H5 clipped values wrong on most rows")
        assert m["last_login_where_known"]["non_null_rows"] > 0, (b, "last_login_where_known is all null")
        assert m["trust_loaded_at"]["pre_move_rows"] >= 0.5 * m["_pre_move_points"], (b, "H2 on most pre-move rows")
    h = rep["H"]["mechanisms"]
    assert h["legacy_schedule"]["rows"] >= 200, ("H3 legacy_schedule rows", h["legacy_schedule"]["rows"])
    assert h["current_plan"]["rows"] >= 1000, ("H4 current_plan rows", h["current_plan"]["rows"])
    assert h["plan_changed_at"]["rows"] >= 200, ("H4 plan_changed_at rows", h["plan_changed_at"]["rows"])


def cut_candidates(w, ext, limit=5):
    """Check-B cut times on H that meet the design's section 5 (for the grader's CUTS; facts, not a choice)."""
    sp = ext["scoring_points"]
    out = {"cut1": [], "cut2": [], "cut2_relaxed_no_export_pending": []}
    o0, n = w["outage"]["start"], w["outage"]["nights"]
    for k in range(6, 10):
        if k <= n:
            t = o0 + (k - 1) * DAY + 6 * HOUR
            out["cut1"].append({"cut": pd.Timestamp(t, unit="s").strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "failed_nights_before": k,
                                "batch_points_at_cut": int(((sp["as_of"] == t) & (sp["trigger"] == "batch")).sum())})
    h = w["hourly"]
    hc, hok = h["commit"].to_numpy(), h["ok"].to_numpy()
    ex = w["exports"]
    pcg = w["plan_changes"]
    tick = sp[(sp["trigger"] == "ticket") & (sp["as_of"] > w["first_hourly"])]
    for t in tick["as_of"].tolist():
        j = int(np.searchsorted(hc, t, side="left")) - 1
        if j < 0 or hok[j]:
            continue                                   # the hour's run before t did not fail
        plan_pend = int(((pcg["changed_at"] < t) & (pcg["_loaded_at"] > t)).sum())
        if plan_pend == 0:
            continue                                   # no plan change waiting for the next sync
        pend = ex[((ex["partition"] + DAY + 6 * HOUR + 50 * 60) < t) & (ex["commit"] > t)]
        if len(pend) == 0:                             # no late export partition pending at t
            if len(out["cut2_relaxed_no_export_pending"]) < limit:
                out["cut2_relaxed_no_export_pending"].append(
                    {"cut": pd.Timestamp(t, unit="s").strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "failed_hourly_run": pd.Timestamp(int(hc[j]), unit="s").strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "plan_changes_pending_sync": plan_pend})
            continue
        out["cut2"].append({"cut": pd.Timestamp(t, unit="s").strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "failed_hourly_run": pd.Timestamp(int(hc[j]), unit="s").strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "pending_export_partitions": [pd.Timestamp(int(x), unit="s").strftime("%Y-%m-%d")
                                                          for x in pend["partition"].tolist()],
                            "plan_changes_pending_sync": plan_pend})
        if len(out["cut2"]) >= limit:
            break
    return out


# ------------------------------------------------------------------------------------------------ visibility check
def visibility_pairs(w, ext, table):
    """Counts for a table order_id, visible_at (int64 epoch seconds) against the simulator's truth on the extract's
    orders and scoring points: (order, scoring point) pairs where (visible_at < as_of) differs, over every point and
    over the order's own customer's points (all, and those after ordered_at), plus missing, extra and repeated rows."""
    o = ext["orders"][["order_id", "customer_id", "ordered_at"]].reset_index(drop=True)
    true = w["orders"].set_index("order_id")["visible_at"].reindex(o["order_id"]).to_numpy(dtype="int64")
    ids = table["order_id"].to_numpy(dtype="int64")
    known = np.isin(ids, o["order_id"].to_numpy())
    dup = pd.Series(ids).duplicated(keep=False).to_numpy()
    got = pd.Series(table["visible_at"].to_numpy(dtype="int64"), index=ids)
    one = got[~pd.Series(ids).duplicated(keep="first").to_numpy()]
    has = o["order_id"].isin(one.index).to_numpy()
    mine = one.reindex(o["order_id"]).to_numpy(dtype="float64", na_value=np.nan)
    rep = {"orders": len(o), "rows": int(len(table)), "missing_orders": int((~has).sum()),
           "extra_rows": int((~known).sum()), "repeated_rows": int(dup.sum())}
    ok = has
    a, b = np.clip(true[ok], 0, STRIDE - 1), np.clip(mine[ok], 0, STRIDE - 1).astype("int64")
    lo, hi = np.minimum(a, b), np.maximum(a, b)      # (a < t) != (b < t) exactly when lo < t <= hi
    sp = ext["scoring_points"]
    t_all = np.sort(sp["as_of"].to_numpy(dtype="int64"))
    rep["orders_differing"] = int((a != b).sum())
    rep["pairs_all_points"] = int((np.searchsorted(t_all, hi, "right") - np.searchsorted(t_all, lo, "right")).sum())
    keys = np.sort(sp["customer_id"].to_numpy(dtype="int64") * STRIDE + sp["as_of"].to_numpy(dtype="int64"))
    c = o["customer_id"].to_numpy(dtype="int64")[ok] * STRIDE
    rep["pairs_own_customer"] = int((np.searchsorted(keys, c + hi, "right")
                                     - np.searchsorted(keys, c + lo, "right")).sum())
    lo2 = np.maximum(lo, o["ordered_at"].to_numpy(dtype="int64")[ok])
    rep["pairs_own_customer_after_order"] = int(np.maximum(np.searchsorted(keys, c + hi, "right")
                                                           - np.searchsorted(keys, c + lo2, "right"), 0).sum())
    rep["ok"] = (rep["pairs_all_points"] == 0 and rep["missing_orders"] == 0 and rep["extra_rows"] == 0
                 and rep["repeated_rows"] == 0)
    return rep


def main(argv):
    if "--visibility" not in argv or "--brand" not in argv:
        raise SystemExit("usage: mechanisms.py --visibility <csv> --brand <visible|H>")
    path, brand = argv[argv.index("--visibility") + 1], argv[argv.index("--brand") + 1]
    import extract_io
    import gen_data as G
    w = G.brand_world(brand)
    ext = G.extract_tables(w)
    raw = pd.read_csv(path, dtype={"order_id": "int64", "visible_at": "str"}, keep_default_na=False)
    if list(raw.columns) != ["order_id", "visible_at"]:
        raise SystemExit(f"{path}: the columns are {list(raw.columns)}, not order_id, visible_at")
    form = raw["visible_at"].map(lambda v: re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", v) is not None)
    if not form.all():
        raise SystemExit(f"{path}: {int((~form).sum())} visible_at values are not YYYY-MM-DDTHH:MM:SSZ")
    table = pd.DataFrame({"order_id": raw["order_id"], "visible_at": extract_io.to_seconds(raw["visible_at"])})
    rep = dict(brand=brand, **visibility_pairs(w, ext, table))
    print(json.dumps(rep, indent=1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

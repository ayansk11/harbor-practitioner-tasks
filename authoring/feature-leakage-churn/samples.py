"""The live scoring service's log sample for the visible brand, and the evidence asserts (authoring only; called by
gen_data.py).

logs/live_2026-01_sample.jsonl  a 10% sample of the requests of January 2026, the first live month, in time order:
                                one JSON object per line with customer_id, as_of, trigger, features (the 11 values the
                                service computed: ref_truth) and score (churn-hgb-v3's score for those values, 4
                                decimals)
Asserts: the written lines parse back to ref_truth's values cell for cell; the extract's files (seven CSV tables and
`_ops/`) round-trip to the in-memory extract; each mechanism shows in evidence an agent has (the sample, or the
visible extract and its scheduler records); the starting code (v3, the nop) runs on both extracts, equals ref_truth
where the design says v3 is right (tickets_30d, tenure_days, app_minutes_7d) and differs where it says v3 is wrong.
Every January request comes after the move day, so the sample does not show when an order placed before the move
became visible; the scheduler's records do.
"""
import json
import os
import tempfile

import numpy as np
import pandas as pd

import extract_io
import gen_data as G
import mechanisms as M
import ref_truth as R
import v3_model

SAMPLE_SHARE = 0.10
LIVE_NAME = "live_2026-01_sample.jsonl"
ORDER_FEATS = ["orders_7d", "orders_30d", "spend_30d_cents", "days_since_last_order"]


def pick(sp, lo, hi, stream):
    rows = sp[(sp["as_of"] >= lo) & (sp["as_of"] < hi)].sort_values(["as_of", "customer_id"], kind="mergesort")
    keep = np.random.default_rng(stream).random(len(rows)) < SAMPLE_SHARE
    return rows[keep].reset_index(drop=True)


def _json_value(v, col):
    if col in R.STR_FEATS:
        return None if (v is None or (isinstance(v, float) and np.isnan(v))) else str(v)
    if col in R.INT_FEATS:
        return int(v)
    v = float(v)
    return None if np.isnan(v) else v


def lines(rows, scores=None):
    out = []
    for i in range(len(rows)):
        r = rows.iloc[i]
        rec = {"customer_id": int(r["customer_id"]), "as_of": G.iso(r["as_of"]), "trigger": str(r["trigger"]),
               "features": {f: _json_value(r[f], f) for f in R.FEATURES}}
        if scores is not None:
            rec["score"] = round(float(scores[i]), 4)
        out.append(json.dumps(rec))
    return out


def parse(text_lines):
    recs = [json.loads(x) for x in text_lines]
    df = pd.DataFrame([{"customer_id": r["customer_id"], "as_of": G.ts(r["as_of"]), **r["features"]} for r in recs])
    return df


def keyed(df):
    return df.set_index(["customer_id", "as_of"])


def v3_seconds(f):
    f = f.copy()
    f["as_of"] = v3_model.seconds(f["as_of"])
    return f


def compare(a, b, cols):
    """Mismatched cells per feature between two tables with the same row order."""
    return {c: int(M.differs(a[c].to_numpy(), b[c].to_numpy(), c).sum()) for c in cols}


def _layout(folder):
    """The extract folder holds the seven CSV files and `_ops/` with the two record files, nothing else."""
    assert set(os.listdir(folder)) == {n + ".csv" for n in extract_io.TABLES} | {extract_io.OPS_DIR}, folder
    assert set(os.listdir(os.path.join(folder, extract_io.OPS_DIR))) == set(extract_io.OPS_FILES), folder


def build(wv, extv, trv, wh, exth, trh):
    sp = extv["scoring_points"]
    seed = wv["cfg"]["seed"]
    live = pick(sp, G.LIVE_FROM, G.LIVE_TO, [seed, 77])
    tv = keyed(trv)
    live_t = tv.loc[list(zip(live["customer_id"], live["as_of"]))].reset_index()
    live_t["trigger"] = live["trigger"].to_numpy()
    with tempfile.TemporaryDirectory() as tmp:
        vdir, hdir = os.path.join(tmp, "V"), os.path.join(tmp, "H")
        extract_io.write_dataset(extv, vdir)
        extract_io.write_dataset(exth, hdir)
        _layout(vdir)
        _layout(hdir)
        v3v = v3_model.features(vdir)
        fit = v3_model.offline(vdir, v3v)
        v3h = v3_model.features(hdir)
        back = extract_io.read_dataset(vdir)
    for name in extract_io.TABLES:   # the files round-trip to the in-memory extract
        a = extv[name][extract_io.TABLES[name]].sort_values(extract_io.SORT_KEYS[name], kind="mergesort")
        b = back[name][extract_io.TABLES[name]]
        assert len(a) == len(b), name
        for c in extract_io.TABLES[name]:
            x, y = a[c].reset_index(drop=True), b[c].reset_index(drop=True)
            if c == "app_minutes_7d":
                assert np.array_equal(x.to_numpy("float64"), y.to_numpy("float64"), equal_nan=True), (name, c)
            elif c == "last_login_at":
                assert (x.isna() == y.isna()).all() and (x[x.notna()].astype("int64") ==
                                                         y[y.notna()].astype("int64")).all(), (name, c)
            else:
                assert (x.astype(str).to_numpy() == y.astype(str).to_numpy()).all(), (name, c)
    for k in ("tasks", "parity"):    # and so do the scheduler's records, frame for frame
        pd.testing.assert_frame_equal(back["_ops"][k], extv["_ops"][k], check_exact=True)
    live_scores = v3_model.score(fit, live_t[["customer_id", "as_of"] + R.FEATURES])
    live_lines = lines(live_t, live_scores)

    # the sample is ref_truth, cell for cell
    assert compare(parse(live_lines), live_t, R.FEATURES) == {f: 0 for f in R.FEATURES}, "the sample differs"

    # the nop (v3 as shipped) on both extracts against ref_truth
    rep = {"live_rows": len(live_lines), "AUC_OFF_v3": round(fit["auc"], 3)}
    for b, f3, tr in (("visible", v3v, trv), ("H", v3h, trh)):
        f3 = keyed(v3_seconds(f3)).loc[list(zip(tr["customer_id"], tr["as_of"]))].reset_index()
        mm = compare(f3, tr, R.FEATURES)
        rep[f"nop_mismatched_cells_{b}"] = mm
        rep[f"nop_days_since_last_login_non_null_{b}"] = int(f3["days_since_last_login"].notna().sum())
        for c in ("tickets_30d", "tenure_days", "app_minutes_7d"):
            assert mm[c] == 0, (b, c, "v3 should equal ref_truth here")
        for c in ORDER_FEATS + ["status", "plan", "te_district", "days_since_last_login"]:
            assert mm[c] >= 100, (b, c, "v3 should be wrong here")
        assert rep[f"nop_days_since_last_login_non_null_{b}"] > 0
        if b == "visible":
            v3vis = f3

    # evidence an agent has: the January sample
    v3k = keyed(v3vis)
    lv3 = v3k.loc[list(zip(live_t["customer_id"], live_t["as_of"]))].reset_index()
    batch = (live_t["trigger"] == "batch").to_numpy()
    d_orders = np.zeros(len(live_t), bool)
    for c in ORDER_FEATS:
        d_orders |= M.differs(lv3[c].to_numpy(), live_t[c].to_numpy(), c)
    cur_plan = live_t["customer_id"].map(extv["customers"].set_index("customer_id")["plan"])
    pc, pt = live_t["customer_id"].tolist(), live_t["as_of"].tolist()
    var = M.variants(wv, extv, pc, pt)
    ev = {
        "jan_batch_rows": int(batch.sum()),
        "H1_jan_batch_rows_orders_differ_from_event_time": int((d_orders & batch).sum()),
        "H1_jan_rows_status_differs_from_v3": int(M.differs(lv3["status"].to_numpy(), live_t["status"].to_numpy(),
                                                            "status").sum()),
        "H4_jan_rows_plan_differs_from_current_plan": int((cur_plan.to_numpy() != live_t["plan"].to_numpy()).sum()),
        "H4_jan_rows_plan_differs_from_changed_at_rule": int(M.differs(var["plan_changed_at"][1]()["plan"],
                                                                       live_t["plan"].to_numpy(), "plan").sum()),
        "H5_jan_rows_login_differs_from_clip": int(M.differs(lv3["days_since_last_login"].to_numpy(),
                                                             live_t["days_since_last_login"].to_numpy(),
                                                             "days_since_last_login").sum()),
        "H6_jan_rows_te_differs_from_proxy": int(M.differs(lv3["te_district"].to_numpy(),
                                                           live_t["te_district"].to_numpy(), "te_district").sum()),
        "H7_jan_rows_status_differs_from_latest_loaded": int(M.differs(
            var["status_latest_loaded"][1]()["status"], live_t["status"].to_numpy(), "status").sum()),
    }
    n = len(live_t)
    assert ev["H1_jan_batch_rows_orders_differ_from_event_time"] >= 0.5 * ev["jan_batch_rows"], ev
    assert ev["H4_jan_rows_plan_differs_from_current_plan"] >= 5, ev
    assert ev["H5_jan_rows_login_differs_from_clip"] >= 0.5 * n, ev
    assert ev["H6_jan_rows_te_differs_from_proxy"] >= 0.5 * n, ev
    assert ev["H7_jan_rows_status_differs_from_latest_loaded"] >= 2, ev

    # evidence an agent has: the visible extract's scheduler records (legacy runs, the analyze tail, the dual run and
    # the rename) and its export load order
    t = extv["_ops"]["tasks"]
    leg = M.legacy_tasks(extv["_ops"]).sort_values("run", kind="mergesort")
    rolled = (leg["outcome"] == "rollback").to_numpy().astype(int)
    longest, cur = 0, 0
    for x in rolled:
        cur = cur + 1 if x else 0
        longest = max(longest, cur)
    committed = leg[(leg["outcome"] == "commit").to_numpy(dtype=bool)]
    at = committed["at"].to_numpy(dtype="int64")
    late_ok = int(((at % G.DAY) > G.BATCH_AT).sum())
    tail = committed["end_at"].to_numpy(dtype="int64") - at
    hourly = t[(t["job"] == "orders_hourly").to_numpy(dtype=bool)]
    dual = hourly[(hourly["table"] == "orders_new").to_numpy(dtype=bool)]
    part = extv["status_snapshots"].groupby("snapshot_date")["_loaded_at"].max().sort_index()
    ooo = int((part.to_numpy()[:-1] > part.to_numpy()[1:]).sum())
    ev.update({"H3_visible_longest_rollback_streak": longest, "H3_visible_rolled_back_runs": int(rolled.sum()),
               "H3_visible_runs_committed_after_0600": late_ok,
               "visible_runs_ending_3h_or_more_after_their_commit": int((tail >= 3 * G.HOUR).sum()),
               "visible_dual_run_tasks_into_orders_new": len(dual),
               "visible_dual_run_tasks_committed": int((dual["outcome"] == "commit").sum()),
               "visible_parity_lines": len(extv["_ops"]["parity"]),
               "visible_rename_committed_at": G.iso(M.cutover_at(extv["_ops"])),
               "H7_visible_partitions_loaded_after_the_next_days": ooo,
               "H7_visible_2026_01_01_partition_loaded": G.iso(part.loc[G.ts("2026-01-01")])})
    assert 9 <= longest <= 11 and rolled.sum() > longest and late_ok >= 1 and ooo >= 1, ev
    assert ev["visible_runs_ending_3h_or_more_after_their_commit"] >= 1 and len(dual) >= 1, ev
    assert ev["visible_dual_run_tasks_committed"] >= 1 and ev["visible_parity_lines"] >= 1, ev
    assert part.loc[G.ts("2026-01-01")] > part.loc[G.ts("2026-01-02")], ev
    rep["evidence"] = ev
    return {"live": live_lines, "report": rep}


def write(ev, logs_dir):
    os.makedirs(logs_dir, exist_ok=True)
    with open(os.path.join(logs_dir, LIVE_NAME), "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(ev["live"]) + "\n")

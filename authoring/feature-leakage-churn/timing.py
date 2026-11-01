"""Run-time measurements for the cap in grade.py (authoring only; Mac numbers, not the Daytona runner).

1. canonical, alt and original (v3 as shipped) CLI on H (unzipped, as grade.py gives it) and on the visible extract:
   a fresh `python -m churn.build_features` process each time (interpreter start and imports included), isolated
   (-I -B), with the environment the grader gives agent code (kit.RUNNER_ENV, HOME aside), 5 runs each; median, max.
2. a deliberately naive valid approach (per prediction, filter the full frames with pandas boolean masks: the rows
   committed before t, then each query of live/features.py) on the first 600 predictions of H, extrapolated linearly
   to all of H. Its 600 rows are first compared with tests/expected/H_features.parquet (the grader's reference) under
   the instruction's tolerances, so the time is that of a valid approach.
The load average before and after is printed, since other jobs on the Mac change the numbers.
python timing.py
"""
import gzip
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SUBMISSION = os.path.abspath(os.path.join(HERE, "..", ".."))
TASK = os.path.join(SUBMISSION, "tasks", "feature-leakage-churn")
PY = os.path.join(SUBMISSION, ".venv", "bin", "python")
# the environment the grader gives agent code (kit.RUNNER_ENV, HOME aside)
RUNNER_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
              "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1"}
# python -m churn.build_features from the current folder, with the interpreter isolated (-I leaves the cwd out)
CLI = ("import os, runpy, sys; sys.path.insert(0, os.getcwd()); sys.argv = ['churn.build_features'] + sys.argv[1:]; "
       "runpy.run_module('churn.build_features', run_name='__main__', alter_sys=True)")
N_NAIVE = 600

NAIVE = r'''
import json, re, sys, time
import numpy as np, pandas as pd
d, n_rows, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
t_load = time.monotonic()
ts = lambda s: pd.to_datetime(s, utc=True)
sec = lambda s: ((ts(s) - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)).to_numpy(dtype="int64")
cu = pd.read_csv(f"{d}/customers.csv", dtype={"postcode_district": "str"}); cu["signup_at"] = ts(cu.signup_at)
pcg = pd.read_csv(f"{d}/plan_changes.csv"); pcg["changed_at"] = ts(pcg.changed_at); pcg["_loaded_at"] = ts(pcg._loaded_at)
sp = pd.read_csv(f"{d}/scoring_points.csv"); sp["as_of"] = ts(sp.as_of)
od = pd.read_csv(f"{d}/orders.csv"); od["ordered_at"] = ts(od.ordered_at); od["_loaded_at"] = ts(od._loaded_at)
tk = pd.read_csv(f"{d}/tickets.csv"); tk["opened_at"] = ts(tk.opened_at); tk["_loaded_at"] = ts(tk._loaded_at)
sn = pd.read_csv(f"{d}/status_snapshots.csv"); sn["snapshot_date"] = ts(sn.snapshot_date); sn["_loaded_at"] = ts(sn._loaded_at)
lb = pd.read_csv(f"{d}/labels.csv"); lb["_loaded_at"] = ts(lb._loaded_at)
dist = cu.set_index("customer_id").postcode_district; lb["district"] = lb.customer_id.map(dist)
signup, plan_now = cu.set_index("customer_id").signup_at, cu.set_index("customer_id").plan
# when each order became visible, from the scheduler's records in _ops/: an order below the last committed legacy
# watermark at the commit of the committed legacy_orders range that holds it, any later one at the later of its
# _loaded_at and the commit of the rename that gave orders_new the name orders
com = {o["txn"]: o for o in map(json.loads, open(f"{d}/_ops/commits.jsonl"))}
load = re.compile(r"selected orders where ordered_at >= \S+ and ordered_at < (\S+): \d+ rows; sent txn (\d+) to commit "
                  r"into orders")
ranges, renamed, cutover = [], set(), None
for line in open(f"{d}/_ops/scheduler.log"):
    _, job, run, event = line.rstrip("\n").split(" ", 3)
    m = load.fullmatch(event) if job == "legacy_orders" else None
    if m and com[int(m[2])]["outcome"] == "commit":
        ranges.append((m[1], com[int(m[2])]["at"]))
    elif job == "schema_migrations" and event == "statement: ALTER TABLE orders_new RENAME TO orders":
        renamed.add(run)
    elif job == "schema_migrations" and run in renamed and event.startswith("sent txn "):
        c = com[int(event.split()[2])]
        cutover = c["at"] if c["outcome"] == "commit" else cutover
hi, at = sec(pd.Series([r[0] for r in ranges])), sec(pd.Series([r[1] for r in ranges]))
order = np.argsort(hi, kind="stable")
hi, at = hi[order], at[order]
x = sec(od.ordered_at)
vis = np.maximum(sec(od._loaded_at), sec(pd.Series([cutover]))[0])
held = x < hi[-1]
vis[held] = at[np.searchsorted(hi, x[held], side="right")]
od["visible_at"] = pd.to_datetime(vis, unit="s", utc=True)
W7, W30, DAY = pd.Timedelta(days=7), pd.Timedelta(days=30), pd.Timedelta(days=1)
t0 = time.monotonic(); rows = []
for r in sp.head(n_rows).itertuples():
    c, t = r.customer_id, r.as_of
    o = od[(od.customer_id == c) & (od.visible_at < t) & (od.ordered_at < t)]
    o30 = o[o.ordered_at >= t - W30]
    k = tk[(tk.customer_id == c) & (tk._loaded_at < t) & (tk.opened_at >= t - W30) & (tk.opened_at < t)]
    s = sn[(sn.customer_id == c) & (sn._loaded_at < t)]
    ch = pcg[pcg.customer_id == c]; chv = ch[ch._loaded_at < t]
    plan = (chv.loc[chv.changed_at.idxmax(), "new_plan"] if len(chv) else
            ch.loc[ch.changed_at.idxmin(), "old_plan"] if len(ch) else plan_now[c])
    a = sp[(sp.customer_id == c) & (sp.as_of < t) & sp.app_minutes_7d.notna()]
    app = r.app_minutes_7d if not np.isnan(r.app_minutes_7d) else (
        a.loc[a.as_of.idxmax(), "app_minutes_7d"] if len(a) else np.nan)
    L = lb[lb._loaded_at < t]; Ld = L[L.district == dist[c]]
    p = L.churned_30d.sum() / len(L) if len(L) else 0.05
    rows.append({"customer_id": c, "as_of": t, "orders_7d": int((o.ordered_at >= t - W7).sum()),
                 "orders_30d": len(o30), "spend_30d_cents": int(o30.amount_cents.sum()), "tickets_30d": len(k),
                 "days_since_last_order": (t - o.ordered_at.max()) / DAY if len(o) else np.nan,
                 "tenure_days": (t - signup[c]) / DAY,
                 "status": s.loc[s.snapshot_date.idxmax(), "status"] if len(s) else None, "plan": plan,
                 "app_minutes_7d": app, "te_district": (Ld.churned_30d.sum() + 20 * p) / (len(Ld) + 20)})
loop = time.monotonic() - t0
pd.DataFrame(rows).to_parquet(out, index=False)
print(t0 - t_load, loop, len(sp))
'''


def app_copy(tmp, name):
    app = os.path.join(tmp, f"app_{name}")
    shutil.copytree(os.path.join(TASK, "environment", "app"), app,
                    ignore=shutil.ignore_patterns("data", "__pycache__", ".venv"))
    if name != "original":
        src = os.path.join(TASK, "solution", name, "churn")
        for f in sorted(os.listdir(src)):
            if f.endswith(".py"):
                shutil.copy(os.path.join(src, f), os.path.join(app, "churn", f))
    return app


def main():
    import pandas as pd
    import make_expected as ME
    print(f"load average before: {os.getloadavg()}")
    with tempfile.TemporaryDirectory() as tmp:
        h = os.path.join(tmp, "H")
        src = os.path.join(TASK, "tests", "hidden", "H")
        for root, _, files in os.walk(src):  # unzipped as grade.py does, the _ops/ folder too
            dst = os.path.join(h, os.path.relpath(root, src))
            os.makedirs(dst, exist_ok=True)
            for f in sorted(files):
                with gzip.open(os.path.join(root, f)) as a, open(os.path.join(dst, f[:-3]), "wb") as b:
                    shutil.copyfileobj(a, b)
        extracts = {"H": h, "visible": os.path.join(TASK, "environment", "app", "data")}
        for name in ("canonical", "alt", "original"):
            app = app_copy(tmp, name)
            for ext, data in extracts.items():
                times = []
                for i in range(5):
                    t0 = time.monotonic()
                    subprocess.run([PY, "-I", "-B", "-c", CLI, "--data", data, "--out",
                                    os.path.join(tmp, f"{name}_{ext}_{i}.parquet")], cwd=app, check=True,
                                   capture_output=True, env=dict(RUNNER_ENV, HOME=app))
                    times.append(time.monotonic() - t0)
                print(f"{name:10s} on {ext:7s} runs (s): {[round(t, 2) for t in times]} median "
                      f"{statistics.median(times):.2f} max {max(times):.2f}", flush=True)
        out = os.path.join(tmp, "naive.parquet")
        r = subprocess.run([PY, "-I", "-B", "-c", NAIVE, h, str(N_NAIVE), out], capture_output=True, text=True,
                           check=True, env=dict(RUNNER_ENV, HOME=tmp))
        setup, loop, rows = r.stdout.split()
        setup, loop, rows = float(setup), float(loop), int(rows)
        got = pd.read_parquet(out)
        exp = pd.read_parquet(os.path.join(TASK, "tests", "expected", "H_features.parquet"))
        keys = pd.MultiIndex.from_arrays([got["customer_id"].astype("int64"), ME.seconds_of(got["as_of"])])
        exp = exp[pd.MultiIndex.from_arrays([exp["customer_id"], exp["as_of"]]).isin(keys)].reset_index(drop=True)
        rep = ME.compare(got, exp)
        print(f"naive per-row pandas filtering, first {N_NAIVE} rows of H vs tests/expected: rows {rep['rows']}, "
              f"mismatched cells {rep['mismatched_cells']}, missing {rep['missing_rows']}, extra {rep['extra_rows']}"
              f" ({'valid' if rep['ok'] else 'NOT VALID'})")
        print(f"naive: load and setup {setup:.1f} s, {loop:.1f} s for {N_NAIVE} predictions -> about "
              f"{setup + loop / N_NAIVE * rows:.0f} s for all {rows} (linear extrapolation)")
    print(f"load average after: {os.getloadavg()}")


if __name__ == "__main__":
    main()

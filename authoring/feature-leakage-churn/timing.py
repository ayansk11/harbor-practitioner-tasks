"""Run-time measurements for the cap in grade.py (authoring only; Mac numbers, not the Daytona runner).

1. canonical, alt and original CLI on the hidden extract H: fresh `python -m churn.build_features` process each time,
   with the grader's environment variables (kit.RUNNER_ENV), 5 runs each, median and max (this is what one grader run costs, interpreter start and imports included).
2. a deliberately naive valid approach (filter the full orders/tickets/snapshots/labels frames once per prediction,
   pandas boolean masks) on the first 600 predictions of H, extrapolated linearly to all of H.
python timing.py
"""
import gzip, os, shutil, statistics, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
SUBMISSION = os.path.abspath(os.path.join(HERE, "..", ".."))
TASK = os.path.join(SUBMISSION, "tasks", "feature-leakage-churn")
PY = os.path.join(SUBMISSION, ".venv", "bin", "python")
# the environment the grader gives agent code (kit.RUNNER_ENV, HOME aside)
RUNNER_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
              "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1"}

NAIVE = r'''
import sys, time
import numpy as np, pandas as pd
d = sys.argv[1]; n_rows = int(sys.argv[2])
ts = lambda s: pd.to_datetime(s, utc=True)
cu = pd.read_csv(f"{d}/customers.csv"); cu["signup_at"] = ts(cu.signup_at)
sp = pd.read_csv(f"{d}/scoring_points.csv"); sp["as_of"] = ts(sp.as_of)
od = pd.read_csv(f"{d}/orders.csv"); od["ordered_at"] = ts(od.ordered_at)
tk = pd.read_csv(f"{d}/tickets.csv"); tk["opened_at"] = ts(tk.opened_at)
sn = pd.read_csv(f"{d}/status_snapshots.csv"); sn["snapshot_date"] = ts(sn.snapshot_date)
lb = pd.read_csv(f"{d}/labels.csv"); lb["label_available_at"] = ts(lb.label_available_at)
dist = cu.set_index("customer_id").postcode_district; lb["district"] = lb.customer_id.map(dist)
W7, W30 = pd.Timedelta(days=7), pd.Timedelta(days=30)
t0 = time.monotonic(); out = []
for r in sp.head(n_rows).itertuples():
    c, t = r.customer_id, r.as_of
    o = od[(od.customer_id == c) & (od.ordered_at < t)]
    o30 = o[o.ordered_at >= t - W30]
    k = tk[(tk.customer_id == c) & (tk.opened_at < t) & (tk.opened_at >= t - W30)]
    s = sn[(sn.customer_id == c) & (sn.snapshot_date < t.floor("D"))]
    a = sp[(sp.customer_id == c) & (sp.as_of <= t) & sp.app_minutes_7d.notna()]
    L = lb[lb.label_available_at < t]; Ld = L[L.district == dist[c]]
    p = L.churned_30d.mean() if len(L) else 0.05
    out.append((len(o[o.ordered_at >= t - W7]), len(o30), int(o30.amount_cents.sum()), len(k),
                s.sort_values("snapshot_date").status.iloc[-1] if len(s) else None,
                a.sort_values("as_of").app_minutes_7d.iloc[-1] if len(a) else None,
                (Ld.churned_30d.sum() + 20 * p) / (len(Ld) + 20)))
print(time.monotonic() - t0, len(sp))
'''


def main():
    with tempfile.TemporaryDirectory() as tmp:
        h = os.path.join(tmp, "H")
        os.makedirs(h)
        src = os.path.join(TASK, "tests", "hidden", "H")
        for f in os.listdir(src):
            with gzip.open(os.path.join(src, f)) as a, open(os.path.join(h, f[:-3]), "wb") as b:
                shutil.copyfileobj(a, b)
        for name in ("canonical", "alt", "original"):
            app = os.path.join(tmp, name)
            shutil.copytree(os.path.join(TASK, "environment", "app"), app,
                            ignore=shutil.ignore_patterns("data", "__pycache__"))
            if name != "original":
                for f in os.listdir(os.path.join(TASK, "solution", name, "churn")):
                    shutil.copy(os.path.join(TASK, "solution", name, "churn", f), os.path.join(app, "churn", f))
            times = []
            for i in range(5):
                t0 = time.monotonic()
                subprocess.run([PY, "-m", "churn.build_features", "--data", h, "--out",
                                os.path.join(tmp, f"{name}{i}.parquet")], cwd=app, check=True, capture_output=True,
                               env=RUNNER_ENV)
                times.append(time.monotonic() - t0)
            print(f"{name:10s} runs on H (s): {[round(t, 2) for t in times]} median {statistics.median(times):.2f}"
                  f" max {max(times):.2f}")
        n = 600
        r = subprocess.run([PY, "-c", NAIVE, h, str(n)], capture_output=True, text=True, check=True, env=RUNNER_ENV)
        secs, rows = r.stdout.split()
        secs, rows = float(secs), int(rows)
        print(f"naive per-row pandas filtering: {secs:.1f} s for {n} predictions -> about {secs / n * rows:.0f} s "
              f"for all {rows} (linear extrapolation)")


if __name__ == "__main__":
    main()

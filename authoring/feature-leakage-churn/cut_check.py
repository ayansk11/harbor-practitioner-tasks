"""Cuts through check B's perturbation, beyond the two graded ones (authoring only; grade.py runs the graded cuts).

python cut_check.py [--random N] [--seed S] [--extract DIR] [--no-solutions] [--corrupt] [--json FILE]

For every cut: perturb.perturb(H, cut, seed), then invariants.check(H, copy, cut), which must find no problem; then
the canonical and the alt solution (each applied to a copy of environment/app/churn as solve.sh applies it) run their
CLI on H and on the copy, as fresh processes with the environment the grader gives agent code (OMP_NUM_THREADS=1): on
the copy, each solution's rows with as_of <= cut must equal its own rows on H (check B's rule, compare.py's
tolerances), each must give one row per scoring point of the copy with days_since_last_login all null, and the two
must agree on every row of the copy. The cuts:
- the graded ones, with their seeds (read from tests/grade.py), each perturbed twice to show the copy is the same;
- targeted ones from H's records: inside a legacy load (after its sent line, before its commit) before D0 and after
  it, inside a rolled-back legacy load, D0 itself, inside the backfill and the D0 run, the move day C, inside C's
  legacy load, inside the parity lines, inside the cutover (sent, not yet committed), after it, just after a dual-run
  commit, just after a rolled-back hourly run, inside the drop;
- N random ones (seeded), uniform over the scoring period up to two days before the extract.
A cut never falls on the second of a commit of H (the invariant "no commit at the cut" would report the cut itself).
--corrupt also applies hand-made corruptions to the copies of the graded cuts, each breaking one documented rule, and
requires invariants.check to report every one.
H: --extract DIR (a plain extract: seven CSV files and _ops/), else tests/hidden/H unzipped (its _ops/*.gz too) into
a temporary folder. Temporary folders go under $TMPDIR. Exit status 0 iff every cut is clean (and, with --corrupt,
every corruption is reported).
"""
import argparse
import ast
import glob
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SUBMISSION = os.path.abspath(os.path.join(HERE, "..", ".."))
TASK = os.path.join(SUBMISSION, "tasks", "feature-leakage-churn")
TESTS = os.path.join(TASK, "tests")
PY = os.path.join(SUBMISSION, ".venv", "bin", "python")
sys.path.insert(0, TESTS)
import compare as C  # noqa: E402
import dataset_io as D  # noqa: E402
import invariants as INV  # noqa: E402
import ops_io as OPS  # noqa: E402
import perturb as PT  # noqa: E402

DAY, HOUR = 86400, 3600
SOLUTIONS = ("canonical", "alt")
RUN_CLI = ("import os, runpy, sys; sys.path.insert(0, os.getcwd()); sys.argv = ['churn.build_features'] + "
           "sys.argv[1:]; runpy.run_module('churn.build_features', run_name='__main__', alter_sys=True)")
RUN_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1"}
GRADED = [("cut1", "2024-11-27T06:00:00Z", 101), ("cut2", "2025-11-14T08:13:16Z", 202)]   # if grade.py has no CUTS


def secs(text):
    return int(pd.Timestamp(text).value // 10 ** 9)


def iso(sec):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(sec)))


def graded_cuts():
    """grade.py's CUTS: (name, ISO time, seed) per graded cut."""
    tree = ast.parse(open(os.path.join(TESTS, "grade.py")).read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "CUTS" for t in node.targets):
            return [tuple(c[:3]) for c in ast.literal_eval(node.value)]
    return GRADED


def unzip_extract(src, dst):
    """A copy of an extract folder with every .gz file unzipped (subfolders such as _ops/ included)."""
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        out = os.path.join(dst, os.path.relpath(root, src))
        os.makedirs(out, exist_ok=True)
        for f in sorted(files):
            if f.startswith("."):
                continue
            if f.endswith(".gz"):
                with gzip.open(os.path.join(root, f)) as a, open(os.path.join(out, f[:-3]), "wb") as b:
                    shutil.copyfileobj(a, b)
            else:
                shutil.copy(os.path.join(root, f), os.path.join(out, f))
    return dst


def digest(folder):
    """SHA-256 over every file of a folder (relative path and bytes), in path order."""
    h = hashlib.sha256()
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            h.update(os.path.relpath(p, folder).encode() + b"\0")
            with open(p, "rb") as g:
                h.update(g.read())
    return h.hexdigest()


# ------------------------------------------------------------------ the cuts
def commit_seconds(h):
    """Every commit second of H: task commits, every table's _loaded_at, customer writes and order visibility."""
    t = h["_ops"]["tasks"]
    parts = [t["at"].dropna().to_numpy(dtype=np.int64), h["customers"]["_updated_at"].to_numpy(dtype=np.int64),
             INV.order_visible_at(h["orders"], t)]
    parts += [h[n]["_loaded_at"].to_numpy(dtype=np.int64) for n in ("orders", "tickets", "status_snapshots",
                                                                   "labels", "plan_changes")]
    return np.unique(np.concatenate(parts))


def off_commits(cut, forbidden):
    cut = int(cut)
    while np.isin(cut, forbidden):
        cut += 1
    return cut


def targeted_cuts(h):
    """(kind, cut) pairs from H's records (each kind only if H has such a moment)."""
    v = INV._view(h["_ops"]["tasks"])
    job, com = v["job"], v["outcome"] == "commit"
    st, se, at, hi = v["started_at"], v["sent_at"], v["at"], v["hi"]
    first_point = int(h["scoring_points"]["as_of"].min())
    L = np.flatnonzero(job == "legacy_orders")
    C_, D0 = int(hi[L].max()), int(hi[job == "legacy_backfill"].max())
    out = []

    def middle(idx):
        return int(idx[len(idx) // 2]) if len(idx) else None

    gap = (at - se >= 2) & (se > first_point)
    for kind, m in (("legacy_inside_pre_D0", (job == "legacy_orders") & com & gap & (hi < D0)),
                    ("legacy_inside_dual", (job == "legacy_orders") & com & gap & (hi > D0) & (hi < C_)),
                    ("legacy_inside_rollback", (job == "legacy_orders") & ~com & gap)):
        i = middle(np.flatnonzero(m))
        if i is not None:
            out.append((kind, se[i] + 1))
    def inside(kind, i):
        """A cut after task i's sent line and before its commit, when a whole second lies between them."""
        if at[i] - se[i] >= 2:
            out.append((kind, se[i] + 1))

    out.append(("D0", D0))
    inside("D0_run_inside", int(np.flatnonzero((job == "legacy_orders") & (hi == D0))[0]))
    inside("backfill_inside", int(np.flatnonzero(job == "legacy_backfill")[0]))
    out.append(("C", C_))
    inside("C_run_inside", int(np.flatnonzero((job == "legacy_orders") & (hi == C_))[0]))
    q = int(np.flatnonzero(job == "dq_checks")[0])
    out.append(("parity_inside", st[q] + 1 + (C_ - D0) // DAY // 2))
    stm = [str(s).split("; ") for s in v["statements"]]
    x = [i for i in range(len(job)) if job[i] == "schema_migrations" and INV.RENAME in stm[i]][0]
    d = [i for i in range(len(job)) if job[i] == "schema_migrations" and INV.DROP in stm[i]][0]
    inside("cutover_inside", x)
    out.append(("after_cutover", at[x] + 1))
    hr = job == "orders_hourly"
    i = middle(np.flatnonzero(hr & com & (v["table"] == "orders_new")))
    if i is not None:
        out.append(("after_dual_commit", at[i] + 1))
    i = middle(np.flatnonzero(hr & ~com))
    if i is not None:
        out.append(("after_hourly_rollback", at[i] + 1))
    inside("drop_inside", d)
    return out


# ------------------------------------------------------------------ the solutions
def app_copy(sol, tmp):
    """environment/app/churn with solution/<sol>/churn/*.py copied over it, as solve.sh applies a solution."""
    app = os.path.join(tmp, sol)
    shutil.copytree(os.path.join(TASK, "environment", "app", "churn"), os.path.join(app, "churn"),
                    ignore=shutil.ignore_patterns("__pycache__", ".*"))
    for f in sorted(glob.glob(os.path.join(TASK, "solution", sol, "churn", "*.py"))):
        shutil.copy(f, os.path.join(app, "churn", os.path.basename(f)))
    return app


def run_all(apps, data, outdir):
    """Run every solution's CLI on one extract at once; returns {solution: (normalised frame, non-null count of the
    left-out column)}."""
    procs = {}
    for sol, app in apps.items():
        out = os.path.join(outdir, f"{sol}.parquet")
        procs[sol] = (subprocess.Popen([PY, "-I", "-B", "-c", RUN_CLI, "--data", data, "--out", out], cwd=app,
                                       env=dict(RUN_ENV, HOME=app), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                       text=True), out)
    res = {}
    for sol, (proc, out) in procs.items():
        _, err = proc.communicate(timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(f"{sol} failed on {data} (exit {proc.returncode}): {err[-800:]}")
        df = pd.read_parquet(out)
        res[sol] = (C.normalise(df), C.dropped_nonnull(df))
    return res


def judge(cut, got, base, points):
    """The solutions' problems on one copy (empty when check B's rule and the agreement hold)."""
    probs = []
    for sol, (g, nn) in got.items():
        ok_k, kd = C.key_check(g, points)
        bg = base[sol][0]
        ok_b, bd = C.compare(g[g["as_of"] <= cut], bg[bg["as_of"] <= cut])
        if not ok_k:
            probs.append(f"{sol}: keys {kd}")
        if not ok_b:
            probs.append(f"{sol}: rows at or before the cut changed: {bd}")
        if nn:
            probs.append(f"{sol}: {nn} non-null days_since_last_login values")
    if len(got) == 2:
        ok_a, ad = C.compare(got["canonical"][0], got["alt"][0])
        if not ok_a:
            probs.append(f"canonical and alt differ on the copy: {ad}")
    return probs


# ------------------------------------------------------------------ hand-made corruptions
def _copy(p):
    q = {k: v.copy() for k, v in p.items() if k != "_ops"}
    q["_ops"] = {k: v.copy() for k, v in p["_ops"].items()}
    return q


def _recount(q):
    q["_ops"] = OPS.recount(q["_ops"], q)
    return q


def corruptions(h, p, cut):
    """(name, corrupted copy) pairs, each breaking one rule that invariants.check holds; a corruption that has no
    target at this cut is left out."""
    out = []
    t = p["_ops"]["tasks"]
    v = INV._view(t)
    job, com, se, at = v["job"], v["outcome"] == "commit", v["sent_at"], v["at"]
    vis = INV.order_visible_at(p["orders"], t)

    def add(name, fn):
        q = fn(_copy(p))
        if q is not None:
            out.append((name, q))

    def amount(q):
        i = np.flatnonzero(vis < cut)[0]
        q["orders"].loc[q["orders"].index[i], "amount_cents"] += 1
        return q
    add("visible order amount changed", amount)

    def point(q):
        i = q["scoring_points"].index[np.flatnonzero(q["scoring_points"]["as_of"].to_numpy() <= cut)[0]]
        q["scoring_points"].loc[i, "app_minutes_7d"] = 12345.0
        return q
    add("kept scoring point changed", point)

    def sent_task(q):
        i = np.flatnonzero((se >= 0) & (se < cut) & (at > cut))
        i = i if len(i) else np.flatnonzero((se >= 0) & (se < cut))
        k = q["_ops"]["tasks"].index[int(i[-1])]
        q["_ops"]["tasks"].loc[k, "end_at"] += 7
        return q
    add("task sent before the cut changed (its end)", sent_task)

    def flip(q):
        i = np.flatnonzero((job == "legacy_orders") & ~com & (se >= 0) & (se < cut))
        if not len(i):
            return None
        tt = q["_ops"]["tasks"]
        k = tt.index[int(i[-1])]
        tt.loc[k, ["outcome", "state"]] = ["commit", "success"]
        tt.loc[k, "analyze_at"] = int(tt.loc[k, "at"]) + 1
        return q
    add("rolled-back legacy load sent before the cut made a commit", flip)

    def flip_chained(q):
        i = np.flatnonzero((job == "legacy_orders") & ~com & (se >= 0) & (se < cut))
        if not len(i):
            return None
        tt = q["_ops"]["tasks"]
        k = tt.index[int(i[-1])]
        tt.loc[k, ["outcome", "state"]] = ["commit", "success"]
        tt.loc[k, "analyze_at"] = int(tt.loc[k, "at"]) + 1
        tt.loc[k, "end_at"] = max(int(tt.loc[k, "end_at"]), int(tt.loc[k, "at"]) + 2)
        leg = tt.index[(tt["job"] == "legacy_orders").to_numpy()]
        leg = leg[np.argsort(tt.loc[leg, "hi"].to_numpy(dtype=np.int64), kind="mergesort")]
        prev = INV.T0
        for r in leg.tolist():           # every range starts at the end of the last committed one again
            tt.loc[r, "lo"] = prev
            if tt.loc[r, "outcome"] == "commit":
                prev = int(tt.loc[r, "hi"])
        return _recount(q)
    add("rolled-back legacy load sent before the cut made a commit (chain and counts redone)", flip_chained)

    def drop_pending(q):
        tt = q["_ops"]["tasks"]
        ld = np.flatnonzero(np.isin(job, ["legacy_orders", "orders_hourly"]) & (se >= 0) & (se < cut))
        x = q["orders"]["ordered_at"].to_numpy(dtype=np.int64)
        inside = np.zeros(len(x), dtype=bool)
        for i in ld.tolist():
            inside |= (x >= v["lo"][i]) & (x < v["hi"][i])
        cand = np.flatnonzero(inside & (vis >= cut))
        if not len(cand):
            return None
        q["orders"] = q["orders"].drop(q["orders"].index[int(cand[0])]).reset_index(drop=True)
        return _recount(q)
    add("order not yet visible dropped from a range sent before the cut (counts redone)", drop_pending)

    def parity(q):
        q["_ops"]["parity"].loc[q["_ops"]["parity"].index[0], "rows_a"] += 1
        return q
    add("parity count changed", parity)

    def count(q):
        i = np.flatnonzero((job == "billing_export") & (se >= cut))
        if not len(i):
            return None
        q["_ops"]["tasks"].loc[q["_ops"]["tasks"].index[int(i[0])], "rows"] += 1
        return q
    add("row count of a later write changed", count)

    def swap(q):
        i = np.flatnonzero((v["txn"] >= 0) & (se >= cut))
        if len(i) < 2:
            return None
        tt = q["_ops"]["tasks"]
        a, b = tt.index[int(i[0])], tt.index[int(i[-1])]
        ta, tb = tt.loc[a, "txn"], tt.loc[b, "txn"]
        tt.loc[a, "txn"], tt.loc[b, "txn"] = tb, ta
        return q
    add("two later txns swapped", swap)

    def partition(q):
        s = q["status_snapshots"]
        i = np.flatnonzero(s["_loaded_at"].to_numpy() > cut)
        if not len(i):
            return None
        d = s["snapshot_date"].iloc[int(i[0])]
        s.loc[s["snapshot_date"] == d, "_loaded_at"] += 1
        return q
    add("later status partition off its billing_export commit", partition)

    def label(q):
        lb = q["labels"]
        lj = np.flatnonzero(com & (job == "label_job"))
        start = lb["_loaded_at"].map(dict(zip(at[lj].tolist(), v["started_at"][lj].tolist())))
        i = np.flatnonzero((lb["_loaded_at"].to_numpy() > cut) & (lb["churned_30d"].to_numpy() == 1)
                           & (start.to_numpy() <= lb["as_of"].to_numpy() + 30 * DAY))
        if not len(i):
            return None
        lb.loc[lb.index[int(i[0])], "churned_30d"] = 0
        return q
    add("later label of 1 set to 0 in a run before its 30 days passed", label)

    def plan_late(q):
        pc = q["plan_changes"]
        cs = np.flatnonzero(com & (job == "crm_sync"))
        cs = cs[np.argsort(v["started_at"][cs])]
        nxt = dict(zip(at[cs][:-1].tolist(), at[cs][1:].tolist()))
        i = np.flatnonzero((pc["_loaded_at"].to_numpy() > cut) & pc["_loaded_at"].isin(list(nxt)).to_numpy())
        if not len(i):
            return None
        k = pc.index[int(i[0])]
        pc.loc[k, "_loaded_at"] = nxt[int(pc.loc[k, "_loaded_at"])]
        return _recount(q)
    add("later plan change applied by a later sync than the first after it (counts redone)", plan_late)

    def hourly(q):
        i = np.flatnonzero((job == "orders_hourly") & (se >= cut))
        if not len(i):
            return None
        q["_ops"]["tasks"].loc[q["_ops"]["tasks"].index[int(i[0])], "started_at"] -= 1
        return q
    add("later hourly run re-timed", hourly)

    def ticket(q):
        k = q["tickets"]
        i = np.flatnonzero(k["_loaded_at"].to_numpy() > cut + 60)
        if not len(i):
            return None
        r = k.index[int(i[0])]
        k.loc[r, "_loaded_at"] = int(k.loc[r, "opened_at"]) + 31
        return q
    add("later ticket captured 31 s after opening", ticket)

    def login(q):
        cu = q["customers"]
        cs = np.flatnonzero(com & (job == "crm_sync"))
        start = cu["_updated_at"].map(dict(zip(at[cs].tolist(), v["started_at"][cs].tolist())))
        i = np.flatnonzero((cu["_updated_at"].to_numpy() > cut) & start.notna().to_numpy())
        if not len(i):
            return None
        r = cu.index[int(i[0])]
        cu.loc[r, "last_login_at"] = int(start.iloc[int(i[0])]) + 1
        return q
    add("later customer record with a login after its sync's start", login)

    def wrong_load(q):
        o = q["orders"]
        hc = np.flatnonzero(com & (job == "orders_hourly"))
        hc = hc[np.argsort(v["hi"][hc])]
        ats = at[hc]
        i = np.flatnonzero((o["_loaded_at"].to_numpy() > cut) & np.isin(o["_loaded_at"].to_numpy(), ats[:-1]))
        if not len(i):
            return None
        r = o.index[int(i[0])]
        o.loc[r, "_loaded_at"] = int(ats[np.searchsorted(ats, int(o.loc[r, "_loaded_at"])) + 1])
        return q
    add("later order loaded by the hourly commit after its own", wrong_load)

    def gone(q):
        tt = q["_ops"]["tasks"]
        i = np.flatnonzero((job == "label_job") & (v["state"] == "failed") & (v["started_at"] >= cut))
        if not len(i):
            return None
        q["_ops"]["tasks"] = tt.drop(tt.index[int(i[0])]).reset_index(drop=True)
        return q
    add("later failed label_job run removed (it sent nothing)", gone)
    return out


# ------------------------------------------------------------------ main
def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--random", type=int, default=20, help="random cuts (default 20)")
    ap.add_argument("--seed", type=int, default=20261031, help="seed of the random cuts and their perturbations")
    ap.add_argument("--extract", help="a plain extract folder (default: tests/hidden/H, unzipped)")
    ap.add_argument("--no-solutions", action="store_true", help="perturb and invariants only")
    ap.add_argument("--corrupt", action="store_true", help="also check that hand-made corruptions are reported")
    ap.add_argument("--json", help="write the per-cut results here")
    a = ap.parse_args(argv)
    t_start = time.time()
    with tempfile.TemporaryDirectory(prefix="cut-check-") as tmp:
        src = a.extract or unzip_extract(os.path.join(TESTS, "hidden", "H"), os.path.join(tmp, "H"))
        h = D.read_dataset(src)
        forbidden = commit_seconds(h)
        rng = np.random.default_rng(a.seed)
        cuts = [(f"graded_{n}", secs(c), int(s)) for n, c, s in graded_cuts()]
        cuts += [(k, off_commits(c, forbidden), 1000 + i) for i, (k, c) in enumerate(targeted_cuts(h))]
        lo, hi = int(h["scoring_points"]["as_of"].min()), INV.END - 2 * DAY
        for i in range(a.random):
            cuts.append((f"random_{i + 1}", off_commits(int(rng.integers(lo, hi)), forbidden),
                         int(rng.integers(1, 10 ** 6))))
        apps, base = {}, {}
        if not a.no_solutions:
            for sol in SOLUTIONS:
                apps[sol] = app_copy(sol, tmp)
            os.makedirs(os.path.join(tmp, "out_H"))
            base = run_all(apps, src, os.path.join(tmp, "out_H"))
            ref = os.path.join(src, "truth.parquet")       # gen_data.py --out writes each brand's live values here
            ref = ref if os.path.exists(ref) else os.path.join(TESTS, "expected", "H_features.parquet")
            exp = C.load_expected(ref)
            name = "the extract's truth.parquet" if ref.startswith(src) else "tests/expected/H_features.parquet"
            for sol in SOLUTIONS:
                ok, det = C.compare(base[sol][0], exp)
                print(f"{sol} on the extract vs {name}: mismatched_cells {det['mismatched_cells']}, missing "
                      f"{det['missing_rows']}, extra {det['extra_rows']}")
        results, bad = [], []
        for kind, cut, seed in cuts:
            t0 = time.time()
            p = PT.perturb(h, cut, seed)
            probs = INV.check(h, p, cut)
            folder = os.path.join(tmp, "copy")
            shutil.rmtree(folder, ignore_errors=True)
            D.write_dataset(p, folder)
            sha = digest(folder)
            rec = {"kind": kind, "cut": iso(cut), "seed": seed, "invariant_problems": probs, "copy_sha256": sha,
                   "points": int(len(p["scoring_points"])), "kept_points": int((p["scoring_points"]["as_of"]
                                                                                 <= cut).sum())}
            if kind.startswith("graded_"):
                again = os.path.join(tmp, "again")
                shutil.rmtree(again, ignore_errors=True)
                D.write_dataset(PT.perturb(h, cut, seed), again)
                rec["same_copy_twice"] = digest(again) == sha
                if not rec["same_copy_twice"]:
                    probs = probs + ["the copy differs between two perturbations with the same seed"]
            sol_probs = []
            if apps:
                outdir = os.path.join(tmp, "out")
                shutil.rmtree(outdir, ignore_errors=True)
                os.makedirs(outdir)
                got = run_all(apps, folder, outdir)
                sol_probs = judge(cut, got, base, p["scoring_points"])
            rec["solution_problems"] = sol_probs
            if a.corrupt and kind.startswith("graded_"):
                missed = []
                cor = corruptions(h, p, cut)
                for name, q in cor:
                    try:
                        found = INV.check(h, q, cut)
                    except Exception as e:  # a crash is not a report
                        found = []
                        name += f" (check raised {type(e).__name__}: {e})"
                    if not found:
                        missed.append(name)
                rec["corruptions"], rec["corruptions_missed"] = len(cor), missed
                print(f"  {kind}: {len(cor) - len(missed)} of {len(cor)} corruptions reported"
                      + (f"; MISSED: {missed}" if missed else ""))
            rec["seconds"] = round(time.time() - t0, 1)
            clean = not probs and not sol_probs and not rec.get("corruptions_missed")
            bad += [] if clean else [kind]
            results.append(rec)
            print(f"{kind:24s} {iso(cut)} seed {seed:7d} | points {rec['points']} kept {rec['kept_points']} | "
                  f"invariant problems {len(probs)} | solutions {'skipped' if not apps else len(sol_probs)} | "
                  f"copy {sha[:12]} | {rec['seconds']}s"
                  + ("" if clean else " | " + "; ".join((probs + sol_probs)[:4])))
    print(f"{len(results)} cuts in {time.time() - t_start:.0f}s: "
          + ("ALL CLEAN" if not bad else f"PROBLEMS at {len(bad)} cuts: {bad}"))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(results, f, indent=1, sort_keys=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Hit report for the attempts of feature-leakage-churn (authoring only): writes hit_report.json next to this file and
prints a table. DESIGN.md cites it.

The rule it checks (the approved design, section 5): every attempt killed by check A moves at least 100 graded cells
on H and on the visible extract, so each mechanism shows in the agent's own data; an attempt killed only by a check-B
cut moves more than 0 cells at that cut, and its mechanism occurs in the visible extract. The exceptions are named in
EXCEPTIONS: cache_visible on the visible extract, and since the operations-log revision (2026-10-31) hourly_schedule,
killed by check A alone, which must move at least 1 cell on each extract.

For each variant of local_check.VARIANTS: apply it to a fresh copy of environment/app as the local matrix does, run
its CLI on the visible extract (environment/app/data) and on H (tests/hidden/H, unzipped as grade.py does), compare
each output with ref_truth on that extract's world (gen_data.brand_world; the extracts on disk must be byte for byte
what gen_data.py writes, as make_expected.py requires), then grade the same copy with tests/grade.py for the cells
that each check-B cut moves. Graded cells moved, per extract:
  value cells        kept features that differ on rows present in both (the grader's tolerances; make_expected.compare)
  + 10 x missing     each scoring point without an output row (its ten kept features)
  + points x missing columns (a kept feature left out)
  + forbidden        non-null values in a days_since_last_login column (it must be absent or all null)
Extra rows (keys that are not scoring points) are reported but not counted. At a cut, the cells are grade.py's
B_<cut>_changed_cells plus that run's forbidden non-null values.
Every rule-swap attempt is set beside its twin in mechanisms.report (gen_data.py's count for the same mistake, made in
ref_truth's own loop); the two implementations must agree. The JSON holds counts only, so a re-run gives the same
bytes.

python hit_report.py
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pandas as pd  # noqa: E402
import gen_data  # noqa: E402
import local_check as LC  # noqa: E402
import make_expected as ME  # noqa: E402
import mechanisms  # noqa: E402
import ref_truth  # noqa: E402

OUT = os.path.join(HERE, "hit_report.json")
KEYS, KEPT, DROPPED = ME.KEYS, ME.KEPT, ME.DROPPED
FLOOR = 100
# the agent-visible environment the grader gives a run (kit.RUNNER_ENV, HOME aside)
RUN_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1"}
# attempt -> its twin in mechanisms.report; login twins are compared on the non-null count, the rest on value cells
TWINS = {"loaded_at_everywhere": "trust_loaded_at", "v2_rule": "v2_rule", "min_commit": "min_commit",
         "scheduler_end": "scheduler_end", "scheduler_start": "scheduler_start",
         "rollback_as_commit": "rollback_as_commit", "backfill_event_time": "backfill_event_time",
         "legacy_schedule": "legacy_schedule", "hourly_schedule": "hourly_schedule",
         "window_on_loaded_at": "window_on_loaded_at",
         "status_latest_loaded": "status_latest_loaded", "status_event_date": "status_event_date",
         "current_plan": "current_plan", "plan_changed_at": "plan_changed_at", "labels_matured": "labels_matured",
         "clip_last_login": "clip_last_login", "last_login_where_known": "last_login_where_known"}
# v3 as shipped makes four of those mistakes at once (orders by event time, status by date, current plan, te proxy)
NOP_TWINS = ("orders_event_time", "status_event_date", "current_plan", "labels_matured")
# (variant, extract) -> (the floor that applies there instead of FLOOR, why)
HOURLY_WHY = ("the stated exception to the 100-cell floor (since the operations-log revision of 2026-10-31): check A "
              "is its one kill, because a check-B copy keeps the row counts of every selection line written before "
              "its cut; it must still move at least 1 cell on each extract")
EXCEPTIONS = {("cache_visible", "visible"): (0, "the shortcut returns the right table of the visible extract itself, "
              "so it moves no cell there by construction; it is not a mechanism, and H's keys defeat it"),
              ("hourly_schedule", "H"): (1, HOURLY_WHY), ("hourly_schedule", "visible"): (1, HOURLY_WHY)}


def brand(b, tmp):
    """(world, extract, truth, folder of plain CSVs the CLI reads) for one brand; stops unless disk = gen_data."""
    w = gen_data.brand_world(b)
    ext = gen_data.extract_tables(w)
    disk, gz = ((os.path.join(ME.APP, "data"), False) if b == "visible"
                else (os.path.join(ME.TESTS, "hidden", "H"), True))
    bad = ME.same_bytes_as_disk(ext, disk, gz)
    if bad:
        raise SystemExit(f"{b}: the extract on disk is not what gen_data.py writes now ({bad})")
    truth = ref_truth.compute(w, ext["scoring_points"])
    data = disk
    if gz:  # unzipped as grade.py does, the _ops/ folder too
        data = os.path.join(tmp, f"csv_{b}")
        for f in ME.files_under(disk):
            os.makedirs(os.path.dirname(os.path.join(data, f)), exist_ok=True)
            with gzip.open(os.path.join(disk, f)) as src, open(os.path.join(data, f[:-3]), "wb") as dst:
                shutil.copyfileobj(src, dst)
    return w, ext, truth, data


def moved(got_raw, truth):
    """Graded cells an output moves against the truth (see the module docstring), with the parts."""
    g = got_raw.copy()
    miss = [c for c in KEPT if c not in g.columns]
    if miss:  # count a left-out kept feature once per scoring point; compare the other features as usual
        idx = pd.MultiIndex.from_arrays([g["customer_id"].astype("int64").to_numpy(), ME.seconds_of(g["as_of"])])
        t = truth.set_index(KEYS)
        for c in miss:
            g[c] = t[c].reindex(idx).to_numpy()
    rep = ME.compare(g, truth)
    forbidden = int(g[DROPPED].notna().sum()) if DROPPED in g.columns else 0
    parts = {"value_cells": rep["mismatched_cells"], "missing_rows": rep["missing_rows"],
             "extra_rows": rep["extra_rows"], "duplicate_rows": rep["duplicate_rows"], "missing_columns": miss,
             "forbidden_nonnull": forbidden,
             "per_feature": {c: rep[f"mismatch_{c}"] for c in KEPT if rep[f"mismatch_{c}"]}}
    parts["cells_moved"] = (rep["mismatched_cells"] + 10 * rep["missing_rows"] + len(truth) * len(miss)
                            + forbidden)
    return parts


def run_cli(app, shim, data, out):
    r = subprocess.run([shim, "-m", "churn.build_features", "--data", data, "--out", out], cwd=app,
                       env=dict(RUN_ENV, HOME=app), capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"CLI failed (exit {r.returncode}): {r.stderr[-1200:]}")
    return pd.read_parquet(out)


def twin_count(name, mech, b):
    m = mech[b]
    if name == "original":
        return sum(m[t]["cells"] for t in NOP_TWINS), "value_cells"
    if name not in TWINS:
        return None, None
    rec = m[TWINS[name]]
    if "non_null_rows" in rec:
        return rec["non_null_rows"], "forbidden_nonnull"
    return rec["cells"], "value_cells"


def main():
    report = {"floor": FLOOR, "rule": "A-killed attempts: cells_moved >= floor on H and on visible; B-only kills: "
              "cells > 0 at each named cut and value cells > 0 on visible", "variants": {}}
    with tempfile.TemporaryDirectory() as tmp:
        brands, mech = {}, {}
        for b in ("visible", "H"):
            w, ext, truth, data = brand(b, tmp)
            brands[b] = (truth, data)
            mech[b] = mechanisms.report(w, ext, truth)
        report["points"] = {b: len(brands[b][0]) for b in brands}
        problems = []
        for name, expected, named in LC.VARIANTS:
            vt = os.path.join(tmp, name)
            os.makedirs(vt)
            app, shim = LC.apply_solution(name, vt)
            rec = {"expected_reward": expected, "named_checks": list(named)}
            for b, (truth, data) in brands.items():
                rec[b] = moved(run_cli(app, shim, data, os.path.join(vt, f"out_{b}.parquet")), truth)
                tc, kind = twin_count(name, mech, b)
                if tc is not None:
                    rec[b]["twin"] = {"mechanism": TWINS.get(name, "+".join(NOP_TWINS)), "count": tc,
                                      "compared": kind, "agrees": rec[b][kind] == tc}
                    if rec[b][kind] != tc:
                        problems.append(f"{name} {b}: {kind} {rec[b][kind]} != twin {tc}")
            rj, _, _ = LC.grade_app(app, shim, vt)
            rec["reward"] = rj["reward"]
            rec["checks"] = {c: rj.get(f"check_{c}") for c in LC.CHECKS}
            for cut in ("cut1", "cut2"):
                if f"B_{cut}_rows_compared" in rj:
                    rec[f"B_{cut}_cells"] = rj[f"B_{cut}_changed_cells"] + rj.get(f"{cut}_{DROPPED}_nonnull", 0)
            shutil.rmtree(vt, ignore_errors=True)
            if expected == 0:
                floors = {}
                if "A" in named:
                    for b in ("H", "visible"):
                        floor, why = EXCEPTIONS.get((name, b), (FLOOR, None))
                        ok = rec[b]["cells_moved"] >= floor
                        floors[f"A_{b}"] = ok if why is None else (f"{'met' if ok else 'NOT MET'}: exception, "
                                                                   f"floor {floor}: {why}")
                        problems += [] if ok else [f"{name}: {rec[b]['cells_moved']} cells on {b} < {floor}"]
                    for c in named[1:]:  # a cut named beside A moves cells there too
                        ok = rec.get(f"{c}_cells", 0) > 0
                        floors[c] = ok
                        problems += [] if ok else [f"{name}: no cell moved at {c}"]
                else:  # a kill by check-B cuts only
                    for c in named:
                        ok = rec.get(f"{c}_cells", 0) > 0
                        floors[c] = ok
                        problems += [] if ok else [f"{name}: no cell moved at {c}"]
                    ok = rec["visible"]["value_cells"] > 0
                    floors["mechanism_in_visible"] = ok
                    problems += [] if ok else [f"{name}: the mechanism moves no cell on the visible extract"]
                rec["floors"] = floors
            report["variants"][name] = rec
            print(f"{name:24s} named {'+'.join(named) or '-':20s} H {rec['H']['cells_moved']:>7} visible "
                  f"{rec['visible']['cells_moved']:>7} | B1 {rec.get('B_cut1_cells', '-')} B2 "
                  f"{rec.get('B_cut2_cells', '-')} | twin H {rec['H'].get('twin', {}).get('count', '-')} visible "
                  f"{rec['visible'].get('twin', {}).get('count', '-')} | reward {rec['reward']} | "
                  f"{rec.get('floors', {})}", flush=True)
    report["problems"] = problems
    with open(OUT, "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)
        f.write("\n")
    print("HIT REPORT OK" if not problems else f"HIT REPORT PROBLEMS: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

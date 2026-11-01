"""Local proof matrix for feature-leakage-churn (authoring only; the Daytona runs are the real proof).

For each variant: copy environment/app to a fresh folder (the agent's /app), apply solution/solve.sh with SOLUTION set
(nothing for 'original', the no-op: the v3 pipeline as shipped), drop folders named data, __pycache__ or .venv at any
depth (what the /app artifact keeps), then run tests/grade.py in KIT_LOCAL mode against that copy, with the task's
tests/ as the hidden inputs, and read its reward.json.

Every Python process uses the build environment's interpreter in isolated mode (-I -B). A `python3` written into the
temporary folder stands in for the image's python3 (solve.sh calls python3; grade.py calls sys.executable, set to it):
like a plain python3, it puts the working folder first on sys.path for "-m" and the script's folder for a script,
which -I alone leaves out. The kit's privilege steps (uid 1001, /tests mode 0700, the log lock) do not run on the Mac;
the Daytona proof runs them.

Each variant has an expected reward and, for an attempt, the checks named as its kill (DESIGN.md, the attempts
table): each named check must be 0 in reward.json. grade.py stops after a failed or rejected run on H, so the checks
after it never run; the table marks a check that did not run with '-'. Every perturbed copy must keep its invariants
(B_<cut>_invariant_problems = 0), and a solve.sh failure is a defect of the attempt, never a kill. Since 2026-10-31
every sweep before a run must also leave nothing (residual_runner_paths_<run> = 0), and the independence probe
(PROBES) runs only when named: its real expectation needs the verifier container's uid split.

python local_check.py [--json <file>] [variant ...]      (default: every variant of VARIANTS, in the table's order)
"""
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SUBMISSION = os.path.abspath(os.path.join(HERE, "..", ".."))
TASK = os.path.join(SUBMISSION, "tasks", "feature-leakage-churn")
TESTS = os.path.join(TASK, "tests")
PY = os.path.join(SUBMISSION, ".venv", "bin", "python")
EXCLUDE = {"data", "__pycache__", ".venv"}
CHECKS = ("A", "B_cut1", "B_cut2")
# (variant, expected reward, the checks named as its kill)
VARIANTS = [
    ("canonical", 1, ()),
    ("alt", 1, ()),
    ("original", 0, ("A", "B_cut1", "B_cut2")),
    ("loaded_at_everywhere", 0, ("A",)),
    ("v2_rule", 0, ("A",)),
    ("min_commit", 0, ("A",)),
    ("scheduler_end", 0, ("A",)),
    ("scheduler_start", 0, ("A",)),
    ("rollback_as_commit", 0, ("A", "B_cut1")),
    ("backfill_event_time", 0, ("A", "B_cut1")),
    ("legacy_schedule", 0, ("A", "B_cut1")),
    ("hourly_schedule", 0, ("A",)),
    ("window_on_loaded_at", 0, ("A",)),
    ("status_latest_loaded", 0, ("A",)),
    ("status_event_date", 0, ("A",)),
    ("current_plan", 0, ("A", "B_cut2")),
    ("plan_changed_at", 0, ("A", "B_cut2")),
    ("drop_plan", 0, ("A",)),
    ("clip_last_login", 0, ("A", "B_cut1", "B_cut2")),
    ("last_login_where_known", 0, ("A",)),
    ("labels_matured", 0, ("A",)),
    ("log_lookup", 0, ("A",)),
    ("cache_visible", 0, ("A",)),
    ("zero_features", 0, ("A",)),
    ("tune_model", 0, ("A",)),
]
# Since 2026-10-31, run only when named: the probe of the grader's independence between runs. In the verifier
# container its reward must be 0, by check B at both cuts; on the Mac the sweep clears only the work folder (no uid
# split), so the cache it writes into /tmp survives and its local reward is 1 by construction (measured 2026-10-31).
# Its files outside the temporary folders are removed before and after its run.
PROBES = [("cache_in_work", 1, ())]
PROBE_FILES = ("/tmp/churn_cache_in_work.parquet",)
SHIM = r"""#!/bin/bash
# python3 for the local matrix (written by local_check.py): the build environment's Python, isolated, no bytecode.
PY=%s
if [ "${1:-}" = "-m" ]; then
  exec "$PY" -I -B -c 'import os, runpy, sys; sys.path.insert(0, os.getcwd()); m = sys.argv[1]; sys.argv = [m] + sys.argv[2:]; runpy.run_module(m, run_name="__main__", alter_sys=True)' "${@:2}"
fi
if [ -n "${1:-}" ] && [ "${1#-}" = "$1" ] && [ -f "$1" ]; then
  exec "$PY" -I -B -c 'import os, runpy, sys; p = sys.argv[1]; sys.path.insert(0, os.path.dirname(os.path.abspath(p))); sys.argv = sys.argv[1:]; runpy.run_path(p, run_name="__main__")' "$@"
fi
exec "$PY" -I -B "$@"
"""
RUN_GRADE = ("import os, runpy, sys; t = os.environ['GRADE_TESTS_DIR']; sys.path.insert(0, t); "
             "sys.executable = os.environ['GRADE_PY_SHIM']; sys.argv = [os.path.join(t, 'grade.py')]; "
             "runpy.run_path(sys.argv[0], run_name='__main__')")


def check_sums():
    for line in open(os.path.join(TESTS, "SHA256SUMS")):
        digest, rel = line.split()
        assert hashlib.sha256(open(os.path.join(TESTS, rel), "rb").read()).hexdigest() == digest, rel
    return "SHA256SUMS ok"


def remove_probe_files(is_probe):
    """Remove the files a probe leaves outside the temporary folders (PROBE_FILES), for a probe only."""
    for p in PROBE_FILES if is_probe else ():
        if os.path.isfile(p):
            os.remove(p)


def artifact_copy(src, dst):
    def ignore(folder, names):
        return [n for n in names if n in EXCLUDE and os.path.isdir(os.path.join(folder, n))]
    shutil.copytree(src, dst, ignore=ignore, symlinks=True)


def write_shim(folder):
    os.makedirs(folder)
    shim = os.path.join(folder, "python3")
    with open(shim, "w") as f:
        f.write(SHIM % shlex.quote(PY))
    os.chmod(shim, 0o755)
    return shim


def apply_solution(name, tmp):
    """A fresh copy of environment/app with the variant applied (solve.sh, as the oracle runs it). Returns
    (app folder, the python3 stand-in)."""
    app = os.path.join(tmp, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app"), app)
    shim = write_shim(os.path.join(tmp, "bin"))
    if name != "original":
        env = dict(os.environ, PATH=os.path.dirname(shim) + os.pathsep + os.environ["PATH"], APP_DIR=app,
                   SOLUTION=name, PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run(["bash", os.path.join(TASK, "solution", "solve.sh")], env=env, capture_output=True,
                           text=True)
        if r.returncode != 0:
            raise RuntimeError(f"solve.sh failed for {name} (exit {r.returncode}): {r.stderr[-1200:]}")
    return app, shim


def run_variant(name, tmp):
    app, shim = apply_solution(name, tmp)
    return grade_app(app, shim, tmp)


def grade_app(app, shim, tmp):
    """Grade an applied copy of /app: the artifact copy, then tests/grade.py in KIT_LOCAL mode. Returns (reward.json,
    seconds of the grading process, its output)."""
    sub = os.path.join(tmp, "artifact")
    artifact_copy(app, sub)
    logs, work, ktmp = (os.path.join(tmp, x) for x in ("logs", "work", "ktmp"))
    os.makedirs(ktmp)
    genv = dict(os.environ, KIT_LOCAL="1", KIT_SUBMISSION=sub, KIT_LOGS=logs, KIT_WORK=work, TMPDIR=ktmp,
                GRADE_TESTS_DIR=TESTS, GRADE_PY_SHIM=shim, PYTHONDONTWRITEBYTECODE="1")
    t0 = time.monotonic()
    g = subprocess.run([PY, "-I", "-B", "-c", RUN_GRADE], env=genv, capture_output=True, text=True, cwd=TESTS)
    secs = time.monotonic() - t0
    with open(os.path.join(logs, "reward.json")) as f:
        rj = json.load(f)
    return rj, secs, g.stdout + g.stderr


def ran(rj, check):
    """Whether grade.py compared anything for this check (it stops after a failed or rejected run on H)."""
    return ("A_mismatched_cells" in rj) if check == "A" else (f"{check}_rows_compared" in rj)


def verdict(rj, expected, named):
    problems = []
    if rj["reward"] != expected:
        problems.append(f"reward {rj['reward']} != {expected}")
    for cut in ("cut1", "cut2"):
        if rj.get(f"B_{cut}_invariant_problems", 0) != 0:
            problems.append(f"B_{cut}: the perturbed copy broke its invariants (grader defect)")
    for run in ("H", "cut1", "cut2"):
        if rj.get(f"residual_runner_paths_{run}", 0) != 0:
            problems.append(f"{run}: the sweep left {rj[f'residual_runner_paths_{run}']} entries (grader defect)")
    if expected == 1:
        problems += [f"check_{c} is not 1" for c in CHECKS if rj.get(f"check_{c}") != 1]
    else:
        problems += [f"named check {c} did not fail" for c in named if rj.get(f"check_{c}") != 0]
    return problems


def cell(rj, check):
    v = rj.get(f"check_{check}")
    return f"{v}" if ran(rj, check) else f"{v}-"


def main(argv):
    out_json = None
    if argv[:1] == ["--json"]:
        out_json, argv = argv[1], argv[2:]
    print(check_sums())
    table = {v: (e, n) for v, e, n in VARIANTS + PROBES}
    probes = {v for v, _, _ in PROBES}
    want = argv or [v for v, _, _ in VARIANTS]
    results, bad = {}, []
    for name in want:
        expected, named = table[name]
        with tempfile.TemporaryDirectory() as tmp:
            try:
                remove_probe_files(name in probes)
                rj, secs, log = run_variant(name, tmp)
            except Exception as e:  # noqa: BLE001 - reported as a failure of the matrix, never as a kill
                print(f"{name:24s} ERROR {type(e).__name__}: {e}")
                bad.append(name)
                results[name] = {"expected": expected, "named": list(named), "error": str(e)}
                continue
            finally:
                remove_probe_files(name in probes)
        problems = verdict(rj, expected, named)
        bad += [name] if problems else []
        results[name] = {"expected": expected, "named": list(named), "reward_json": rj,
                         "process_seconds": round(secs, 2), "problems": problems}
        runs = "/".join(f"{rj[k]:.2f}" if k in rj else "-" for k in ("seconds_H", "seconds_cut1", "seconds_cut2"))
        print(f"{name:24s} exp {expected} got {rj['reward']:.0f} {'OK' if not problems else 'UNEXPECTED'} | named "
              f"{'+'.join(named) or 'none'} | A {cell(rj, 'A')} B1 {cell(rj, 'B_cut1')} B2 {cell(rj, 'B_cut2')} | "
              f"cells A {rj.get('A_mismatched_cells', '-')} B1 {rj.get('B_cut1_changed_cells', '-')} "
              f"B2 {rj.get('B_cut2_changed_cells', '-')} | login non-null H {rj.get('H_days_since_last_login_nonnull', '-')}"
              f" | bad output H {rj.get('bad_output_H', 0)} | inv {rj.get('B_cut1_invariant_problems', '-')}/"
              f"{rj.get('B_cut2_invariant_problems', '-')} | runs s {runs} | grade {secs:.1f}s"
              + (f" | {'; '.join(problems)}" if problems else ""))
        if os.environ.get("VERBOSE"):
            print(log)
    print("ALL AS EXPECTED" if not bad else f"UNEXPECTED: {bad}")
    if out_json:
        with open(out_json, "w") as f:
            json.dump(results, f, indent=1, sort_keys=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

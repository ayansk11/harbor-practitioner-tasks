"""Local proof matrix for et0-station-ingest (authoring only; the Daytona runs are the real proof).

For each variant: copy environment/app, apply solution/solve.sh with SOLUTION=<variant> (APP_DIR = the copy), drop
folders named data, __pycache__ and .venv at any depth (what the /app artifact keeps), then run tests/grade.py in
KIT_LOCAL mode and read reward.json. Privilege steps (uid 1001, /tests 0700) cannot run on the Mac; Daytona proves those.
Run (repository root): .venv/bin/python authoring/et0-station-ingest/local_check.py [variant ...]
Writes local_results.json next to this file and prints the LOCAL RESULTS table.
"""
import json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "et0-station-ingest"))
PY = sys.executable
RUNS = os.path.join(HERE, ".localruns")
EXPECT = {"canonical": 1.0, "alt": 1.0, "nop": 0.0, "fit_to_metservice": 0.0, "hardcode_output": 0.0,
          "linear_wind": 0.0, "fix_altitude": 0.0, "units_not_latitude": 0.0, "nearest_height": 0.0,
          # real-mode defence probes: 0 on the Mac for a trivial reason (no /tests, no /app); Daytona is the real test
          "read_answers": 0.0, "symlink_output": 0.0, "abs_app_path": 0.0}
EXCLUDE = {"data", "__pycache__", ".venv"}


def artifact_copy(src, dst):
    def ignore(d, names):
        return [n for n in names if n in EXCLUDE and os.path.isdir(os.path.join(d, n))]
    shutil.copytree(src, dst, symlinks=True, ignore=ignore)


def run_variant(name):
    root = os.path.join(RUNS, name)
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    app = os.path.join(root, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app"), app)
    sol = os.path.join(root, "solution")
    shutil.copytree(os.path.join(TASK, "solution"), sol)
    env = dict(os.environ, SOLUTION=name, APP_DIR=app, PYTHON=PY,
               PATH=os.path.dirname(PY) + os.pathsep + os.environ.get("PATH", ""), PYTHONDONTWRITEBYTECODE="1")
    t0 = time.monotonic()
    s = subprocess.run(["bash", os.path.join(sol, "solve.sh")], env=env, capture_output=True, text=True)
    solve_s = time.monotonic() - t0
    art = os.path.join(root, "artifact")
    artifact_copy(app, art)
    logs, work = os.path.join(root, "logs"), os.path.join(root, "work")
    genv = dict(os.environ, KIT_LOCAL="1", KIT_SUBMISSION=art, KIT_LOGS=logs, KIT_WORK=work,
                GRADE_TESTS_DIR=os.path.join(TASK, "tests"), GRADE_PYTHON=PY, PYTHONDONTWRITEBYTECODE="1")
    t0 = time.monotonic()
    g = subprocess.run([PY, os.path.join(TASK, "tests", "grade.py")], env=genv, capture_output=True, text=True,
                       cwd=os.path.join(TASK, "tests"))
    grade_s = time.monotonic() - t0
    with open(os.path.join(root, "solve.log"), "w") as f:
        f.write(s.stdout + "\n--- stderr ---\n" + s.stderr)
    with open(os.path.join(root, "grade.log"), "w") as f:
        f.write(g.stdout + "\n--- stderr ---\n" + g.stderr)
    try:
        payload = json.load(open(os.path.join(logs, "reward.json")))
    except Exception:
        payload = {"reward": None}
    return {"variant": name, "expected": EXPECT.get(name), "got": payload.get("reward"), "solve_rc": s.returncode,
            "solve_seconds": round(solve_s, 2), "grade_seconds": round(grade_s, 2), "metrics": payload}


def main():
    names = sys.argv[1:] or list(EXPECT)
    results = [run_variant(n) for n in names]
    with open(os.path.join(HERE, "local_results.json"), "w") as f:
        json.dump(results, f, indent=1)
    print("| Variant | Expected | Got | solve rc | hidden run s | grade s | visible max err | visible rows over tol | hidden max err | hidden rows over tol |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    bad = 0
    for r in results:
        m = r["metrics"]
        good = r["got"] == r["expected"]
        bad += not good
        print(f"| {r['variant']} | {r['expected']} | {r['got']} | {r['solve_rc']} | {m.get('hidden_run_seconds')} | "
              f"{r['grade_seconds']} | {m.get('visible_max_abs_err')} | {m.get('visible_rows_over_tol')} | "
              f"{m.get('hidden_max_abs_err')} | {m.get('hidden_rows_over_tol')} |")
    print("ALL AS EXPECTED" if not bad else f"{bad} VARIANT(S) NOT AS EXPECTED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

"""Local proof matrix for ab-test-reanalysis (authoring only; the Daytona runs are the real proof).

For each variant: copy environment/app, apply solution/solve.sh with SOLUTION=<variant> (APP_DIR = the copy), drop
folders named data, __pycache__ and .venv at any depth (what the /app artifact keeps), then run tests/grade.py in
KIT_LOCAL mode and read reward.json. Privilege steps (uid 1001, /tests 0700, the log lock) cannot run on the Mac.
Run: submission/.venv/bin/python submission/authoring/ab-test-reanalysis/local_check.py [variant ...]
Writes local_results.json next to this file and prints the LOCAL RESULTS table.
"""
import json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
PY = sys.executable
RUNS = os.path.join(HERE, ".localruns")
EXPECT = {"canonical": 1.0, "alt": 1.0, "alt_cr1": 1.0, "nop": 0.0, "hardcode_no_ship": 0.0,
          "fix_visible_result_only": 0.0, "fix_bots_only": 0.0, "mean_of_ratios": 0.0, "no_srm_gate": 0.0,
          "constant_inflation": 0.0, "fix_ci_only": 0.0, "icc_tuned": 0.0, "kish_tuned": 0.0}
EXCLUDE = {"data", "__pycache__", ".venv"}
SETS = ("visible", "h_null", "h_pos", "h_srm", "h_bots", "h_twin")


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
    env = dict(os.environ, SOLUTION=name, APP_DIR=app, PYTHON=PY, PYTHONDONTWRITEBYTECODE="1",
               PATH=os.path.dirname(PY) + os.pathsep + os.environ.get("PATH", ""))
    t0 = time.monotonic()
    s = subprocess.run(["bash", os.path.join(sol, "solve.sh")], env=env, capture_output=True, text=True)
    solve_s = time.monotonic() - t0
    art = os.path.join(root, "artifact")
    artifact_copy(app, art)
    shutil.rmtree(app)                                   # keep disk use down; the artifact copy is what is graded
    logs, work = os.path.join(root, "logs"), os.path.join(root, "work")
    genv = dict(os.environ, KIT_LOCAL="1", KIT_SUBMISSION=art, KIT_LOGS=logs, KIT_WORK=work,
                GRADE_TESTS_DIR=os.path.join(TASK, "tests"), GRADE_PYTHON=PY, PYTHONDONTWRITEBYTECODE="1")
    t0 = time.monotonic()
    g = subprocess.run([PY, os.path.join(TASK, "tests", "grade.py")], env=genv, capture_output=True, text=True,
                       cwd=os.path.join(TASK, "tests"))
    grade_s = time.monotonic() - t0
    shutil.rmtree(work, ignore_errors=True)
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


def cell(m, s):
    if m.get(f"{s}_ok") == 1:
        return "pass"
    lo, hi = m.get(f"{s}_ci_lo_err_hw"), m.get(f"{s}_ci_hi_err_hw")
    probs = m.get(f"{s}_problems")
    ci = f" ci {max(lo, hi):.2f}" if lo is not None and hi is not None else ""
    return f"FAIL ({probs} problems{ci})" if probs is not None else "FAIL (unreadable/missing)"


def main():
    names = sys.argv[1:] or list(EXPECT)
    results = [run_variant(n) for n in names]
    with open(os.path.join(HERE, "local_results.json"), "w") as f:
        json.dump(results, f, indent=1)
    print("| Variant | Expected | Got | " + " | ".join(SETS) + " | max hidden run s | solve s | grade s |")
    print("|---|---|---|" + "---|" * len(SETS) + "---|---|---|")
    bad = 0
    for r in results:
        m = r["metrics"]
        good = r["got"] == r["expected"]
        bad += not good
        runs = [m.get(f"{s}_run_seconds") for s in SETS[1:] if m.get(f"{s}_run_seconds") is not None]
        print(f"| {r['variant']} | {r['expected']:g} | {r['got']} | " + " | ".join(cell(m, s) for s in SETS) +
              f" | {max(runs) if runs else '-'} | {r['solve_seconds']} | {r['grade_seconds']} |")
    print("ALL AS EXPECTED" if not bad else f"{bad} VARIANT(S) NOT AS EXPECTED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

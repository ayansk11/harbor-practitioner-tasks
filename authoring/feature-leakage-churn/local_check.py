"""Local proof matrix for feature-leakage-churn (authoring only; the Daytona runs are the real proof).

For each variant: copy environment/app to a fresh folder (the agent's /app), apply solution/solve.sh with SOLUTION set
(nothing for 'original', the no-op), drop folders named data/__pycache__/.venv at any depth (what the /app artifact
keeps), then run tests/grade.py in KIT_LOCAL mode against that copy with the task's tests/ as the hidden inputs.
Also checks tests/SHA256SUMS. Prints a table: variant, expected reward, got reward, A, B cut1, B cut2, run seconds.

python local_check.py [variant ...]      (default: all)
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
SUBMISSION = os.path.abspath(os.path.join(HERE, "..", ".."))
TASK = os.path.join(SUBMISSION, "tasks", "feature-leakage-churn")
PY = os.path.join(SUBMISSION, ".venv", "bin", "python")
EXCLUDE = {"data", "__pycache__", ".venv"}
VARIANTS = [("canonical", 1), ("alt", 1), ("original", 0), ("zero_features", 0), ("drop_leaky", 0),
            ("cache_visible", 0), ("loo_encoding", 0), ("closed_right", 0), ("tune_model", 0),
            ("miss_imputation", 0), ("status_same_day", 0), ("open_left_30d", 0), ("label_at_t", 0)]


def check_sums():
    tests = os.path.join(TASK, "tests")
    for line in open(os.path.join(tests, "SHA256SUMS")):
        digest, rel = line.split()
        assert hashlib.sha256(open(os.path.join(tests, rel), "rb").read()).hexdigest() == digest, rel
    return "SHA256SUMS ok"


def artifact_copy(src, dst):
    def ignore(_, names):
        return [n for n in names if n in EXCLUDE and os.path.isdir(os.path.join(_, n))]
    shutil.copytree(src, dst, ignore=ignore, symlinks=True)


def run_variant(name, tmp):
    app = os.path.join(tmp, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app"), app)
    env = dict(os.environ, PATH=os.path.dirname(PY) + os.pathsep + os.environ["PATH"], APP_DIR=app)
    if name != "original":
        env["SOLUTION"] = name
        r = subprocess.run(["bash", os.path.join(TASK, "solution", "solve.sh")], env=env, capture_output=True,
                           text=True)
        if r.returncode != 0:
            print(f"  solve.sh failed for {name}: {r.stderr[-800:]}")
    sub = os.path.join(tmp, "artifact")
    artifact_copy(app, sub)
    logs, work = os.path.join(tmp, "logs"), os.path.join(tmp, "work")
    genv = dict(os.environ, KIT_LOCAL="1", KIT_SUBMISSION=sub, KIT_LOGS=logs, KIT_WORK=work,
                GRADE_TESTS_DIR=os.path.join(TASK, "tests"))
    t0 = time.monotonic()
    g = subprocess.run([PY, os.path.join(TASK, "tests", "grade.py")], env=genv, capture_output=True, text=True,
                       cwd=os.path.join(TASK, "tests"))
    secs = time.monotonic() - t0
    with open(os.path.join(logs, "reward.json")) as f:
        rj = json.load(f)
    return rj, secs, g.stdout


def main():
    print(check_sums())
    want = sys.argv[1:] or [v for v, _ in VARIANTS]
    expected = dict(VARIANTS)
    rows = []
    for name in want:
        with tempfile.TemporaryDirectory() as tmp:
            rj, secs, out = run_variant(name, tmp)
        rows.append((name, expected[name], rj))
        flag = "OK" if rj["reward"] == expected[name] else "UNEXPECTED"
        print(f"{name:16s} expected {expected[name]} got {rj['reward']:.0f} {flag} | A {rj.get('check_A')} "
              f"B1 {rj.get('check_B_cut1')} B2 {rj.get('check_B_cut2')} | A cells {rj.get('A_mismatched_cells')} "
              f"B1 cells {rj.get('B_cut1_changed_cells')} B2 cells {rj.get('B_cut2_changed_cells')} | run s "
              f"{rj.get('seconds_H')}/{rj.get('seconds_cut1')}/{rj.get('seconds_cut2')} | grade total {secs:.1f}s")
        if os.environ.get("VERBOSE"):
            print(out)
            print(json.dumps(rj))
    bad = [r for r in rows if r[2]["reward"] != r[1]]
    print("ALL AS EXPECTED" if not bad else f"UNEXPECTED: {[r[0] for r in bad]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

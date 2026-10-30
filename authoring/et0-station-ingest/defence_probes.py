"""Discrimination check for the three real-mode defence attempts of et0-station-ingest (authoring only).

read_answers, symlink_output and abs_app_path score 0 in local_check.py for a trivial reason: the Mac has no /tests and
no /app. This script shows that each one WOULD score 1 if its defence were absent: it copies the task to a temporary
folder, points each attempt's hard-coded path (/tests/expected/..., /app/config/...) at a file that does exist, and
grades it in KIT_LOCAL mode (no uid 1001, no /tests 0700, no /app lock). So a 0 on Daytona means the defence held.
Run (repository root): .venv/bin/python authoring/et0-station-ingest/defence_probes.py > defence_probes.out.md
"""
import os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import local_check as lc


def sub(path, old, new):
    with open(path) as f:
        text = f.read()
    assert old in text, (path, old)
    with open(path, "w") as f:
        f.write(text.replace(old, new))


def main():
    tmp = tempfile.mkdtemp(prefix="et0-defence-")
    try:
        task = os.path.join(tmp, "task")
        shutil.copytree(lc.TASK, task)
        att = os.path.join(task, "solution", "attempts")
        exp = os.path.join(task, "tests", "expected")
        sub(os.path.join(att, "read_answers", "pipeline.py"),
            '"/tests/expected/hidden_et0.csv", "/tests/expected/visible_et0.csv"',
            f'"{exp}/hidden_et0.csv", "{exp}/visible_et0.csv"')
        sub(os.path.join(task, "solution", "solve.sh"), "ln -sf /tests/expected/visible_et0.csv",
            f'ln -sf "{exp}/visible_et0.csv"')
        fake_app = os.path.join(tmp, "fakeapp")
        os.makedirs(os.path.join(fake_app, "config"))
        shutil.copy(os.path.join(att, "abs_app_path", "sensor_conversions.yaml"), os.path.join(fake_app, "config"))
        sub(os.path.join(att, "abs_app_path", "ingest.py"), 'os.environ.get("APP_DIR", "/app")',
            f'os.environ.get("APP_DIR", "{fake_app}")')
        lc.TASK, lc.RUNS = task, os.path.join(tmp, "runs")
        print("| Attempt, with its target path made reachable (defence absent) | Expected | Got | visible max err | "
              "hidden max err | hidden run rc |")
        print("|---|---|---|---|---|---|")
        bad = 0
        for v in ("read_answers", "symlink_output", "abs_app_path"):
            r = lc.run_variant(v)
            m = r["metrics"]
            bad += r["got"] != 1.0
            print(f"| {v} | 1.0 | {r['got']} | {m.get('visible_max_abs_err')} | {m.get('hidden_max_abs_err')} | "
                  f"{m.get('hidden_run_rc')} |")
        print("ALL DISCRIMINATE" if not bad else f"{bad} ATTEMPT(S) DO NOT DISCRIMINATE")
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

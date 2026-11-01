"""Local proof matrix for ab-test-reanalysis (authoring only; the Daytona runs are the real proof).

For each variant: copy environment/app, apply solution/solve.sh with SOLUTION=<variant> (APP_DIR = the copy), drop
folders named data, __pycache__ and .venv at any depth (what the /app artifact keeps), then run tests/grade.py in
KIT_LOCAL mode and read reward.json. Privilege steps (uid 1001, /tests 0700, the log lock, the private network) cannot
run on the Mac. Two interpreter modes, each for every variant:
  venv   this venv's Python (it has pyarrow, so pandas stores strings with pyarrow);
  image  the same Python with pyarrow blocked (sys.modules["pyarrow"] = None) for solve.sh and for every graded run,
         as in the task images, which install no pyarrow (environment/Dockerfile, tests/Dockerfile).
Expected rewards: 1 for canonical, alt_time and alt_recount; 0 for nop and for every attempt under solution/attempts/
(folders or files; names starting with "_" are helpers), as tools/proof_matrix.py expects them on Daytona; 0 for every
local probe under probes/ next to this file (same layout as an attempt folder; not part of the task package, so
proof_matrix.py never sees them: the run copies a probe into its own scratch solution/attempts/ only).
A 0-expected run counts as expected only if solve.sh exited 0 and no graded run crashed (a broken patch or a missing
name must not pass as a wrong answer). Each attempt and probe is also checked against the failing sets of the design
(DESIGN_FAILS, from section 5 of the approved design and the paths measured by gen_data.py): every named set fails
with the named keys, every other set passes.
Run: submission/.venv/bin/python -I -B submission/authoring/ab-test-reanalysis/local_check.py [--all] [--modes venv,image]
     [variant ...]
With no variant: canonical, alt_time, alt_recount and nop; --all adds every attempt and every probe. Writes
local_results.json and local_check.out.md next to this file (logs of each run under .localruns/, git-ignored) and
prints the table.
"""
import argparse, json, os, re, shutil, stat, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
PY = sys.executable
RUNS = os.path.join(HERE, ".localruns")
VALID = ("canonical", "alt_time", "alt_recount")
EXCLUDE = {"data", "__pycache__", ".venv"}
SETS = ("visible", "h_null", "h_pos", "h_srm", "h_plain", "h_neg")
KEYS = ("n_users", "pageviews", "clicks", "ctr", "diff", "srm_p", "srm_flag", "ci_95", "decision")
# the revision's design (section 5): attempts for Daytona, then the local-only probes; used for a coverage note only
DESIGN_ATTEMPTS = ("literal_bot_filter", "platform_clicked", "keep_overrides", "not_nav_clicked", "b_only_patch",
                   "no_bot_filter", "item_click_events", "pageview_ci", "hardcode_no_ship", "fix_visible_only")
DESIGN_PROBES = ("drop_nav_pageviews", "user_click_join", "srm_all_assigned", "text_time", "keep_pre_assignment")
PROBES = os.path.join(HERE, "probes")
# The failing sets each wrong variant must show: {set: keys that must be among its failing keys}; a key with an arm
# ("n_users.B") must fail in that arm, a bare key in either; a set not named must pass. From the design's section 5
# ("Fails on") and the measured paths (generation_report.out.md); None = the design states no failing sets.
ALL6 = SETS
DESIGN_FAILS = {
    "nop": {"visible": ("n_users",), "h_null": ("n_users",), "h_pos": ("n_users",), "h_srm": ("n_users",),
            "h_plain": ("clicks",), "h_neg": ("n_users",)},
    "literal_bot_filter": {"visible": ("n_users.B", "decision"), "h_null": ("n_users.A", "decision"),
                           "h_pos": ("n_users.B", "decision"), "h_srm": ("n_users.B",),
                           "h_neg": ("n_users.B", "decision")},
    "platform_clicked": {**{s: ("clicks",) for s in ALL6}, "visible": ("clicks", "decision")},
    "keep_overrides": {"visible": ("n_users.B",), "h_null": ("n_users.A",), "h_srm": ("n_users.B", "decision")},
    "not_nav_clicked": {s: ("clicks",) for s in ALL6},
    "b_only_patch": {**{s: ("clicks.A",) for s in ALL6}, "h_null": ("n_users.A", "clicks.A")},
    "no_bot_filter": {s: ("n_users",) for s in ALL6},
    "item_click_events": {s: ("clicks",) for s in ALL6},
    "pageview_ci": {s: ("ci_95",) for s in ALL6},
    "hardcode_no_ship": {"h_pos": ("decision",), "h_plain": ("decision",), "h_srm": ("decision",)},
    "fix_visible_only": {"h_null": ("n_users",), "h_pos": ("n_users",), "h_srm": ("n_users",),
                         "h_plain": ("clicks",), "h_neg": ("n_users",)},
    "drop_nav_pageviews": {"visible": ("pageviews.B",), "h_null": ("pageviews.A",), "h_pos": ("pageviews.B",),
                           "h_srm": ("pageviews.B",), "h_neg": ("pageviews.B",)},
    "user_click_join": {s: ("clicks",) for s in ALL6},
    "srm_all_assigned": {**{s: ("srm_p",) for s in ALL6}, "h_srm": ("srm_p", "srm_flag", "decision")},
    "text_time": None,
    "keep_pre_assignment": None,
}
LAUNCHER = '''import os, runpy, sys
sys.modules["pyarrow"] = None          # as in the task images: no pyarrow installed
args = sys.argv[1:]
if args[:1] == ["-m"]:                 # python -m <module> ...: the current folder first on sys.path
    sys.argv = [args[1]] + args[2:]
    sys.path.insert(0, os.getcwd())
    runpy.run_module(args[1], run_name="__main__", alter_sys=True)
else:                                  # python <script> ...: the script's folder first on sys.path
    sys.argv = args
    sys.path.insert(0, os.path.dirname(os.path.abspath(args[0])))
    runpy.run_path(args[0], run_name="__main__")
'''


def attempts():
    d = os.path.join(TASK, "solution", "attempts")
    if not os.path.isdir(d):
        return []
    return sorted({os.path.splitext(n)[0] for n in os.listdir(d) if not n.startswith((".", "_"))})


def probes():
    if not os.path.isdir(PROBES):
        return []
    return sorted(n for n in os.listdir(PROBES) if not n.startswith((".", "_")) and os.path.isdir(os.path.join(PROBES, n)))


def expected(name):
    return 1.0 if name in VALID else 0.0


def image_python(root):
    """An executable that runs this venv's Python with pyarrow blocked, for both `-m module` and `script.py` calls."""
    os.makedirs(root, exist_ok=True)
    launcher = os.path.join(root, "noarrow_launcher.py")
    with open(launcher, "w", encoding="ascii") as f:
        f.write(LAUNCHER)
    shim = os.path.join(root, "python-noarrow")
    with open(shim, "w", encoding="ascii") as f:
        f.write(f'#!/bin/bash\nexec "{PY}" -I -B "{launcher}" "$@"\n')
    os.chmod(shim, os.stat(shim).st_mode | stat.S_IXUSR)
    return shim


def artifact_copy(src, dst):
    def ignore(d, names):
        return [n for n in names if n in EXCLUDE and os.path.isdir(os.path.join(d, n))]
    shutil.copytree(src, dst, symlinks=True, ignore=ignore)


def failed_keys(log_text, s):
    """The readout keys that grade.py reported as wrong for set s, with the arm where it names one (from its log
    lines '<set>: <key>.<arm>=...' and '<set>: <key>=...'), e.g. ['n_users.B', 'diff', 'decision']."""
    found = []
    for m in re.finditer(rf"^\[kit\] {re.escape(s)}: (\w+)(\.[AB])?=", log_text, re.M):
        k = m.group(1) + (m.group(2) or "")
        if m.group(1) in KEYS and k not in found:
            found.append(k)
    if re.search(rf"^\[kit\] {re.escape(s)}: (run failed|result\.json (is not|unreadable)|output/result\.json "
                 rf"unreadable)", log_text, re.M):
        found.insert(0, "run/readout")
    return found


def run_variant(name, mode, python):
    root = os.path.join(RUNS, mode, name)
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    app = os.path.join(root, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app"), app)
    sol = os.path.join(root, "solution")
    shutil.copytree(os.path.join(TASK, "solution"), sol)
    if name in probes():                                 # a local probe: staged in this scratch copy only
        shutil.copytree(os.path.join(PROBES, name), os.path.join(sol, "attempts", name))
    env = dict(os.environ, SOLUTION=name, APP_DIR=app, PYTHON=python, PYTHONDONTWRITEBYTECODE="1",
               PATH=os.path.dirname(PY) + os.pathsep + os.environ.get("PATH", ""))
    t0 = time.monotonic()
    s = subprocess.run(["bash", os.path.join(sol, "solve.sh")], env=env, capture_output=True, text=True)
    solve_s = time.monotonic() - t0
    art = os.path.join(root, "artifact")
    artifact_copy(app, art)
    shutil.rmtree(app)                                   # keep disk use down; the artifact copy is what is graded
    logs, work = os.path.join(root, "logs"), os.path.join(root, "work")
    genv = dict(os.environ, KIT_LOCAL="1", KIT_SUBMISSION=art, KIT_LOGS=logs, KIT_WORK=work,
                GRADE_TESTS_DIR=os.path.join(TASK, "tests"), GRADE_PYTHON=python, PYTHONDONTWRITEBYTECODE="1")
    tests = os.path.join(TASK, "tests")
    # -I drops the script folder from sys.path, and /tests (grade.py's own insert) does not exist here: add tests/
    boot = f"import runpy, sys; sys.path.insert(0, {tests!r}); runpy.run_path({os.path.join(tests, 'grade.py')!r}, " \
           "run_name='__main__')"
    t0 = time.monotonic()
    g = subprocess.run([PY, "-I", "-B", "-c", boot], env=genv, capture_output=True, text=True, cwd=tests)
    grade_s = time.monotonic() - t0
    shutil.rmtree(work, ignore_errors=True)
    with open(os.path.join(root, "solve.log"), "w") as f:
        f.write(s.stdout + "\n--- stderr ---\n" + s.stderr)
    with open(os.path.join(root, "grade.log"), "w") as f:
        f.write(g.stdout + "\n--- stderr ---\n" + g.stderr)
    try:
        with open(os.path.join(logs, "reward.json")) as f:
            payload = json.load(f)
    except Exception:
        payload = {"reward": None}
    return {"variant": name, "mode": mode, "expected": expected(name), "got": payload.get("reward"),
            "solve_rc": s.returncode, "solve_seconds": round(solve_s, 2), "grade_seconds": round(grade_s, 2),
            "failed_keys": {st: failed_keys(g.stdout, st) for st in SETS}, "metrics": payload}


def kind(name):
    if name in VALID:
        return "valid"
    if name == "nop":
        return "nop"
    return "probe" if name in probes() else "attempt"


def crashed(r):
    """Sets whose graded run failed or whose readout could not be read."""
    return [s for s in SETS if "run/readout" in (r["failed_keys"].get(s) or [])]


def reward_ok(r):
    """The reward is the expected one, solve.sh exited 0, and a 0 is not the result of a crash."""
    return r["solve_rc"] == 0 and r["got"] == r["expected"] and (r["expected"] == 1 or not crashed(r))


def design_problems(r):
    """None where the design states no failing sets (and for the valid solutions); else the departures from
    DESIGN_FAILS (an empty list: the variant fails exactly where the design says, with the named keys)."""
    exp = DESIGN_FAILS.get(r["variant"])
    if r["expected"] == 1 or exp is None:
        return None
    out = []
    for s in SETS:
        ok = r["metrics"].get(f"{s}_ok") == 1
        got = r["failed_keys"].get(s) or []
        if s in exp:
            if ok:
                out.append(f"{s} passes")
                continue
            out += [f"{s} lacks {k}" for k in exp[s] if not any(g == k or g.split(".")[0] == k for g in got)]
        elif not ok:
            out.append(f"{s} fails ({', '.join(got) or 'see grade.log'})")
    return out


def cell(r, s):
    m = r["metrics"]
    if m.get(f"{s}_ok") == 1:
        return "pass"
    keys = r["failed_keys"].get(s) or []
    n = m.get(f"{s}_problems")
    more = f" (+{n - len(keys)} not logged)" if isinstance(n, int) and n > len(keys) else ""
    lo, hi = m.get(f"{s}_ci_lo_err_hw"), m.get(f"{s}_ci_hi_err_hw")
    ci = f" (ci {max(lo, hi):.2f})" if lo is not None and hi is not None and "ci_95" in keys else ""
    return "FAIL: " + (", ".join(keys) if keys else "see grade.log") + more + ci


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="*")
    ap.add_argument("--all", action="store_true",
                    help="also every attempt under solution/attempts/ and every local probe under probes/")
    ap.add_argument("--modes", default="venv,image")
    a = ap.parse_args()
    found, local = attempts(), probes()
    names = a.variants or (list(VALID) + ["nop"] + (found + local if a.all else []))
    modes = [m for m in a.modes.split(",") if m]
    if not set(modes) <= {"venv", "image"}:
        raise SystemExit("modes: venv, image")
    started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    t_all = time.monotonic()
    results = []
    for mode in modes:
        python = PY if mode == "venv" else image_python(os.path.join(RUNS, "image-python"))
        results += [run_variant(n, mode, python) for n in names]
    took = round(time.monotonic() - t_all, 1)
    finished = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    for r in results:
        r["kind"], r["reward_ok"], r["design_problems"] = kind(r["variant"]), reward_ok(r), design_problems(r)
    with open(os.path.join(HERE, "local_results.json"), "w") as f:
        json.dump({"started": started, "finished": finished, "seconds": took, "modes": modes, "results": results},
                  f, indent=1)
    L = ["# local_check.out.md (local_check.py)", "",
         f"Run {started} to {finished} (Mac clock), {took} s; variants: {', '.join(names)}; modes: {', '.join(modes)} "
         "(image = pyarrow blocked, as in the task images). Expected: 1 for canonical, alt_time, alt_recount; 0 for "
         "nop, every attempt and every local probe (a 0 counts only if solve.sh exited 0 and no graded run crashed). "
         "A FAIL cell names the readout keys grade.py reported as wrong, with the arm where it names one. Design: "
         "\"as designed\" when the variant fails exactly on the sets the design names, with the named keys "
         "(DESIGN_FAILS), else the departures; \"-\" where the design names no failing sets.", "",
         "| Variant | Kind | Mode | Expected | Got | " + " | ".join(SETS) +
         " | Design | max hidden run s | solve rc | solve s | grade s |",
         "|---|---|---|---|---|" + "---|" * len(SETS) + "---|---|---|---|---|"]
    bad = off = 0
    for r in results:
        m = r["metrics"]
        bad += not r["reward_ok"]
        dp = r["design_problems"]
        off += bool(dp)
        runs = [m.get(f"{s}_run_seconds") for s in SETS[1:] if m.get(f"{s}_run_seconds") is not None]
        L.append(f"| {r['variant']} | {r['kind']} | {r['mode']} | {r['expected']:g} | {r['got']} | " +
                 " | ".join(cell(r, s) for s in SETS) +
                 f" | {'-' if dp is None else ('as designed' if not dp else 'NOT: ' + '; '.join(dp))}" +
                 f" | {max(runs) if runs else '-'} | {r['solve_rc']} | {r['solve_seconds']} | {r['grade_seconds']} |")
    slowest = max(results, key=lambda r: r["grade_seconds"])
    L += ["", f"Slowest grading pass: {slowest['grade_seconds']} s ({slowest['variant']}, {slowest['mode']}).",
          f"Attempts found under solution/attempts/: {', '.join(found) or 'none'}; local probes found under probes/: "
          f"{', '.join(local) or 'none'}" + ("" if a.all or a.variants else " (not run; pass --all)") + ".",
          "Design attempts not found under solution/attempts/: " +
          (", ".join(x for x in DESIGN_ATTEMPTS if x not in found) or "none") +
          "; design local probes not found under probes/: " +
          (", ".join(x for x in DESIGN_PROBES if x not in local) or "none") +
          "; entries of solution/attempts/ not in the design: " +
          (", ".join(x for x in found if x not in DESIGN_ATTEMPTS) or "none") + ".", "",
          "ALL AS EXPECTED" if not (bad or off) else
          f"{bad} VARIANT RUN(S) NOT AS EXPECTED (reward, solve rc or crash); {off} NOT FAILING AS DESIGNED"]
    with open(os.path.join(HERE, "local_check.out.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    return 1 if bad or off else 0


if __name__ == "__main__":
    sys.exit(main())

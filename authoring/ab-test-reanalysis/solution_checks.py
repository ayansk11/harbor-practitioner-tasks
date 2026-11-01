"""Authoring check of the valid solutions of ab-test-reanalysis: canonical, alt_time and alt_recount.

For each variant: copy environment/app, apply solution/solve.sh with SOLUTION=<variant> to the copy (this also
regenerates output/result.json from the copy's data), keep what the /app artifact keeps (folders named data,
__pycache__ and .venv dropped at any depth), then run the readout command
    python -m abtest.report --data <folder> --out <file>
from that copy's top folder on six export folders: exp0, a copy of environment/app/data (the visible export), and
exp1 to exp5, the four .csv.gz files of tests/hidden/<set>/ staged unchanged. Each run is timed and its peak resident
memory read (getrusage in a one-child wrapper process). Two interpreter modes:
    venv   the authoring venv as it is (pandas finds pyarrow there);
    image  the same interpreter with pyarrow hidden (sys.modules["pyarrow"] = None), like the task images, which
           install numpy, pandas and scipy and no pyarrow (environment/Dockerfile).
Each readout is compared with ref_a's readout of the same folder, recomputed here, and with tests/expected/<set>.json
(which must equal it):
    canonical  n_users, pageviews, clicks, srm_p, srm_flag and decision identical (==); ctr, diff, bounds within 1e-9;
    alt_*      n_users, pageviews, clicks, srm_flag and decision identical; srm_p within 1e-12 relative;
    every one  grade.py's compare() passes (tests/grade.py run with a stub kit module, its own tolerances), and so do
               the instruction's rules as coded here; output/result.json written by solve.sh equals the venv run on
               exp0; the counts are the same for every variant and mode.
Run: submission/.venv/bin/python -I -B submission/authoring/ab-test-reanalysis/solution_checks.py
         [--scratch DIR] [--modes venv,image] [variant ...]
Writes solution_checks.json and solution_checks.out.md next to this file (paths relative; times are this machine's).
"""
import argparse, json, math, os, platform, runpy, shutil, subprocess, sys, time, types

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
PY = sys.executable
sys.path.insert(0, HERE)
import ref_a  # noqa: E402  (stdlib reference, rule route)

VARIANTS = ("canonical", "alt_time", "alt_recount")
HIDDEN = ("h_null", "h_pos", "h_srm", "h_plain", "h_neg")
SETS = ("visible",) + HIDDEN
FILES = ("assignments.csv.gz", "bot_flags.csv.gz", "pageviews.csv.gz", "module_clicks.csv.gz")
EXCLUDE = {"data", "__pycache__", ".venv"}
COUNTS = ("n_users", "pageviews", "clicks")
ARMS = ("A", "B")
STRICT_TOL = 1e-9
ALT_SRM_REL = 1e-12
WRAP = ("import json, resource, subprocess, sys, time\n"
        "t = time.perf_counter()\n"
        "r = subprocess.run(sys.argv[2:], cwd=sys.argv[1], capture_output=True, text=True)\n"
        "dt = time.perf_counter() - t\n"
        "rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss\n"
        "print(json.dumps({'rc': r.returncode, 'seconds': dt, 'maxrss': rss, 'stdout': r.stdout[-1500:],"
        " 'stderr': r.stderr[-1500:]}))\n")
IMAGE_RUN = ("import runpy, sys; sys.modules['pyarrow'] = None; "
             "runpy.run_module('abtest.report', run_name='__main__', alter_sys=True)")
RSS_UNIT = 1 if sys.platform == "darwin" else 1024         # ru_maxrss: bytes on macOS, KiB on Linux


class Clean:
    """Replaces absolute paths in text with placeholders, so no machine path reaches the written files."""

    def __init__(self, scratch):
        self.pairs = sorted({(scratch, "<scratch>"), (TASK, "<task>"), (HERE, "<authoring>"),
                             (os.path.dirname(os.path.dirname(PY)), "<venv>")}, key=lambda p: -len(p[0]))

    def __call__(self, text):
        for old, new in self.pairs:
            text = text.replace(old, new)
        return text


def run_env(variant, app):
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env.update(SOLUTION=variant, APP_DIR=app, PYTHON=PY, PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
               PATH=os.path.dirname(PY) + os.pathsep + os.environ.get("PATH", ""))
    return env


def artifact_copy(src, dst):
    def ignore(d, names):
        return [n for n in names if n in EXCLUDE and os.path.isdir(os.path.join(d, n))]
    shutil.copytree(src, dst, symlinks=True, ignore=ignore)


def stage_sets(root):
    """exp0 = the visible export, exp1..exp5 = the hidden ones; the four .csv.gz files copied unchanged."""
    folders = {}
    for i, name in enumerate(SETS):
        src = os.path.join(TASK, "environment", "app", "data") if name == "visible" else \
            os.path.join(TASK, "tests", "hidden", name)
        dst = os.path.join(root, f"exp{i}")
        shutil.rmtree(dst, ignore_errors=True)
        os.makedirs(dst)
        for f in FILES:
            shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))
        folders[name] = dst
    return folders


def command(mode, data, out):
    base = [PY, "-B", "-E", "-s"]                           # -I would hide abtest: -m needs the cwd on sys.path
    if mode == "venv":
        return base + ["-m", "abtest.report", "--data", data, "--out", out]
    return base + ["-c", IMAGE_RUN, "--data", data, "--out", out]


def timed(cwd, cmd):
    p = subprocess.run([PY, "-I", "-B", "-c", WRAP, cwd] + cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return {"rc": -1, "seconds": None, "maxrss": None, "stdout": "", "stderr": p.stderr[-1500:]}
    return json.loads(p.stdout.strip().splitlines()[-1])


def load_grade_compare():
    """compare() of tests/grade.py, run with a stub kit module (no sandbox, no /tests): (function, tolerances)."""
    stub = types.ModuleType("kit")
    stub.TESTS_DIR, stub.LOCAL, stub.SCRATCH = os.path.join(TASK, "tests"), True, ""
    stub.log = lambda msg: None
    stub.main = lambda fn: None
    saved = sys.modules.get("kit")
    sys.modules["kit"] = stub
    try:
        ns = runpy.run_path(os.path.join(TASK, "tests", "grade.py"), run_name="grade_checked")
        return ns["compare"], {k: ns.get(k) for k in ("BAND", "CTR_TOL", "SRM_REL", "SRM_TINY")}, None
    except Exception as e:                                  # grade.py being rewritten: fall back to own rules
        return None, {}, f"{type(e).__name__}: {e}"
    finally:
        if saved is None:
            sys.modules.pop("kit", None)
        else:
            sys.modules["kit"] = saved


def instruction_rules(got, exp, band=0.25, tol=1e-9, srm_rel=0.01, srm_tiny=1e-12):
    """The instruction's grading rules, coded independently of grade.py. Returns the failed checks."""
    bad = [f"{k}.{a}" for k in COUNTS for a in ARMS if got.get(k, {}).get(a) != exp[k][a]]
    bad += [f"ctr.{a}" for a in ARMS if not abs(got["ctr"][a] - exp["ctr"][a]) <= tol]
    bad += ["diff"] if not abs(got["diff"] - exp["diff"]) <= tol else []
    both_tiny = got["srm_p"] < srm_tiny and exp["srm_p"] < srm_tiny
    bad += ["srm_p"] if not (both_tiny or abs(got["srm_p"] - exp["srm_p"]) <= srm_rel * exp["srm_p"]) else []
    bad += [k for k in ("srm_flag", "decision") if got[k] != exp[k]]
    hw = exp["half_width"]
    bad += [f"ci_95[{i}]" for i in (0, 1) if not abs(got["ci_95"][i] - exp["ci_95"][i]) <= band * hw]
    return bad


def strict(variant, got, ref):
    """Identity checks against ref_a: the canonical must equal it; an alternative must have its counts."""
    bad = [f"{k}.{a}" for k in COUNTS for a in ARMS if got[k][a] != ref[k][a]]
    bad += [k for k in ("srm_flag", "decision") if got[k] != ref[k]]
    if variant == "canonical":
        bad += ["srm_p"] if got["srm_p"] != ref["srm_p"] else []
        bad += [f"ctr.{a}" for a in ARMS if not abs(got["ctr"][a] - ref["ctr"][a]) <= STRICT_TOL]
        bad += ["diff"] if not abs(got["diff"] - ref["diff"]) <= STRICT_TOL else []
        bad += [f"ci_95[{i}]" for i in (0, 1) if not abs(got["ci_95"][i] - ref["ci_95"][i]) <= STRICT_TOL]
    elif not abs(got["srm_p"] - ref["srm_p"]) <= ALT_SRM_REL * ref["srm_p"]:
        bad.append("srm_p")
    return bad


def check_variant(variant, modes, sets, refs, compare, scratch, clean):
    root = os.path.join(scratch, variant)
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    app = os.path.join(root, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app"), app)
    t0 = time.perf_counter()
    s = subprocess.run(["bash", os.path.join(TASK, "solution", "solve.sh")], env=run_env(variant, app),
                       capture_output=True, text=True)
    res = {"variant": variant, "solve_rc": s.returncode, "solve_seconds": round(time.perf_counter() - t0, 3),
           "solve_out": clean((s.stdout + s.stderr)[-1500:]), "runs": {}, "problems": []}
    art = os.path.join(root, "artifact")
    artifact_copy(app, art)
    shutil.rmtree(app)
    try:
        with open(os.path.join(art, "output", "result.json"), "rb") as f:
            regen_raw = f.read()
        regen = json.loads(regen_raw)
    except Exception as e:
        regen_raw, regen = b"", None
        res["problems"].append(f"output/result.json unreadable: {type(e).__name__}")
    if regen is not None:
        ok, m = compare("visible", regen_raw, refs["visible"]) if compare else (None, {})
        res["regen_grade_ok"] = ok
        res["regen_rules_failed"] = instruction_rules(regen, refs["visible"])
    for mode in modes:
        for name in SETS:
            out = os.path.join(root, "out", mode, name + ".json")
            r = timed(art, command(mode, sets[name], out))
            run = {"rc": r["rc"], "seconds": None if r["seconds"] is None else round(r["seconds"], 3),
                   "peak_mib": None if r["maxrss"] is None else round(r["maxrss"] * RSS_UNIT / 2**20, 1)}
            try:
                with open(out, "rb") as f:
                    raw = f.read()
                got = json.loads(raw)
            except Exception as e:
                run["error"] = f"no readable --out file ({type(e).__name__}); stderr: {clean(r['stderr'][-600:])}"
                res["runs"][f"{mode}/{name}"] = run
                res["problems"].append(f"{mode}/{name}: {run['error']}")
                continue
            ref = refs[name]
            run["counts"] = {k: got[k] for k in COUNTS}
            run["decision"] = got["decision"]
            run["ci_err_hw"] = [abs(got["ci_95"][i] - ref["ci_95"][i]) / ref["half_width"] for i in (0, 1)]
            run["srm_p_rel_err"] = abs(got["srm_p"] - ref["srm_p"]) / ref["srm_p"]
            run["srm_p_identical"] = got["srm_p"] == ref["srm_p"]
            run["ctr_diff_max_abs_err"] = max([abs(got["ctr"][a] - ref["ctr"][a]) for a in ARMS] +
                                              [abs(got["diff"] - ref["diff"])])
            run["strict_failed"] = strict(variant, got, ref)
            run["rules_failed"] = instruction_rules(got, ref)
            if compare:
                ok, _m = compare(name, raw, ref)
                run["grade_compare_ok"] = bool(ok)
            run["notes_present"] = isinstance(got.get("notes"), list) and all(isinstance(x, str) for x in got["notes"])
            if mode == "venv" and name == "visible" and regen is not None:
                run["regen_equal"] = regen == got
            for key in ("strict_failed", "rules_failed"):
                if run[key]:
                    res["problems"].append(f"{mode}/{name}: {key} {run[key]}")
            if r["rc"] != 0 or (compare and not run["grade_compare_ok"]) or run.get("regen_equal") is False:
                res["problems"].append(f"{mode}/{name}: rc {r['rc']}, grade_compare_ok {run.get('grade_compare_ok')}, "
                                       f"regen_equal {run.get('regen_equal')}")
            res["runs"][f"{mode}/{name}"] = run
    return res


def versions():
    out = {"python": platform.python_version(), "system": f"{platform.system()} {platform.machine()}"}
    for mod in ("numpy", "pandas", "scipy", "pyarrow"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            out[mod] = "not importable"
    return out


def write_report(results, refs, meta, path):
    lines = ["# solution_checks (solution_checks.py)", "",
             f"Run {meta['started']} (this machine's clock), {meta['system']}, Python {meta['python']}; numpy "
             f"{meta['numpy']}, pandas {meta['pandas']}, scipy {meta['scipy']}, pyarrow {meta['pyarrow']} (mode "
             "image hides it). grade.py compare(): " + (meta["grade_compare"] or "loaded") + ".", "",
             "Reference readouts (ref_a, recomputed; tests/expected equal: " +
             ("yes" if meta["expected_equal"] else "NO") + "):", "",
             "| set | n_users A/B | pageviews A/B | clicks A/B | srm_p | decision | half-width |",
             "|---|---|---|---|---|---|---|"]
    for name in SETS:
        r = refs[name]
        lines.append(f"| {name} | {r['n_users']['A']}/{r['n_users']['B']} | {r['pageviews']['A']}/"
                     f"{r['pageviews']['B']} | {r['clicks']['A']}/{r['clicks']['B']} | {r['srm_p']:.4g} | "
                     f"{r['decision']} | {r['half_width']:.6f} |")
    lines += ["", "Per run: counts identical to ref_a (all three count keys, both arms), srm_p identical (==) or its "
              "relative error, CI bound errors in reference half-widths (lower/upper), grade.py compare(), the "
              "instruction's rules, seconds and peak MiB of the whole command (interpreter start included).", "",
              "| variant | mode | set | counts | srm_p | ci err lo/hi (hw) | compare | rules | s | peak MiB |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for res in results:
        for key, run in res["runs"].items():
            mode, name = key.split("/")
            if "error" in run:
                lines.append(f"| {res['variant']} | {mode} | {name} | ERROR | | | | | {run['seconds']} | |")
                continue
            same = "==" if not [p for p in run["strict_failed"] if p.split(".")[0] in COUNTS] else "DIFFER"
            srm = "==" if run["srm_p_identical"] else f"{run['srm_p_rel_err']:.1e}"
            lines.append(f"| {res['variant']} | {mode} | {name} | {same} | {srm} | {run['ci_err_hw'][0]:.4f}/"
                         f"{run['ci_err_hw'][1]:.4f} | {'pass' if run.get('grade_compare_ok') else 'FAIL'} | "
                         f"{'pass' if not run['rules_failed'] else 'FAIL'} | {run['seconds']} | {run['peak_mib']} |")
    lines += ["", "| variant | solve.sh rc | solve.sh s | regenerated readout = venv run on exp0 | "
              "max s venv / image | max peak MiB venv / image | problems |", "|---|---|---|---|---|---|---|"]
    for res in results:
        mx = {}
        for mode in meta["modes"]:
            rs = [r for k, r in res["runs"].items() if k.startswith(mode + "/") and r["seconds"] is not None]
            mx[mode] = (max(r["seconds"] for r in rs) if rs else None,
                        max(r["peak_mib"] for r in rs) if rs else None)
        eq = res["runs"].get("venv/visible", {}).get("regen_equal")
        lines.append(f"| {res['variant']} | {res['solve_rc']} | {res['solve_seconds']} | {eq} | " +
                     " / ".join(str(mx[m][0]) for m in meta["modes"]) + " | " +
                     " / ".join(str(mx[m][1]) for m in meta["modes"]) + f" | {len(res['problems'])} |")
    lines += ["", f"Counts the same for every variant and mode on every set: {meta['counts_agree']}.",
              f"RESULT: {'ALL CHECKS PASS' if meta['all_ok'] else 'PROBLEMS: see solution_checks.json'}", ""]
    with open(path, "w", encoding="ascii") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="*", default=list(VARIANTS))
    ap.add_argument("--scratch", default=os.path.join(HERE, ".localruns", "solutions"))
    ap.add_argument("--modes", default="venv,image")
    a = ap.parse_args()
    scratch = os.path.abspath(a.scratch)
    modes = [m for m in a.modes.split(",") if m]
    clean = Clean(scratch)
    os.makedirs(scratch, exist_ok=True)
    meta = dict(versions(), started=time.strftime("%Y-%m-%d %H:%M:%S %Z"), modes=modes)
    sets = stage_sets(os.path.join(scratch, "sets"))
    refs, equal = {}, True
    for name in SETS:
        refs[name] = json.loads(json.dumps(ref_a.analyse(sets[name])))
        with open(os.path.join(TASK, "tests", "expected", name + ".json"), encoding="utf-8") as f:
            equal = equal and json.load(f) == refs[name]
    meta["expected_equal"] = equal
    compare, tol, err = load_grade_compare()
    meta["grade_compare"] = f"not usable ({err}); the instruction's rules only" if err else \
        "loaded, tolerances " + ", ".join(f"{k} {v}" for k, v in tol.items())
    results = [check_variant(v, modes, sets, refs, compare, scratch, clean) for v in a.variants]
    runs = [(key.split("/")[1], run) for res in results for key, run in res["runs"].items()]
    meta["counts_agree"] = (len(runs) == len(results) * len(modes) * len(SETS) and
                            all(run.get("counts") == {k: refs[name][k] for k in COUNTS} for name, run in runs))
    meta["all_ok"] = (equal and meta["counts_agree"] and compare is not None and
                      all(not r["problems"] and r["solve_rc"] == 0 for r in results))
    with open(os.path.join(HERE, "solution_checks.json"), "w", encoding="ascii") as f:
        json.dump({"meta": meta, "refs": refs, "results": results}, f, indent=1)
    write_report(results, refs, meta, os.path.join(HERE, "solution_checks.out.md"))
    for res in results:
        print(res["variant"], "solve rc", res["solve_rc"], f"{res['solve_seconds']} s,", len(res["problems"]),
              "problems", *res["problems"][:6], sep=" ")
    print("expected == ref_a:", equal, "| counts agree:", meta["counts_agree"], "| grade compare:",
          meta["grade_compare"])
    print("ALL CHECKS PASS" if meta["all_ok"] else "PROBLEMS: see solution_checks.json")
    return 0 if meta["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

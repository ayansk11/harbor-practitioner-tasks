"""Local proof matrix for one task package (the Mac, no Docker): tests/grade.py in KIT_LOCAL mode on every variant.

Reusable: the task slug is the name of the folder this script sits in (submission/authoring/<slug>/), so another task
can copy the file unchanged if its package follows the template:
  - solution/solve.sh applies SOLUTION=<variant> to APP_DIR (default /app);
  - variants: canonical and alt (expected reward 1); original (nothing applied: what a no-op agent leaves, expected
    0); every folder in solution/attempts/ (expected 0);
  - tests/grade.py honours KIT_LOCAL, KIT_SUBMISSION, KIT_LOGS, KIT_WORK and GRADE_TESTS_DIR (base/verifier_kit/README.md, "Local authoring").
  - optional: ablations.py next to this script defines ABLATIONS = {name: {"base": variant, "expected": 0 or 1,
    "patch": [(path under app, old text, new text), ...], "env": {VAR: value}}}: local-only variants (never shipped).
Per variant: copy environment/app to a scratch folder, apply the variant, run the visible pytest suite there (if the
app has tests/), drop folders named data, __pycache__ and .venv at any depth (what the /app artifact keeps), run
grade.py, read reward.json. Also: package integrity (tests/SHA256SUMS, tests/original equals the shipped code, no
__pycache__ in the package).

Usage: submission/.venv/bin/python submission/authoring/<slug>/local_check.py [--repeat N] [variant ...]
With no variant names it runs all of them and writes submission/docs/<slug>/local_results.txt.
"""
import argparse, datetime as dt, filecmp, hashlib, importlib.util, json, os, pathlib, re, shutil, subprocess, sys
import tempfile, time

HERE = pathlib.Path(__file__).resolve().parent
SLUG = HERE.name
SUB = HERE.parents[1]
TASK = SUB / "tasks" / SLUG
PY = SUB / ".venv" / "bin" / "python"
OUT = SUB / "docs" / SLUG / "local_results.txt"
EXCLUDE = {"data", "__pycache__", ".venv"}


def load_ablations():
    p = HERE / "ablations.py"
    if not p.exists():
        return {}
    spec = importlib.util.spec_from_file_location("ablations", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ABLATIONS


ABLATIONS = load_ablations()
ATTEMPTS = sorted(p.name for p in (TASK / "solution" / "attempts").iterdir() if p.is_dir()) \
    if (TASK / "solution" / "attempts").is_dir() else []
EXPECT = {"canonical": 1.0, "alt": 1.0, "original": 0.0, **{a: 0.0 for a in ATTEMPTS},
          **{a: float(v.get("expected", 0)) for a, v in ABLATIONS.items()}}


def drop_excluded(root):
    for p in sorted(root.rglob("*"), key=lambda x: -len(x.parts)):
        if p.is_dir() and p.name in EXCLUDE:
            shutil.rmtree(p)


def base_env():
    return {"PATH": f"{PY.parent}:/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp"), "LANG": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1"}


def make_app(scratch, variant):
    base = scratch / variant
    shutil.rmtree(base, ignore_errors=True)
    app = base / "app"
    shutil.copytree(TASK / "environment" / "app", app)
    abl = ABLATIONS.get(variant)
    applied = abl["base"] if abl else variant
    if applied != "original":
        env = dict(base_env(), APP_DIR=str(app), SOLUTION=applied)
        r = subprocess.run(["bash", str(TASK / "solution" / "solve.sh")], env=env, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"solve.sh SOLUTION={applied} failed: {r.stderr[-500:]}")
    for rel, old, new in (abl or {}).get("patch", []):
        p = app / rel
        text = p.read_text()
        assert text.count(old) == 1, (variant, rel, old[:60])
        p.write_text(text.replace(old, new))
    return base, app


def visible_suite(app):
    if not (app / "tests").is_dir():
        return "n/a"
    r = subprocess.run([str(PY), "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], cwd=app, env=base_env(),
                       capture_output=True, text=True, timeout=600)
    last = (r.stdout.strip().splitlines() or ["?"])[-1]
    return ("pass" if r.returncode == 0 else "FAIL") + f" ({last.strip()})"


def grade(scratch, variant):
    base, app = make_app(scratch, variant)
    suite = visible_suite(app)
    drop_excluded(app)
    logs, work = base / "logs", base / "work"
    env = dict(base_env(), KIT_LOCAL="1", KIT_SUBMISSION=str(app), KIT_LOGS=str(logs), KIT_WORK=str(work),
               GRADE_TESTS_DIR=str(TASK / "tests"))
    env.update(ABLATIONS.get(variant, {}).get("env", {}))
    t0 = time.monotonic()
    p = subprocess.run([str(PY), str(TASK / "tests" / "grade.py")], cwd=TASK / "tests", env=env,
                       capture_output=True, text=True, timeout=1800)
    secs = time.monotonic() - t0
    (base / "grade_stdout.txt").write_text(p.stdout + p.stderr)
    try:
        reward = json.loads((logs / "reward.json").read_text())
    except (OSError, ValueError) as e:
        reward = {"reward": None, "error": repr(e)}
    fails = [ln.split("FAIL ", 1)[1] for ln in p.stdout.splitlines() if "  FAIL " in ln]
    failed_checks = sorted(k[:-3] for k, v in reward.items() if k.endswith("_ok") and v == 0)
    return {"variant": variant, "expected": EXPECT[variant], "reward": reward.get("reward"), "seconds": round(secs, 2),
            "failed_checks": failed_checks, "metrics": reward, "visible_suite": suite, "first_failures": fails[:3],
            "stdout": str(base / "grade_stdout.txt")}


def integrity():
    out, tests = [], TASK / "tests"
    sums = tests / "SHA256SUMS"
    if sums.exists():
        bad = [rel for digest, rel in (ln.split("  ", 1) for ln in sums.read_text().splitlines() if ln.strip())
               if hashlib.sha256((tests / rel).read_bytes()).hexdigest() != digest]
        out.append(f"SHA256SUMS: {'ok' if not bad else 'MISMATCH ' + ', '.join(bad)}")
    orig = tests / "original"
    if orig.is_dir():
        diffs = []
        for p in sorted(orig.rglob("*")):
            if p.is_file():
                q = TASK / "environment" / "app" / p.relative_to(orig)
                if not q.exists() or not filecmp.cmp(p, q, shallow=False):
                    diffs.append(str(p.relative_to(orig)))
        out.append(f"tests/original equals the shipped code: {'yes' if not diffs else 'NO: ' + ', '.join(diffs)}")
    caches = [str(p.relative_to(TASK)) for p in TASK.rglob("__pycache__")]
    out.append(f"__pycache__ in the package: {caches or 'none'}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="*")
    ap.add_argument("--repeat", type=int, default=1, help="run each named variant this many times")
    args = ap.parse_args()
    names = args.variants or (["canonical", "alt", "original"] + ATTEMPTS + list(ABLATIONS))
    unknown = [n for n in names if n not in EXPECT]
    if unknown:
        sys.exit(f"unknown variants: {unknown}; known: {sorted(EXPECT)}")
    scratch = pathlib.Path(os.environ.get("LOCAL_SCRATCH") or tempfile.mkdtemp(prefix=f"{SLUG}-local-"))
    started = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    rows = []
    for name in names:
        for _ in range(args.repeat):
            r = grade(scratch, name)
            rows.append(r)
            mark = "ok" if r["reward"] == r["expected"] else "UNEXPECTED"
            print(f"{name:28s} expected {r['expected']:.0f} got {r['reward']} {mark:10s} {r['seconds']:7.2f}s "
                  f"failed checks: {','.join(r['failed_checks']) or '-'}  visible suite: {r['visible_suite']}",
                  flush=True)
    lines = [f"# local_check.py results for {SLUG}", f"started {started} (Mac clock); python {sys.version.split()[0]}",
             f"command: {PY} {pathlib.Path(__file__)} {' '.join(sys.argv[1:])}".rstrip(), f"scratch: {scratch}", ""]
    lines += integrity() + [""]
    lines.append("| Variant | Expected | Got | Grade time (s) | Failed checks | Visible suite | First failure |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        first = (r["first_failures"][0] if r["first_failures"] else "-").replace("|", "/")[:160]
        lines.append(f"| {r['variant']} | {r['expected']:.0f} | {r['reward']} | {r['seconds']} | "
                     f"{', '.join(r['failed_checks']) or '-'} | {r['visible_suite']} | {first} |")
    ok = all(r["reward"] == r["expected"] for r in rows)
    lines += ["", f"ALL AS EXPECTED: {'yes' if ok else 'NO'}", "", "metrics per run:"]
    lines += [f"- {r['variant']}: {json.dumps(r['metrics'])}" for r in rows]
    text = "\n".join(lines) + "\n"
    print("\n" + text)
    if not args.variants:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text)
        print(f"wrote {OUT}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

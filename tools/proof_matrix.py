"""Run a task's proof matrix with Harbor (Docker by default; Daytona was used) and write
validation/<slug>/PROOF_RESULTS_<tag>.md and proof_results_<tag>.json.

Usage: python tools/proof_matrix.py <slug> [--n 2] [--oracle-k 10] [--tag <suffix>] [--only v1,v2]
       [--without-agent-network-line]
Variants: canonical (oracle x k), every alt* folder under solution/, nop (the nop agent), every attempt under
solution/attempts/ (files or folders; names starting with "_" are helpers), and one --force-build oracle.
Expected rewards: 1 for canonical, alt* and force-build; 0 for nop and attempts.
--without-agent-network-line runs a copy of the task whose task.toml lacks its [agent] network_mode line, for a backend
that cannot apply that setting (Daytona Tier 1 refuses Harbor's runtime network switch, so every trial there fails;
Daytona's documentation sets the same limits for Tier 2, which was not tried). The copy,
jobs/<slug>/package-<tag>/<slug>, differs from the task in that one line only.

Runner options (defaults suit a reviewer with Docker): --env docker (Harbor's default backend; the proofs used
--env daytona), --env-file <path> (only if your backend needs keys, e.g. a .env with DAYTONA_API_KEY; this script
passes the path to Harbor and never opens the file), --harbor <path> (default: `harbor` on PATH). Each also reads an
environment variable: HARBOR_ENV, HARBOR_ENV_FILE, HARBOR_BIN.
"""
import argparse, datetime, glob, json, os, pathlib, re, shutil, subprocess, sys, tomllib
ROOT = pathlib.Path(__file__).resolve().parents[1]

ap = argparse.ArgumentParser()
ap.add_argument("slug"); ap.add_argument("--n", type=int, default=2); ap.add_argument("--oracle-k", type=int, default=10)
ap.add_argument("--tag", default=datetime.datetime.now().strftime("%m%d-%H%M")); ap.add_argument("--only", default="")
ap.add_argument("--env", default=os.environ.get("HARBOR_ENV", "docker"))
ap.add_argument("--env-file", default=os.environ.get("HARBOR_ENV_FILE", ""))
ap.add_argument("--harbor", default=os.environ.get("HARBOR_BIN", shutil.which("harbor") or "harbor"))
ap.add_argument("--without-agent-network-line", action="store_true")
a = ap.parse_args()
task = ROOT / "tasks" / a.slug
jobs_dir = ROOT / "jobs" / a.slug
package = f"tasks/{a.slug}"
if a.without_agent_network_line:
    src = (task / "task.toml").read_text()
    kept, table = [], ""
    for line in src.splitlines(keepends=True):
        s = line.split("#", 1)[0].strip()
        if s.startswith("["): table = s
        if not (table == "[agent]" and re.match(r"network_mode\s*=", s)): kept.append(line)
    want = tomllib.loads(src); want.get("agent", {}).pop("network_mode", None)
    if len(kept) != len(src.splitlines()) - 1 or tomllib.loads("".join(kept)) != want:
        sys.exit("--without-agent-network-line: task.toml must have exactly one [agent] network_mode line")
    copy = jobs_dir / f"package-{a.tag}" / a.slug
    shutil.rmtree(copy, ignore_errors=True)  # caches and editor or tool state are not part of the package
    shutil.copytree(task, copy, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", ".claude-flow"))
    (copy / "task.toml").write_text("".join(kept))
    task, package = copy, f"jobs/{a.slug}/package-{a.tag}/{a.slug}, a copy of tasks/{a.slug} without its [agent] network_mode line"
sol = task / "solution"
alts = sorted(p.name for p in sol.iterdir() if p.is_dir() and p.name.startswith("alt"))
attempts = sorted({p.stem for p in (sol / "attempts").iterdir() if not p.name.startswith("_")}) if (sol / "attempts").is_dir() else []
plan = [("canonical", ["-a", "oracle", "-k", str(a.oracle_k)], 1)]
plan += [(x, ["-a", "oracle", "--ae", f"SOLUTION={x}"], 1) for x in alts]
plan += [("nop", ["-a", "nop"], 0)]
plan += [(x, ["-a", "oracle", "--ae", f"SOLUTION={x}"], 0) for x in attempts]
plan += [("force-build", ["-a", "oracle", "--force-build"], 1)]
if a.only:
    keep = set(a.only.split(",")); plan = [p for p in plan if p[0] in keep]
out_dir = ROOT / "validation" / a.slug
out_dir.mkdir(parents=True, exist_ok=True)
rows = []
for name, args, expected in plan:
    job = f"{a.slug}-{name}-{a.tag}"
    cmd = [a.harbor, "run", "-p", str(task), "-e", a.env] + (["--env-file", os.path.expanduser(a.env_file)] if a.env_file else []) + ["-n", str(a.n), "-o", str(jobs_dir), "--job-name", job] + args
    t0 = datetime.datetime.now()
    print(f"[{t0:%H:%M:%S}] {name}: {' '.join(args)}", flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    trials = []
    for rj in sorted(glob.glob(str(jobs_dir / job / "*" / "result.json"))):
        r = json.load(open(rj))
        vr = r.get("verifier_result") or {}
        rew = (vr.get("rewards") or {}).get("reward") if isinstance(vr.get("rewards"), dict) else vr.get("reward")
        exc = (r.get("exception_info") or {}).get("exception_type")
        trials.append({"trial": pathlib.Path(rj).parent.name, "reward": rew, "exception": exc})
    rewards = [t["reward"] for t in trials]
    ok = bool(trials) and all(t["exception"] is None and t["reward"] is not None and float(t["reward"]) == expected for t in trials)
    rows.append({"variant": name, "args": " ".join(args), "expected": expected, "rewards": rewards,
                 "exceptions": [t["exception"] for t in trials if t["exception"]], "trials": len(trials), "pass": ok,
                 "job": f"jobs/{a.slug}/{job}", "started": f"{t0:%Y-%m-%d %H:%M:%S}", "harbor_rc": p.returncode})
    print(f"    -> rewards {rewards} exceptions {rows[-1]['exceptions']} {'PASS' if ok else 'FAIL'}", flush=True)
    json.dump({"slug": a.slug, "tag": a.tag, "package": package, "rows": rows}, open(out_dir / f"proof_results_{a.tag}.json", "w"), indent=1)
allpass = all(r["pass"] for r in rows)
md = [f"# Proof matrix: {a.slug} (run {a.tag}, backend {a.env}, Harbor 0.25.0; local clock)", "", f"Package: {package}", "",
      f"Overall: {'ALL AS EXPECTED' if allpass else 'NOT ALL AS EXPECTED'}", "",
      "| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |", "|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['variant']} | `{r['args']}` | {r['expected']} | {r['rewards']} | {r['exceptions'] or '-'} | {'PASS' if r['pass'] else 'FAIL'} | `{r['job']}` |")
(out_dir / f"PROOF_RESULTS_{a.tag}.md").write_text("\n".join(md) + "\n")
print("\n".join(md)); sys.exit(0 if allpass else 1)

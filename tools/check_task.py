"""Static checks for one task package (run before every Daytona proof run): python tools/check_task.py tasks/<slug>."""
import hashlib, pathlib, re, subprocess, sys, tomllib
ROOT = pathlib.Path(__file__).resolve().parents[1]
DIGEST = (ROOT / "tools" / "BASE_IMAGE_DIGEST").read_text().strip()
EXPECTED_ARTIFACT = {"source": "/app", "exclude": ["data", "__pycache__", ".venv"]}
task = pathlib.Path(sys.argv[1]).resolve()
problems = []
def need(p):
    if not (task / p).exists(): problems.append(f"missing {p}")
for p in ["task.toml", "instruction.md", "environment/Dockerfile", "tests/test.sh", "tests/Dockerfile", "tests/grade.py",
          "tests/kit.py", "solution/solve.sh"]:
    need(p)
cfg = tomllib.loads((task / "task.toml").read_text()) if (task / "task.toml").exists() else {}
if cfg.get("artifacts") != [EXPECTED_ARTIFACT]:
    problems.append(f"artifacts must be exactly [{EXPECTED_ARTIFACT}]")
v = cfg.get("verifier", {})
if v.get("environment_mode") != "separate": problems.append("verifier.environment_mode must be 'separate'")
# The agent may be denied network ([agent] network_mode = "no-network"); no other network setting is allowed: the graders
# need no network, and Daytona Tier 1 refuses network overrides.
if cfg.get("agent", {}).get("network_mode", "no-network") != "no-network": problems.append("agent.network_mode, if set, must be 'no-network'")
for sect, t in (("agent", cfg.get("agent", {})), ("verifier", v), ("environment", cfg.get("environment", {})),
                ("verifier.environment", v.get("environment", {}))):
    for key in ("network_mode", "allowed_hosts", "allow_internet"):
        if key in t and (sect, key) != ("agent", "network_mode"): problems.append(f"{sect}.{key} must not be set (Daytona Tier 1 refuses network overrides)")
for df in ("environment/Dockerfile", "tests/Dockerfile"):
    f = task / df
    if f.exists():
        txt = f.read_text()
        froms = re.findall(r"^FROM\s+(\S+)", txt, re.M)
        if not froms or any(fr != f"python:3.12-slim-bookworm@{DIGEST}" for fr in froms):
            problems.append(f"{df}: FROM must be python:3.12-slim-bookworm@{DIGEST}")
        for line in re.findall(r"^\s*RUN .*pip install.*$", txt.replace("\\\n", " "), re.M):
            for tok in line.split("pip install", 1)[1].split("&&")[0].split():
                if not tok.startswith("-") and "==" not in tok: problems.append(f"{df}: pip package not pinned with ==: {tok}")
env_df = (task / "environment/Dockerfile").read_text() if (task / "environment/Dockerfile").exists() else ""
if re.search(r"^\s*(COPY|ADD)\b.*\b(tests|solution)\b", env_df, re.M): problems.append("environment/Dockerfile copies tests or solution")
kit = ROOT / "base" / "verifier_kit"
for f in ("kit.py", "test.sh"):
    a, b = kit / f, task / "tests" / f
    if b.exists() and hashlib.sha256(a.read_bytes()).digest() != hashlib.sha256(b.read_bytes()).digest():
        problems.append(f"tests/{f} differs from base/verifier_kit (run tools/sync_kit.py)")
if (task / "instruction.md").exists() and "Only /app is kept when we grade" not in (task / "instruction.md").read_text():
    problems.append("instruction.md lacks the shared closing sentence about what is kept when grading")
lint = subprocess.run(["harbor", "lint", str(task), "--json"], capture_output=True, text=True)
if lint.returncode != 0 or lint.stdout.strip() not in ("[]", ""):
    problems.append(f"harbor lint: {lint.stdout.strip()[:500]} {lint.stderr.strip()[:200]}")
print("\n".join(problems) if problems else f"OK {task.name}")
sys.exit(1 if problems else 0)

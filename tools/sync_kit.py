"""Copy base/verifier_kit/{kit.py,test.sh} into every tasks/<slug>/tests/ (or --check that they are identical)."""
import hashlib, pathlib, shutil, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
KIT = ROOT / "base" / "verifier_kit"
FILES = ["kit.py", "test.sh"]
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
check = "--check" in sys.argv
bad = 0
for task in sorted((ROOT / "tasks").iterdir()):
    tests = task / "tests"
    if not tests.is_dir():
        continue
    for f in FILES:
        src, dst = KIT / f, tests / f
        if check:
            if not dst.exists() or h(src) != h(dst):
                print(f"MISMATCH {dst.relative_to(ROOT)}"); bad += 1
        else:
            shutil.copy2(src, dst)
            if f == "test.sh":
                dst.chmod(0o755)
    print(f"{'checked' if check else 'synced'} {task.name}")
sys.exit(1 if bad else 0)

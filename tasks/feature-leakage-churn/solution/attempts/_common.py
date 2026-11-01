"""Helpers for the wrong and shortcut attempts (each must score 0). They never read tests or expected answers.

solve.sh runs an attempt as `python3 attempts/<name>.py <app dir>`; the attempt edits <app dir>/churn in place. Most
attempts start from the canonical solution and change one rule (the realistic mistake, everything else right); the
others change the v3 pipeline as shipped. V3 holds the v3 sources as they were before the attempt changed anything.
"""
import os
import shutil
import sys

APP = sys.argv[1] if len(sys.argv) > 1 else "/app"
SOL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHURN = os.path.join(APP, "churn")
CANONICAL = ("attributes.py", "build_features.py", "encoding.py", "ops.py", "status.py", "visibility.py",
             "windows.py")
V3 = {n: open(os.path.join(CHURN, n)).read() for n in sorted(os.listdir(CHURN)) if n.endswith(".py")}


def use_canonical(skip=(), dest=None):
    """Copy the canonical modules over the churn package (dest, default <app dir>/churn), except the modules named in
    skip, which stay as v3 ships them."""
    dest = dest or CHURN
    for n in CANONICAL:
        if n not in skip:
            shutil.copy(os.path.join(SOL, "canonical", "churn", n), os.path.join(dest, n))


def edit(name, old, new):
    """Replace the one occurrence of old in churn/<name> with new."""
    p = os.path.join(CHURN, name)
    with open(p) as f:
        s = f.read()
    assert s.count(old) == 1, f"{name}: the text to replace occurs {s.count(old)} times, not once"
    with open(p, "w") as f:
        f.write(s.replace(old, new))


def append(name, text):
    """Add text at the end of churn/<name>."""
    with open(os.path.join(CHURN, name), "a") as f:
        f.write(text)


def v3_function(module, name):
    """The source of top-level function `name` in v3's churn/<module>, up to the next top-level statement."""
    lines = V3[module].splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith(f"def {name}("))
    end = next((i for i in range(start + 1, len(lines)) if lines[i][:1] not in ("", " ", "\n")), len(lines))
    return "".join(lines[start:end]).rstrip() + "\n"

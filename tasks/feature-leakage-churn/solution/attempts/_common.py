"""Helpers for the wrong and shortcut attempts (each must score 0). They never read tests or expected answers."""
import os, shutil, sys

APP = sys.argv[1] if len(sys.argv) > 1 else "/app"
SOL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def use_canonical(*names):
    for n in names:
        shutil.copy(os.path.join(SOL, "canonical", "churn", n), os.path.join(APP, "churn", n))


def edit(name, old, new):
    p = os.path.join(APP, "churn", name)
    s = open(p).read()
    assert old in s, f"{name}: text to replace not found"
    open(p, "w").write(s.replace(old, new))

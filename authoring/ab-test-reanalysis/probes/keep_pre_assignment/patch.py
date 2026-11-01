"""Local probe keep_pre_assignment (must score 0; not part of the task package, not run on Daytona): every other rule
is right (the canonical files), but the pageviews before the user's assigned_at are counted too (the module showed v1
to every user then, whatever the arm).
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

APP = pathlib.Path(sys.argv[1])


def edit(rel, old, new):
    p = APP / rel
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        sys.exit(f"patch.py: the canonical text was not found once in {rel}")
    p.write_text(s.replace(old, new), encoding="utf-8")


edit("abtest/load.py",
     '    pv = pv.loc[pv["ts"] >= pv["assigned_at"]]\n',
     '    # every pageview row of the user counts, before and after assignment\n')

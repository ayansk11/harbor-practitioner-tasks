"""Shortcut attempt hardcode_no_ship (must score 0): the canonical numbers, but the decision is always "no_ship", the
cautious answer to the PM, hard-coded. Right on every export whose readout is no_ship, wrong where the plan's rule
gives "ship" or "invalid".
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

APP = pathlib.Path(sys.argv[1])


def edit(rel, old, new):
    p = APP / rel
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        sys.exit(f"patch.py: the canonical text was not found once in {rel}")
    p.write_text(s.replace(old, new), encoding="utf-8")


old = 'def decide(srm_flag, ci_low):\n    """EXPERIMENT.md section 7, in this order."""\n'
edit("abtest/report.py", old, old + '    return "no_ship"  # the PM wants a yes or no; never ship on this data\n')

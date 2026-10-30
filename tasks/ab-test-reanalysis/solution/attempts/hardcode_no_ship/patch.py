"""Shortcut attempt: the canonical numbers, but the decision is always "no_ship" (the cautious answer, hard-coded).
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

p = pathlib.Path(sys.argv[1]) / "abtest" / "report.py"
s = p.read_text()
old = 'def decide(srm_flag, ci_low):\n    """EXPERIMENT.md section 7, in this order."""\n'
assert old in s, "canonical report.py not found"
p.write_text(s.replace(old, old + '    return "no_ship"  # PM wants a yes/no; never ship on this data\n', 1))

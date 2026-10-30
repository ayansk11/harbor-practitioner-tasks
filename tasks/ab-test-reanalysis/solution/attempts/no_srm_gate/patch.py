"""Wrong attempt: bots, CI and SRM numbers fixed, but the decision ignores the SRM flag.
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

p = pathlib.Path(sys.argv[1]) / "abtest" / "report.py"
s = p.read_text()
old = '    if srm_flag:\n        return "invalid"\n'
assert old in s, "canonical report.py not found"
p.write_text(s.replace(old, "", 1))

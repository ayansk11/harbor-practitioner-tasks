"""Wrong attempt: per-user CTR averaged over users (mean of ratios) with a user-level t interval, instead of the
plan's ratio of sums. Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

app = pathlib.Path(sys.argv[1]) / "abtest"
p = app / "report.py"
s = p.read_text()
old = '    ctr = {arm: clicks[arm] / views[arm] for arm in ARMS}\n'
new = ('    viewed = {arm: arms[arm][arms[arm]["views"] > 0] for arm in ARMS}\n'
       '    ctr = {arm: float((viewed[arm]["clicks"] / viewed[arm]["views"]).mean()) for arm in ARMS}\n')
assert old in s, "canonical report.py not found"
s = s.replace(old, new, 1)
old = '    diff, (ci_low, ci_high) = diff_ci(arms["A"], arms["B"])\n'
assert old in s
s = s.replace(old, '    diff, (ci_low, ci_high) = diff_ci(viewed["A"], viewed["B"])\n', 1)
p.write_text(s)
(app / "stats.py").write_text('''"""Statistics: per-user CTR, Welch interval over users."""
import math

from scipy.stats import chisquare, norm

Z = float(norm.ppf(0.975))
SRM_ALPHA = 0.001
CI_METHOD = "mean of per-user CTR, Welch normal interval"


def diff_ci(arm_a, arm_b):
    ra = arm_a["clicks"] / arm_a["views"]
    rb = arm_b["clicks"] / arm_b["views"]
    diff = float(rb.mean() - ra.mean())
    se = math.sqrt(rb.var(ddof=1) / len(rb) + ra.var(ddof=1) / len(ra))
    return diff, (diff - Z * se, diff + Z * se)


def srm_pvalue(n_a, n_b):
    return float(chisquare([n_a, n_b]).pvalue)
''')

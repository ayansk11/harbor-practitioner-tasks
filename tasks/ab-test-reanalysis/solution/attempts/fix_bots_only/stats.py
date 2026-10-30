"""Wrong attempt: bots excluded from both arms, SRM and decision rule added, but the CI still treats every pageview
as an independent trial (pageview-level standard error). Replaces abtest/stats.py after the canonical files."""
import math

from scipy.stats import chisquare, norm

Z = float(norm.ppf(0.975))
SRM_ALPHA = 0.001
CI_METHOD = "two-proportion normal interval on pageviews"


def diff_ci(arm_a, arm_b):
    ca, va = float(arm_a["clicks"].sum()), float(arm_a["views"].sum())
    cb, vb = float(arm_b["clicks"].sum()), float(arm_b["views"].sum())
    pa, pb = ca / va, cb / vb
    se = math.sqrt(pa * (1 - pa) / va + pb * (1 - pb) / vb)
    diff = pb - pa
    return diff, (diff - Z * se, diff + Z * se)


def srm_pvalue(n_a, n_b):
    return float(chisquare([n_a, n_b]).pvalue)

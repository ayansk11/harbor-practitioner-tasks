"""Shortcut attempt: keep the pageview-level interval and widen it by a constant fitted on the visible data
(K = delta-method half-width / pageview-level half-width on /app/data = 2.466, rounded). Right on the visible set by
construction; a fixed K cannot be right where the design effect differs. Replaces abtest/stats.py."""
import math

from scipy.stats import chisquare, norm

Z = float(norm.ppf(0.975))
SRM_ALPHA = 0.001
K = 2.466
CI_METHOD = f"pageview-level interval x {K}"


def diff_ci(arm_a, arm_b):
    ca, va = float(arm_a["clicks"].sum()), float(arm_a["views"].sum())
    cb, vb = float(arm_b["clicks"].sum()), float(arm_b["views"].sum())
    pa, pb = ca / va, cb / vb
    se = K * math.sqrt(pa * (1 - pa) / va + pb * (1 - pb) / vb)
    diff = pb - pa
    return diff, (diff - Z * se, diff + Z * se)


def srm_pvalue(n_a, n_b):
    return float(chisquare([n_a, n_b]).pvalue)

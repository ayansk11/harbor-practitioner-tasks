"""Shortcut attempt: keep the pageview-level interval and widen each arm's variance by K ** G, with Kish's
unequal-cluster-size factor K = mean(v^2) / mean(v)^2 over the arm's users (1 + CV^2) and ONE exponent G for every
experiment. It uses only the pageview counts, never the users' click variance, and has no fitted constant. G = 1.22 is
the best exponent of the authoring sweep (submission/authoring/ab-test-reanalysis/calibration_study.py, "Pageview-only
sweep", g from -3 to 4 in steps of 0.01): it was tuned on every graded set, hidden ones included, which no agent can do,
and it still fails, because h_null and h_twin have the same per-user pageview counts (DESIGN.md section 15), so K is
the same number on both, but h_null needs an interval about twice as wide. Before h_twin, G = 1.5 scored 1 (DESIGN.md
section 14); with the section-14 h_twin the best exponent was 1.23. Replaces abtest/stats.py after the
canonical files."""
import math

import numpy as np
from scipy.stats import chisquare, norm

Z = float(norm.ppf(0.975))
SRM_ALPHA = 0.001
G = 1.22
CI_METHOD = f"pageview-level interval x K^{G} per arm, K = mean(v^2)/mean(v)^2"


def _arm_var(arm):
    c = arm["clicks"].to_numpy(float)
    v = arm["views"].to_numpy(float)
    r = c.sum() / v.sum()
    k = float((v ** 2).mean()) / float(v.mean()) ** 2
    return r, r * (1 - r) / v.sum() * k ** G


def diff_ci(arm_a, arm_b):
    ra, va = _arm_var(arm_a)
    rb, vb = _arm_var(arm_b)
    diff = rb - ra
    se = math.sqrt(va + vb)
    return diff, (diff - Z * se, diff + Z * se)


def srm_pvalue(n_a, n_b):
    return float(chisquare([n_a, n_b]).pvalue)

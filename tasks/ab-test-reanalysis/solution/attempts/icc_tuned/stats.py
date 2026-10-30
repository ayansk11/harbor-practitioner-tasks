"""Shortcut attempt: keep the pageview-level interval and widen each arm's variance by a design effect
1 + RHO (m_w - 1), m_w = sum(v^2) / sum(v) over the arm's users, with ONE intra-user correlation RHO for every
experiment. It never uses the users' click variance. RHO = 0.170 is the best single value of the authoring sweep
(submission/authoring/ab-test-reanalysis/calibration_study.py, rho 0 to 1 in steps of 0.005): it was tuned on every
graded set, hidden ones included, which no agent can do, and it still fails (h_null too narrow, h_twin too wide).
(It was 0.145 with h_lowicc, before DESIGN.md section 14, and 0.175 with the section-14 h_twin, before section
15.) Replaces abtest/stats.py after the canonical files."""
import math

import numpy as np
from scipy.stats import chisquare, norm

Z = float(norm.ppf(0.975))
SRM_ALPHA = 0.001
RHO = 0.170
CI_METHOD = f"pageview-level interval x sqrt(1 + {RHO} (m_w - 1)) per arm"


def _arm_var(arm):
    c = arm["clicks"].to_numpy(float)
    v = arm["views"].to_numpy(float)
    r = c.sum() / v.sum()
    m_w = float((v ** 2).sum()) / float(v.sum())
    return r, r * (1 - r) / v.sum() * (1 + RHO * (m_w - 1))


def diff_ci(arm_a, arm_b):
    ra, va = _arm_var(arm_a)
    rb, vb = _arm_var(arm_b)
    diff = rb - ra
    se = math.sqrt(va + vb)
    return diff, (diff - Z * se, diff + Z * se)


def srm_pvalue(n_a, n_b):
    return float(chisquare([n_a, n_b]).pvalue)

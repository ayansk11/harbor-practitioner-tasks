"""Statistics (second alt): cluster-robust (CR1) standard error from a pageview-level regression (EXPERIMENT.md 5c).

Model: clicked = b0 + b1 * [variant == B] + e over counted pageviews, errors clustered by user. b1 is CTR_B - CTR_A.
With one binary regressor the sandwich only needs each user's summed residual, so the per-user sums suffice.
"""
import math

import numpy as np
from scipy.stats import chisquare, norm

SRM_ALPHA = 0.001
CI_METHOD = "CR1 cluster-robust standard error, clustered by user"


def diff_ci(arm_a, arm_b):
    ca, va = arm_a["clicks"].to_numpy(float), arm_a["views"].to_numpy(float)
    cb, vb = arm_b["clicks"].to_numpy(float), arm_b["views"].to_numpy(float)
    xtx = np.array([[va.sum() + vb.sum(), vb.sum()], [vb.sum(), vb.sum()]])
    xty = np.array([ca.sum() + cb.sum(), cb.sum()])
    beta = np.linalg.solve(xtx, xty)
    ua = ca - beta[0] * va                       # summed residual of each user in A (regressor row [1, 0])
    ub = cb - (beta[0] + beta[1]) * vb           # in B (regressor row [1, 1])
    scores = np.vstack([np.c_[ua, np.zeros_like(ua)], np.c_[ub, ub]])
    meat = scores.T @ scores
    bread = np.linalg.inv(xtx)
    g = len(scores)
    n_obs = va.sum() + vb.sum()
    cov = bread @ meat @ bread * (g / (g - 1)) * ((n_obs - 1) / (n_obs - 2))
    se = math.sqrt(cov[1, 1])
    z = norm.ppf(0.975)
    return float(beta[1]), (float(beta[1] - z * se), float(beta[1] + z * se))


def srm_pvalue(n_a, n_b):
    return float(chisquare([n_a, n_b]).pvalue)

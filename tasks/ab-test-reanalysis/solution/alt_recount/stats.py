"""Statistics (alt_recount solution): CR1 cluster-robust interval (EXPERIMENT.md section 5c) and the SRM test.

Model: clicked = b0 + b1 * [variant == B] + e over the counted pageviews, errors clustered by user; b1 = CTR_B - CTR_A.
With one binary regressor the sandwich (X'X)^-1 M (X'X)^-1 has a closed form: Var(b1) = sum_A u_i^2 / V_A^2 +
sum_B u_i^2 / V_B^2, with u_i = c_i - CTR_arm * n_i each user's summed residual and V the arm's pageviews, times the
CR1 factor G/(G-1) * (n-1)/(n-k): G clusters (users with a counted pageview), n pageviews, k = 2 coefficients.
"""
import math

import numpy as np
from scipy.stats import chi2, norm

SRM_ALPHA = 0.001
CI_METHOD = "CR1 cluster-robust standard error by user, pageview-level regression on a B indicator"


def cr1_ci(clicks_a, views_a, clicks_b, views_b):
    """(diff, lower, upper) of the 95% CI of CTR_B - CTR_A; inputs are per-user arrays of one arm each."""
    terms, n_obs, clusters, ctr = 0.0, 0.0, 0, {}
    for arm, c, v in (("A", clicks_a, views_a), ("B", clicks_b, views_b)):
        c = np.asarray(c, dtype=float)
        v = np.asarray(v, dtype=float)
        ctr[arm] = c.sum() / v.sum()
        u = c - ctr[arm] * v
        terms += float(np.dot(u, u)) / float(v.sum()) ** 2
        n_obs += float(v.sum())
        clusters += int(np.count_nonzero(v))
    var = terms * clusters / (clusters - 1) * (n_obs - 1) / (n_obs - 2)
    diff = float(ctr["B"] - ctr["A"])
    half = float(norm.ppf(0.975)) * math.sqrt(var)
    return diff, diff - half, diff + half


def srm_pvalue(n_a, n_b):
    """Pearson chi-square of the user counts against 50/50, 1 df, no continuity correction."""
    expected = (n_a + n_b) / 2.0
    stat = ((n_a - expected) ** 2 + (n_b - expected) ** 2) / expected
    return float(chi2.sf(stat, df=1))

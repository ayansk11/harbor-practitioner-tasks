"""Statistics for the CTR readout (EXPERIMENT.md sections 5 and 6). The unit of randomization is the user."""
import math

import numpy as np
from scipy.stats import norm

Z = float(norm.ppf(0.975))
SRM_ALPHA = 0.001
CI_METHOD = "delta method, users as the unit"


def ratio_delta(clicks, views):
    """CTR = sum(clicks) / sum(views) over users, and its delta-method variance.

    clicks, views: one entry per counted user, users with zero pageviews included. Var = N/(N-1) * sum((c - r v)^2) /
    (sum v)^2, the usual linearisation of a ratio of two user-level means.
    """
    c = np.asarray(clicks, dtype=float)
    v = np.asarray(views, dtype=float)
    n = len(c)
    r = c.sum() / v.sum()
    var = n / (n - 1) * float(np.sum((c - r * v) ** 2)) / float(v.sum()) ** 2
    return float(r), var


def diff_ci(arm_a, arm_b):
    """CTR_B - CTR_A and its 95% CI; arm_a, arm_b: per-user frames with columns clicks, views."""
    ra, va = ratio_delta(arm_a["clicks"], arm_a["views"])
    rb, vb = ratio_delta(arm_b["clicks"], arm_b["views"])
    diff = rb - ra
    se = math.sqrt(va + vb)
    return diff, (diff - Z * se, diff + Z * se)


def srm_pvalue(n_a, n_b):
    """Pearson chi-square goodness of fit of the user counts against 50/50 (1 df, no continuity correction).

    With 1 df the upper tail is erfc(sqrt(chi2 / 2)); scipy.stats.chisquare([n_a, n_b]).pvalue gives the same p to
    about 1e-14 relative.
    """
    n_a, n_b = int(n_a), int(n_b)
    e = (n_a + n_b) / 2
    chi2 = ((n_a - e) ** 2 + (n_b - e) ** 2) / e
    return math.erfc(math.sqrt(chi2 / 2))

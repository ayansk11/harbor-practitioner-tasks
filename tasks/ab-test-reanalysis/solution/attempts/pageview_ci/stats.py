"""Wrong attempt pageview_ci (must score 0): every count, the sample ratio check and the decision rule are the plan's
(the canonical files), but the interval is the two-proportion normal interval on pageviews, as if every counted
pageview were an independent trial, and it is labelled as the plan's delta method. The unit of randomization is the
user (EXPERIMENT.md section 5) and one user's pageviews are correlated, so this interval is narrower than the plan's
by about the square root of the design effect. Replaces abtest/stats.py after the canonical files."""
import math

from scipy.stats import norm

Z = float(norm.ppf(0.975))
SRM_ALPHA = 0.001
CI_METHOD = "delta method, users as the unit"   # the plan's label; the interval below is not that method


def diff_ci(arm_a, arm_b):
    """CTR_B - CTR_A and a 95% CI from the pageview-level standard error; arm_a, arm_b: per-user frames."""
    ca, va = float(arm_a["clicks"].sum()), float(arm_a["views"].sum())
    cb, vb = float(arm_b["clicks"].sum()), float(arm_b["views"].sum())
    pa, pb = ca / va, cb / vb
    se = math.sqrt(pa * (1 - pa) / va + pb * (1 - pb) / vb)
    diff = pb - pa
    return diff, (diff - Z * se, diff + Z * se)


def srm_pvalue(n_a, n_b):
    """Pearson chi-square goodness of fit against 50/50 (1 df, no continuity correction): erfc(sqrt(chi2 / 2)), as in
    the canonical stats.py."""
    n_a, n_b = int(n_a), int(n_b)
    e = (n_a + n_b) / 2
    chi2 = ((n_a - e) ** 2 + (n_b - e) ** 2) / e
    return math.erfc(math.sqrt(chi2 / 2))

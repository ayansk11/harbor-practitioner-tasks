"""Significance test for the CTR readout."""
import math
from dataclasses import dataclass

from scipy.stats import norm


@dataclass
class ZTest:
    diff: float
    ci_low: float
    ci_high: float
    z: float
    p_value: float


def ctr_ztest(clicks_a, views_a, clicks_b, views_b, alpha=0.05):
    """Two-proportion z-test of CTR B vs A, with each pageview as a trial."""
    pa = clicks_a / views_a
    pb = clicks_b / views_b
    pooled = (clicks_a + clicks_b) / (views_a + views_b)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / views_a + 1 / views_b))
    z = (pb - pa) / se_pooled
    p_value = 2 * norm.sf(abs(z))
    se = math.sqrt(pa * (1 - pa) / views_a + pb * (1 - pb) / views_b)
    crit = norm.ppf(1 - alpha / 2)
    diff = pb - pa
    return ZTest(diff, diff - crit * se, diff + crit * se, z, p_value)

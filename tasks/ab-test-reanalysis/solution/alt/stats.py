"""Statistics (alt solution): user-level bootstrap CI (EXPERIMENT.md 5b) and the SRM chi-square by hand."""
import numpy as np
from scipy.stats import chi2

RESAMPLES = 5000
SEED = 20260914
SRM_ALPHA = 0.001


def bootstrap_diff_ci(clicks_a, views_a, clicks_b, views_b, resamples=RESAMPLES, seed=SEED, chunk=250):
    """Percentile 95% CI of CTR_B - CTR_A; each replicate resamples users with replacement within each arm."""
    rng = np.random.default_rng(seed)
    reps = np.empty(resamples)
    na, nb = len(clicks_a), len(clicks_b)
    for start in range(0, resamples, chunk):
        k = min(chunk, resamples - start)
        ia = rng.integers(0, na, size=(k, na))
        ib = rng.integers(0, nb, size=(k, nb))
        reps[start:start + k] = clicks_b[ib].sum(axis=1) / views_b[ib].sum(axis=1) - \
            clicks_a[ia].sum(axis=1) / views_a[ia].sum(axis=1)
    lo, hi = np.percentile(reps, [2.5, 97.5])
    return float(lo), float(hi)


def srm_pvalue(n_a, n_b):
    expected = (n_a + n_b) / 2.0
    stat = ((n_a - expected) ** 2 + (n_b - expected) ** 2) / expected
    return float(chi2.sf(stat, df=1))

"""Statistics (alt_time solution): user-level bootstrap CI (EXPERIMENT.md section 5b) and the SRM chi-square."""
import numpy as np
from scipy.stats import chisquare

RESAMPLES = 5000
SEED = 20260914
CHUNK = 250          # resamples drawn at once: about 3 int32 arrays of CHUNK x users per arm in memory
SRM_ALPHA = 0.001
CI_METHOD = f"user-level bootstrap, {RESAMPLES} resamples within each arm, percentile"


def bootstrap_ci(clicks_a, views_a, clicks_b, views_b, resamples=RESAMPLES, seed=SEED, chunk=CHUNK):
    """Percentile 95% CI of CTR_B - CTR_A; each replicate resamples users with replacement within each arm."""
    ca, va = np.asarray(clicks_a, np.int32), np.asarray(views_a, np.int32)
    cb, vb = np.asarray(clicks_b, np.int32), np.asarray(views_b, np.int32)
    rng = np.random.default_rng(seed)
    reps = np.empty(resamples)
    for start in range(0, resamples, chunk):
        k = min(chunk, resamples - start)
        ia = rng.integers(0, len(ca), size=(k, len(ca)), dtype=np.int32)
        ib = rng.integers(0, len(cb), size=(k, len(cb)), dtype=np.int32)
        reps[start:start + k] = (cb[ib].sum(axis=1, dtype=np.int64) / vb[ib].sum(axis=1, dtype=np.int64)
                                 - ca[ia].sum(axis=1, dtype=np.int64) / va[ia].sum(axis=1, dtype=np.int64))
    lo, hi = np.percentile(reps, [2.5, 97.5])
    return float(lo), float(hi)


def srm_pvalue(n_a, n_b):
    return float(chisquare([n_a, n_b]).pvalue)

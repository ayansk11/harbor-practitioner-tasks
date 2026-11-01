"""Population (alt_recount solution): exclusions recounted from the events themselves.

Users the assignment service randomized (method = hash), minus users with a ua_crawler flag (a client rule), minus
users for whom the velocity rule fires when it is recounted on item: events only (docs/BOT_SCREENING.md: 8 or more
module_click events within 60 s, counted per UTC day by the nightly run, first run 2026-08-28 02:00 UTC over
2026-08-27). Arrow taps and "See all" open no product, so the recount leaves out the carousel users the platform's
velocity flags catch; only click-fraud traffic remains, which on these exports is already flagged ua_crawler, so the
population is the same as excluding by rule type.
"""
from datetime import datetime, timezone

import numpy as np

VEL_EVENTS = 8
VEL_WINDOW_S = 60
DAY_S = 86400
FIRST_DAY = int(datetime(2026, 8, 27, tzinfo=timezone.utc).timestamp()) // DAY_S


def recount_velocity(user_codes, times):
    """Codes of the users with VEL_EVENTS events within VEL_WINDOW_S seconds on one UTC day (from FIRST_DAY)."""
    u = np.asarray(user_codes, dtype=np.int64)
    t = np.asarray(times, dtype=float)
    if len(t) < VEL_EVENTS:
        return set()
    day = np.floor_divide(t, DAY_S).astype(np.int64)
    order = np.lexsort((t, day, u))
    u, day, t = u[order], day[order], t[order]
    i = np.arange(len(t) - VEL_EVENTS + 1)
    j = i + VEL_EVENTS - 1                     # 8 consecutive events of one user on one day: first i, last j
    fire = (u[i] == u[j]) & (day[i] == day[j]) & (t[j] - t[i] <= VEL_WINDOW_S) & (day[i] >= FIRST_DAY)
    return set(u[i[fire]].tolist())

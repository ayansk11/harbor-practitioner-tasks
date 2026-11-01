"""Generate the visible and hidden exports of the ab-test-reanalysis task (authoring time only; revision of 2026-10-30).

Run: submission/.venv/bin/python -I -B submission/authoring/ab-test-reanalysis/gen_data.py
       [--search-only] [--sets name,name] [--write-shipped-readout]

What it writes (into submission/tasks/ab-test-reanalysis/):
  environment/app/data/<file>.csv.gz      the visible export (EXP-2291; the agent sees it; dropped at grading)
  tests/hidden/<set>/<file>.csv.gz        five hidden exports of the same layout (h_null, h_pos, h_srm, h_plain, h_neg)
  tests/expected/<set>.json               the reference readout of each export, from ref_a.py (stdlib, rule route)
  tests/SHA256SUMS                        hashes of every hidden input and expected file
  <file> = assignments, bot_flags, pageviews, module_clicks; gzip level 9, mtime 0, no file name (byte-stable).
and, next to this script, generation_report.out.md and generation_report.json (seeds, conditions, margins, the
paths table, row counts, sizes; no clock times, so both are byte-identical on a rerun).
--write-shipped-readout also runs the shipped code (environment/app/abtest) on the visible export to write
environment/app/output/result.json; it is off by default because the shipped code is written by another step.

How a set is made (synthetic; nothing here comes from a real product). The window is 2026-09-01 00:00Z to
2026-09-15 00:00Z for every set.
  - Hash users are randomized to A or B with probability p_b; a share is crawler traffic (ua_crawler), a smaller
    share of it click-fraud bots. Override accounts (dogfood or QA; arm, size and behaviour per set) get their arm by
    hand (assignments.method = override); they are never bots, have one assignment row and no flag.
  - Each human has an item-click propensity p ~ Beta (mean ctr, intra-user correlation rho); the treatment arm B
    multiplies it by (1 + lift). Post-assignment pageviews: a floored, zero-inflated lognormal (heavy tail); some
    users also have pageviews 300 s to 3 days before assigned_at (the module shows v1 there); many users have their
    first counted pageview exactly at assigned_at; some assignment rows of hash users repeat exactly.
  - Module events (module_clicks): 0 to 2 item:<product> events per pageview (the second with p 0.05, 15 to 60 s
    after the first); a rare "See all" (link:all) in every module version from 2026-09-08; in the carousel arm (v2,
    per set) humans use the carousel Poisson(lam sqrt(p0/ctr)) times, each use 6 + Poisson(4) nav:next / nav:prev
    taps 0.5 to 3 s apart on an isolated pageview (no other pageview of the user within 600 s, the burst well
    inside one UTC day); the item and link events of such a pageview follow the taps (1 to 4 s apart; 100 to 200 s
    after a use of fewer than 8 taps, so 7 taps never trip the velocity rule). Click-fraud bots make bursts of
    10 + Poisson(4) pageviews 2 to 4 s apart, each with one item click.
  - pageviews.clicked = 1 if at least one module event was logged on the pageview (any target).
  - bot_flags: one ua_crawler row per crawler, flagged at its first request, 1 to 1800 s before the earlier of its
    first logged pageview and assigned_at (the first request need not be a product pageview of the export); one
    velocity row per user and UTC day D on which the documented rule fires on module_clicks (8 or more events of any
    target within 60 s), flagged at 02:00:00Z on D + 1 (the nightly run; first run 2026-08-28).
  - Every timestamp is ISO 8601 with Z or a +hh:mm / -hh:mm offset, drawn per row (same instant, different text).
Assertions: data_checks.py (a) to (n) on the written files, plus ref_a = ref_b and generator = ref_a; any failure
stops generation. Seed search: for each set, seeds base, base + 1, ... are tried in order and the first whose arrays
meet every hard condition (CONDITIONS in conditions()) is kept; for the visible set the soft condition (the readout
that keeps the override accounts ships) is kept only if at least 3 of the first 300 seeds meet hard and soft
conditions, else it is relaxed (docs/ab-test-reanalysis/DESIGN.md, the approved design's seed conditions).
"""
import argparse, gzip, hashlib, io, json, math, os, subprocess, sys, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
APP = os.path.join(TASK, "environment", "app")
TESTS = os.path.join(TASK, "tests")
sys.path.insert(0, HERE)
import data_checks  # noqa: E402
import ref_a  # noqa: E402
import ref_b  # noqa: E402

T0 = np.datetime64("2026-09-01T00:00:00", "s")     # window start, UTC (all sets)
DAY = 86400
SPAN = 14 * DAY                                     # window end 2026-09-15 00:00Z
SEE_ALL_FROM = 7 * DAY                              # 2026-09-08 00:00Z: "See all" in every module version
VEL_N, VEL_WIN, VEL_RUN = 8, 60, 2 * 3600          # velocity: 8 or more events within 60 s; nightly at 02:00Z
VEL_FIRST_DAY = -5                                  # first nightly run 2026-08-28 02:00Z covers 2026-08-27
ISO = 600                                           # isolation of a carousel pageview (s)
P2ND = 0.05                                         # second item event on an item-clicked pageview
Z975 = 1.959963984540054
FILES = ("assignments.csv", "bot_flags.csv", "pageviews.csv", "module_clicks.csv")
CAPS = dict(users=50_000, pageviews=500_000, clicks=100_000)     # the instruction's per-export limits
FLOOR = 20                                          # min rows per arm that make the attempts fail (see conditions)

MARGIN = 0.5                    # reference decision bound at least this many half-widths from 0
SRM_OK_MIN = 0.05               # sets without SRM: reference SRM p at least this
SRM_FLAG_RANGE = (1e-11, 1e-5)  # h_srm: flagged, and above 1e-12 so the 1%-relative comparison applies
SHIPPED_SRM_MAX = 1e-5          # visible: the shipped readout's SRM p below this
H2_MARGIN = 0.5                 # visible: the filter-only readout ships with lower bound >= this (own half-widths)
DASH_LIFT = (0.07, 0.13)        # visible: the team dashboard's relative lift
KEEP_SRM_MIN, KEEP_MARGIN = 0.005, 0.35   # h_srm: the keep-overrides readout hides the SRM and ships
ALL_ASSIGNED_MIN_REL = 0.03     # (m): SRM on all assigned users misses the reference srm_p by at least 3% relative
DE_MIN = 5.5                    # (n)
SOFT_SCAN, SOFT_MIN_PASS = 300, 3

TZ_COMMON = [("Z", 0, 0.66), ("+00:00", 0, 0.04), ("+01:00", 60, 0.06), ("+02:00", 120, 0.04), ("+05:30", 330, 0.05),
             ("-04:00", -240, 0.09), ("-05:00", -300, 0.03), ("-07:00", -420, 0.03)]
TZ_WIDE = [("Z", 0, 0.34), ("+00:00", 0, 0.06), ("+01:00", 60, 0.06), ("+05:30", 330, 0.10), ("+05:45", 345, 0.05),
           ("+09:00", 540, 0.08), ("+13:00", 780, 0.03), ("-03:30", -210, 0.06), ("-04:00", -240, 0.10),
           ("-07:00", -420, 0.07), ("-10:00", -600, 0.05)]

# role: "null" -> reference no_ship with lower bound <= -MARGIN hw; "pos" -> ship with lower >= +MARGIN hw;
#       "srm" -> SRM flagged (invalid) while the CI alone would ship (lower >= +MARGIN hw).
# carousel: the arm whose module is v2 (arrows), or None. ovr: the override cohort or None.
# literal_invalid: the literal bot filter (every flagged user out) must give "invalid" (section 5, TARGET).
COMMON = dict(p_b=0.5, fraud=0.0006, bot_pv=22, zero=0.08, pre=0.20, tie=0.6, dup=0.010, see_all=0.004, tz=TZ_COMMON,
              de=(DE_MIN, 1e9), literal_invalid=True, ovr=None)
SETS = [
    dict(COMMON, name="visible", role="null", seed=1000, n_users=34000, crawl=0.020, pv_mean=11.5, sigma=1.0,
         ctr=0.100, rho=0.20, lift=0.0, carousel="B", lam=0.11, versions={"A": "v1", "B": "v2"},
         ovr=dict(kind="dogfood", n=100, arm="B", start=2 * DAY, pv_mean=40.0, sigma=0.35, pv_min=10, ctr=0.36,
                  rho=0.08)),
    dict(COMMON, name="h_null", role="null", seed=2000, n_users=32000, crawl=0.015, pv_mean=9.0, sigma=1.3,
         ctr=0.110, rho=0.42, lift=0.0, carousel="A", lam=0.13, de=(18.0, 25.0), versions={"A": "v2", "B": "grid"},
         ovr=dict(kind="qa", n=150, arm="A", start=0, pv_mean=12.0, sigma=0.5, pv_min=3, ctr=0.010, rho=0.05)),
    dict(COMMON, name="h_pos", role="pos", seed=3000, n_users=32000, crawl=0.015, pv_mean=11.0, sigma=1.0,
         ctr=0.120, rho=0.20, lift=0.10, carousel="B", lam=0.10, versions={"A": "v1", "B": "v2"}),
    dict(COMMON, name="h_srm", role="srm", seed=4000, n_users=34000, p_b=0.486, crawl=0.015, pv_mean=11.0, sigma=1.0,
         ctr=0.100, rho=0.20, lift=0.13, carousel="B", lam=0.10, literal_invalid=False,
         versions={"A": "v1", "B": "v2"},
         ovr=dict(kind="qa", n=500, arm="B", start=0, pv_mean=12.0, sigma=0.5, pv_min=3, ctr=0.020, rho=0.05)),
    dict(COMMON, name="h_plain", role="pos", seed=5000, n_users=30000, crawl=0.050, pv_mean=9.0, sigma=1.1,
         ctr=0.090, rho=0.20, lift=0.13, carousel=None, lam=0.0, tz=TZ_WIDE, literal_invalid=False,
         versions={"A": "v1", "B": "v1 with another ranking (no arrows)"}),
    dict(COMMON, name="h_neg", role="null", seed=6000, n_users=34000, crawl=0.020, pv_mean=11.0, sigma=1.0,
         ctr=0.100, rho=0.20, lift=-0.10, carousel="B", lam=0.22, versions={"A": "v1", "B": "v2"}),
]
SET_NAMES = [c["name"] for c in SETS]


def lognormal_counts(rng, n, mean, sigma, cap=600):
    m = math.log(mean) - sigma * sigma / 2
    return np.minimum(np.floor(rng.lognormal(m, sigma, n)), cap).astype(np.int64)


def group_starts(sorted_keys):
    """Index of the first element of each element's run in a sorted key array."""
    n = len(sorted_keys)
    if n == 0:
        return np.zeros(0, np.int64)
    new = np.r_[True, sorted_keys[1:] != sorted_keys[:-1]]
    return np.maximum.accumulate(np.where(new, np.arange(n), 0))


def windows(user, t, k):
    """Per user, events sorted by (user, t): spans of each run of k consecutive events of one user.
    Returns (first index, span, same UTC day) for windows inside one user."""
    o = np.lexsort((t, user))
    u, tt = user[o], t[o]
    if len(tt) < k:
        return o, np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0, bool)
    i = np.arange(len(tt) - (k - 1))
    j = i + k - 1
    same = u[j] == u[i]
    i, j = i[same], j[same]
    span = tt[j] - tt[i]
    sameday = np.floor_divide(tt[j], DAY) == np.floor_divide(tt[i], DAY)
    return o, i, span, sameday


def velocity_pairs(user, t):
    """The documented velocity rule on module events: (user, UTC day) pairs with 8 or more events within 60 s on
    that day (the nightly run of day + 1 covers day). Returns an array of shape (k, 2)."""
    o, i, span, sameday = windows(user, t, VEL_N)
    fire = (span <= VEL_WIN) & sameday
    fu = user[o][i][fire]
    fd = np.floor_divide(t[o][i][fire], DAY)
    keep = fd >= VEL_FIRST_DAY
    if not keep.any():
        return np.zeros((0, 2), np.int64)
    return np.unique(np.stack([fu[keep], fd[keep]], 1), axis=0)


def simulate(cfg, seed):
    """Numbers only (no text): users, pageviews, module events and flags as arrays."""
    rng = np.random.default_rng(seed)
    n = cfg["n_users"]
    ovr = cfg["ovr"]
    no = ovr["n"] if ovr else 0
    N = n + no
    ids = rng.choice(np.arange(1_000_000, 10_000_000), size=N, replace=False)
    is_hash = np.r_[np.ones(n, bool), np.zeros(no, bool)]
    arm = np.zeros(N, np.int8)
    arm[:n] = rng.random(n) < cfg["p_b"]
    if no:
        arm[n:] = 1 if ovr["arm"] == "B" else 0
    crawler = np.r_[rng.random(n) < cfg["crawl"], np.zeros(no, bool)]
    fraud = np.r_[rng.random(n) < cfg["fraud"], np.zeros(no, bool)]
    crawler |= fraud
    assigned = np.zeros(N, np.int64)
    assigned[:n] = np.floor(rng.beta(1.0, 2.5, n) * (SPAN - 6 * 3600))
    if no:
        st = ovr["start"]
        assigned[n:] = st + np.floor(rng.beta(1.0, 2.0, no) * (SPAN - st - 6 * 3600))
    k = 1.0 / cfg["rho"] - 1.0
    p0 = rng.beta(cfg["ctr"] * k, (1 - cfg["ctr"]) * k, N)
    if no:
        ko = 1.0 / ovr["rho"] - 1.0
        p0[n:] = rng.beta(ovr["ctr"] * ko, (1 - ovr["ctr"]) * ko, no)
    p = p0.copy()
    treat = is_hash & (arm == 1)
    p[treat] = np.minimum(p0[treat] * (1 + cfg["lift"]), 0.95)
    p[crawler] = 0.003
    npost = lognormal_counts(rng, N, cfg["pv_mean"], cfg["sigma"])
    npost[rng.random(N) < cfg["zero"]] = 0
    nbot = np.maximum(lognormal_counts(rng, N, cfg["bot_pv"], 0.6), 3)
    npost = np.where(crawler, nbot, npost)
    if no:
        npost[n:] = np.maximum(lognormal_counts(rng, no, ovr["pv_mean"], ovr["sigma"]), ovr["pv_min"])
    npre = np.where(rng.random(N) < cfg["pre"], 1 + rng.poisson(0.8, N), 0)
    dup = is_hash & (rng.random(N) < cfg["dup"])
    # regular pageviews: post (optional tie at assigned_at, the rest strictly after) and pre (300 s to 3 days before)
    u_post = np.repeat(np.arange(N), npost)
    first = np.r_[True, u_post[1:] != u_post[:-1]] if len(u_post) else np.zeros(0, bool)
    tie_user = rng.random(N) < cfg["tie"]
    room = SPAN - assigned[u_post]
    t_post = assigned[u_post] + 1 + np.floor(rng.random(len(u_post)) * (room - 1)).astype(np.int64)
    t_post = np.where(first & tie_user[u_post], assigned[u_post], t_post)
    u_pre = np.repeat(np.arange(N), npre)
    t_pre = assigned[u_pre] - (300 + np.floor(rng.random(len(u_pre)) * (3 * DAY)).astype(np.int64))
    pv_user = np.r_[u_post, u_pre]
    pv_t = np.r_[t_post, t_pre]
    pv_post = np.r_[np.ones(len(u_post), bool), np.zeros(len(u_pre), bool)]
    P = len(pv_user)
    has1 = rng.random(P) < p[pv_user]
    has2 = has1 & (rng.random(P) < P2ND)
    sa = (~crawler[pv_user]) & (pv_t >= SEE_ALL_FROM) & (rng.random(P) < cfg["see_all"])
    # carousel uses on isolated post-assignment pageviews of carousel-arm humans
    car_code = {"A": 0, "B": 1}.get(cfg["carousel"], -1)
    car_user = is_hash & ~crawler & (arm == car_code)
    uses = np.zeros(N, np.int64)
    if car_code >= 0:
        uses[car_user] = rng.poisson(cfg["lam"] * np.sqrt(p0[car_user] / cfg["ctr"]))
    o = np.lexsort((pv_t, pv_user))
    us, ts = pv_user[o], pv_t[o]
    same_prev = np.r_[False, us[1:] == us[:-1]]
    gap_prev = np.where(same_prev, ts - np.r_[ts[:1], ts[:-1]], 10 * DAY)
    same_next = np.r_[us[1:] == us[:-1], False]
    gap_next = np.where(same_next, np.r_[ts[1:], ts[-1:]] - ts, 10 * DAY)
    sod = np.mod(ts, DAY)
    elig = (pv_post[o] & (gap_prev > ISO) & (gap_next > ISO) & (sod <= DAY - 300) & (ts + 300 < SPAN)
            & (uses[us] > 0))
    key = rng.random(P)
    idx = np.nonzero(elig)[0]
    sel = np.zeros(P, bool)
    if len(idx):
        o2 = np.lexsort((key[idx], us[idx]))
        sidx = idx[o2]
        rank = np.arange(len(sidx)) - group_starts(us[sidx])
        sel[o[sidx[rank < uses[us[sidx]]]]] = True
    car_pv = np.nonzero(sel)[0]                        # indices into the regular pageviews
    # nav taps
    n_taps = 6 + rng.poisson(4, len(car_pv))
    tap_pv = np.repeat(car_pv, n_taps)
    offs = rng.uniform(0.5, 3.0, len(tap_pv))
    gstart = np.r_[0, np.cumsum(n_taps)[:-1]] if len(car_pv) else np.zeros(0, np.int64)
    offs[gstart] = 0.0
    cs = np.cumsum(offs)
    within = cs - np.repeat(cs[gstart], n_taps) if len(car_pv) else cs
    lead = rng.uniform(2.0, 15.0, len(car_pv))
    tap_tf = pv_t[tap_pv] + np.repeat(lead, n_taps) + within
    tap_next = rng.random(len(tap_pv)) < 0.8
    last_tap = tap_tf[gstart + n_taps - 1] if len(car_pv) else np.zeros(0)
    # event times of the non-nav events of every regular pageview
    c1 = pv_t + rng.uniform(3.0, 90.0, P)
    c2 = c1 + rng.uniform(15.0, 60.0, P)
    sat = pv_t + rng.uniform(3.0, 90.0, P)
    if len(car_pv):
        g1 = rng.uniform(1.0, 4.0, len(car_pv))
        g2 = rng.uniform(1.0, 4.0, len(car_pv))
        g3 = rng.uniform(1.0, 4.0, len(car_pv))
        late = np.where(n_taps >= VEL_N, 0.0, rng.uniform(99.0, 196.0, len(car_pv)))
        e1 = last_tap + late + g1
        e2 = e1 + g2
        e3 = e2 + g3
        c1[car_pv] = e1
        c2[car_pv] = e2
        sat[car_pv] = np.where(has1[car_pv], e3, e1)
    prod1 = rng.integers(10000, 100000, P)
    prod2 = 10000 + (prod1 - 10000 + rng.integers(1, 89999, P)) % 90000
    # click-fraud bursts (crawlers): extra post pageviews, each with one item event
    fb_user, fb_tf, fb_ct = [], [], []
    regular_by_user = None
    for i in np.nonzero(fraud)[0]:
        if regular_by_user is None:
            ord_u = np.lexsort((pv_t, pv_user))
            regular_by_user = (pv_user[ord_u], pv_t[ord_u])
        lo_i = np.searchsorted(regular_by_user[0], i, "left")
        hi_i = np.searchsorted(regular_by_user[0], i, "right")
        mine = list(regular_by_user[1][lo_i:hi_i])
        nb = 1 + min(int(rng.poisson(0.7)), 2)
        a0, a1 = int(assigned[i]) + 900, SPAN - 900
        for _b in range(nb):
            if a1 <= a0:
                break
            start = None
            for _try in range(200):
                s0 = int(rng.integers(a0, a1))
                if not 900 <= s0 % DAY <= DAY - 900:
                    continue
                if mine and min(abs(s0 - x) for x in mine) <= 900:
                    continue
                start = s0
                break
            if start is None:
                continue
            nbp = 10 + int(rng.poisson(4))
            gaps = np.r_[0.0, rng.uniform(2.0, 4.0, nbp - 1)]
            ptf = start + np.cumsum(gaps)
            ctf = ptf + rng.uniform(0.5, 1.5, nbp)
            fb_user.append(np.full(nbp, i))
            fb_tf.append(ptf)
            fb_ct.append(ctf)
            mine += list(np.floor(ptf).astype(np.int64))
    if fb_user:
        fb_user = np.concatenate(fb_user)
        fb_t = np.floor(np.concatenate(fb_tf)).astype(np.int64)
        fb_ct = np.floor(np.concatenate(fb_ct)).astype(np.int64)
    else:
        fb_user, fb_t, fb_ct = np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0, np.int64)
    fb_prod = rng.integers(10000, 100000, len(fb_user))
    F = len(fb_user)
    # all pageviews: regular then fraud-burst rows
    all_user = np.r_[pv_user, fb_user]
    all_t = np.r_[pv_t, fb_t]
    all_post = np.r_[pv_post, np.ones(F, bool)]
    # module events: (pageview index, time, kind, product); kind 0 item, 1 nav:next, 2 nav:prev, 3 link:all
    e_pv = np.r_[np.nonzero(has1)[0], np.nonzero(has2)[0], tap_pv, np.nonzero(sa)[0], P + np.arange(F)]
    e_t = np.floor(np.r_[c1[has1], c2[has2], tap_tf, sat[sa], fb_ct]).astype(np.int64)
    e_kind = np.r_[np.zeros(int(has1.sum()) + int(has2.sum()), np.int8), np.where(tap_next, 1, 2).astype(np.int8),
                   np.full(int(sa.sum()), 3, np.int8), np.zeros(F, np.int8)]
    e_prod = np.r_[prod1[has1], prod2[has2], np.zeros(len(tap_pv) + int(sa.sum()), np.int64), fb_prod]
    e_user = all_user[e_pv]
    # flags of each pageview
    item_pv = np.r_[has1, np.ones(F, bool)]
    any_pv = np.zeros(P + F, bool)
    any_pv[e_pv] = True
    nav_pv = np.zeros(P + F, bool)
    nav_pv[tap_pv] = True
    link_pv = np.r_[sa, np.zeros(F, bool)]
    two_pv = np.r_[has2, np.zeros(F, bool)]
    # bot flags
    first_t = assigned.copy()
    np.minimum.at(first_t, all_user, all_t)
    crawl_flag_t = first_t - (1 + np.floor(rng.random(N) * 1800).astype(np.int64))
    vpairs = velocity_pairs(e_user, e_t)
    vel = np.zeros(N, bool)
    if len(vpairs):
        vel[vpairs[:, 0]] = True
    pv_id0 = int(rng.integers(36 ** 5, 36 ** 6 - 2_000_000))
    return dict(rng=rng, N=N, n_hash=n, ids=ids, is_hash=is_hash, arm=arm, crawler=crawler, fraud=fraud,
                assigned=assigned, dup=dup, uses=uses, car_user=car_user,
                pv_user=all_user, pv_t=all_t, pv_post=all_post, item_pv=item_pv, any_pv=any_pv, nav_pv=nav_pv,
                link_pv=link_pv, two_pv=two_pv, n_regular=P,
                e_pv=e_pv, e_t=e_t, e_kind=e_kind, e_prod=e_prod, e_user=e_user,
                crawl_flag_t=crawl_flag_t, vpairs=vpairs, vel=vel, pv_id0=pv_id0)


def arm_readout(mask, arm, clicks, views):
    """The plan's readout on per-user arrays: delta method on per-user sums, SRM chi-square, the decision."""
    out = {"n_users": {}, "pageviews": {}, "clicks": {}, "ctr": {}}
    var = {}
    for a, code in (("A", 0), ("B", 1)):
        m = mask & (arm == code)
        c = clicks[m].astype(float)
        v = views[m].astype(float)
        N = int(m.sum())
        C, V = float(c.sum()), float(v.sum())
        R = C / V
        var[a] = N / (N - 1) * float(((c - R * v) ** 2).sum()) / V ** 2
        out["n_users"][a], out["pageviews"][a], out["clicks"][a], out["ctr"][a] = N, int(V), int(C), R
    Ra, Rb = out["ctr"]["A"], out["ctr"]["B"]
    diff = Rb - Ra
    hw = Z975 * math.sqrt(var["A"] + var["B"])
    na, nb = out["n_users"]["A"], out["n_users"]["B"]
    e = (na + nb) / 2
    chi2 = ((na - e) ** 2 + (nb - e) ** 2) / e
    srm_p = math.erfc(math.sqrt(chi2 / 2))
    lo, hi = diff - hw, diff + hw
    naive = math.sqrt(Ra * (1 - Ra) / out["pageviews"]["A"] + Rb * (1 - Rb) / out["pageviews"]["B"])
    decision = "invalid" if srm_p < 0.001 else ("ship" if lo > 0 else "no_ship")
    out.update(diff=diff, half_width=hw, ci_95=[lo, hi], srm_p=srm_p, decision=decision, lo_hw=lo / hw,
               hi_hw=hi / hw, de=(var["A"] + var["B"]) / naive ** 2, rel_lift=Rb / Ra - 1)
    return out


def srm_of(mask, arm):
    na, nb = int((mask & (arm == 0)).sum()), int((mask & (arm == 1)).sum())
    e = (na + nb) / 2
    return na, nb, math.erfc(math.sqrt((((na - e) ** 2 + (nb - e) ** 2) / e) / 2))


def paths(s):
    """Per-user sums over counted (post-assignment) pageviews and the readout of every analysis path."""
    N = s["N"]
    post = s["pv_post"]
    u = s["pv_user"][post]
    V = np.bincount(u, minlength=N)
    C_item = np.bincount(u, weights=s["item_pv"][post], minlength=N)
    C_any = np.bincount(u, weights=s["any_pv"][post], minlength=N)
    arm = s["arm"]
    allu = np.ones(N, bool)
    ref = s["is_hash"] & ~s["crawler"]
    R = {
        "reference": arm_readout(ref, arm, C_item, V),
        "shipped": arm_readout(~s["crawler"] & ~s["vel"], arm, C_any, V),
        "filter_only": arm_readout(~s["crawler"], arm, C_any, V),
        "keep_overrides": arm_readout(~s["crawler"], arm, C_item, V),
        "dashboard": arm_readout(allu, arm, C_any, V),
        "literal_bot_filter": arm_readout(ref & ~s["vel"], arm, C_item, V),
        "platform_clicked": arm_readout(ref, arm, C_any, V),
    }
    na, nb, p_all = srm_of(allu, arm)
    R["all_assigned"] = dict(n_users={"A": na, "B": nb}, srm_p=p_all)
    return R


def construction(cfg, s):
    """Array-level versions of the construction assertions (data_checks.py re-checks them on the files)."""
    bad = []
    N, arm = s["N"], s["arm"]
    if N > CAPS["users"] or len(s["pv_user"]) > CAPS["pageviews"] or len(s["e_t"]) > CAPS["clicks"]:
        bad.append(f"caps: users {N}, pageviews {len(s['pv_user'])}, clicks {len(s['e_t'])}")
    # (f) every run of 8 consecutive events of a user spans < 40 s on one UTC day, or > 90 s
    _o, _i, span, sameday = windows(s["e_user"], s["e_t"], VEL_N)
    nf = int((((span >= 40) & (span <= 90)) | ((span < 40) & ~sameday)).sum())
    if nf:
        bad.append(f"(f) {nf} ambiguous 8-event windows")
    # (d) no non-crawler has 5 item events within 60 s
    it = (s["e_kind"] == 0) & ~s["crawler"][s["e_user"]]
    _o, _i, span5, _sd = windows(s["e_user"][it], s["e_t"][it], 5)
    nd = int((span5 <= 60).sum())
    if nd:
        bad.append(f"(d) {nd} windows of 5 item events within 60 s (non-crawlers)")
    # (c) velocity-only users: carousel-arm hash humans with 8 or more nav taps on each flagged day
    vp = s["vpairs"]
    if len(vp):
        human = ~s["crawler"][vp[:, 0]]
        hv = vp[human]
        if not (s["car_user"][hv[:, 0]]).all():
            bad.append("(c) a velocity-only user is not a carousel-arm human")
        nav = s["e_kind"] > 0
        nav &= s["e_kind"] < 3
        key_e = s["e_user"][nav] * 1000 + np.floor_divide(s["e_t"][nav], DAY) + 100
        cnt = dict(zip(*np.unique(key_e, return_counts=True)))
        short = [tuple(x) for x in hv if cnt.get(int(x[0]) * 1000 + int(x[1]) + 100, 0) < VEL_N]
        if short:
            bad.append(f"(c) {len(short)} velocity-only user-days with fewer than 8 nav taps")
    # floors: rows that make attempts fail, among reference users, per arm
    ref = s["is_hash"] & ~s["crawler"]
    pu = s["pv_user"]
    cnt_ref = ref[pu]
    for label, m in (("see-all-only counted pageviews", s["pv_post"] & s["link_pv"] & ~s["item_pv"]),
                     ("counted pageviews with two item events", s["pv_post"] & s["two_pv"]),
                     ("pre-assignment item-clicked pageviews", ~s["pv_post"] & s["item_pv"])):
        for a, code in (("A", 0), ("B", 1)):
            k = int((m & cnt_ref & (arm[pu] == code)).sum())
            if k < FLOOR:
                bad.append(f"floor: {label} in {a} = {k} < {FLOOR}")
    return bad


def conditions(cfg, R, s):
    """Hard and soft seed conditions on the realised arrays (the approved design's seed conditions, plus the targets
    of its paths and hidden-set tables that define what each set stops; docs/ab-test-reanalysis/DESIGN.md).
    Returns (hard failures, soft failures)."""
    bad, soft = [], []
    ref = R["reference"]
    lo_de, hi_de = cfg["de"]
    if not (lo_de <= ref["de"] <= hi_de):
        bad.append(f"DE {ref['de']:.2f} not in {cfg['de']}")
    if ref["de"] < DE_MIN:
        bad.append(f"(n) DE {ref['de']:.2f} < {DE_MIN}")
    m = ref["lo_hw"]
    if cfg["role"] == "null" and not m <= -MARGIN:
        bad.append(f"reference lower/hw {m:+.2f} > -{MARGIN}")
    if cfg["role"] in ("pos", "srm") and not m >= MARGIN:
        bad.append(f"reference lower/hw {m:+.2f} < {MARGIN}")
    if cfg["role"] == "srm":
        if not SRM_FLAG_RANGE[0] < ref["srm_p"] < SRM_FLAG_RANGE[1]:
            bad.append(f"reference srm_p {ref['srm_p']:.3g} outside {SRM_FLAG_RANGE}")
        k = R["keep_overrides"]
        if not k["srm_p"] >= KEEP_SRM_MIN:
            bad.append(f"keep_overrides srm_p {k['srm_p']:.3g} < {KEEP_SRM_MIN}")
        if not k["lo_hw"] >= KEEP_MARGIN:
            bad.append(f"keep_overrides lower/hw {k['lo_hw']:+.2f} < {KEEP_MARGIN}")
    elif ref["srm_p"] < SRM_OK_MIN:
        bad.append(f"reference srm_p {ref['srm_p']:.3g} < {SRM_OK_MIN}")
    rel = abs(R["all_assigned"]["srm_p"] - ref["srm_p"]) / ref["srm_p"]
    if rel < ALL_ASSIGNED_MIN_REL:
        bad.append(f"(m) srm_all_assigned relative miss {rel:.4f} < {ALL_ASSIGNED_MIN_REL}")
    if cfg["literal_invalid"] and not R["literal_bot_filter"]["srm_p"] < 0.001:
        bad.append(f"literal filter srm_p {R['literal_bot_filter']['srm_p']:.3g} not flagged")
    if cfg["name"] == "visible":
        if not R["shipped"]["srm_p"] < SHIPPED_SRM_MAX:
            bad.append(f"shipped srm_p {R['shipped']['srm_p']:.3g} >= {SHIPPED_SRM_MAX}")
        f = R["filter_only"]
        if not (f["decision"] == "ship" and f["lo_hw"] >= H2_MARGIN):
            bad.append(f"filter-only {f['decision']} lower/hw {f['lo_hw']:+.2f}")
        lift = R["dashboard"]["rel_lift"]
        if not DASH_LIFT[0] <= lift <= DASH_LIFT[1]:
            bad.append(f"dashboard lift {lift:+.4f} outside {DASH_LIFT}")
        if R["keep_overrides"]["decision"] != "ship":
            soft.append(f"keep_overrides {R['keep_overrides']['decision']} (lower/hw "
                        f"{R['keep_overrides']['lo_hw']:+.2f})")
    if cfg["name"] == "h_neg":
        if not (R["platform_clicked"]["diff"] > 0 > ref["diff"]):
            bad.append(f"h_neg: platform diff {R['platform_clicked']['diff']:+.5f}, item diff {ref['diff']:+.5f}")
    bad += construction(cfg, s)
    return bad, soft


def search(cfg, max_tries=3000, log=None):
    """First seed from the base that meets every hard condition (and, for the visible set, the soft one unless it
    is relaxed under the rule above). Returns (seed, tries, s, R, info)."""
    soft_rule = cfg["name"] == "visible"
    info = dict(soft_rule=soft_rule, soft_kept=None, soft_passes_in_scan=None, scanned=0, construction_rejects=0)
    passes = []                     # seeds meeting hard + soft (visible only)
    first_hard = None
    for i in range(max_tries):
        seed = cfg["seed"] + i
        s = simulate(cfg, seed)
        R = paths(s)
        bad, soft = conditions(cfg, R, s)
        info["scanned"] = i + 1
        if any(b.startswith(("(c)", "(d)", "(f)", "caps", "floor")) for b in bad):
            info["construction_rejects"] += 1
        if log is not None:
            log.append((seed, bad, soft))
        if bad:
            continue
        if not soft_rule:
            return seed, i + 1, s, R, info
        if first_hard is None:
            first_hard = (seed, i + 1, s, R)
        if not soft:
            passes.append((seed, i + 1, s, R))
            if len(passes) >= SOFT_MIN_PASS:
                break
        if i + 1 >= SOFT_SCAN and first_hard is not None:
            break
    if not soft_rule:
        raise SystemExit(f"{cfg['name']}: no seed in {max_tries} tries met the conditions")
    info["soft_passes_in_scan"] = len(passes)
    if len(passes) >= SOFT_MIN_PASS:
        info["soft_kept"] = True
        seed, tries, s, R = passes[0]
        return seed, tries, s, R, info
    if first_hard is None:
        raise SystemExit(f"{cfg['name']}: no seed in {info['scanned']} tries met the hard conditions")
    info["soft_kept"] = False
    seed, tries, s, R = first_hard
    return seed, tries, s, R, info


# ---------------------------------------------------------------------------------------------------- text


def fmt_times(secs, rng, tz):
    """Seconds since T0 (UTC) -> ISO 8601 strings, each with a randomly drawn suffix from tz (same instant)."""
    names = np.array([t[0] for t in tz])
    mins = np.array([t[1] for t in tz], dtype=np.int64)
    probs = np.array([t[2] for t in tz], dtype=float)
    k = rng.choice(len(tz), size=len(secs), p=probs / probs.sum())
    local = T0 + (np.asarray(secs, np.int64) + mins[k] * 60).astype("timedelta64[s]")
    base = np.datetime_as_string(local, unit="s")
    return np.char.add(base.astype("U19"), names[k])


B36 = np.array(list("0123456789abcdefghijklmnopqrstuvwxyz"))


def base36(x, width=6):
    x = np.asarray(x, np.int64)
    cols = [B36[(x // 36 ** k) % 36] for k in range(width - 1, -1, -1)]
    out = cols[0].astype("U%d" % width)
    for c in cols[1:]:
        out = np.char.add(out, c)
    return out


def join_cols(cols):
    out = cols[0]
    for c in cols[1:]:
        out = np.char.add(np.char.add(out, ","), c)
    return out


def build_text(cfg, s):
    rng = s["rng"]     # the kept seed's generator, continued: text formatting is part of the same fixed stream
    uid = np.char.add("u", s["ids"].astype("U7"))
    # assignments: one row per user (plus exact repeats of hash rows right after the original), by instant
    a_txt = fmt_times(s["assigned"], rng, cfg["tz"])
    order = np.argsort(s["assigned"], kind="stable")
    variant = np.where(s["arm"] == 1, "B", "A")
    method = np.where(s["is_hash"], "hash", "override")
    rows = join_cols([uid, variant, a_txt, method])
    reps = np.where(s["dup"][order], 2, 1)
    assignments = "user_id,variant,assigned_at,method\n" + "\n".join(np.repeat(rows[order], reps).tolist()) + "\n"
    # pageviews: by instant (ties keep generation order); pageview_id = a base-36 counter in that order
    po = np.argsort(s["pv_t"], kind="stable")
    pid_of = np.empty(len(po), np.int64)
    pid_of[po] = s["pv_id0"] + np.arange(len(po))
    pid_txt = base36(pid_of)
    t_txt = fmt_times(s["pv_t"][po], rng, cfg["tz"])
    lines = join_cols([pid_txt[po], uid[s["pv_user"][po]], t_txt, s["any_pv"][po].astype(np.int8).astype("U1")])
    pageviews = "pageview_id,user_id,ts,clicked\n" + "\n".join(lines.tolist()) + "\n"
    # module_clicks: by instant (ties keep generation order)
    eo = np.argsort(s["e_t"], kind="stable")
    tgt = np.where(s["e_kind"] == 1, "nav:next", np.where(s["e_kind"] == 2, "nav:prev", "link:all")).astype("U11")
    tgt = np.where(s["e_kind"] == 0, np.char.add("item:", s["e_prod"].astype("U5")), tgt)
    e_txt = fmt_times(s["e_t"][eo], rng, cfg["tz"])
    lines = join_cols([pid_txt[s["e_pv"][eo]], uid[s["e_user"][eo]], e_txt, tgt[eo]])
    clicks = "pageview_id,user_id,ts,target\n" + "\n".join(lines.tolist()) + "\n"
    # bot_flags: one ua_crawler row per crawler, one velocity row per flagged user-day, by instant
    cu = np.nonzero(s["crawler"])[0]
    vp = s["vpairs"]
    f_user = np.r_[cu, vp[:, 0]].astype(np.int64)
    f_t = np.r_[s["crawl_flag_t"][cu], (vp[:, 1] + 1) * DAY + VEL_RUN].astype(np.int64)
    f_rule = np.r_[np.full(len(cu), "ua_crawler"), np.full(len(vp), "velocity")]
    fo = np.argsort(f_t, kind="stable")
    f_txt = fmt_times(f_t[fo], rng, cfg["tz"])
    lines = join_cols([uid[f_user[fo]], f_rule[fo], f_txt])
    flags = "user_id,rule,flagged_at\n" + "\n".join(lines.tolist()) + ("\n" if len(fo) else "")
    return {"assignments.csv": assignments, "bot_flags.csv": flags, "pageviews.csv": pageviews,
            "module_clicks.csv": clicks}


def write_gz(folder, files):
    os.makedirs(folder, exist_ok=True)
    for name, text in files.items():
        buf = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=buf, compresslevel=9, mtime=0) as g:
            g.write(text.encode("utf-8"))
        with open(os.path.join(folder, name + ".gz"), "wb") as f:
            f.write(buf.getvalue())


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def set_folder(name):
    return os.path.join(APP, "data") if name == "visible" else os.path.join(TESTS, "hidden", name)


def remove_old(names):
    """Remove the files this generator owns (and the old layout's files the revision drops). Returns the list."""
    gone = []
    targets = []
    if "visible" in names:
        targets += [os.path.join(APP, "data", f) for f in ("users.csv", "assignments.csv", "pageviews.csv")]
        targets += [os.path.join(APP, "data", f + ".gz") for f in FILES]
    for name in names:
        if name != "visible":
            targets += [os.path.join(TESTS, "hidden", name, f + ".gz") for f in FILES + ("users.csv",)]
    for old in ("h_bots", "h_twin"):
        targets += [os.path.join(TESTS, "hidden", old, f + ".gz") for f in ("assignments.csv", "users.csv",
                                                                           "pageviews.csv")]
        targets.append(os.path.join(TESTS, "expected", old + ".json"))
    targets += [os.path.join(TESTS, "expected", n + ".json") for n in names]
    for t in targets:
        if os.path.exists(t):
            os.remove(t)
            gone.append(os.path.relpath(t, TASK))
    for old in ("h_bots", "h_twin"):
        d = os.path.join(TESTS, "hidden", old)
        if os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
            gone.append(os.path.relpath(d, TASK) + "/")
    return gone


def _plain(x):
    """JSON fallback for numpy scalars and arrays (integers stay integers)."""
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    raise TypeError(f"not JSON serializable: {type(x).__name__}")


def compact(R):
    """A path readout for the report (rounded only in the markdown; full precision in the JSON)."""
    keys = ("n_users", "pageviews", "clicks", "ctr", "diff", "half_width", "ci_95", "srm_p", "decision", "lo_hw",
            "hi_hw", "de", "rel_lift")
    return {k: R[k] for k in keys if k in R}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search-only", action="store_true")
    ap.add_argument("--sets", default=",".join(SET_NAMES))
    ap.add_argument("--write-shipped-readout", action="store_true")
    args = ap.parse_args()
    names = [x for x in args.sets.split(",") if x]
    for x in names:
        if x not in SET_NAMES:
            raise SystemExit(f"unknown set {x}")
    t_start = time.time()
    report = {"sets": {}, "constants": dict(
        MARGIN=MARGIN, SRM_OK_MIN=SRM_OK_MIN, SRM_FLAG_RANGE=SRM_FLAG_RANGE, SHIPPED_SRM_MAX=SHIPPED_SRM_MAX,
        H2_MARGIN=H2_MARGIN, DASH_LIFT=DASH_LIFT, KEEP_SRM_MIN=KEEP_SRM_MIN, KEEP_MARGIN=KEEP_MARGIN,
        ALL_ASSIGNED_MIN_REL=ALL_ASSIGNED_MIN_REL, DE_MIN=DE_MIN, FLOOR=FLOOR, CAPS=CAPS, SOFT_SCAN=SOFT_SCAN,
        SOFT_MIN_PASS=SOFT_MIN_PASS, ISO=ISO, P2ND=P2ND)}
    if not args.search_only:
        gone = remove_old(names)       # printed, not reported: the report must be byte-identical on a rerun
        print("removed before writing: " + (", ".join(gone) if gone else "nothing"), flush=True)
    for cfg in SETS:
        if cfg["name"] not in names:
            continue
        t1 = time.time()
        seed, tries, s, R, info = search(cfg)
        entry = dict(seed=seed, tries=tries, search=info, role=cfg["role"], versions=cfg["versions"],
                     carousel_arm=cfg["carousel"], override=cfg["ovr"], crawler_share=cfg["crawl"],
                     lift=cfg["lift"], p_b=cfg["p_b"], paths={k: compact(v) if "decision" in v else v
                                                             for k, v in R.items()})
        print(f"{cfg['name']}: seed {seed} after {tries} tries ({time.time() - t1:.1f} s); reference "
              f"{R['reference']['decision']} lower/hw {R['reference']['lo_hw']:+.2f} srm_p "
              f"{R['reference']['srm_p']:.3g} DE {R['reference']['de']:.2f}; soft {info['soft_kept']}", flush=True)
        report["sets"][cfg["name"]] = entry
        if args.search_only:
            continue
        files = build_text(cfg, s)
        folder = set_folder(cfg["name"])
        write_gz(folder, files)
        ra = ref_a.analyse(folder)
        rb = ref_b.readout(folder)
        gen = R["reference"]
        for key in ("n_users", "pageviews", "clicks"):
            if ra[key] != gen[key]:
                raise SystemExit(f"{cfg['name']}: ref_a {key} {ra[key]} != generator {gen[key]}")
            if ra[key] != rb[key]:
                raise SystemExit(f"{cfg['name']}: ref_a {key} {ra[key]} != ref_b {rb[key]}")
        for key in ("diff", "half_width", "srm_p"):
            if not math.isclose(ra[key], gen[key], rel_tol=1e-9, abs_tol=1e-15):
                raise SystemExit(f"{cfg['name']}: ref_a {key}={ra[key]!r} != generator {gen[key]!r}")
        if not math.isclose(ra["srm_p"], rb["srm_p"], rel_tol=1e-12, abs_tol=0.0):
            raise SystemExit(f"{cfg['name']}: ref_a srm_p {ra['srm_p']!r} != ref_b {rb['srm_p']!r}")
        errs = [abs(ra["ctr"][a] - rb["ctr"][a]) for a in ("A", "B")]
        errs += [abs(ra["diff"] - rb["diff"]), abs(ra["ci_95"][0] - rb["ci_95"][0]),
                 abs(ra["ci_95"][1] - rb["ci_95"][1])]
        if max(errs) > 1e-9:
            raise SystemExit(f"{cfg['name']}: ref_a and ref_b differ by {max(errs):.3g}")
        if ra["decision"] != rb["decision"] or ra["srm_flag"] != rb["srm_flag"]:
            raise SystemExit(f"{cfg['name']}: ref_a and ref_b decisions differ")
        chk = data_checks.check(folder, cfg, ra)
        if chk["failures"]:
            raise SystemExit(f"{cfg['name']}: assertions failed: {chk['failures'][:8]}")
        for k in ("reference", "shipped", "filter_only", "keep_overrides", "dashboard", "literal_bot_filter",
                  "platform_clicked"):
            a_, b_ = chk["paths"][k], R[k]
            for key in ("n_users", "pageviews", "clicks"):
                if a_[key] != b_[key]:
                    raise SystemExit(f"{cfg['name']}: path {k} {key} files {a_[key]} != arrays {b_[key]}")
            if not math.isclose(a_["diff"], b_["diff"], rel_tol=1e-9, abs_tol=1e-15):
                raise SystemExit(f"{cfg['name']}: path {k} diff files {a_['diff']} != arrays {b_['diff']}")
        entry["ref_ab_max_abs_diff"] = max(errs)
        entry["checks"] = {k: v for k, v in chk.items() if k not in ("failures", "paths")}
        # the paths as measured on the written files (equal to the arrays' on every count and diff, checked above)
        entry["paths"] = {k: compact(v) if "decision" in v else v for k, v in chk["paths"].items()}
        entry["files"] = {f + ".gz": os.path.getsize(os.path.join(folder, f + ".gz")) for f in FILES}
        entry["rows"] = {f: files[f].count("\n") - 1 for f in FILES}
        exp = os.path.join(TESTS, "expected", cfg["name"] + ".json")
        os.makedirs(os.path.dirname(exp), exist_ok=True)
        with open(exp, "w", encoding="utf-8") as f:
            json.dump(ra, f, indent=1, sort_keys=True)
            f.write("\n")
        print(f"  wrote {os.path.relpath(folder, TASK)} ({sum(entry['files'].values())} bytes gz) and "
              f"{os.path.relpath(exp, TASK)}; checks {len(chk['passed'])} passed ({time.time() - t1:.1f} s)",
              flush=True)
    if args.search_only:
        print(json.dumps({k: {kk: v[kk] for kk in ("seed", "tries", "search")} for k, v in report["sets"].items()}))
        return
    # SHA256SUMS over every hidden input and expected file (paths relative to tests/): exactly the five hidden sets x
    # the four files plus the six expected readouts; anything else under tests/hidden or tests/expected stops here
    hidden_names = [x for x in SET_NAMES if x != "visible"]
    listed = [os.path.join(TESTS, "hidden", h, f + ".gz") for h in hidden_names for f in FILES]
    listed += [os.path.join(TESTS, "expected", x + ".json") for x in SET_NAMES]
    present = []
    top = os.path.join(TESTS, "hidden")
    for root, dirs, fnames in os.walk(top):
        present += [os.path.join(root, x) for x in fnames]
        present += [os.path.join(root, d) + os.sep for d in dirs if d not in hidden_names or root != top]
    present += [os.path.join(TESTS, "expected", x) for x in os.listdir(os.path.join(TESTS, "expected"))]
    extra = sorted(set(present) - set(listed))
    missing = [p for p in listed if not os.path.isfile(p)]
    if extra or missing:
        raise SystemExit(f"tests/hidden or tests/expected: unexpected {extra[:5]}, missing {missing[:5]}")
    if len(listed) != 26:
        raise SystemExit(f"SHA256SUMS would list {len(listed)} files, not 26")
    with open(os.path.join(TESTS, "SHA256SUMS"), "w", encoding="utf-8") as f:
        for p in sorted(listed):
            f.write(f"{sha(p)}  {os.path.relpath(p, TESTS)}\n")
    report["sha256sums_files"] = len(listed)
    if args.write_shipped_readout:
        out = os.path.join(APP, "output", "result.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        # no -I here: -I implies -P, which keeps the cwd (the app folder) off sys.path, so -m could not find abtest
        r = subprocess.run([sys.executable, "-B", "-m", "abtest.report", "--data", "data", "--out",
                            "output/result.json"], cwd=APP, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"shipped code failed: {r.stderr[-2000:]}")
        report["shipped_readout"] = json.load(open(out, encoding="utf-8"))
    if set(names) == set(SET_NAMES):
        with open(os.path.join(HERE, "generation_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=1, sort_keys=True, default=_plain)
            f.write("\n")
        with open(os.path.join(HERE, "generation_report.out.md"), "w", encoding="utf-8") as f:
            f.write(markdown_report(report))
    print(f"done in {time.time() - t_start:.1f} s; SHA256SUMS lists {len(listed)} files", flush=True)


def markdown_report(rep):
    L = ["# generation_report (gen_data.py)", "",
         "Written by gen_data.py (deterministic: no clock times). Full precision: generation_report.json.", "",
         "Seeds are tried in order from each set's base; the first meeting every hard condition is kept (visible: "
         "the soft condition too, unless fewer than %d of the first %d seeds meet it)." % (SOFT_MIN_PASS, SOFT_SCAN),
         "", "| set | role | seed (tries) | carousel arm | overrides | reference A/B | decision | lower/hw | "
         "upper/hw | srm_p | DE | literal-filter srm_p | srm_all_assigned rel. miss |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, e in rep["sets"].items():
        r = e["paths"]["reference"]
        lit = e["paths"]["literal_bot_filter"]
        aa = e["paths"]["all_assigned"]
        ov = e["override"]
        ovs = f"{ov['n']} {ov['kind']} in {ov['arm']}" if ov else "none"
        L.append(f"| {name} | {e['role']} | {e['seed']} ({e['tries']}) | {e['carousel_arm'] or 'none'} | {ovs} | "
                 f"{r['n_users']['A']}/{r['n_users']['B']} | {r['decision']} | {r['lo_hw']:+.3f} | "
                 f"{r['hi_hw']:+.3f} | {r['srm_p']:.4g} | {r['de']:.2f} | {lit['srm_p']:.3g} | "
                 f"{abs(aa['srm_p'] - r['srm_p']) / r['srm_p']:.4f} |")
    L += ["", "Paths, measured on the written files (data_checks.py). Users: shipped = every user (any method) with "
          "no bot_flags row; filter_only and keep_overrides = every user without a ua_crawler row; dashboard and "
          "dashboard_all_rows = every assigned user; reference, platform_clicked and not_nav_clicked = hash users "
          "without a ua_crawler row; literal_bot_filter = hash users with no bot_flags row. Pageviews: ts at or after "
          "assigned_at (dashboard_all_rows: every row). Clicks: platform = pageviews.clicked (shipped, filter_only, "
          "dashboard, dashboard_all_rows, platform_clicked); item = the pageview has an item: event (reference, "
          "keep_overrides, literal_bot_filter); not_nav = an item: or link:all event.", "",
          "| set | path | n_users A/B | pageviews A/B | clicks A/B | CTR A | CTR B | rel. lift | lower/hw | srm_p | "
          "decision |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, e in rep["sets"].items():
        for k in ("shipped", "filter_only", "keep_overrides", "dashboard", "dashboard_all_rows", "literal_bot_filter",
                  "platform_clicked", "not_nav_clicked", "reference"):
            r = e["paths"][k]
            L.append(f"| {name} | {k} | {r['n_users']['A']}/{r['n_users']['B']} | {r['pageviews']['A']}/"
                     f"{r['pageviews']['B']} | {r['clicks']['A']}/{r['clicks']['B']} | {r['ctr']['A']:.5f} | "
                     f"{r['ctr']['B']:.5f} | {r['rel_lift']:+.4f} | {r['lo_hw']:+.2f} | {r['srm_p']:.3g} | "
                     f"{r['decision']} |")
    L += ["", "Assignment counts (all assigned users, every method, bots in): distinct users and rows (exact repeats "
          "in) per arm, and the SRM p of the distinct counts:", "", "| set | users A/B | rows A/B | srm_p |",
          "|---|---|---|---|"]
    for name, e in rep["sets"].items():
        aa = e["paths"]["all_assigned"]
        rows = aa.get("rows", {"A": "-", "B": "-"})
        L.append(f"| {name} | {aa['n_users']['A']}/{aa['n_users']['B']} | {rows['A']}/{rows['B']} | "
                 f"{aa['srm_p']:.4g} |")
    L += ["", "Rows and sizes (gzip bytes):", "", "| set | assignments rows | bot_flags rows | pageviews rows | "
          "module_clicks rows | gz bytes total |", "|---|---|---|---|---|---|"]
    for name, e in rep["sets"].items():
        if "rows" in e:
            r = e["rows"]
            L.append(f"| {name} | {r['assignments.csv']} | {r['bot_flags.csv']} | {r['pageviews.csv']} | "
                     f"{r['module_clicks.csv']} | {sum(e['files'].values())} |")
    L += ["", f"tests/SHA256SUMS lists {rep.get('sha256sums_files')} files."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()

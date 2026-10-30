"""Generate the visible and hidden datasets for the ab-test-reanalysis task (authoring time only).

Run: submission/.venv/bin/python submission/authoring/ab-test-reanalysis/gen_data.py [--search-only]

What it writes (into submission/tasks/ab-test-reanalysis/):
  environment/app/data/{assignments,users,pageviews}.csv      the visible experiment (agent sees it; dropped at grading)
  tests/hidden/<set>/{assignments,users,pageviews}.csv.gz     five hidden experiments (gzip, mtime 0: byte-stable)
  tests/expected/<set>.json                                   reference values from ref_a.py (stdlib, delta method)
  tests/SHA256SUMS                                            hashes of every hidden and expected file
and generation_report.out.md next to this script (seeds, realised design effects, margins).

How a set is made (synthetic; nothing here comes from a real product):
  - users are assigned A or B with probability p_b (0.5 except the SRM set); a share bot_frac is flagged is_bot = 1;
  - each human user has a click propensity p_i ~ Beta with mean ctr and intra-user correlation rho, and a number of
    post-assignment pageviews from a zero-inflated, floored lognormal (heavy tail; sigma sets the tail). Together they
    set the design effect DE = Var(user-level diff) / Var(pageview-level diff);
  - B multiplies p_i by (1 + lift); bots get many pageviews and click with probability 0.003;
  - some users also have pageviews before assigned_at (must be dropped), many users have their first counted pageview
    exactly at assigned_at (must be kept), some assignment rows are repeated exactly (count once);
  - every timestamp is written as ISO 8601 with Z or a +hh:mm / -hh:mm offset (same instant, different text).
A twin set (twin_of; h_twin, DESIGN.md section 15) is not a new draw: it re-makes its base set's kept realisation and
redraws only the clicks from its own seed (simulate_twin), so every file but the clicked column is the base set's.
Seed search: for each set, seeds base, base+1, ... are tried in order and the first one whose realised data meets the
set's stated conditions (CONDITIONS below) is kept. The kept seed and the number of tries go to the report.
"""
import argparse, gzip, hashlib, io, json, math, os, subprocess, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
APP = os.path.join(TASK, "environment", "app")
TESTS = os.path.join(TASK, "tests")
sys.path.insert(0, HERE)
import ref_a  # noqa: E402

T0 = np.datetime64("2026-09-01T00:00:00", "s")      # experiment start, UTC
SPAN = 14 * 86400                                  # 14 days, seconds
Z975 = 1.959963984540054

TZ_COMMON = [("Z", 0, 0.66), ("+00:00", 0, 0.04), ("+01:00", 60, 0.06), ("+02:00", 120, 0.04), ("+05:30", 330, 0.05),
             ("-04:00", -240, 0.09), ("-05:00", -300, 0.03), ("-07:00", -420, 0.03)]
TZ_WIDE = [("Z", 0, 0.34), ("+00:00", 0, 0.06), ("+01:00", 60, 0.06), ("+05:30", 330, 0.10), ("+05:45", 345, 0.05),
           ("+09:00", 540, 0.08), ("+13:00", 780, 0.03), ("-03:30", -210, 0.06), ("-04:00", -240, 0.10),
           ("-07:00", -420, 0.07), ("-10:00", -600, 0.05)]

# role: "null" -> decision no_ship with lower bound <= -MARGIN half-widths; "pos" -> ship with lower >= +MARGIN;
#       "srm" -> SRM flagged (decision invalid) while its CI alone would say ship (lower >= +MARGIN).
SETS = [
    dict(name="visible", role="null", seed=1000, n_users=40000, p_b=0.5, bot_frac=0.020, bot_pv=22, pv_mean=11.0,
         sigma=1.0, zero=0.08, ctr=0.080, rho=0.20, lift=0.0, pre=0.20, tie=0.6, dup=0.010, tz=TZ_COMMON, de=(6.0, 8.5)),
    dict(name="h_null", role="null", seed=2000, n_users=38000, p_b=0.5, bot_frac=0.015, bot_pv=20, pv_mean=9.0,
         sigma=1.3, zero=0.08, ctr=0.110, rho=0.42, lift=0.0, pre=0.20, tie=0.6, dup=0.010, tz=TZ_COMMON, de=(21.0, 32.0)),
    dict(name="h_pos", role="pos", seed=3000, n_users=40000, p_b=0.5, bot_frac=0.015, bot_pv=20, pv_mean=9.0,
         sigma=1.0, zero=0.08, ctr=0.120, rho=0.20, lift=0.100, pre=0.20, tie=0.6, dup=0.010, tz=TZ_COMMON,
         de=(6.0, 8.5)),
    dict(name="h_srm", role="srm", seed=4000, n_users=40000, p_b=0.515, bot_frac=0.015, bot_pv=20, pv_mean=9.0,
         sigma=1.0, zero=0.08, ctr=0.100, rho=0.24, lift=0.110, pre=0.20, tie=0.6, dup=0.010, tz=TZ_COMMON,
         de=(6.5, 9.5)),
    dict(name="h_bots", role="null", seed=5000, n_users=34000, p_b=0.5, bot_frac=0.060, bot_pv=40, pv_mean=9.0,
         sigma=1.1, zero=0.08, ctr=0.090, rho=0.22, lift=0.0, pre=0.25, tie=0.6, dup=0.015, tz=TZ_WIDE, de=(6.5, 10.5)),
    # h_twin (DESIGN.md sections 14 and 15): the exact pageview twin of h_null. Since 2026-10-29 (DESIGN.md section 15)
    # it is NOT a new draw: it takes h_null's kept realisation as it is (the same users and ids, arm labels, bot flags,
    # assigned_at, repeated assignment rows, pageview rows with their users and instants, and the same timestamp text,
    # because the text is built from h_null's own generator stream) and redraws ONLY the clicks, from its own seed: a new
    # click propensity per user with rho 0.09 (h_null 0.42), mean CTR 0.110, a true lift of 9% on B, bots at 0.003.
    # So assignments.csv and users.csv are byte-identical to h_null's and pageviews.csv differs only in the clicked
    # column: every statistic of the pageview counts (per user, per arm) is identical on the two sets, while the
    # user-level reference half-widths differ by a factor of about 2 (design effect 23 against 5.2 to 5.8; the narrow
    # DE range keeps that factor large). Only twin_of, the seed, ctr, rho, lift, role and the DE range are used.
    dict(name="h_twin", role="pos", twin_of="h_null", seed=7000, ctr=0.110, rho=0.09, lift=0.090, de=(5.2, 5.8)),
]
TWIN_BASE_SEED = {"h_null": 2006}   # the kept h_null seed; if h_null's search ever keeps another seed, stop (see main)
TWIN_MIN_MISS = 0.33    # a twin's guaranteed miss for pageview-only multipliers (twin_min_miss) at least this
MARGIN = 0.5            # decision bounds at least this many reference half-widths from 0 (design asks >= 0.35)
SRM_OK_MIN = 0.05       # sets without SRM: chi-square p at least this (far from the 0.001 flag)
SRM_FLAG_RANGE = (1e-11, 1e-5)   # the SRM set: flagged, and above 1e-12 so the 1%-relative comparison applies
VISIBLE_STORY = dict(rel_lift=(0.037, 0.044), p=(2.0e-4, 3.49e-4))   # what the shipped (wrong) code must report


def lognormal_counts(rng, n, mean, sigma, cap=600):
    m = math.log(mean) - sigma * sigma / 2
    return np.minimum(np.floor(rng.lognormal(m, sigma, n)), cap).astype(np.int64)


def simulate(cfg, seed):
    """Numbers only (no text): per-user and per-pageview arrays."""
    rng = np.random.default_rng(seed)
    n = cfg["n_users"]
    ids = rng.choice(np.arange(1_000_000, 9_999_999), size=n, replace=False)
    var_b = (rng.random(n) < cfg["p_b"]).astype(np.int8)
    bot = (rng.random(n) < cfg["bot_frac"]).astype(np.int8)
    assigned = np.floor(rng.beta(1.0, 2.5, n) * (SPAN - 6 * 3600)).astype(np.int64)
    k = 1.0 / cfg["rho"] - 1.0
    p = rng.beta(cfg["ctr"] * k, (1 - cfg["ctr"]) * k, n)
    p = np.where(var_b == 1, np.minimum(p * (1 + cfg["lift"]), 0.95), p)
    p = np.where(bot == 1, 0.003, p)
    npost = lognormal_counts(rng, n, cfg["pv_mean"], cfg["sigma"])
    npost[rng.random(n) < cfg["zero"]] = 0
    nbot = np.maximum(lognormal_counts(rng, n, cfg["bot_pv"], 0.6), 3)
    npost = np.where(bot == 1, nbot, npost)
    npre = np.where(rng.random(n) < cfg["pre"], 1 + rng.poisson(0.8, n), 0)
    # post-assignment pageviews: optional tie at assigned_at, the rest strictly after, before the end of the window
    users_post = np.repeat(np.arange(n), npost)
    first = np.r_[True, users_post[1:] != users_post[:-1]] if len(users_post) else np.zeros(0, bool)
    tie_user = rng.random(n) < cfg["tie"]
    room = SPAN - assigned[users_post]
    t_post = assigned[users_post] + 1 + np.floor(rng.random(len(users_post)) * (room - 1)).astype(np.int64)
    t_post = np.where(first & tie_user[users_post], assigned[users_post], t_post)
    users_pre = np.repeat(np.arange(n), npre)
    t_pre = assigned[users_pre] - (60 + np.floor(rng.random(len(users_pre)) * (3 * 86400)).astype(np.int64))
    pv_user = np.r_[users_post, users_pre]
    pv_t = np.r_[t_post, t_pre]
    pv_post = np.r_[np.ones(len(users_post), bool), np.zeros(len(users_pre), bool)]
    clicked = (rng.random(len(pv_user)) < p[pv_user]).astype(np.int8)
    dup = rng.random(n) < cfg["dup"]
    return dict(ids=ids, var_b=var_b, bot=bot, assigned=assigned, pv_user=pv_user, pv_t=pv_t, pv_post=pv_post,
                clicked=clicked, dup=dup, rng=rng)


def simulate_twin(cfg, seed, base_cfg, base_seed):
    """A twin of a base set: the base set's realisation (users, arms, bots, assigned_at, repeats, pageview rows and
    instants) re-made exactly by simulate(base_cfg, base_seed), with ONLY the clicks redrawn from this set's seed.
    The returned rng is the base set's own stream at the same position, so build_text gives the same timestamp text,
    row order and users.csv order as for the base set; only the clicked column of pageviews.csv differs."""
    s = simulate(base_cfg, base_seed)
    rng = np.random.default_rng(seed)
    n = len(s["ids"])
    k = 1.0 / cfg["rho"] - 1.0
    p = rng.beta(cfg["ctr"] * k, (1 - cfg["ctr"]) * k, n)
    p = np.where(s["var_b"] == 1, np.minimum(p * (1 + cfg["lift"]), 0.95), p)
    p = np.where(s["bot"] == 1, 0.003, p)
    s["clicked"] = (rng.random(len(s["pv_user"])) < p[s["pv_user"]]).astype(np.int8)
    return s


def arm_stats(c, v):
    """Delta-method variance of the ratio sum(c)/sum(v) over users (sample-variance form)."""
    N = len(c)
    R = c.sum() / v.sum()
    var = N / (N - 1) * float(((c - R * v) ** 2).sum()) / float(v.sum()) ** 2
    return R, var, int(c.sum()), int(v.sum()), N


def quick_stats(s, *, bots_both=True):
    """The analysis on the arrays: correct (bots out of both arms) or the shipped code's (bots out of B only)."""
    n = len(s["ids"])
    keep = (s["bot"] == 0) | ((s["var_b"] == 0) & (not bots_both))
    post = s["pv_post"]
    c_u = np.bincount(s["pv_user"][post], weights=s["clicked"][post], minlength=n)
    v_u = np.bincount(s["pv_user"][post], minlength=n).astype(float)
    out = {}
    for arm, code in (("A", 0), ("B", 1)):
        m = keep & (s["var_b"] == code)
        out[arm] = arm_stats(c_u[m], v_u[m])
    (Ra, va, ca, pa, Na), (Rb, vb, cb, pb, Nb) = out["A"], out["B"]
    diff = Rb - Ra
    hw = Z975 * math.sqrt(va + vb)
    naive_se = math.sqrt(Ra * (1 - Ra) / pa + Rb * (1 - Rb) / pb)
    pool = (ca + cb) / (pa + pb)
    z = diff / math.sqrt(pool * (1 - pool) * (1 / pa + 1 / pb))
    p_naive = math.erfc(abs(z) / math.sqrt(2))
    e = (Na + Nb) / 2
    chi2 = ((Na - e) ** 2 + (Nb - e) ** 2) / e
    return dict(Na=Na, Nb=Nb, Ra=Ra, Rb=Rb, diff=diff, hw=hw, lo=diff - hw, hi=diff + hw,
                de=(va + vb) / naive_se ** 2, naive_hw=Z975 * naive_se, srm_p=math.erfc(math.sqrt(chi2 / 2)),
                rel_lift=Rb / Ra - 1, p_naive=p_naive, pv=pa + pb)


def twin_min_miss(st, base):
    """Twin vs base set (identical pageview counts per user and arm): the smallest worst-set bound error, in reference
    half-widths, that ANY interval of the form diff +/- z sqrt(sum over arms of R(1-R)/V x M_arm) must make on one of
    the two when M_A, M_B >= 0 are computed from the pageview data alone (so they are equal on the two sets). V is
    equal, so the twin/base ratio of such widths lies in [sqrt(q_lo), sqrt(q_hi)], q = R(1-R) twin / R(1-R) base per
    arm, whatever M is; both sets pass only if (1 + e) / (1 - e) >= sqrt(q_lo) x hw_base / hw_twin = r, so e >=
    (r - 1) / (r + 1) (DESIGN.md section 15)."""
    q_lo = min(st[k] * (1 - st[k]) / (base[k] * (1 - base[k])) for k in ("Ra", "Rb"))
    r = math.sqrt(q_lo) * base["hw"] / st["hw"]
    return (r - 1) / (r + 1)


def conditions(cfg, st, orig, base_st=None):
    """The stated conditions a realised set must meet. Returns a list of failed conditions (empty = keep)."""
    bad = []
    if base_st is not None:
        e = twin_min_miss(st, base_st)
        if not e >= TWIN_MIN_MISS:
            bad.append(f"twin minimum miss {e:.3f} < {TWIN_MIN_MISS}")
    lo_de, hi_de = cfg["de"]
    if not lo_de <= st["de"] <= hi_de:
        bad.append(f"DE {st['de']:.2f} not in {cfg['de']}")
    m = st["lo"] / st["hw"]
    if cfg["role"] == "null" and not m <= -MARGIN:
        bad.append(f"lower/hw {m:.2f} > -{MARGIN}")
    if cfg["role"] in ("pos", "srm") and not m >= MARGIN:
        bad.append(f"lower/hw {m:.2f} < {MARGIN}")
    if cfg["role"] == "srm":
        if not SRM_FLAG_RANGE[0] <= st["srm_p"] <= SRM_FLAG_RANGE[1]:
            bad.append(f"srm_p {st['srm_p']:.3g} outside {SRM_FLAG_RANGE}")
    elif st["srm_p"] < SRM_OK_MIN:
        bad.append(f"srm_p {st['srm_p']:.3g} < {SRM_OK_MIN}")
    if cfg["name"] == "visible":
        a, b = VISIBLE_STORY["rel_lift"]
        if not a <= orig["rel_lift"] <= b:
            bad.append(f"shipped-code lift {orig['rel_lift']:.4f} outside {VISIBLE_STORY['rel_lift']}")
        a, b = VISIBLE_STORY["p"]
        if not a <= orig["p_naive"] <= b:
            bad.append(f"shipped-code p {orig['p_naive']:.3g} outside {VISIBLE_STORY['p']}")
    return bad


def search(cfg, kept, max_tries=400):
    """kept: {set name: (cfg, kept seed)} of the sets already searched (a twin needs its base set's)."""
    base = None
    if "twin_of" in cfg:
        base_cfg, base_seed = kept[cfg["twin_of"]]
        if base_seed != TWIN_BASE_SEED[cfg["twin_of"]]:
            raise SystemExit(f"{cfg['twin_of']} kept seed {base_seed}, expected {TWIN_BASE_SEED[cfg['twin_of']]}")
        base = (base_cfg, base_seed)
    base_st = quick_stats(simulate(*base)) if base else None
    for i in range(max_tries):
        seed = cfg["seed"] + i
        s = simulate(cfg, seed) if base is None else simulate_twin(cfg, seed, *base)
        st = quick_stats(s)
        orig = quick_stats(s, bots_both=False)
        if not conditions(cfg, st, orig, base_st):
            return seed, i + 1, s, st, orig
    raise SystemExit(f"{cfg['name']}: no seed in {max_tries} tries met the conditions")


def fmt_times(secs, rng, tz):
    """Seconds since T0 (UTC) -> ISO 8601 strings, each with a randomly chosen suffix from tz (same instant)."""
    names = np.array([t[0] for t in tz])
    mins = np.array([t[1] for t in tz], dtype=np.int64)
    probs = np.array([t[2] for t in tz], dtype=float)
    k = rng.choice(len(tz), size=len(secs), p=probs / probs.sum())
    local = T0 + (secs + mins[k] * 60).astype("timedelta64[s]")
    base = np.datetime_as_string(local, unit="s")
    return np.char.add(base.astype("U19"), names[k])


def build_text(cfg, s):
    rng = s["rng"]   # the kept seed's generator, continued: text formatting is part of the same fixed stream
    ids = np.char.add("u", s["ids"].astype("U7"))
    # assignments: one row per user, sorted by instant; exact repeats right after the original row
    a_txt = fmt_times(s["assigned"], rng, cfg["tz"])
    order = np.argsort(s["assigned"], kind="stable")
    rows = []
    variant = np.where(s["var_b"] == 1, "B", "A")
    for i in order:
        row = f"{ids[i]},{variant[i]},{a_txt[i]}"
        rows.append(row)
        if s["dup"][i]:
            rows.append(row)
    assignments = "user_id,variant,assigned_at\n" + "\n".join(rows) + "\n"
    # users: every assigned user once, shuffled
    perm = rng.permutation(len(ids))
    users = "user_id,is_bot\n" + "\n".join(f"{ids[i]},{int(s['bot'][i])}" for i in perm) + "\n"
    # pageviews: sorted by instant (ties keep generation order)
    o = np.argsort(s["pv_t"], kind="stable")
    t_txt = fmt_times(s["pv_t"][o], rng, cfg["tz"])
    uid = ids[s["pv_user"][o]]
    clk = s["clicked"][o].astype("U1")
    lines = np.char.add(np.char.add(np.char.add(np.char.add(uid, ","), t_txt), ","), clk)
    pageviews = "user_id,ts,clicked\n" + "\n".join(lines.tolist()) + "\n"
    return {"assignments.csv": assignments, "users.csv": users, "pageviews.csv": pageviews}


def write_plain(folder, files):
    os.makedirs(folder, exist_ok=True)
    for name, text in files.items():
        with open(os.path.join(folder, name), "w", encoding="utf-8", newline="") as f:
            f.write(text)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search-only", action="store_true")
    args = ap.parse_args()
    report = ["# generation_report (gen_data.py)", "",
              "Seeds are searched in order from each set's base; the first that meets the stated conditions is kept.",
              f"Conditions: decision bound margin >= {MARGIN} half-widths; SRM p >= {SRM_OK_MIN} (no SRM) or in "
              f"{SRM_FLAG_RANGE} (SRM set); design effect in the set's range; visible set: shipped-code lift in "
              f"{VISIBLE_STORY['rel_lift']} and p in {VISIBLE_STORY['p']}.", "",
              "| set | role | seed | tries | users A/B (no bots) | pageviews | CTR A | CTR B | diff | half-width | lower/hw "
              "| DE | sqrt(DE) | SRM p | shipped-code lift | shipped-code p |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    expected_files = []
    kept, kept_st, twins = {}, {}, []
    for cfg in SETS:
        seed, tries, s, st, orig = search(cfg, kept)
        kept[cfg["name"]] = (cfg, seed)
        kept_st[cfg["name"]] = st
        report.append(f"| {cfg['name']} | {cfg['role']} | {seed} | {tries} | {st['Na']}/{st['Nb']} | {st['pv']} | "
                      f"{st['Ra']:.5f} | {st['Rb']:.5f} | {st['diff']:+.5f} | {st['hw']:.5f} | "
                      f"{st['lo'] / st['hw']:+.2f} | {st['de']:.2f} | {math.sqrt(st['de']):.3f} | {st['srm_p']:.3g} | "
                      f"{orig['rel_lift']:+.4f} | {orig['p_naive']:.3g} |")
        print(report[-1], flush=True)
        if "twin_of" in cfg:
            twins.append(f"- {cfg['name']} is the twin of {cfg['twin_of']} (kept seed {kept[cfg['twin_of']][1]}): the "
                         f"same users, arms, bots, assigned_at, repeated rows, pageview rows and timestamp text; only "
                         f"the clicks are redrawn, from seed {seed} (rho {cfg['rho']}, CTR {cfg['ctr']}, lift "
                         f"{cfg['lift']}). Guaranteed miss of any pageview-only multiplier on one of the two "
                         f"(twin_min_miss): {twin_min_miss(st, kept_st[cfg['twin_of']]):.4f} half-widths (needs >= "
                         f"{TWIN_MIN_MISS}).")
        if args.search_only:
            continue
        # a twin is written with its base set's text settings (offsets), from the base set's own stream (simulate_twin)
        files = build_text(kept[cfg["twin_of"]][0] if "twin_of" in cfg else cfg, s)
        if cfg["name"] == "visible":
            folder = os.path.join(APP, "data")
            write_plain(folder, files)
        else:
            folder = os.path.join(TESTS, "hidden", cfg["name"])
            write_gz(folder, files)
        ref = ref_a.analyse(folder)
        # cross-check: the stdlib reference reading the text must equal the generator's own numbers
        for key, mine in (("diff", st["diff"]), ("half_width", st["hw"]), ("srm_p", st["srm_p"])):
            if not math.isclose(ref[key], mine, rel_tol=1e-9, abs_tol=1e-15):
                raise SystemExit(f"{cfg['name']}: ref_a {key}={ref[key]!r} != generator {mine!r}")
        if (ref["n_users"]["A"], ref["n_users"]["B"]) != (st["Na"], st["Nb"]):
            raise SystemExit(f"{cfg['name']}: user counts differ between ref_a and the generator")
        os.makedirs(os.path.join(TESTS, "expected"), exist_ok=True)
        exp = os.path.join(TESTS, "expected", cfg["name"] + ".json")
        with open(exp, "w", encoding="utf-8") as f:
            json.dump(ref, f, indent=1, sort_keys=True)
            f.write("\n")
        expected_files.append(exp)
    if args.search_only:
        return
    # SHA256SUMS over every hidden input and expected file (paths relative to tests/)
    listed = []
    for root, _dirs, names in os.walk(os.path.join(TESTS, "hidden")):
        listed += [os.path.join(root, n) for n in names]
    listed += expected_files
    with open(os.path.join(TESTS, "SHA256SUMS"), "w", encoding="utf-8") as f:
        for p in sorted(listed):
            f.write(f"{sha(p)}  {os.path.relpath(p, TESTS)}\n")
    # the shipped (wrong) readout, made by the shipped code itself
    out = os.path.join(APP, "output", "result.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run([sys.executable, "-m", "abtest.report", "--data", "data", "--out", "output/result.json"],
                       cwd=APP, capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if r.returncode != 0:
        raise SystemExit(f"shipped code failed: {r.stderr}")
    report += [""] + twins
    report += ["", "Shipped code's readout (environment/app/output/result.json):", "```",
               open(out, encoding="utf-8").read().strip(), "```", "", "File sizes (bytes):"]
    for root, _dirs, names in sorted(os.walk(os.path.join(APP, "data"))) + sorted(os.walk(os.path.join(TESTS, "hidden"))):
        for n in sorted(names):
            p = os.path.join(root, n)
            report.append(f"- `{os.path.relpath(p, TASK)}`: {os.path.getsize(p)}")
    with open(os.path.join(HERE, "generation_report.out.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print("wrote data, expected values, SHA256SUMS, result.json and generation_report.out.md")


if __name__ == "__main__":
    main()

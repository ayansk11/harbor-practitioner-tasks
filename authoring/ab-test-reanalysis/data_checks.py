"""Assertions on one written export of ab-test-reanalysis ((a) to (n) of docs/ab-test-reanalysis/DESIGN.md, plus
caps, floors and format checks), computed from the four .csv.gz files alone with pandas and numpy, independently of
the generator's arrays. gen_data.py stops on any failure. Also returns every analysis path's readout measured on
the files.

check(folder, cfg, ref) -> {"failures": [...], "passed": [...], "paths": {...}, measured values}
  cfg: the set's generator config (name, carousel arm); ref: ref_a's readout of the same folder.
Run alone: python data_checks.py <folder> <set name>   (prints the result as JSON).

The assertions:
 (a) every ua_crawler flag is raised at least 1 s before the user's assigned_at; one ua_crawler row per crawler;
 (b) every velocity flag is raised after the user's assigned_at, at 02:00:00 UTC (the nightly run);
 (c) every velocity-only user (no ua_crawler row) is a hash-assigned user of the carousel (v2) arm with 8 or more
     nav: taps on each flagged day, among them 8 within 60 s;
 (d) no user without a ua_crawler row has 5 item: events within 60 s;
 (e) the three population routes give the same users per arm: rule (no ua_crawler row), time (no flag of any rule
     at or before assigned_at) and recount (ua_crawler plus the velocity rule recounted on item: events only);
 (f) every run of 8 consecutive module events of one user spans under 40 s within one UTC day, or more than 90 s;
 (g) every module event has its pageview (same user), at or after the pageview's ts; events of pre-assignment
     pageviews fall before assigned_at;
 (h) pageviews.clicked = 1 exactly when the pageview has at least one module event;
 (i) ref_a = ref_b: checked in gen_data.py;
 (j) the velocity rows are exactly the user-days on which the documented rule (8 or more module events of any target
     within 60 s on one UTC day; the run of day + 1 at 02:00 UTC; first run 2026-08-28) fires on module_clicks;
     the same with "within 60 s" read as < 60 s or <= 60 s;
 (k) override accounts have one assignment row and no bot_flags row;
 (l) targets are item:<digits>, nav:prev, nav:next or link:all only; nav: only in the carousel arm and only on
     post-assignment pageviews; link:all only from 2026-09-08 00:00Z (its pageview too);
 (m) the SRM test on all assigned users misses the reference srm_p by at least 3% relative;
 (n) the design effect of the reference readout is at least 5.5.
 caps: at most 50,000 assigned users, 500,000 pageview rows and 100,000 module_clicks rows;
 floors: per arm, among the reference users, at least 20 counted pageviews with link:all and no item: event, 20
     counted pageviews with two item: events, 20 pre-assignment pageviews with an item: event.
"""
import json, math, os, re, sys

import numpy as np
import pandas as pd

T0 = pd.Timestamp("2026-09-01T00:00:00Z")
DAY = 86400
SEE_ALL_FROM = 7 * DAY
VEL_FIRST_DAY = -5
Z975 = 1.959963984540054
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$")
TARGET_RE = re.compile(r"^(item:\d+|nav:prev|nav:next|link:all)$")
CAPS = dict(users=50_000, pageviews=500_000, clicks=100_000)
FLOOR = 20
DE_MIN = 5.5
ALL_ASSIGNED_MIN_REL = 0.03


def _read(folder, name):
    p = os.path.join(folder, name + ".gz")
    return pd.read_csv(p if os.path.exists(p) else os.path.join(folder, name), dtype=str, keep_default_na=False)


def _secs(col):
    """ISO 8601 text with offsets -> whole seconds since 2026-09-01T00:00Z (resolution independent)."""
    t = pd.to_datetime(col, utc=True, format="ISO8601")
    return ((t - T0) // pd.Timedelta(seconds=1)).to_numpy(np.int64)


def _fires(key, t, n, win):
    """For events with integer group keys and times: True per event i if [t_i, t_i + win] holds >= n events of
    the same key (sliding window by binary search; a second algorithm next to the generator's)."""
    if len(t) == 0:
        return np.zeros(0, bool)
    span = int(t.max() - t.min()) + 10 * win + 1
    v = key.astype(np.int64) * span + (t - t.min())
    o = np.argsort(v, kind="stable")
    vs = v[o]
    cnt = np.searchsorted(vs, vs + win, side="right") - np.arange(len(vs))
    out = np.zeros(len(t), bool)
    out[o] = cnt >= n
    return out


def _rule_days(ucode, t, n=8, win=60):
    """Set of (user code, UTC day) on which >= n events fall within win seconds on that day."""
    day = np.floor_divide(t, DAY)
    key = ucode.astype(np.int64) * 64 + (day + 20)
    f = _fires(key, t, n, win)
    pairs = {(int(u), int(d)) for u, d in zip(ucode[f], day[f]) if d >= VEL_FIRST_DAY}
    return pairs


def _readout(mask, arm, clicks, views):
    out = {"n_users": {}, "pageviews": {}, "clicks": {}, "ctr": {}}
    var = {}
    for a, code in (("A", 0), ("B", 1)):
        m = mask & (arm == code)
        c, v = clicks[m].astype(float), views[m].astype(float)
        N, C, V = int(m.sum()), float(c.sum()), float(v.sum())
        R = C / V
        var[a] = N / (N - 1) * float(np.sum((c - R * v) ** 2)) / V ** 2
        out["n_users"][a], out["pageviews"][a], out["clicks"][a], out["ctr"][a] = N, int(V), int(C), R
    Ra, Rb = out["ctr"]["A"], out["ctr"]["B"]
    diff = Rb - Ra
    hw = Z975 * math.sqrt(var["A"] + var["B"])
    na, nb = out["n_users"]["A"], out["n_users"]["B"]
    e = (na + nb) / 2
    srm_p = math.erfc(math.sqrt((((na - e) ** 2 + (nb - e) ** 2) / e) / 2))
    naive = Ra * (1 - Ra) / out["pageviews"]["A"] + Rb * (1 - Rb) / out["pageviews"]["B"]
    lo = diff - hw
    out.update(diff=diff, half_width=hw, ci_95=[lo, diff + hw], srm_p=srm_p, lo_hw=lo / hw, hi_hw=(diff + hw) / hw,
               de=(var["A"] + var["B"]) / naive, rel_lift=Rb / Ra - 1,
               decision="invalid" if srm_p < 0.001 else ("ship" if lo > 0 else "no_ship"))
    return out


def check(folder, cfg, ref):
    fails, passed, meas = [], [], {}

    def req(name, ok, detail=""):
        (passed if ok else fails).append(name if ok else f"{name}: {detail}")

    a_raw = _read(folder, "assignments.csv")
    f = _read(folder, "bot_flags.csv")
    pv = _read(folder, "pageviews.csv")
    mc = _read(folder, "module_clicks.csv")
    req("columns", list(a_raw.columns) == ["user_id", "variant", "assigned_at", "method"]
        and list(f.columns) == ["user_id", "rule", "flagged_at"]
        and list(pv.columns) == ["pageview_id", "user_id", "ts", "clicked"]
        and list(mc.columns) == ["pageview_id", "user_id", "ts", "target"], "unexpected columns")
    for name, col in (("assigned_at", a_raw["assigned_at"]), ("flagged_at", f["flagged_at"]), ("pv ts", pv["ts"]),
                      ("click ts", mc["ts"])):
        bad = int((~col.str.match(TS_RE)).sum())
        req(f"timestamp format {name}", bad == 0, f"{bad} rows")
    a = a_raw.drop_duplicates()
    req("one assignment per user", not a["user_id"].duplicated().any(), "conflicting rows")
    req("variant and method values",
        a["variant"].isin(["A", "B"]).all() and a["method"].isin(["hash", "override"]).all())
    users = pd.Index(a["user_id"])
    N = len(users)
    arm = (a["variant"].to_numpy() == "B").astype(np.int8)
    is_hash = a["method"].to_numpy() == "hash"
    t0 = _secs(a["assigned_at"])
    fu = users.get_indexer(f["user_id"])
    pu = users.get_indexer(pv["user_id"])
    mu = users.get_indexer(mc["user_id"])
    req("flags of assigned users", (fu >= 0).all())
    req("pageviews of assigned users", (pu >= 0).all())
    req("clicks of assigned users", (mu >= 0).all())
    req("rules", f["rule"].isin(["ua_crawler", "velocity"]).all())
    req("clicked values", pv["clicked"].isin(["0", "1"]).all())
    req("pageview_id unique", not pv["pageview_id"].duplicated().any())
    req("no repeated flag rows", not f.duplicated().any())
    ft = _secs(f["flagged_at"])
    pt = _secs(pv["ts"])
    ct = _secs(mc["ts"])
    is_ua = f["rule"].to_numpy() == "ua_crawler"
    is_vel = ~is_ua
    crawler = np.zeros(N, bool)
    crawler[fu[is_ua]] = True
    anyflag = np.zeros(N, bool)
    anyflag[fu] = True
    vel = np.zeros(N, bool)
    vel[fu[is_vel]] = True
    # caps
    req("caps", N <= CAPS["users"] and len(pv) <= CAPS["pageviews"] and len(mc) <= CAPS["clicks"],
        f"users {N}, pageviews {len(pv)}, clicks {len(mc)}")
    meas["rows"] = dict(assignments=len(a_raw), distinct_users=N, bot_flags=len(f), pageviews=len(pv),
                        module_clicks=len(mc), exact_repeats=len(a_raw) - len(a))
    # (a)
    ok_a = bool((ft[is_ua] <= t0[fu[is_ua]] - 1).all()) and not f.loc[is_ua, "user_id"].duplicated().any()
    req("(a) ua_crawler flags >= 1 s before assigned_at, one per crawler", ok_a)
    # (b)
    ok_b = bool((ft[is_vel] > t0[fu[is_vel]]).all()) and bool((np.mod(ft[is_vel], DAY) == 7200).all())
    req("(b) velocity flags after assigned_at at 02:00:00 UTC", ok_b)
    # (g)
    pid_index = pd.Index(pv["pageview_id"])
    mpv = pid_index.get_indexer(mc["pageview_id"])
    ok_g = bool((mpv >= 0).all())
    if not ok_g or not ((fu >= 0).all() and (pu >= 0).all() and (mu >= 0).all()):
        req("(g) every event has its pageview", False, f"{int((mpv < 0).sum())} events without a pageview")
        return dict(failures=fails, passed=passed, paths={}, **meas)    # the remaining checks need the joins
    if ok_g:
        ok_g = bool((pu[mpv] == mu).all()) and bool((ct >= pt[mpv]).all())
        pre_pv = pt < t0[pu]
        e_pre = pre_pv[mpv]
        ok_g = ok_g and bool((ct[e_pre] < t0[mu[e_pre]]).all())
    req("(g) every event has its pageview, at or after it; pre-assignment events before assigned_at", ok_g)
    # (h)
    has_event = np.zeros(len(pv), bool)
    has_event[mpv[mpv >= 0]] = True
    ok_h = bool(((pv["clicked"].to_numpy() == "1") == has_event).all())
    req("(h) clicked = has a module event", ok_h)
    # (l)
    tg = mc["target"]
    req("(l) only documented targets", bool(tg.str.match(TARGET_RE).all()))
    is_item = tg.str.startswith("item:").to_numpy()
    is_nav = tg.str.startswith("nav:").to_numpy()
    is_link = (tg == "link:all").to_numpy()
    car = {"A": 0, "B": 1}.get(cfg.get("carousel"), -1)
    nav_ok = bool((arm[mu[is_nav]] == car).all()) if is_nav.any() else True
    nav_ok = nav_ok and (car >= 0 or not is_nav.any())
    nav_ok = nav_ok and bool((pt[mpv[is_nav]] >= t0[mu[is_nav]]).all())
    req("(l) nav: only in the carousel arm, on post-assignment pageviews", nav_ok)
    link_ok = bool((ct[is_link] >= SEE_ALL_FROM).all()) and bool((pt[mpv[is_link]] >= SEE_ALL_FROM).all())
    req("(l) link:all only from 2026-09-08", link_ok)
    meas["targets"] = dict(item=int(is_item.sum()), nav=int(is_nav.sum()), link=int(is_link.sum()),
                           nav_arm={"A": int((arm[mu[is_nav]] == 0).sum()), "B": int((arm[mu[is_nav]] == 1).sum())})
    # (j) the documented rule on all module events
    rule_le = _rule_days(mu, ct, 8, 60)
    rule_lt = _rule_days(mu, ct, 8, 59)
    rows = {(int(u), int(x // DAY) - 1) for u, x in zip(fu[is_vel], ft[is_vel])}
    req("(j) velocity rows = the documented rule on module_clicks (<= 60 s)", rows == rule_le,
        f"rows {len(rows)}, rule {len(rule_le)}, only rows {len(rows - rule_le)}, only rule {len(rule_le - rows)}")
    req("(j) the same with < 60 s", rule_lt == rule_le, f"{len(rule_lt ^ rule_le)} user-days differ")
    req("(j) one velocity row per user-day", int(is_vel.sum()) == len(rows))
    # (f)
    o = np.lexsort((ct, mu))
    us, ts = mu[o], ct[o]
    if len(ts) >= 8:
        i = np.arange(len(ts) - 7)
        same = us[i + 7] == us[i]
        span = (ts[i + 7] - ts[i])[same]
        sday = (np.floor_divide(ts[i + 7], DAY) == np.floor_divide(ts[i], DAY))[same]
        nf = int((((span >= 40) & (span <= 90)) | ((span < 40) & ~sday)).sum())
    else:
        nf = 0
    req("(f) no ambiguous 8-event window", nf == 0, f"{nf} windows")
    # (d)
    nonc = ~crawler[mu]
    m5 = is_item & nonc
    d_viol = _fires(mu[m5], ct[m5], 5, 60) if m5.any() else np.zeros(0, bool)
    req("(d) no non-crawler with 5 item events within 60 s", not d_viol.any(), f"{int(d_viol.sum())} events")
    # (c)
    vel_only = vel & ~crawler
    nav_days = _rule_days(mu[is_nav], ct[is_nav], 8, 60)
    navcnt = pd.Series(1, index=pd.MultiIndex.from_arrays([mu[is_nav], np.floor_divide(ct[is_nav], DAY)])
                       ).groupby(level=[0, 1]).sum().to_dict() if is_nav.any() else {}
    ok_c = True
    for u, d in rows:
        if not vel_only[u]:
            continue
        if not (is_hash[u] and arm[u] == car and (u, d) in nav_days and navcnt.get((u, d), 0) >= 8):
            ok_c = False
            break
    req("(c) velocity-only users: carousel-arm hash humans with 8+ nav taps (8 within 60 s) that day", ok_c)
    meas["velocity_only_users"] = {"A": int((vel_only & (arm == 0)).sum()), "B": int((vel_only & (arm == 1)).sum())}
    meas["velocity_rows"] = int(is_vel.sum())
    meas["ua_crawler_users"] = {"A": int((crawler & (arm == 0)).sum()), "B": int((crawler & (arm == 1)).sum())}
    # (e)
    early = np.zeros(N, bool)
    e_mask = ft <= t0[fu]
    early[fu[e_mask]] = True
    recount = {u for u, _d in _rule_days(mu[is_item], ct[is_item], 8, 60)}
    rec = np.zeros(N, bool)
    if recount:
        rec[list(recount)] = True
    rule_route = is_hash & ~crawler
    time_route = is_hash & ~early
    recount_route = is_hash & ~(crawler | rec)
    req("(e) rule route = time route = recount route",
        bool((rule_route == time_route).all() and (rule_route == recount_route).all()),
        f"rule {int(rule_route.sum())}, time {int(time_route.sum())}, recount {int(recount_route.sum())}")
    meas["item_recount_users"] = len(recount)
    meas["item_recount_users_all_crawlers"] = bool(crawler[list(recount)].all()) if recount else True
    # (k)
    ovr = ~is_hash
    rowcount = a_raw["user_id"].value_counts()
    ok_k = bool((rowcount.reindex(users[ovr]).to_numpy() == 1).all()) and not anyflag[ovr].any()
    req("(k) override accounts: one row, no flag", ok_k)
    meas["override_users"] = {"A": int((ovr & (arm == 0)).sum()), "B": int((ovr & (arm == 1)).sum())}
    # per-user sums and the paths
    post = pt >= t0[pu]
    item_pv = np.zeros(len(pv), bool)
    item_pv[mpv[is_item]] = True
    two_pv = np.bincount(mpv[is_item], minlength=len(pv)) >= 2
    link_pv = np.zeros(len(pv), bool)
    link_pv[mpv[is_link]] = True
    plat_pv = pv["clicked"].to_numpy() == "1"
    V = np.bincount(pu[post], minlength=N)
    C_item = np.bincount(pu[post], weights=item_pv[post], minlength=N)
    C_plat = np.bincount(pu[post], weights=plat_pv[post], minlength=N)
    allu = np.ones(N, bool)
    P = {"reference": _readout(rule_route, arm, C_item, V),
         "shipped": _readout(~anyflag, arm, C_plat, V),
         "filter_only": _readout(~crawler, arm, C_plat, V),
         "keep_overrides": _readout(~crawler, arm, C_item, V),
         "dashboard": _readout(allu, arm, C_plat, V),
         "literal_bot_filter": _readout(is_hash & ~anyflag, arm, C_item, V),
         "platform_clicked": _readout(rule_route, arm, C_plat, V),
         "not_nav_clicked": None}
    nn_pv = np.zeros(len(pv), bool)
    nn_pv[mpv[is_item | is_link]] = True
    P["not_nav_clicked"] = _readout(rule_route, arm, np.bincount(pu[post], weights=nn_pv[post], minlength=N), V)
    V_all = np.bincount(pu, minlength=N)
    C_all = np.bincount(pu, weights=plat_pv, minlength=N)
    P["dashboard_all_rows"] = _readout(allu, arm, C_all, V_all)
    na, nb = int((arm == 0).sum()), int((arm == 1).sum())
    e = (na + nb) / 2
    p_all = math.erfc(math.sqrt((((na - e) ** 2 + (nb - e) ** 2) / e) / 2))
    rows_arm = a_raw["variant"].value_counts()
    P["all_assigned"] = dict(n_users={"A": na, "B": nb}, srm_p=p_all,
                             rows={"A": int(rows_arm.get("A", 0)), "B": int(rows_arm.get("B", 0))})
    # the files' reference must equal ref_a's counts
    for key in ("n_users", "pageviews", "clicks"):
        req(f"reference {key} = ref_a", P["reference"][key] == ref[key], f"{P['reference'][key]} vs {ref[key]}")
    # (m), (n)
    rel = abs(p_all - P["reference"]["srm_p"]) / P["reference"]["srm_p"]
    req("(m) srm_all_assigned misses by >= 3% relative", rel >= ALL_ASSIGNED_MIN_REL, f"{rel:.4f}")
    req("(n) design effect >= 5.5", P["reference"]["de"] >= DE_MIN, f"{P['reference']['de']:.3f}")
    meas["srm_all_assigned_rel_miss"] = rel
    # floors (reference users, counted pageviews, per arm)
    refu = rule_route[pu]
    floors = {}
    for label, m in (("see_all_only_counted", post & link_pv & ~item_pv), ("two_item_counted", post & two_pv),
                     ("pre_assignment_item", ~post & item_pv)):
        floors[label] = {x: int((m & refu & (arm[pu] == c)).sum()) for x, c in (("A", 0), ("B", 1))}
        req(f"floor {label}", min(floors[label].values()) >= FLOOR, str(floors[label]))
    meas["floors"] = floors
    meas["pre_assignment_pageviews_ref"] = int((~post & refu).sum())
    meas["zero_view_users_ref"] = int((V[rule_route] == 0).sum())
    meas["ties_at_assigned_ref"] = int((pt == t0[pu])[refu].sum())
    return dict(failures=fails, passed=passed, paths=P, **meas)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_data, ref_a  # noqa: E402
    folder, name = sys.argv[1], sys.argv[2]
    cfg = next(c for c in gen_data.SETS if c["name"] == name)
    res = check(folder, cfg, ref_a.analyse(folder))
    print(json.dumps({k: v for k, v in res.items() if k != "paths"}, indent=1, default=float))

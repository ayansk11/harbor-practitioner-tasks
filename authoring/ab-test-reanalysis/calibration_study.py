"""Calibrate the CI band for ab-test-reanalysis on the committed data (DESIGN.md section 5, the design's "Main risk").

Run: submission/.venv/bin/python submission/authoring/ab-test-reanalysis/calibration_study.py [--seeds 200]
Reads the visible set (environment/app/data), the hidden sets as committed (tests/hidden/<set>/*.csv.gz) and the
reference values in tests/expected/<set>.json. Needs nothing that a clean checkout lacks.

All errors are bound errors in units of the reference half-width hw_ref: e = (bound - reference bound) / hw_ref.
Valid methods (the plan allows them): delta without the N/(N-1) factor; CR1 cluster-robust OLS; user-level bootstrap
with B = 2000 (the plan's minimum) for --seeds seeds, read three ways (percentile, basic, normal); B = 5000 percentile
(the alt solution's setting); pooled (not stratified) B = 2000 percentile. Wrong methods: the pageview-level interval
(attempt fix_bots_only) and the pageview-level interval times a constant K fitted on the visible data (attempt
constant_inflation). The band rule (design): band > 2 x spread of the valid methods, fix_bots_only misses by >= 2 x
band on every set, and no constant multiple of the pageview-level interval fits every set.
ICC shortcut sweep (added 2026-10-28, DESIGN.md section 13): the pageview-level variance of each arm times
1 + rho (m - 1), with one rho for every set, m = m_w = sum(v^2) / sum(v) (the weighted cluster size) or m = mean v;
rho from 0 to 1 in steps of 0.005 (and 0.0001 for the best rho). Check: no rho passes every set.
Pageview-only sweep (added 2026-10-28, DESIGN.md section 14): the pageview-level variance of each arm
times a multiplier built from that arm's pageview counts only, for 16 features f of the counts (Kish's K = mean(v^2) /
mean(v)^2, CV, tail shares, quantile ratios, Gini, share of users with no pageview, ...) in three forms, f^g (no
constant), c f^g and 1 + c f^g with c fitted so the visible readout is exact (what an agent could fit), g from -3 to 4
in steps of 0.01. Check: no form passes every set, and every form's best worst-set error is above the band. The
h_null / h_twin pair (since 2026-10-29, DESIGN.md section 15: h_twin is h_null's exact users and pageview rows with only
the clicks redrawn) is checked twice: the per-user pageview counts of each arm must be identical on the two sets (so any
multiplier computed from them is equal on both), and the smallest worst error any pair of per-arm multipliers
M_A, M_B >= 0 can reach on the two must be above the band: (r - 1) / (r + 1) with r = sqrt(q_lo) x hw_null / hw_twin,
q_lo the smaller per-arm ratio R(1-R) twin / R(1-R) null (the ratio for one common multiplier, sqrt(DE) null / sqrt(DE)
twin, is reported too).
Bootstrap margin (added in DESIGN.md section 14): for every set, bound and bootstrap group, |mean error| + 4 SD must
be below the band (the spread above is a sample maximum, so this states the margin in SDs as well).
Writes calibration_study.out.md and calibration.json next to this script.
"""
import argparse, json, math, os, sys, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ref_b  # noqa: E402

TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
SETS = ["visible", "h_null", "h_pos", "h_srm", "h_bots", "h_twin"]
Z975 = ref_b.Z975


def folder(name):
    return os.path.join(TASK, "environment", "app", "data") if name == "visible" else os.path.join(TASK, "tests", "hidden", name)


def errs(ci, ref):
    return ((ci[0] - ref["ci_95"][0]) / ref["half_width"], (ci[1] - ref["ci_95"][1]) / ref["half_width"])


def naive_ci(ref):
    ra, rb = ref["ctr"]["A"], ref["ctr"]["B"]
    va, vb = ref["pageviews"]["A"], ref["pageviews"]["B"]
    se = math.sqrt(ra * (1 - ra) / va + rb * (1 - rb) / vb)
    return ref["diff"] - Z975 * se, ref["diff"] + Z975 * se, Z975 * se


def icc_inputs(arms):
    """Per arm: CTR, pageviews, users, m_w = sum(v^2)/sum(v), mean v, and the effective rho of the delta variance."""
    out = {}
    for arm, (c, n) in arms.items():
        N, V = len(c), float(n.sum())
        R = float(c.sum()) / V
        var_pv = R * (1 - R) / V
        var_d = N / (N - 1) * float(((c - R * n) ** 2).sum()) / V ** 2
        mw = float((n ** 2).sum()) / V
        out[arm] = {"R": R, "V": V, "N": N, "mw": mw, "mbar": V / N, "var_pv": var_pv, "var_delta": var_d,
                    "rho_eff": (var_d / var_pv - 1) / (mw - 1)}
    return out


def icc_err(st, rho, m_key):
    """Worst bound error (reference half-widths) of the ICC-corrected pageview interval on one set."""
    hw = Z975 * math.sqrt(sum(a["var_pv"] * (1 + rho * (a[m_key] - 1)) for a in st["icc"].values()))
    lo, hi = st["diff"] - hw, st["diff"] + hw
    return max(abs(lo - st["ref_ci"][0]), abs(hi - st["ref_ci"][1])) / st["half_width"]


def icc_sweep(res, band, step=0.005, top=1.0, fine=0.0001):
    """For m_w and mean-v: each set's passing rho window, the intersection, the most sets one rho passes, and the rho
    that minimises the worst-set error (on the step grid and on a fine grid)."""
    grid = [round(i * step, 6) for i in range(int(round(top / step)) + 1)]
    fine_grid = [i * fine for i in range(int(round(top / fine)) + 1)]
    out = {}
    for m_key in ("mw", "mbar"):
        win, err_at = {}, {}
        for s, st in res["sets"].items():
            errs_s = [icc_err(st, r, m_key) for r in grid]
            ok = [r for r, e in zip(grid, errs_s) if e <= band]
            win[s] = [min(ok), max(ok)] if ok else None
            err_at[s] = errs_s
        n_pass = [sum(err_at[s][i] <= band for s in res["sets"]) for i in range(len(grid))]
        worst = [max(err_at[s][i] for s in res["sets"]) for i in range(len(grid))]
        i_best = min(range(len(grid)), key=lambda i: worst[i])
        r_best = grid[i_best]
        fine_worst = [(max(icc_err(st, r, m_key) for st in res["sets"].values()), r) for r in fine_grid]
        f_err, f_rho = min(fine_worst)
        all_ok = [grid[i] for i in range(len(grid)) if n_pass[i] == len(res["sets"])]
        best_count = max(n_pass)
        out[m_key] = {"grid": [0.0, top, step], "windows": win, "rho_passing_all": all_ok,
                      "max_sets_passed": best_count,
                      "rho_with_max_sets": [grid[i] for i in range(len(grid)) if n_pass[i] == best_count],
                      "best_rho": r_best, "best_worst_err": worst[i_best],
                      "best_errs": {s: err_at[s][i_best] for s in res["sets"]},
                      "fine_best_rho": round(f_rho, 4), "fine_best_worst_err": f_err}
    return out


def _gini(v):
    v = np.sort(v)
    n = len(v)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(v) / (n * v.sum()))


# features of one arm's pageview counts per counted user (v: zeros included); every one ignores the clicks
FEATURES = {
    "K = mean(v^2)/mean(v)^2": lambda v: float((v ** 2).mean() / v.mean() ** 2),
    "CV = sd/mean": lambda v: float(v.std(ddof=1) / v.mean()),
    "K over users with v > 0": lambda v: float((v[v > 0] ** 2).mean() / v[v > 0].mean() ** 2),
    "m_w = sum(v^2)/sum(v)": lambda v: float((v ** 2).sum() / v.sum()),
    "mean v": lambda v: float(v.mean()),
    "sd v": lambda v: float(v.std(ddof=1)),
    "mean v over users with v > 0": lambda v: float(v[v > 0].mean()),
    "max/mean": lambda v: float(v.max() / v.mean()),
    "p99/mean": lambda v: float(np.percentile(v, 99) / v.mean()),
    "p90/mean": lambda v: float(np.percentile(v, 90) / v.mean()),
    "median/mean": lambda v: float(max(np.median(v), 0.5) / v.mean()),
    "Gini": _gini,
    "share of views, top 1% of users": lambda v: float(np.sort(v)[-max(1, len(v) // 100):].sum() / v.sum()),
    "share of views, top 10% of users": lambda v: float(np.sort(v)[-max(1, len(v) // 10):].sum() / v.sum()),
    "share of users with no pageview": lambda v: float(max((v == 0).mean(), 1e-3)),
    "sd of log(1 + v)": lambda v: float(np.log1p(v).std(ddof=1)),
}
FORMS = ("f^g", "c f^g", "1 + c f^g")


def mult_err(st, ma, mb):
    """Worst bound error (reference half-widths) of the pageview-level interval with arm variances x ma, x mb."""
    a, b = st["icc"]["A"], st["icc"]["B"]
    hw = Z975 * math.sqrt(a["var_pv"] * ma + b["var_pv"] * mb)
    lo, hi = st["diff"] - hw, st["diff"] + hw
    return max(abs(lo - st["ref_ci"][0]), abs(hi - st["ref_ci"][1])) / st["half_width"]


def feature_sweep(res, band, g_lo=-3.0, g_hi=4.0, step=0.01):
    """Each feature and form: the g-window passing every set (or None) and the g with the smallest worst-set error."""
    grid = [round(g_lo + i * step, 4) for i in range(int(round((g_hi - g_lo) / step)) + 1)]
    vis = res["sets"]["visible"]
    target = (vis["half_width"] / Z975) ** 2                    # the visible readout's reference variance
    out = {}
    for fname in FEATURES:
        out[fname] = {}
        for form in FORMS:
            ok, best = [], (math.inf, None, None)
            for g in grid:
                fa = {s: st["feat"][fname]["A"] ** g for s, st in res["sets"].items()}
                fb = {s: st["feat"][fname]["B"] ** g for s, st in res["sets"].items()}
                base = vis["icc"]["A"]["var_pv"] * fa["visible"] + vis["icc"]["B"]["var_pv"] * fb["visible"]
                if form == "f^g":
                    c, k = 1.0, 0.0
                elif form == "c f^g":
                    c, k = target / base, 0.0
                else:
                    c, k = (target - vis["icc"]["A"]["var_pv"] - vis["icc"]["B"]["var_pv"]) / base, 1.0
                    if c < 0:
                        continue
                w = max(mult_err(st, k + c * fa[s], k + c * fb[s]) for s, st in res["sets"].items())
                if w <= band:
                    ok.append(g)
                if w < best[0]:
                    best = (w, g, c)
            out[fname][form] = {"window": [min(ok), max(ok)] if ok else None, "best_worst_err": best[0],
                                "best_g": best[1], "best_c": best[2]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--seeds-extra", type=int, default=30)
    ap.add_argument("--band", type=float, default=None, help="the band grade.py uses (checks are run at this band)")
    ap.add_argument("--reuse", action="store_true", help="re-render from calibration.json without recomputing")
    args = ap.parse_args()
    if args.reuse:
        with open(os.path.join(HERE, "calibration.json")) as f:
            res = json.load(f)
        return render(res, args, res["seeds"], res["seeds_extra"])
    t_start = time.time()
    refs = {s: json.load(open(os.path.join(TASK, "tests", "expected", s + ".json"))) for s in SETS}
    # the constant fitted on the visible data, as the constant_inflation attempt does: K = hw_delta / hw_pageview
    k_visible = round(refs["visible"]["half_width"] / naive_ci(refs["visible"])[2], 3)
    res = {"k_visible": k_visible, "seeds": args.seeds, "seeds_extra": args.seeds_extra, "sets": {}}
    pv_counts = {}
    for s in SETS:
        ref = refs[s]
        arms = ref_b.per_user(folder(s))
        pv_counts[s] = {a: arms[a][1] for a in "AB"}
        assert {a: len(v[0]) for a, v in arms.items()} == ref["n_users"], s
        assert all(int(arms[a][1].sum()) == ref["pageviews"][a] for a in "AB"), s
        d = {}
        diff = ref["diff"]
        d["delta_refb"] = errs(ref_b.delta(arms)[1:], ref)
        d["delta_no_N_factor"] = errs(ref_b.delta(arms, small_sample=False)[1:], ref)
        d["cr1"] = errs(ref_b.cr1(arms)[1:], ref)
        boot = {"percentile": [], "basic": [], "normal": []}
        for seed in range(1, args.seeds + 1):
            cis = ref_b.bootstrap_cis(diff, ref_b.bootstrap_draws(arms, 2000, seed))
            for kind, ci in cis.items():
                boot[kind].append(errs(ci, ref))
        b5000 = [errs(ref_b.bootstrap_cis(diff, ref_b.bootstrap_draws(arms, 5000, 10_000 + seed))["percentile"], ref)
                 for seed in range(args.seeds_extra)]
        pooled = [errs(ref_b.bootstrap_cis(diff, ref_b.bootstrap_draws(arms, 2000, 20_000 + seed, pooled=True))
                       ["percentile"], ref) for seed in range(args.seeds_extra)]
        lo, hi, nhw = naive_ci(ref)
        wrong = {"fix_bots_only (pageview-level CI)": errs((lo, hi), ref),
                 f"constant_inflation (K={k_visible})": errs((diff - k_visible * nhw, diff + k_visible * nhw), ref)}
        groups = {f"bootstrap B=2000 {k} ({args.seeds} seeds)": np.array(v) for k, v in boot.items()}
        groups[f"bootstrap B=5000 percentile ({args.seeds_extra} seeds)"] = np.array(b5000)
        groups[f"pooled bootstrap B=2000 percentile ({args.seeds_extra} seeds)"] = np.array(pooled)
        summary = {}
        for name, e in d.items():
            summary[name] = {"max_abs": max(abs(e[0]), abs(e[1])), "lo": e[0], "hi": e[1]}
        for name, arr in groups.items():
            summary[name] = {"max_abs": float(np.abs(arr).max()), "mean_lo": float(arr[:, 0].mean()),
                             "mean_hi": float(arr[:, 1].mean()), "sd_lo": float(arr[:, 0].std(ddof=1)),
                             "sd_hi": float(arr[:, 1].std(ddof=1))}
        res["sets"][s] = {"icc": icc_inputs(arms),
                          "feat": {f: {a: fn(arms[a][1]) for a in ("A", "B")} for f, fn in FEATURES.items()},
                          "diff": diff, "ref_ci": ref["ci_95"], "half_width": ref["half_width"],
                          "de": (ref["half_width"] / nhw) ** 2, "sqrt_de": ref["half_width"] / nhw,
                          "lower_over_hw": ref["ci_95"][0] / ref["half_width"], "srm_p": ref["srm_p"],
                          "decision": ref["decision"], "valid": summary,
                          "wrong": {k: {"lo": v[0], "hi": v[1], "max_abs": max(abs(v[0]), abs(v[1]))}
                                    for k, v in wrong.items()}}
        print(f"{s}: done ({time.time() - t_start:.0f} s)", flush=True)
    if "h_null" in pv_counts and "h_twin" in pv_counts:
        res["twin_identical_counts"] = all(np.array_equal(pv_counts["h_null"][a], pv_counts["h_twin"][a]) for a in "AB")
    res["seconds"] = round(time.time() - t_start, 1)
    with open(os.path.join(HERE, "calibration.json"), "w") as f:
        json.dump(res, f, indent=1)
    return render(res, args, args.seeds, args.seeds_extra)


def render(res, args, seeds, seeds_extra):
    k_visible = res["k_visible"]
    spread = max(v["max_abs"] for st in res["sets"].values() for v in st["valid"].values())
    rule_band = math.ceil(2 * spread * 100 + 1e-9) / 100     # next whole percent strictly above 2 x spread
    if rule_band <= 2 * spread:
        rule_band += 0.01
    band = args.band if args.band is not None else rule_band
    fbo = {s: st["wrong"]["fix_bots_only (pageview-level CI)"]["max_abs"] for s, st in res["sets"].items()}
    r = [st["sqrt_de"] for st in res["sets"].values()]
    minimax = (max(r) - min(r)) / (max(r) + min(r))           # best any constant K can do (its worst set error)
    margins = {s: abs(st["lower_over_hw"]) for s, st in res["sets"].items()}
    res.update(spread=spread, rule_band=rule_band, band=band, fix_bots_only_min=min(fbo.values()),
               minimax_constant_error=minimax, min_decision_margin=min(margins.values()))
    icc = res["icc_sweep"] = icc_sweep(res, band)
    fs = res["feature_sweep"] = feature_sweep(res, band)
    fs_open = [(f, form) for f, v in fs.items() for form, r in v.items() if r["window"]]
    fs_min = min((r["best_worst_err"], f, form) for f, v in fs.items() for form, r in v.items())
    twin = None
    if "h_null" in res["sets"] and "h_twin" in res["sets"]:
        n, t = res["sets"]["h_null"], res["sets"]["h_twin"]
        rr = n["sqrt_de"] / t["sqrt_de"]
        q = {a: t["icc"][a]["R"] * (1 - t["icc"][a]["R"]) / (n["icc"][a]["R"] * (1 - n["icc"][a]["R"])) for a in "AB"}
        rm = math.sqrt(min(q.values())) * n["half_width"] / t["half_width"]
        twin = res["twin_pair"] = {"sqrt_de_ratio": rr, "common_multiplier_min_err": (rr - 1) / (rr + 1),
                                   "identical_counts": res.get("twin_identical_counts"), "q": q,
                                   "hw_ratio": n["half_width"] / t["half_width"], "per_arm_r": rm,
                                   "per_arm_min_err": (rm - 1) / (rm + 1)}
    # bootstrap margin in SDs: |mean| + 4 SD per bound, set and bootstrap group (the spread above is a sample maximum)
    m4 = max(max(abs(v["mean_lo"]) + 4 * v["sd_lo"], abs(v["mean_hi"]) + 4 * v["sd_hi"])
             for st in res["sets"].values() for v in st["valid"].values() if "sd_lo" in v)
    res["boot_mean_plus_4sd"] = m4
    checks = {
        "band > 2 x spread": band > 2 * spread,
        "fix_bots_only misses by >= 2 x band on every set": min(fbo.values()) >= 2 * band,
        "no constant K fits every set (best K's worst error > band)": minimax > band,
        "ICC shortcut, m = sum(v^2)/sum(v): no rho in [0, 1] passes every set (best rho's worst error > band)":
            not icc["mw"]["rho_passing_all"] and icc["mw"]["fine_best_worst_err"] > band,
        "ICC shortcut, m = mean pageviews per user: no rho in [0, 1] passes every set":
            not icc["mbar"]["rho_passing_all"] and icc["mbar"]["fine_best_worst_err"] > band,
        f"pageview-only multipliers ({len(FEATURES)} features x {len(FORMS)} forms): none passes every set "
        "(every form's best worst-set error > band)": not fs_open and fs_min[0] > band,
        "valid bootstrap: |mean| + 4 SD of the bound error < band for every set, bound and group": m4 < band,
        "h_null / h_twin: identical per-user pageview counts per arm, and any per-arm multipliers M_A, M_B >= 0 from "
        "them miss one of the two by more than the band": bool(twin and twin["identical_counts"]
                                                              and twin["per_arm_min_err"] > band),
        "every decision bound >= 0.35 hw from 0, and farther than band": min(margins.values()) >= max(0.35, band),
        "SRM set: 1e-12 < srm_p < 0.001; other sets srm_p >= 0.05":
            all((1e-12 < st["srm_p"] < 1e-3) if s == "h_srm" else st["srm_p"] >= 0.05 for s, st in res["sets"].items()),
    }
    res["checks"] = checks
    with open(os.path.join(HERE, "calibration.json"), "w") as f:
        json.dump(res, f, indent=1)
    L = ["# calibration_study.out.md (calibration_study.py)", "",
         f"Bound errors in reference half-widths (reference = delta method in tests/expected/). Seeds: B=2000 x "
         f"{seeds}; B=5000 and pooled x {seeds_extra}. Run time {res['seconds']} s.", "",
         "## Per set", "",
         "| set | DE | sqrt(DE) | lower/hw | SRM p | decision | max valid error | fix_bots_only error | "
         f"constant_inflation error (K={k_visible}) |", "|---|---|---|---|---|---|---|---|---|"]
    for s, st in res["sets"].items():
        mv = max(v["max_abs"] for v in st["valid"].values())
        w = list(st["wrong"].values())
        L.append(f"| {s} | {st['de']:.2f} | {st['sqrt_de']:.3f} | {st['lower_over_hw']:+.3f} | {st['srm_p']:.3g} | "
                 f"{st['decision']} | {mv:.4f} | {w[0]['max_abs']:.4f} | {w[1]['max_abs']:.4f} |")
    L += ["", "## Valid methods, worst bound error per set", "",
          "| method | " + " | ".join(SETS) + " |", "|---|" + "---|" * len(SETS)]
    for name in res["sets"]["visible"]["valid"]:
        L.append(f"| {name} | " + " | ".join(f"{res['sets'][s]['valid'][name]['max_abs']:.4f}" for s in SETS) + " |")
    L += ["", "Bootstrap B=2000 percentile, mean and SD of the bound error (lo; hi):", ""]
    key = f"bootstrap B=2000 percentile ({seeds} seeds)"
    for s in SETS:
        v = res["sets"][s]["valid"][key]
        L.append(f"- {s}: lo mean {v['mean_lo']:+.4f} sd {v['sd_lo']:.4f}; hi mean {v['mean_hi']:+.4f} "
                 f"sd {v['sd_hi']:.4f}")
    L += ["", "## Band", "",
          f"- spread (worst valid-method bound error, all sets; a sample maximum over the seeds): {spread:.4f}",
          f"- bootstrap |mean| + 4 SD (worst set, bound and group): {m4:.4f} (needs < band)",
          f"- rule band (next whole percent strictly above 2 x spread): {rule_band:.2f}",
          f"- band checked below (the one grade.py uses): {band:.2f}",
          f"- fix_bots_only, smallest miss over the sets: {min(fbo.values()):.4f} (needs >= 2 x band = {2 * band:.2f})",
          f"- best constant K, worst-set error: {minimax:.4f} (needs > band)",
          f"- smallest decision margin |lower|/hw: {min(margins.values()):.3f} (needs >= max(0.35, band))", "",
          "## ICC shortcut sweep", "",
          "Interval = diff +/- z sqrt(sum over arms of R(1-R)/V x (1 + rho (m - 1))), one rho for all sets; bound error in "
          f"reference half-widths; a set passes when both errors <= {band:.2f}. rho_eff = (Var_delta / Var_pageview - 1) "
          "/ (m_w - 1) per arm (A/B).", "",
          "| set | m_w A/B | mean v A/B | rho_eff A/B | passing rho, m = m_w | passing rho, m = mean v |",
          "|---|---|---|---|---|---|"]
    for s, st in res["sets"].items():
        a, b = st["icc"]["A"], st["icc"]["B"]
        w1, w2 = icc["mw"]["windows"][s], icc["mbar"]["windows"][s]
        L.append(f"| {s} | {a['mw']:.1f} / {b['mw']:.1f} | {a['mbar']:.2f} / {b['mbar']:.2f} | "
                 f"{a['rho_eff']:.3f} / {b['rho_eff']:.3f} | {'%.3f to %.3f' % tuple(w1) if w1 else 'none'} | "
                 f"{'%.3f to %.3f' % tuple(w2) if w2 else 'none'} |")
    for m_key, label in (("mw", "m = m_w"), ("mbar", "m = mean v")):
        v = icc[m_key]
        rr = v["rho_with_max_sets"]
        L += ["", f"{label} (rho {v['grid'][0]} to {v['grid'][1]}, step {v['grid'][2]}):",
              f"- rho passing every set: {v['rho_passing_all'] or 'none'}",
              f"- most sets passed by one rho: {v['max_sets_passed']} of {len(res['sets'])} "
              f"(rho {rr[0]:.3f} to {rr[-1]:.3f})",
              f"- best rho (smallest worst-set error) on the grid: {v['best_rho']:.3f}, worst error "
              f"{v['best_worst_err']:.4f}; per set: " + ", ".join(f"{s} {e:.3f}" for s, e in v["best_errs"].items()),
              f"- best rho on a 0.0001 grid: {v['fine_best_rho']:.4f}, worst error {v['fine_best_worst_err']:.4f}"]
    L += ["", "## Pageview-only sweep", "",
          "Interval = diff +/- z sqrt(sum over arms of R(1-R)/V x M), M built from the arm's pageview counts only: "
          "f^g, c f^g or 1 + c f^g, c fitted so the visible readout is exact, g from -3 to 4 step 0.01. A form passes "
          f"when one g passes every set (both bound errors <= {band:.2f}).", "",
          "| feature | visible A/B | h_null A/B | " + ("h_twin A/B | " if twin else "") +
          " | ".join(f"{fm}: passing g / best worst error (g)" for fm in FORMS) + " |",
          "|---|---|---|" + ("---|" if twin else "") + "---|" * len(FORMS)]
    for f, v in fs.items():
        vals = [res["sets"][s]["feat"][f] for s in (["visible", "h_null"] + (["h_twin"] if twin else []))]
        cells = []
        for fm in FORMS:
            r = v[fm]
            w = "%.2f to %.2f" % tuple(r["window"]) if r["window"] else "none"
            cells.append(f"{w} / {r['best_worst_err']:.3f} ({r['best_g']})")
        L.append(f"| {f} | " + " | ".join(f"{x['A']:.3g} / {x['B']:.3g}" for x in vals) + " | " + " | ".join(cells) + " |")
    L += ["", f"- forms passing every set: {', '.join(f'{f} [{fm}]' for f, fm in fs_open) or 'none'}",
          f"- smallest best worst-set error over all forms: {fs_min[0]:.4f} ({fs_min[1]}, {fs_min[2]})"]
    if twin:
        L += [f"- h_null / h_twin: per-user pageview counts of each arm identical: {twin['identical_counts']}; "
              f"sqrt(DE) ratio {twin['sqrt_de_ratio']:.4f}, so one common multiplier on both misses one of them by at "
              f"least {twin['common_multiplier_min_err']:.4f} half-widths; per-arm multipliers M_A, M_B >= 0: "
              f"q = R(1-R) twin / null A {twin['q']['A']:.4f}, B {twin['q']['B']:.4f}, r = sqrt(q_lo) x "
              f"{twin['hw_ratio']:.4f} = {twin['per_arm_r']:.4f}, minimum miss {twin['per_arm_min_err']:.4f} half-widths"]
    L += ["", "## Checks", ""] + [f"- {'PASS' if ok else 'FAIL'}: {name}" for name, ok in checks.items()]
    with open(os.path.join(HERE, "calibration_study.out.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())

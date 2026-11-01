"""Calibrate the CI band of ab-test-reanalysis on the committed data (the revision's design, section 9 "Band").

Run: submission/.venv/bin/python -I -B submission/authoring/ab-test-reanalysis/calibration_study.py [--seeds 200]
Reads the visible export (environment/app/data), the five hidden exports as committed (tests/hidden/<set>/*.csv.gz),
the reference readouts (tests/expected/<set>.json, ref_a, delta method) and the band of tests/grade.py (BAND). Per
user clicks and counted pageviews come from ref_b.per_user (the time route, which equals ref_a's population on every
set by the generator's assertion e); the script asserts that they reproduce each reference's n_users, pageviews and
clicks exactly. Needs nothing that a clean checkout lacks.

All errors are bound errors in units of the reference half-width hw: e = (bound - reference bound) / hw.
Plan methods (EXPERIMENT.md section 5; the binding gate is computed over these only):
  delta, recomputed by ref_b (with the N/(N-1) factor, as the reference) and without that factor;
  CR1, pageview-level OLS of clicked on a B indicator with cluster-robust errors by user;
  user bootstrap within each arm, percentile: B = 2,000 (the plan's minimum) for --seeds seeds, and B = 5,000 (the
  alt_time solution's setting) for --seeds-extra seeds.
Other readings, not plan methods (reported, never gating): bootstrap B = 2,000 read as basic and normal intervals;
pooled (not within-arm) bootstrap B = 2,000 percentile.
Wrong method (the attempt pageview_ci): the pageview-level interval, each pageview an independent trial.
Binding gates (the design: the 0.25 band stays only if both hold; otherwise the data changes, never the band):
  1. the worst plan-method bound error over every set, bound and seed is <= band / 2 (0.125 at band 0.25);
  2. pageview_ci's smallest miss over the sets (per set, the larger of its two bound errors) is >= 2 x band (0.5).
Data conditions re-checked here (the generator's seed conditions that the band relies on): every reference lower bound
at least 0.5 hw from 0 (a bound inside the band cannot flip a decision); srm_p in (1e-11, 1e-5) on h_srm and >= 0.05
elsewhere; DE >= 5.5 on every set.
Information only (no gate; the revised design drops the multiplier attempts, since the shipped CI is correct): the
bootstrap's |mean| + 4 SD of the bound error; the best constant multiple K of the pageview-level interval; the ICC
shortcut sweep (one rho for every set, m = sum(v^2)/sum(v) or mean v); the pageview-only multiplier sweep (16 features
of each arm's pageview counts x 3 forms).
Writes calibration_study.out.md and calibration.json next to this script; exit 0 only if the binding gates and the
data conditions pass.
"""
import argparse, json, math, os, re, sys, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ref_b  # noqa: E402

TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
SETS = ["visible", "h_null", "h_pos", "h_srm", "h_plain", "h_neg"]
Z975 = ref_b.Z975
PV = "pageview_ci (pageview-level interval)"


def folder(name):
    return os.path.join(TASK, "environment", "app", "data") if name == "visible" else os.path.join(TASK, "tests", "hidden", name)


def grade_band():
    """The band tests/grade.py uses (its BAND line), read as text so that the grader's kit is never imported."""
    with open(os.path.join(TASK, "tests", "grade.py"), encoding="utf-8") as f:
        m = re.search(r"^BAND = ([0-9.]+)", f.read(), re.M)
    if not m:
        raise SystemExit("no BAND line in tests/grade.py")
    return float(m.group(1))


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
        fine_worst = [(max(icc_err(st, r, m_key) for st in res["sets"].values()), r) for r in fine_grid]
        f_err, f_rho = min(fine_worst)
        all_ok = [grid[i] for i in range(len(grid)) if n_pass[i] == len(res["sets"])]
        best_count = max(n_pass)
        out[m_key] = {"grid": [0.0, top, step], "windows": win, "rho_passing_all": all_ok,
                      "max_sets_passed": best_count,
                      "rho_with_max_sets": [grid[i] for i in range(len(grid)) if n_pass[i] == best_count],
                      "best_rho": grid[i_best], "best_worst_err": worst[i_best],
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


def method_names(seeds, seeds_extra):
    plan = ["delta (ref_b, N/(N-1) factor)", "delta without the N/(N-1) factor", "CR1 by user",
            f"bootstrap B=2000 percentile ({seeds} seeds)", f"bootstrap B=5000 percentile ({seeds_extra} seeds)"]
    other = [f"bootstrap B=2000 basic ({seeds} seeds)", f"bootstrap B=2000 normal ({seeds} seeds)",
             f"pooled bootstrap B=2000 percentile ({seeds_extra} seeds)"]
    return plan, other


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--seeds-extra", type=int, default=30)
    ap.add_argument("--band", type=float, default=None, help="default: the BAND of tests/grade.py")
    ap.add_argument("--reuse", action="store_true", help="re-render from calibration.json without recomputing")
    args = ap.parse_args()
    if args.reuse:
        with open(os.path.join(HERE, "calibration.json")) as f:
            res = json.load(f)
        return render(res, args, res["seeds"], res["seeds_extra"])
    t_start = time.time()
    started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    refs = {}
    for s in SETS:
        with open(os.path.join(TASK, "tests", "expected", s + ".json")) as f:
            refs[s] = json.load(f)
    # the constant fitted on the visible data (information only): K = hw_delta / hw_pageview
    k_visible = round(refs["visible"]["half_width"] / naive_ci(refs["visible"])[2], 3)
    plan_names, other_names = method_names(args.seeds, args.seeds_extra)
    res = {"k_visible": k_visible, "seeds": args.seeds, "seeds_extra": args.seeds_extra, "started": started,
           "plan_methods": plan_names, "other_methods": other_names, "sets": {}}
    for s in SETS:
        t_set = time.time()
        ref = refs[s]
        arms = ref_b.per_user(folder(s))
        assert {a: len(v[0]) for a, v in arms.items()} == ref["n_users"], s
        assert all(int(arms[a][1].sum()) == ref["pageviews"][a] for a in "AB"), s
        assert all(int(arms[a][0].sum()) == ref["clicks"][a] for a in "AB"), s
        diff = ref["diff"]
        point = {plan_names[0]: errs(ref_b.delta(arms)[1:], ref),
                 plan_names[1]: errs(ref_b.delta(arms, small_sample=False)[1:], ref),
                 plan_names[2]: errs(ref_b.cr1(arms)[1:], ref)}
        boot = {"percentile": [], "basic": [], "normal": []}
        for seed in range(1, args.seeds + 1):
            cis = ref_b.bootstrap_cis(diff, ref_b.bootstrap_draws(arms, 2000, seed))
            for kind, ci in cis.items():
                boot[kind].append(errs(ci, ref))
        b5000 = [errs(ref_b.bootstrap_cis(diff, ref_b.bootstrap_draws(arms, 5000, 10_000 + seed))["percentile"], ref)
                 for seed in range(args.seeds_extra)]
        pooled = [errs(ref_b.bootstrap_cis(diff, ref_b.bootstrap_draws(arms, 2000, 20_000 + seed, pooled=True))
                       ["percentile"], ref) for seed in range(args.seeds_extra)]
        groups = {plan_names[3]: np.array(boot["percentile"]), plan_names[4]: np.array(b5000),
                  other_names[0]: np.array(boot["basic"]), other_names[1]: np.array(boot["normal"]),
                  other_names[2]: np.array(pooled)}
        summary = {}
        for name, e in point.items():
            summary[name] = {"max_abs": max(abs(e[0]), abs(e[1])), "lo": e[0], "hi": e[1]}
        for name, arr in groups.items():
            summary[name] = {"max_abs": float(np.abs(arr).max()), "mean_lo": float(arr[:, 0].mean()),
                             "mean_hi": float(arr[:, 1].mean()), "sd_lo": float(arr[:, 0].std(ddof=1)),
                             "sd_hi": float(arr[:, 1].std(ddof=1)), "n": int(len(arr))}
        lo, hi, nhw = naive_ci(ref)
        wrong = {PV: errs((lo, hi), ref),
                 f"constant K={k_visible} (fitted on visible; information)": errs((diff - k_visible * nhw,
                                                                                    diff + k_visible * nhw), ref)}
        res["sets"][s] = {"icc": icc_inputs(arms),
                          "feat": {f: {a: fn(arms[a][1]) for a in ("A", "B")} for f, fn in FEATURES.items()},
                          "diff": diff, "ref_ci": ref["ci_95"], "half_width": ref["half_width"],
                          "de": (ref["half_width"] / nhw) ** 2, "sqrt_de": ref["half_width"] / nhw,
                          "lower_over_hw": ref["ci_95"][0] / ref["half_width"],
                          "upper_over_hw": ref["ci_95"][1] / ref["half_width"], "srm_p": ref["srm_p"],
                          "decision": ref["decision"], "n_users": ref["n_users"], "methods": summary,
                          "wrong": {k: {"lo": v[0], "hi": v[1], "max_abs": max(abs(v[0]), abs(v[1]))}
                                    for k, v in wrong.items()},
                          "seconds": round(time.time() - t_set, 1)}
        print(f"{s}: done ({time.time() - t_start:.0f} s)", flush=True)
    res["seconds"] = round(time.time() - t_start, 1)
    res["finished"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    with open(os.path.join(HERE, "calibration.json"), "w") as f:
        json.dump(res, f, indent=1)
    return render(res, args, args.seeds, args.seeds_extra)


def render(res, args, seeds, seeds_extra):
    plan, other = res["plan_methods"], res["other_methods"]
    band = args.band if args.band is not None else grade_band()
    sets = res["sets"]
    worst_plan = {s: max(st["methods"][m]["max_abs"] for m in plan) for s, st in sets.items()}
    worst_other = {s: max(st["methods"][m]["max_abs"] for m in other) for s, st in sets.items()}
    spread = max(worst_plan.values())
    spread_at = max(worst_plan, key=worst_plan.get)
    pv_miss = {s: st["wrong"][PV]["max_abs"] for s, st in sets.items()}
    r = [st["sqrt_de"] for st in sets.values()]
    minimax = (max(r) - min(r)) / (max(r) + min(r))           # best any constant K can do (its worst set error)
    margins = {s: abs(st["lower_over_hw"]) for s, st in sets.items()}
    m4 = max(max(abs(v["mean_lo"]) + 4 * v["sd_lo"], abs(v["mean_hi"]) + 4 * v["sd_hi"])
             for st in sets.values() for name, v in st["methods"].items() if name in plan and "sd_lo" in v)
    res.update(band=band, spread_plan=spread, spread_plan_set=spread_at, worst_other=max(worst_other.values()),
               pageview_ci_min_miss=min(pv_miss.values()), minimax_constant_error=minimax,
               min_decision_margin=min(margins.values()), boot_plan_mean_plus_4sd=m4)
    icc = res["icc_sweep"] = icc_sweep(res, band)
    fs = res["feature_sweep"] = feature_sweep(res, band)
    fs_open = [(f, form) for f, v in fs.items() for form, x in v.items() if x["window"]]
    fs_min = min((x["best_worst_err"], f, form) for f, v in fs.items() for form, x in v.items())
    gates = {
        f"worst plan-method bound error <= band / 2 = {band / 2:.3f} (every set, bound and seed)": spread <= band / 2,
        f"pageview_ci smallest miss over the sets >= 2 x band = {2 * band:.2f}": min(pv_miss.values()) >= 2 * band,
    }
    data = {
        "every reference lower bound >= 0.5 hw from 0": min(margins.values()) >= 0.5,
        "h_srm: 1e-11 < srm_p < 1e-5; every other set: srm_p >= 0.05":
            all((1e-11 < st["srm_p"] < 1e-5) if s == "h_srm" else st["srm_p"] >= 0.05 for s, st in sets.items()),
        "DE >= 5.5 on every set": min(st["de"] for st in sets.values()) >= 5.5,
    }
    info = {
        f"other readings (basic, normal, pooled) worst error <= band / 2": max(worst_other.values()) <= band / 2,
        "plan bootstrap |mean| + 4 SD of the bound error < band (every set, bound and group)": m4 < band,
        "no constant K of the pageview interval fits every set (best K's worst error > band)": minimax > band,
        "ICC shortcut, m = m_w: no rho in [0, 1] passes every set":
            not icc["mw"]["rho_passing_all"] and icc["mw"]["fine_best_worst_err"] > band,
        "ICC shortcut, m = mean v: no rho in [0, 1] passes every set":
            not icc["mbar"]["rho_passing_all"] and icc["mbar"]["fine_best_worst_err"] > band,
        f"pageview-only multipliers ({len(FEATURES)} features x {len(FORMS)} forms): none passes every set":
            not fs_open and fs_min[0] > band,
    }
    res["gates"], res["data_conditions"], res["information"] = gates, data, info
    with open(os.path.join(HERE, "calibration.json"), "w") as f:
        json.dump(res, f, indent=1)
    L = ["# calibration_study.out.md (calibration_study.py)", "",
         f"Bound errors in reference half-widths hw (reference = ref_a's delta method, tests/expected/). Band {band:g} "
         f"(tests/grade.py). Seeds: B=2000 x {seeds}; B=5000 and pooled x {seeds_extra}. Run {res.get('started')} to "
         f"{res.get('finished')} (Mac clock), {res['seconds']} s by the script's timer.", "",
         "## Per set", "",
         "| set | n_users A/B | DE | sqrt(DE) | lower/hw | upper/hw | srm_p | decision | worst plan-method error | "
         "worst other reading | pageview_ci miss | s |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s, st in sets.items():
        L.append(f"| {s} | {st['n_users']['A']}/{st['n_users']['B']} | {st['de']:.2f} | {st['sqrt_de']:.3f} | "
                 f"{st['lower_over_hw']:+.3f} | {st['upper_over_hw']:+.3f} | {st['srm_p']:.4g} | {st['decision']} | "
                 f"{worst_plan[s]:.4f} | {worst_other[s]:.4f} | {pv_miss[s]:.4f} | {st['seconds']} |")
    L += ["", "## Worst bound error per method and set", "",
          "| method | plan method | " + " | ".join(SETS) + " |", "|---|---|" + "---|" * len(SETS)]
    for name in plan + other:
        L.append(f"| {name} | {'yes' if name in plan else 'no'} | " +
                 " | ".join(f"{sets[s]['methods'][name]['max_abs']:.4f}" for s in SETS) + " |")
    for name in sets["visible"]["wrong"]:
        L.append(f"| {name} | no (wrong) | " + " | ".join(f"{sets[s]['wrong'][name]['max_abs']:.4f}" for s in SETS)
                 + " |")
    L += ["", "Plan bootstrap groups, mean and SD of the bound error (lo; hi):", ""]
    for name in plan[3:]:
        for s in SETS:
            v = sets[s]["methods"][name]
            L.append(f"- {name}, {s}: lo mean {v['mean_lo']:+.4f} sd {v['sd_lo']:.4f}; hi mean {v['mean_hi']:+.4f} "
                     f"sd {v['sd_hi']:.4f}")
    L += ["", "## Band", "",
          f"- worst plan-method bound error (all sets, bounds and seeds; a sample maximum): {spread:.4f} ({spread_at}); "
          f"needs <= {band / 2:.3f}",
          f"- pageview_ci, smallest miss over the sets: {min(pv_miss.values()):.4f} "
          f"({min(pv_miss, key=pv_miss.get)}); needs >= {2 * band:.2f}",
          f"- other readings (not plan methods), worst error: {max(worst_other.values()):.4f}",
          f"- plan bootstrap |mean| + 4 SD (worst set, bound and group): {m4:.4f}",
          f"- best constant K of the pageview interval, worst-set error: {minimax:.4f}",
          f"- smallest decision margin |lower|/hw: {min(margins.values()):.3f} ({min(margins, key=margins.get)})", "",
          "## ICC shortcut sweep (information)", "",
          "Interval = diff +/- z sqrt(sum over arms of R(1-R)/V x (1 + rho (m - 1))), one rho for all sets; a set "
          f"passes when both bound errors are <= {band:g}. rho_eff = (Var_delta / Var_pageview - 1) / (m_w - 1).", "",
          "| set | m_w A/B | mean v A/B | rho_eff A/B | passing rho, m = m_w | passing rho, m = mean v |",
          "|---|---|---|---|---|---|"]
    for s, st in sets.items():
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
              f"- most sets passed by one rho: {v['max_sets_passed']} of {len(sets)} (rho {rr[0]:.3f} to {rr[-1]:.3f})",
              f"- best rho on the grid: {v['best_rho']:.3f}, worst error {v['best_worst_err']:.4f}; per set: " +
              ", ".join(f"{s} {e:.3f}" for s, e in v["best_errs"].items()),
              f"- best rho on a 0.0001 grid: {v['fine_best_rho']:.4f}, worst error {v['fine_best_worst_err']:.4f}"]
    L += ["", "## Pageview-only multiplier sweep (information)", "",
          "Interval = diff +/- z sqrt(sum over arms of R(1-R)/V x M), M from the arm's pageview counts only: f^g, c f^g "
          "or 1 + c f^g, c fitted so the visible readout is exact, g from -3 to 4 step 0.01; a form passes when one g "
          f"passes every set (both bound errors <= {band:g}).", "",
          "| feature | visible A/B | h_null A/B | " + " | ".join(f"{fm}: passing g / best worst error (g)" for fm in FORMS)
          + " |", "|---|---|---|" + "---|" * len(FORMS)]
    for f, v in fs.items():
        vals = [sets[s]["feat"][f] for s in ("visible", "h_null")]
        cells = []
        for fm in FORMS:
            x = v[fm]
            w = "%.2f to %.2f" % tuple(x["window"]) if x["window"] else "none"
            cells.append(f"{w} / {x['best_worst_err']:.3f} ({x['best_g']})")
        L.append(f"| {f} | " + " | ".join(f"{x['A']:.3g} / {x['B']:.3g}" for x in vals) + " | " + " | ".join(cells) + " |")
    L += ["", f"- forms passing every set: {', '.join(f'{f} [{fm}]' for f, fm in fs_open) or 'none'}",
          f"- smallest best worst-set error over all forms: {fs_min[0]:.4f} ({fs_min[1]}, {fs_min[2]})",
          "", "## Binding gates (the design: the band stays only if both pass; else change the data, never the band)", ""]
    L += [f"- {'PASS' if ok else 'FAIL'}: {name}" for name, ok in gates.items()]
    L += ["", "## Data conditions (re-checked)", ""] + [f"- {'PASS' if ok else 'FAIL'}: {n}" for n, ok in data.items()]
    L += ["", "## Information (no gate)", ""] + [f"- {'yes' if ok else 'no'}: {n}" for n, ok in info.items()]
    ok_all = all(gates.values()) and all(data.values())
    L += ["", "RESULT: " + ("BAND KEPT (all binding gates and data conditions pass)" if ok_all else
                            "BAND NOT SUPPORTED BY THIS DATA (change the data, never the band)")]
    with open(os.path.join(HERE, "calibration_study.out.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[-20:]))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

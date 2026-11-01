# Pre-revision record (status line added 2026-10-31): made for the first version of this task (commit 495c9f5 or
# earlier); it reads the first version's six sets, h_bots and h_twin among them, which the revision removed or
# replaced, so it no longer runs. The section numbers it cites are those of that version's design record (git show
# 495c9f5:docs/ab-test-reanalysis/DESIGN.md). Kept as history; the revision's records are
# calibration_study.out.md, generation_report.out.md and local_check.out.md.
"""Probes of interval rules that use the clicks (DESIGN.md limitation 9(c)-(d) and section 16; authoring only).

The twin pair h_null / h_twin closes every rule built from the pageview data alone (DESIGN.md section 15). This script
measures the rules outside that proof: (1) user-level click-dispersion estimates of the design effect, (2) rules built
from arm-level click aggregates (CTRs, diff, relative lift), and (3) the per-arm bound of section 15 for other variance
bases. Parts 1-3 use a fast evaluator: with the exact diff of the canonical code, a bound error is |w / H - 1| for a
half-width w against the reference half-width H. Part 4 runs chosen rules through the real grader: environment/app +
solution/canonical + the probe's stats.py, the visible readout regenerated, the /app copy rules, tests/grade.py in
KIT_LOCAL mode (as local_check.py). Run dirs: .localruns/probes/ (git-ignored). Reads the committed files only.
Run: submission/.venv/bin/python submission/authoring/ab-test-reanalysis/click_rule_probes.py
Writes click_rule_probes.out.md next to this file.
"""
import gzip, itertools, json, os, shutil, subprocess, sys, tempfile, time

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
TESTS = os.path.join(TASK, "tests")
PY = sys.executable
SETS = ("visible", "h_null", "h_pos", "h_srm", "h_bots", "h_twin")
Z = 1.959963984540054
BAND = 0.25
E = {s: json.load(open(os.path.join(TESTS, "expected", s + ".json"))) for s in SETS}
H = np.array([E[s]["half_width"] for s in SETS])
lH = np.log(H)


def per_user():
    """Per-user clicks and views of the counted users, by the canonical solution's own code, on all six sets."""
    tmp = tempfile.mkdtemp(prefix="probes_")
    try:
        shutil.copytree(os.path.join(TASK, "environment", "app", "abtest"), os.path.join(tmp, "abtest"))
        for f in ("filters.py", "stats.py", "report.py"):
            shutil.copy(os.path.join(TASK, "solution", "canonical", f), os.path.join(tmp, "abtest", f))
        sys.path.insert(0, tmp)
        from abtest.filters import exclude_bots
        from abtest.load import load_assignments, load_pageviews, load_users
        from abtest.report import per_user_counts
        out = {}
        for s in SETS:
            if s == "visible":
                d = os.path.join(TASK, "environment", "app", "data")
            else:
                d = os.path.join(tmp, "sets", s)
                os.makedirs(d)
                for f in ("assignments", "users", "pageviews"):
                    with gzip.open(os.path.join(TESTS, "hidden", s, f + ".csv.gz"), "rb") as g, \
                            open(os.path.join(d, f + ".csv"), "wb") as h:
                        shutil.copyfileobj(g, h)
            a = exclude_bots(load_assignments(d), load_users(d))
            pu = per_user_counts(a, load_pageviews(d, a))
            for arm in "AB":
                x = pu[pu["variant"] == arm]
                c, v = x["clicks"].to_numpy(float), x["views"].to_numpy(float)
                assert (len(c), c.sum(), v.sum()) == (E[s]["n_users"][arm], E[s]["clicks"][arm],
                                                      E[s]["pageviews"][arm]), (s, arm)
                out[s, arm] = (c, v)
        return out
    finally:
        sys.path.remove(tmp)
        shutil.rmtree(tmp, ignore_errors=True)


P = per_user()


def hw(var_fn):
    """Half-width per set for a rule var_fn(c, v) -> variance of the arm's CTR."""
    return np.array([Z * np.sqrt(sum(var_fn(*P[s, a]) for a in "AB")) for s in SETS])


def errs(w):
    return np.abs(w / H - 1)


def delta(c, v):
    n, r = len(c), c.sum() / v.sum()
    return n / (n - 1) * np.sum((c - r * v) ** 2) / v.sum() ** 2


def pv(c, v):
    r = c.sum() / v.sum()
    return r * (1 - r) / v.sum()


def disp(k):
    """Per-user CTR variance among users with >= k views over its binomial value, times the pageview variance."""
    def f(c, v):
        r, m = c.sum() / v.sum(), v >= k
        return pv(c, v) * np.var(c[m] / v[m], ddof=1) / np.mean(r * (1 - r) / v[m])
    return f


def disp_feat(c, v, k, kind):
    r, m = c.sum() / v.sum(), v >= k
    if kind == "zzb":           # share of users with no click / its binomial value, users with >= k views
        return np.mean(c[m] == 0) / np.mean((1 - r) ** v[m])
    return np.var(c[m] / v[m]) / np.mean(r * (1 - r) / v[m])


def anova(c, v):
    """One-way ANOVA ICC of the clicks within users (users with a view), and Kish's 1 + rho (m_w - 1)."""
    r, m = c.sum() / v.sum(), v > 0
    c1, v1 = c[m], v[m]
    n, V = len(v1), v1.sum()
    msb = np.sum((c1 - r * v1) ** 2 / v1) / (n - 1)
    msw = np.sum(c1 * (1 - c1 / v1)) / (V - n)
    n0 = (V - np.sum(v1 ** 2) / V) / (n - 1)
    rho = (msb - msw) / (msb + (n0 - 1) * msw)
    return pv(c, v) * (1 + rho * (np.sum(v ** 2) / v.sum() - 1))


def c_vis(w):
    """Constant on the width that makes the visible readout exact (the only scalar the visible set can pin)."""
    return 1 / (w[0] / H[0])


def c_free(w):
    t = w / H
    return 2 / (t.max() + t.min())


# click aggregates per set (no per-user data)
def aggs(s):
    ra, rb = E[s]["ctr"]["A"], E[s]["ctr"]["B"]
    rp = (E[s]["clicks"]["A"] + E[s]["clicks"]["B"]) / (E[s]["pageviews"]["A"] + E[s]["pageviews"]["B"])
    return {"abs(diff)": abs(rb - ra), "abs(rel)": abs(rb / ra - 1), "R_A": ra, "R_B": rb, "R_pool": rp,
            "R_pool(1-R_pool)": rp * (1 - rp), "sum R(1-R)": ra * (1 - ra) + rb * (1 - rb), "max R": max(ra, rb),
            "min R": min(ra, rb)}


AG = {s: aggs(s) for s in SETS}
NAMES = list(AG["visible"])
LA = {n: np.log([AG[s][n] for s in SETS]) for n in NAMES}
W_PV = hw(pv)


def mult_err(lm, cfit):
    """Pageview-level interval with the variance times exp(lm) per set (common to both arms), constant fitted by cfit."""
    w = W_PV * np.exp(lm / 2)
    return float(np.max(np.abs(cfit(w) * w / H - 1)))


def main():
    t0 = time.monotonic()
    L = ["# click_rule_probes.out.md (click_rule_probes.py)", ""]
    L.append(f"Fast evaluator: delta-method check, max |w/H - 1| over the six sets = {errs(hw(delta)).max():.1e} "
             "(the per-user counts match tests/expected/ exactly).")
    L += ["", "## 1. Click-dispersion estimates (each arm's pageview variance x D, no constant, exponent 1)", "",
          "D = sample variance of per-user CTR among users with >= k views / mean of R(1-R)/v over those users.", "",
          "| k | worst | " + " | ".join(SETS) + " | all six within 0.25 |", "|---|---|" + "---|" * len(SETS) + "---|"]
    win = []
    for k in range(5, 41):
        e = errs(hw(disp(k)))
        win += [k] if e.max() <= BAND else []
        L.append(f"| {k} | {e.max():.3f} | " + " | ".join(f"{x:.3f}" for x in e) + f" | {'yes' if e.max() <= BAND else 'no'} |")
    L += ["", f"Thresholds that pass all six: {win}.", ""]
    t = hw(disp(20)) / H
    L.append(f"k = 20: best constant on the width {c_free(hw(disp(20))):.4f} (on the variance "
             f"{c_free(hw(disp(20))) ** 2:.4f}), worst error with it {(t.max() - t.min()) / (t.max() + t.min()):.4f}.")
    e = errs(hw(anova))
    L += ["", f"ANOVA ICC + Kish (1 + rho (m_w - 1)), no constant: worst {e.max():.3f} (" +
          ", ".join(f"{s} {x:.3f}" for s, x in zip(SETS, e)) + ")."]
    for kind, k, g in (("zzb", 5, 2.0), ("disp", 10, 1.5)):
        w = np.array([Z * np.sqrt(sum(pv(*P[s, a]) * disp_feat(*P[s, a], k, kind) ** g for a in "AB")) for s in SETS])
        e = np.abs(c_vis(w) * w / H - 1)
        L.append(f"{kind} (>= {k} views)^{g}, constant fitted on the visible set: worst {e.max():.3f}.")
    L += ["", "## 2. Arm-level click aggregates (pageview variance x c f^g, one multiplier for both arms)", ""]
    g1 = np.round(np.arange(-12, 12.0001, 0.01), 2)
    L += ["One aggregate, exponent -12 to 12 in steps of 0.01:", "", "| f | c free: worst (g) | c on visible: worst (g) |",
          "|---|---|---|"]
    best1 = 9.0
    for n in NAMES:
        bf = min((mult_err(g * LA[n], c_free), g) for g in g1)
        bv = min((mult_err(g * LA[n], c_vis), g) for g in g1)
        best1 = min(best1, bf[0], bv[0])
        L.append(f"| {n} | {bf[0]:.3f} ({bf[1]}) | {bv[0]:.3f} ({bv[1]}) |")
    L += ["", f"Best over the {len(NAMES)} aggregates and both constant rules: {best1:.3f}.", ""]
    g2 = np.round(np.arange(-16, 16.0001, 0.1), 1)
    res = []
    for n1, n2 in itertools.combinations(NAMES, 2):
        b = min((mult_err(a * LA[n1] + bb * LA[n2], c_vis), a, bb) for a in g2 for bb in g2)
        res.append((b[0], n1, n2, b[1], b[2]))
    res.sort()
    npass = sum(r[0] <= BAND for r in res)
    L.append(f"Two aggregates, constant fitted on the visible set, exponents -16 to 16 in steps of 0.1: {npass} of "
             f"{len(res)} pairs pass all six; best five: " +
             "; ".join(f"{a}^{x} {b}^{y} {e:.3f}" for e, a, b, x, y in res[:5]) + ".")
    e3 = mult_err(4.03 * LA["abs(diff)"] - 4.61 * LA["abs(rel)"], c_free)
    L += ["", f"c abs(diff)^4.03 abs(rel)^-4.61 with c also tuned on the six readouts (three hidden-tuned parameters): "
          f"worst {e3:.4f}."]
    L.append("Pair ratios h_twin / h_null: " + ", ".join(f"{n} {AG['h_twin'][n] / AG['h_null'][n]:.4f}"
                                                        for n in ("abs(diff)", "abs(rel)", "R_A", "R_B", "R_pool")) + ".")
    L += ["", "## 3. Per-arm multipliers M_A, M_B >= 0 from the pageview data, other variance bases (section 15 (c))", ""]
    Hn, Ht = E["h_null"]["half_width"], E["h_twin"]["half_width"]
    r = Hn / Ht
    L.append(f"r = H_null / H_twin = {Hn:.6f} / {Ht:.6f} = {r:.4f}. V per arm is the same on both sets, so the twin/null "
             "width ratio lies between sqrt(q_min) and sqrt(q_max), q = base_twin / base_null per arm; the best worst "
             "error is (r sqrt(q_min) - 1) / (r sqrt(q_min) + 1). Grid check: M_A, M_B in {0, 0.01 .. 1000} (1,202 values each).")
    L += ["", "| base per arm | q_A | q_B | r sqrt(q_min) | bound | grid |", "|---|---|---|---|---|---|"]
    grid = np.concatenate([[0.0], np.logspace(-2, 3, 1201)])
    for label, fn in (("R(1-R)/V", lambda R, Rp: R * (1 - R)), ("R/V", lambda R, Rp: R), ("(1-R)/V", lambda R, Rp: 1 - R),
                      ("R_pool(1-R_pool)/V", lambda R, Rp: Rp * (1 - Rp))):
        q, base = {}, {}
        for s in ("h_null", "h_twin"):
            rp = AG[s]["R_pool"]
            base[s] = [fn(E[s]["ctr"][a], rp) / E[s]["pageviews"][a] for a in "AB"]
        q = [base["h_twin"][i] / base["h_null"][i] for i in range(2)]
        rr = r * np.sqrt(min(q))
        bound = (rr - 1) / (rr + 1)
        MA, MB = np.meshgrid(grid, grid)
        ok = (MA + MB) > 0
        wn = Z * np.sqrt(base["h_null"][0] * MA + base["h_null"][1] * MB)
        wt = Z * np.sqrt(base["h_twin"][0] * MA + base["h_twin"][1] * MB)
        ge = np.maximum(np.abs(wn / Hn - 1), np.abs(wt / Ht - 1))[ok].min()
        L.append(f"| {label} | {q[0]:.4f} | {q[1]:.4f} | {rr:.4f} | {bound:.4f} | {ge:.4f} |")
    L += ["", "## 4. Real grader (KIT_LOCAL), reward and worst bound error per readout", "",
          "| probe | reward | " + " | ".join(SETS) + " |", "|---|---|" + "---|" * len(SETS)]
    for name, src in probes().items():
        rew, cells = real_grade(name, src)
        L.append(f"| {name} | {rew} | " + " | ".join(cells) + " |")
    L += ["", f"Run time {time.monotonic() - t0:.1f} s."]
    with open(os.path.join(HERE, "click_rule_probes.out.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


HEAD = '''"""Probe stats.py written by click_rule_probes.py (authoring only; not shipped)."""
import math
import numpy as np
from scipy.stats import chisquare, norm
Z = float(norm.ppf(0.975))
SRM_ALPHA = 0.001
CI_METHOD = "probe"
def srm_pvalue(n_a, n_b):
    return float(chisquare([n_a, n_b]).pvalue)
def _rv(arm):
    c = arm["clicks"].to_numpy(float); v = arm["views"].to_numpy(float)
    return c, v, c.sum() / v.sum()
def _pv(c, v, r):
    return r * (1 - r) / v.sum()
'''
PER_ARM = '''def diff_ci(a, b):
    ca, va, ra = _rv(a); cb, vb, rb = _rv(b); diff = rb - ra
    se = math.sqrt(_var(ca, va, ra) + _var(cb, vb, rb)); return diff, (diff - Z * se, diff + Z * se)
'''


def probes():
    out = {}
    for k in (10, 17, 18, 20, 26, 27):
        out[f"disp k={k}, c 1, g 1"] = HEAD + f'''def _var(c, v, r):
    m = v >= {k}
    return _pv(c, v, r) * np.var(c[m] / v[m], ddof=1) / np.mean(r * (1 - r) / v[m])
''' + PER_ARM
    out["ANOVA ICC + Kish m_w"] = HEAD + '''def _var(c, v, r):
    m = v > 0; c1, v1 = c[m], v[m]; n = len(v1); V = v1.sum()
    msb = np.sum((c1 - r * v1) ** 2 / v1) / (n - 1)
    msw = np.sum(c1 * (1 - c1 / v1)) / (V - n)
    n0 = (V - np.sum(v1 ** 2) / V) / (n - 1)
    rho = (msb - msw) / (msb + (n0 - 1) * msw)
    return _pv(c, v, r) * (1 + rho * (np.sum(v ** 2) / v.sum() - 1))
''' + PER_ARM
    for kind, k, g in (("zzb", 5, 2.0), ("disp", 10, 1.5)):
        w = np.array([Z * np.sqrt(sum(pv(*P[s, a]) * disp_feat(*P[s, a], k, kind) ** g for a in "AB")) for s in SETS])
        cv = float(c_vis(w) ** 2)
        feat = ("np.mean(c[m] == 0) / np.mean((1 - r) ** v[m])" if kind == "zzb"
                else "np.var(c[m] / v[m]) / np.mean(r * (1 - r) / v[m])")
        out[f"{kind} >= {k} views, g {g}, c on visible"] = HEAD + f'''def _var(c, v, r):
    m = v >= {k}
    return _pv(c, v, r) * {cv!r} * ({feat}) ** {g}
''' + PER_ARM
    for label, lm, cfit, expr in (
            ("c abs(diff)^4.03 abs(rel)^-4.61, c tuned on all six", 4.03 * LA["abs(diff)"] - 4.61 * LA["abs(rel)"], c_free,
             "abs(diff) ** 4.03 * abs(rb / ra - 1) ** -4.61"),
            ("c R_A^9.9 R_B^-7.5, c on visible", 9.9 * LA["R_A"] - 7.5 * LA["R_B"], c_vis, "ra ** 9.9 * rb ** -7.5")):
        w = W_PV * np.exp(lm / 2)
        cv = float(cfit(w) ** 2)
        out[label] = HEAD + f'''def diff_ci(a, b):
    ca, va, ra = _rv(a); cb, vb, rb = _rv(b); diff = rb - ra
    se = math.sqrt((_pv(ca, va, ra) + _pv(cb, vb, rb)) * {cv!r} * {expr}); return diff, (diff - Z * se, diff + Z * se)
'''
    return out


def real_grade(name, src):
    slug = "".join(ch if ch.isalnum() else "_" for ch in name)
    root = os.path.join(HERE, ".localruns", "probes", slug)
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    app = os.path.join(root, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app"), app)
    for f in ("filters.py", "stats.py", "report.py"):
        shutil.copy(os.path.join(TASK, "solution", "canonical", f), os.path.join(app, "abtest", f))
    with open(os.path.join(app, "abtest", "stats.py"), "w") as f:
        f.write(src)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([PY, "-m", "abtest.report", "--data", "data", "--out", "output/result.json"], cwd=app, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    art = os.path.join(root, "artifact")
    excl = {"data", "__pycache__", ".venv"}
    shutil.copytree(app, art, ignore=lambda d, ns: [n for n in ns if n in excl and os.path.isdir(os.path.join(d, n))])
    shutil.rmtree(app)
    logs, work = os.path.join(root, "logs"), os.path.join(root, "work")
    genv = dict(env, KIT_LOCAL="1", KIT_SUBMISSION=art, KIT_LOGS=logs, KIT_WORK=work, GRADE_TESTS_DIR=TESTS,
                GRADE_PYTHON=PY)
    subprocess.run([PY, os.path.join(TESTS, "grade.py")], env=genv, capture_output=True, text=True, cwd=TESTS)
    shutil.rmtree(work, ignore_errors=True)
    m = json.load(open(os.path.join(logs, "reward.json")))
    cells = []
    for s in SETS:
        e = max(m.get(f"{s}_ci_lo_err_hw", float("nan")), m.get(f"{s}_ci_hi_err_hw", float("nan")))
        cells.append(f"{'pass' if m.get(f'{s}_ok') == 1 else 'FAIL'} {e:.3f}")
    return m["reward"], cells


if __name__ == "__main__":
    main()

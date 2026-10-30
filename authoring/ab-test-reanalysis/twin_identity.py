"""Prove that h_twin is an exact pageview twin of h_null, and do the half-width arithmetic (DESIGN.md section 15).

Run: submission/.venv/bin/python submission/authoring/ab-test-reanalysis/twin_identity.py
Reads only the committed files (tests/hidden/h_null, tests/hidden/h_twin, tests/expected/h_null.json, h_twin.json).
Writes twin_identity.out.md next to this script; exits 1 if any identity check fails.

1. Text: assignments.csv and users.csv must be byte-identical; pageviews.csv must have the same rows in the same order
   with the same user_id and ts text, so only the clicked column may differ.
2. Numbers: with the plan's population rules (bots out of both arms, exact repeated assignment rows once, pageviews
   strictly before assigned_at dropped), each counted user's pageview count, aligned by user_id, must be equal on the two
   sets, per arm; so every statistic of the counts (Kish's K, m_w, tail shares, quantiles, ... and the 16 features of
   calibration_study.py) is equal, and any function of the pageview data gives the same value on both sets.
3. Arithmetic: the reference half-widths of the two sets, and the smallest worst-set error any interval whose width is
   built from the pageview data must make on one of them: (a) a width from the pageview data only; (b) the pageview-level
   interval times one common multiplier; (c) the pageview-level variance of each arm times its own multiplier M_A, M_B
   >= 0 (the bracket bound, checked against a brute-force grid).
"""
import csv, gzip, io, json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import calibration_study as cs  # noqa: E402  (FEATURES, Z975; importing runs nothing)

TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
NULL, TWIN = (os.path.join(TASK, "tests", "hidden", s) for s in ("h_null", "h_twin"))
BAND = 0.25


def raw(folder, name):
    with open(os.path.join(folder, name + ".gz"), "rb") as f:
        gz = f.read()
    return gz, gzip.decompress(gz)


def per_user(folder):
    """user_id -> (arm, counted pageviews, clicks) for every counted (non-bot) user; stdlib only."""
    from datetime import datetime
    text = {n: raw(folder, n)[1].decode("utf-8") for n in ("assignments.csv", "users.csv", "pageviews.csv")}
    rows = list(csv.DictReader(io.StringIO(text["assignments.csv"])))
    seen, arm, t0 = set(), {}, {}
    for r in rows:
        key = (r["user_id"], r["variant"], r["assigned_at"])
        if key in seen:
            continue
        seen.add(key)
        assert r["user_id"] not in arm, "conflicting assignment rows"
        arm[r["user_id"]] = r["variant"]
        t0[r["user_id"]] = datetime.fromisoformat(r["assigned_at"].replace("Z", "+00:00"))
    bots = {r["user_id"] for r in csv.DictReader(io.StringIO(text["users.csv"])) if r["is_bot"] == "1"}
    out = {u: [a, 0, 0] for u, a in arm.items() if u not in bots}
    for r in csv.DictReader(io.StringIO(text["pageviews.csv"])):
        u = r["user_id"]
        if u in out and datetime.fromisoformat(r["ts"].replace("Z", "+00:00")) >= t0[u]:
            out[u][1] += 1
            out[u][2] += int(r["clicked"])
    return out


def main():
    L = ["# twin_identity.out.md (twin_identity.py)", "", "h_twin against h_null, from the committed files.", "",
         "## 1. Text", ""]
    ok = True
    for name in ("assignments.csv", "users.csv"):
        (gn, tn), (gt, tt) = raw(NULL, name), raw(TWIN, name)
        same = gn == gt and tn == tt
        ok &= same
        L.append(f"- {name}: gzip files byte-identical {gn == gt}, plain text byte-identical {tn == tt} "
                 f"({len(tn):,} bytes, {tn.count(b'\n') - 1:,} data rows)")
    pn = raw(NULL, "pageviews.csv")[1].decode().splitlines()
    pt = raw(TWIN, "pageviews.csv")[1].decode().splitlines()
    same_rows = len(pn) == len(pt)
    key_same = same_rows and all(a.rsplit(",", 1)[0] == b.rsplit(",", 1)[0] for a, b in zip(pn, pt))
    n_diff = sum(a != b for a, b in zip(pn, pt))
    ok &= key_same and pn[0] == pt[0]
    L.append(f"- pageviews.csv: header equal {pn[0] == pt[0]}; rows {len(pn) - 1:,} / {len(pt) - 1:,}; user_id and ts "
             f"text equal on every row, same order: {key_same}; rows whose clicked value differs: {n_diff:,}")

    L += ["", "## 2. Per-user pageview counts (plan's population rules; aligned by user_id)", ""]
    un, ut = per_user(NULL), per_user(TWIN)
    same_users = un.keys() == ut.keys() and all(un[u][0] == ut[u][0] for u in un)
    same_counts = same_users and all(un[u][1] == ut[u][1] for u in un)
    ok &= same_users and same_counts
    L.append(f"- the same counted users with the same arms: {same_users} ({len(un):,} users); every user's counted "
             f"pageviews equal: {same_counts}")
    L += ["", "| arm | set | users | pageviews | clicks | sum v^2 | m_w | K | max v | p99 v | users with v = 0 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    vecs = {}
    for a in ("A", "B"):
        ids = sorted(u for u in un if un[u][0] == a)
        for label, d in (("h_null", un), ("h_twin", ut)):
            v = np.array([d[u][1] for u in ids], float)
            c = np.array([d[u][2] for u in ids], float)
            vecs[(a, label)] = (c, v)
            L.append(f"| {a} | {label} | {len(v):,} | {int(v.sum()):,} | {int(c.sum()):,} | {int((v ** 2).sum()):,} | "
                     f"{(v ** 2).sum() / v.sum():.4f} | {(v ** 2).mean() / v.mean() ** 2:.4f} | {int(v.max())} | "
                     f"{np.percentile(v, 99):g} | {int((v == 0).sum()):,} |")
        eq = np.array_equal(vecs[(a, "h_null")][1], vecs[(a, "h_twin")][1])
        ok &= eq
        L.append(f"| {a} | equal | | | | | | | | | per-user count vectors np.array_equal: {eq} |")
    feat_eq = all(fn(vecs[(a, "h_null")][1]) == fn(vecs[(a, "h_twin")][1]) for fn in cs.FEATURES.values()
                  for a in ("A", "B"))
    ok &= feat_eq
    L.append("")
    L.append(f"- every one of the {len(cs.FEATURES)} pageview features of calibration_study.py, per arm, is "
             f"bit-identical on the two sets: {feat_eq}")

    L += ["", "## 3. Arithmetic (reference = tests/expected/<set>.json, delta method)", ""]
    ref = {s: json.load(open(os.path.join(TASK, "tests", "expected", s + ".json"))) for s in ("h_null", "h_twin")}
    H = {s: r["half_width"] for s, r in ref.items()}
    a_arm = {s: {a: r["ctr"][a] * (1 - r["ctr"][a]) / r["pageviews"][a] for a in "AB"} for s, r in ref.items()}
    naive = {s: cs.Z975 * math.sqrt(sum(a_arm[s].values())) for s in ref}
    de = {s: (H[s] / naive[s]) ** 2 for s in ref}
    for s in ref:
        L.append(f"- {s}: reference half-width H = {H[s]:.6f}; pageview-level half-width {naive[s]:.6f}; "
                 f"DE = (H / pageview hw)^2 = {de[s]:.3f}, sqrt(DE) = {math.sqrt(de[s]):.4f}; CTR A / B "
                 f"{ref[s]['ctr']['A']:.5f} / {ref[s]['ctr']['B']:.5f}")
    # per-arm design effect each set needs (user-level delta variance / pageview-level variance), from the users
    for s in ("h_null", "h_twin"):
        need = []
        for a in "AB":
            c, v = vecs[(a, s)]
            R = c.sum() / v.sum()
            var_d = len(c) / (len(c) - 1) * ((c - R * v) ** 2).sum() / v.sum() ** 2
            need.append(var_d / (R * (1 - R) / v.sum()))
        L.append(f"- {s}: multiplier each arm's pageview-level variance needs to equal the delta variance, A / B: "
                 f"{need[0]:.3f} / {need[1]:.3f}")
    r_w = H["h_null"] / H["h_twin"]
    e_w = (r_w - 1) / (r_w + 1)
    r_c = math.sqrt(de["h_null"] / de["h_twin"])
    e_c = (r_c - 1) / (r_c + 1)
    q = {a: a_arm["h_twin"][a] / a_arm["h_null"][a] for a in "AB"}
    q_lo, q_hi = min(q.values()), max(q.values())
    r_m = math.sqrt(q_lo) * r_w
    e_m = (r_m - 1) / (r_m + 1)
    L += ["",
          "Both bound errors of an interval with half-width w and the exact diff are |w - H| / H; a wrong centre only adds "
          "to one of them. A set passes only if w is in [(1 - b) H, (1 + b) H], b = 0.25.", "",
          f"- (a) width from the pageview data only (no clicks): w is the same number on both sets. Ratio of the "
          f"reference half-widths r = {H['h_null']:.6f} / {H['h_twin']:.6f} = {r_w:.4f}. Both pass only if (1 + b) / "
          f"(1 - b) >= r; the best common w = 2 H_null H_twin / (H_null + H_twin) misses both by (r - 1) / (r + 1) = "
          f"{e_w:.4f} half-widths.",
          f"- (b) pageview-level interval times one common multiplier sqrt(M): the needed sqrt(M) are sqrt(DE) = "
          f"{math.sqrt(de['h_null']):.4f} and {math.sqrt(de['h_twin']):.4f}, ratio r = {r_c:.4f}; minimum miss (r - 1) "
          f"/ (r + 1) = {e_c:.4f}.",
          f"- (c) each arm's pageview-level variance R(1-R)/V times its own M_A, M_B >= 0 from the pageview data (equal "
          f"on the two sets): V is equal, so for every such pair the twin / null ratio of the widths is between "
          f"sqrt(q_lo) and sqrt(q_hi), q = R(1-R) twin / R(1-R) null per arm: A {q['A']:.4f}, B {q['B']:.4f}. Both "
          f"pass only if (1 + b) / (1 - b) >= sqrt(q_lo) x r = {math.sqrt(q_lo):.4f} x {r_w:.4f} = {r_m:.4f}, so the "
          f"smallest worst error is (r - 1) / (r + 1) = {e_m:.4f} half-widths (reached with M on arm "
          f"{min(q, key=q.get)} alone)."]
    # brute force over (M_A, M_B): 0 and a log grid 1e-2 .. 1e3
    grid = np.r_[0.0, np.logspace(-2, 3, 1201)]
    MA, MB = np.meshgrid(grid, grid, indexing="ij")
    worst = np.zeros_like(MA)
    for s in ("h_null", "h_twin"):
        w = cs.Z975 * np.sqrt(a_arm[s]["A"] * MA + a_arm[s]["B"] * MB)
        worst = np.maximum(worst, np.abs(w - H[s]) / H[s])
    i = np.unravel_index(np.argmin(worst), worst.shape)
    L.append(f"- brute force over M_A, M_B in {{0}} and 1,201 log-spaced values from 0.01 to 1000: smallest worst "
             f"error {worst[i]:.4f} at M_A = {MA[i]:.4g}, M_B = {MB[i]:.4g} (the bound (c) is {e_m:.4f}); with both M "
             f">= 1: {worst[(MA >= 1) & (MB >= 1)].min():.4f}.")
    checks = {"identity (text and per-user counts)": ok, "(a) > band": e_w > BAND, "(b) > band": e_c > BAND,
              "(c) > band": e_m > BAND, "brute force >= bound (c) - 1e-9": worst[i] >= e_m - 1e-9}
    L += ["", "## Checks", ""] + [f"- {'PASS' if v else 'FAIL'}: {k}" for k, v in checks.items()]
    with open(os.path.join(HERE, "twin_identity.out.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())

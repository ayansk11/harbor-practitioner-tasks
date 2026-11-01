"""Checks of the agent-facing files of ab-test-reanalysis (authoring time only; revision of 2026-10-30).

Run: submission/.venv/bin/python -I -B submission/authoring/ab-test-reanalysis/app_checks.py
Writes app_checks.out.md next to this script (deterministic: no clock times; run times go to stdout only) and exits
with status 1 if any check fails. Reads the package, never writes into it.

Part 1, the figures that instruction.md and PM_NOTE.md quote, computed with pandas from the visible export alone
  (environment/app/data), cross-checked with generation_report.json (paths of the visible set), and searched for,
  as formatted here, in the two files:
  - the shipped readout's users per arm: every assigned user (any method) with no bot_flags row; B's shortfall;
  - the assignment dashboard: distinct assigned users per arm over every assignment row (any method, bots in);
  - the team dashboard: CTR per arm over every pageview row of every assigned user, the click being
    pageviews.clicked.
Part 2, the stale-account check (the approved design, section 9 "Docs"): each account given by the shipped README,
  the shipped filter's docstring or the PM's note, one command on the visible export that refutes it, its output,
  and an assertion on that output.
Part 3, the shipped code (environment/app/abtest) on the visible and the five hidden exports: each run exits 0 and
  its readout equals the "shipped" path of generation_report.json (counts and decision exactly, srm_p and diff to
  1e-9 relative); the packaged output/result.json equals a fresh run on the visible export, byte for byte.
Part 4, the claims of docs/ that data_checks.py does not assert, on all six exports; since the fix pass of
  2026-10-31 also the two DATA_DICTIONARY sentences added then (assigned users without a pageview row;
  identical module_clicks rows, each one event, as the velocity rule counts them).
"""
import json, math, os, subprocess, sys, tempfile, time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis"))
APP = os.path.join(TASK, "environment", "app")
DATA = os.path.join(APP, "data")
HIDDEN = ("h_null", "h_pos", "h_srm", "h_plain", "h_neg")
REPORT = json.load(open(os.path.join(HERE, "generation_report.json"), encoding="utf-8"))
sys.path.insert(0, HERE)
import data_checks as dc  # noqa: E402  (the velocity rule, T0 and DAY of the assertions)
FAIL = []
OUT = []


def say(line=""):
    OUT.append(line)


def check(ok, what):
    say(("- PASS: " if ok else "- FAIL: ") + what)
    if not ok:
        FAIL.append(what)


def ts(col):
    return pd.to_datetime(col, utc=True, format="ISO8601")


def read(name):
    return pd.read_csv(os.path.join(DATA, name + ".csv.gz"), dtype=str, keep_default_na=False)


a, f, pv, mc = read("assignments"), read("bot_flags"), read("pageviews"), read("module_clicks")
paths = REPORT["sets"]["visible"]["paths"]

# ---------------------------------------------------------------- part 1: figures
say("# app_checks (app_checks.py)")
say("")
say("Written by app_checks.py (deterministic: no clock times). The visible export is environment/app/data.")
say("")
say("## Part 1: figures quoted in instruction.md and PM_NOTE.md")
a1 = a.drop_duplicates()
flagged = set(f["user_id"])
shipped_users = a1[~a1["user_id"].isin(flagged)].groupby("variant")["user_id"].nunique()
nA, nB = int(shipped_users["A"]), int(shipped_users["B"])
short = 1 - nB / nA
e = (nA + nB) / 2
srm_shipped = math.erfc(math.sqrt((((nA - e) ** 2 + (nB - e) ** 2) / e) / 2))
dash_users = a1.groupby("variant")["user_id"].nunique()
dA, dB = int(dash_users["A"]), int(dash_users["B"])
rows = pv.merge(a1[["user_id", "variant"]], on="user_id", how="inner")
dash = rows.assign(c=rows["clicked"].astype(int)).groupby("variant")["c"].agg(["sum", "size"])
ctrA, ctrB = dash.loc["A", "sum"] / dash.loc["A", "size"], dash.loc["B", "sum"] / dash.loc["B", "size"]
lift = ctrB / ctrA - 1
say(f"- shipped readout users: A {nA:,}, B {nB:,}; B short by {100 * short:.2f}% of A; SRM p {srm_shipped:.3g}")
say(f"- assignment dashboard users: A {dA:,}, B {dB:,} ({100 * dA / (dA + dB):.2f}% / {100 * dB / (dA + dB):.2f}%)")
say(f"- team dashboard: rows A {int(dash.loc['A', 'size']):,}, B {int(dash.loc['B', 'size']):,}; CTR A "
    f"{100 * ctrA:.4f}%, B {100 * ctrB:.4f}%; B {100 * lift:+.3f}% relative")
say("")
say("Cross-checks with generation_report.json (visible paths):")
check({"A": nA, "B": nB} == paths["shipped"]["n_users"], "shipped users equal paths.shipped.n_users")
check({"A": dA, "B": dB} == paths["all_assigned"]["n_users"], "dashboard users equal paths.all_assigned.n_users")
check(abs(ctrA - paths["dashboard_all_rows"]["ctr"]["A"]) < 1e-12 and
      abs(ctrB - paths["dashboard_all_rows"]["ctr"]["B"]) < 1e-12, "team dashboard CTRs equal paths.dashboard_all_rows")
check(abs(srm_shipped - paths["shipped"]["srm_p"]) <= 1e-9 * paths["shipped"]["srm_p"], "shipped SRM p equals paths")

pm = open(os.path.join(APP, "PM_NOTE.md"), encoding="utf-8").read()
ins = open(os.path.join(TASK, "instruction.md"), encoding="utf-8").read()
pct = lambda x, k: f"{100 * x:.{k}f}%"
typed = [
    (pm, "PM_NOTE.md", f"{nA:,} users in A"), (pm, "PM_NOTE.md", f"{nB:,} in B"),
    (pm, "PM_NOTE.md", f"about {round(100 * short)}% fewer in B"),
    (pm, "PM_NOTE.md", f"{dA:,} users in A and {dB:,} in B"),
    (pm, "PM_NOTE.md", f"({pct(dA / (dA + dB), 1)} / {pct(dB / (dA + dB), 1)})"),
    (pm, "PM_NOTE.md", f"{pct(ctrB, 2)} in B against {pct(ctrA, 2)} in A"),
    (pm, "PM_NOTE.md", f"B is {pct(lift, 1)} higher"),
    (ins, "instruction.md", f"about {round(100 * short)}% fewer users in B than in A"),
    (ins, "instruction.md", f"click-through {pct(lift, 1)} above A's"),
]
say("")
say("The figures as typed in the two files (each string must occur in the file):")
for text, name, s in typed:
    check(s in text, f"{name} contains \"{s}\"")

# ---------------------------------------------------------------- part 2: stale accounts
say("")
say("## Part 2: stale-account check")
say("Each command runs on the visible export with a = assignments, f = bot_flags, pv = pageviews, mc = module_clicks")
say("(all read as text), ts = ISO 8601 text to UTC instants.")
NS = dict(pd=pd, a=a, f=f, pv=pv, mc=mc, ts=ts)
ACCOUNTS = [
    ("R1", "README.md", "filters.py applies the platform's bot screening (bot_flags.csv.gz) to both arms",
     'f.merge(a.drop_duplicates(), on="user_id").groupby(["rule", "variant"]).user_id.nunique().unstack()',
     "one rule (ua_crawler, a client property) flags users of both arms alike; velocity flags users of one arm "
     "almost only: it reacts to what that arm's module makes users do, so applying it makes the arms unequal",
     lambda r: r.loc["velocity", "B"] > 20 * r.loc["velocity", "A"]
     and abs(r.loc["ua_crawler", "A"] - r.loc["ua_crawler", "B"]) < 0.1 * r.loc["ua_crawler", "A"]),
    ("R2", "README.md", "a click is a pageview's clicked value, the module click flag",
     'pv[pv.clicked == "1"].assign(item=lambda x: x.pageview_id.isin(mc.loc[mc.target.str.startswith("item:"), '
     '"pageview_id"])).merge(a.drop_duplicates()[["user_id", "variant"]], on="user_id")'
     '.groupby(["variant", "item"]).size().unstack()',
     "clicked = 1 also on pageviews on which no related product was opened (item = False: arrow taps or See all "
     "only), in both arms and far more in B; plan section 4 counts a pageview only when a related product was opened",
     lambda r: r.loc["A", False] > 0 and r.loc["B", False] > 2 * r.loc["A", False]),
    ("R3", "abtest/filters.py docstring", "every flagged user is bot traffic: crawlers and, since SEC-219, click-fraud "
     "bots (rule velocity); plan section 3",
     'f[f.rule == "velocity"].merge(a.drop_duplicates(), on="user_id").assign(crawler=lambda x: x.user_id.isin('
     'f.loc[f.rule == "ua_crawler", "user_id"]), after=lambda x: ts(x.flagged_at) > ts(x.assigned_at))'
     '.groupby(["crawler", "variant", "method"]).agg(users=("user_id", "nunique"), flags=("user_id", "size"), '
     'after_assignment=("after", "mean"))',
     "the users velocity flags without a ua_crawler flag are randomized (hash) users of B only, every flag raised "
     "after the assignment: excluded for what the users did during the experiment, which plan section 3 rules "
     "out; the "
     "click-fraud bots it catches are also ua_crawler users",
     lambda r: set(r.loc[False].index) == {("B", "hash")} and r.loc[(False, "B", "hash"), "after_assignment"] == 1.0
     and r.loc[(False, "B", "hash"), "users"] > 500),
    ("R4", "PM_NOTE.md", "the assignment dashboard shows a clean 50/50 split",
     'a.drop_duplicates().groupby(["method", "variant"]).user_id.nunique()',
     "the dashboard's B includes the override accounts (variant set by hand, not randomized; plan section 3 leaves "
     "the accounts out); the randomized (hash) users are balanced, so the readout's imbalance is made after the "
     "assignment",
     lambda r: set(r.loc["override"].index) == {"B"} and abs(r.loc[("hash", "A")] - r.loc[("hash", "B")])
     < 0.02 * r.loc[("hash", "A")]),
    ("R5", "PM_NOTE.md", f"the team dashboard shows B's click-through {pct(lift, 1)} above A's",
     'pv.merge(a.drop_duplicates()[["user_id", "variant", "method"]], on="user_id").assign(clicked=lambda x: x.clicked'
     '.astype(int), product_opened=lambda x: x.pageview_id.isin(mc.loc[mc.target.str.startswith("item:"), '
     '"pageview_id"])).groupby(["method", "variant"]).agg(rows=("clicked", "size"), clicked=("clicked", "sum"), '
     'product_opened=("product_opened", "sum"))',
     "the dashboard's lead of B is made of clicks that open no product (clicked against product_opened) and of the "
     "override accounts in B, which open products at several times the rate of anyone else; among the randomized "
     "(hash) users, B's lead in product opens, the plan's click (section 4), is a small fraction of the dashboard's "
     "lead",
     lambda r: (lambda h_a, h_b, o_b: (h_b[2] / h_b[0]) / (h_a[2] / h_a[0]) - 1 < 0.25 * lift
                and o_b[2] / o_b[0] > 2 * h_b[2] / h_b[0])(
         r.loc[("hash", "A")].tolist(), r.loc[("hash", "B")].tolist(), r.loc[("override", "B")].tolist())),
]
for key, where, claim, cmd, shows, ok in ACCOUNTS:
    # eval of the fixed command strings above (written in this file, never read from input): the same text is
    # printed, so the record shows exactly the command that produced each output.
    res = eval(cmd, NS)
    say("")
    say(f"### {key}: {where}: \"{claim}\"")
    say("Command:")
    say("")
    say("    " + cmd)
    say("")
    say("Output:")
    say("")
    for line in res.to_string().splitlines():
        say("    " + line)
    say("")
    if key == "R5":
        tot = res.groupby(level="variant").sum()
        rate = lambda fr, col, arm: fr.loc[arm, col] / fr.loc[arm, "rows"]
        hsh = res.loc["hash"]
        say("Relative lift of B (CTR_B / CTR_A - 1): every row, clicked "
            f"{100 * (rate(tot, 'clicked', 'B') / rate(tot, 'clicked', 'A') - 1):+.2f}% (the dashboard); every row, "
            f"product_opened {100 * (rate(tot, 'product_opened', 'B') / rate(tot, 'product_opened', 'A') - 1):+.2f}%;"
            f" hash rows, product_opened "
            f"{100 * (rate(hsh, 'product_opened', 'B') / rate(hsh, 'product_opened', 'A') - 1):+.2f}%. Product-open "
            f"rate of the override rows: {100 * rate(res.loc['override'], 'product_opened', 'B'):.1f}%.")
        say("")
    say(f"What it shows: {shows}.")
    check(bool(ok(res)), f"{key} output refutes the account")


# ---------------------------------------------------------------- part 3: shipped code
def run_shipped(folder, out):
    code = ("import sys, runpy; sys.path.insert(0, '.'); sys.argv = ['abtest.report', '--data', %r, '--out', %r]; "
            "runpy.run_module('abtest.report', run_name='__main__')" % (folder, out))
    t0 = time.time()
    r = subprocess.run([sys.executable, "-I", "-B", "-c", code], cwd=APP, capture_output=True, text=True)
    return r.returncode, time.time() - t0, r.stderr


say("")
say("## Part 3: the shipped code on the six exports")
with tempfile.TemporaryDirectory() as tmp:
    for name in ("visible",) + HIDDEN:
        folder = DATA if name == "visible" else os.path.join(TASK, "tests", "hidden", name)
        out = os.path.join(tmp, name + ".json")
        rc, secs, err = run_shipped(folder, out)
        print(f"shipped code on {name}: exit {rc}, {secs:.2f} s (Mac)", flush=True)
        if rc != 0:
            check(False, f"{name}: shipped code exits {rc}: {err[-300:]}")
            continue
        got = json.load(open(out, encoding="utf-8"))
        exp = REPORT["sets"][name]["paths"]["shipped"]
        same = all(got[k] == exp[k] for k in ("n_users", "pageviews", "clicks", "decision"))
        close = all(abs(got[k] - exp[k]) <= 1e-9 * max(abs(exp[k]), 1e-300) for k in ("srm_p", "diff"))
        check(same and close, f"{name}: shipped readout = paths.shipped (decision {got['decision']}, n_users "
              f"{got['n_users']['A']}/{got['n_users']['B']}, srm_p {got['srm_p']:.3g})")
        if name == "visible":
            packaged = open(os.path.join(APP, "output", "result.json"), "rb").read()
            check(packaged == open(out, "rb").read(), "output/result.json equals a fresh run, byte for byte")

# ---------------------------------------------------------------- part 4: claims of docs/ on every export
say("")
say("## Part 4: claims of the shipped docs, on all six exports")
say("The docs say they apply to every export of this layout. Claims also asserted by data_checks.py ((a) to (l)) are")
say("not repeated here; these are the others (DATA_DICTIONARY, TRACKING, BOT_SCREENING, LAUNCH_EXP-2291).")
END = pd.Timestamp("2026-09-15T00:00:00Z")
for name in ("visible",) + HIDDEN:
    folder = DATA if name == "visible" else os.path.join(TASK, "tests", "hidden", name)
    rd = lambda n: pd.read_csv(os.path.join(folder, n + ".csv.gz"), dtype=str, keep_default_na=False)
    A, F, P, M = rd("assignments"), rd("bot_flags"), rd("pageviews"), rd("module_clicks")
    A1 = A.drop_duplicates()
    at = A1.set_index("user_id")["assigned_at"].pipe(ts)
    pt = ts(P["ts"])
    gap_h = ((at.reindex(P["user_id"]).to_numpy() - pt.to_numpy()) / pd.Timedelta(hours=1))
    last = max(ts(F["flagged_at"]).max(), ts(M["ts"]).max(), pt.max(), at.max())
    nav = M[M["target"].str.startswith("nav:")].merge(A1[["user_id", "variant"]], on="user_id")
    ok = [
        ("one row per user after exact repeats", A1["user_id"].is_unique),
        ("variant in {A, B}, method in {hash, override}", set(A1["variant"]) <= {"A", "B"}
         and set(A1["method"]) <= {"hash", "override"}),
        ("every flagged user, pageview user and event user is assigned", set(F["user_id"]) <= set(A1["user_id"])
         and set(P["user_id"]) <= set(A1["user_id"]) and set(M["user_id"]) <= set(A1["user_id"])),
        ("rules are ua_crawler or velocity; one ua_crawler row per flagged user",
         set(F["rule"]) <= {"ua_crawler", "velocity"} and F.loc[F["rule"] == "ua_crawler", "user_id"].is_unique),
        ("pageview_id unique; every pageview before the end", P["pageview_id"].is_unique and bool((pt < END).all())),
        ("no pageview more than 72.1 h before its user's assigned_at", float(gap_h.max()) < 72.1),
        ("every event's pageview_id is a pageview of the export", set(M["pageview_id"]) <= set(P["pageview_id"])),
        ("arrows (nav:) in at most one arm", nav["variant"].nunique() <= 1),
        ("nothing in the export after 2026-09-15 06:00Z", bool(last <= pd.Timestamp("2026-09-15T06:00:00Z"))),
    ]
    # DATA_DICTIONARY, pageviews (fix pass, 2026-10-31): the pageview on which a user was assigned need not have a row
    sec = lambda c: ((ts(c) - dc.T0) // pd.Timedelta(seconds=1)).to_numpy("int64")
    a_sec = pd.Series(sec(A1["assigned_at"]), index=A1["user_id"].to_numpy())
    p_sec = sec(P["ts"])
    tie_users = set(P.loc[p_sec == a_sec.reindex(P["user_id"]).to_numpy(), "user_id"])
    no_row = int((~A1["user_id"].isin(set(P["user_id"]))).sum())
    no_tie = int((~A1["user_id"].isin(tie_users)).sum())
    ok.append((f"DICT pageviews: assigned users with no pageview at assigned_at ({no_tie}) and with no pageview row "
               f"({no_row}) both occur", no_row > 0 and no_tie > no_row))
    # DATA_DICTIONARY, module_clicks (fix pass): identical rows are clicks on one element in one second, each an event:
    # the documented velocity rule counted over every row gives exactly the velocity rows (a second code path to (j))
    codes, uniq = pd.factorize(pd.concat([M["user_id"], F["user_id"]], ignore_index=True))
    m_code, f_code = codes[:len(M)], codes[len(M):]
    vel = (F["rule"] == "velocity").to_numpy()
    v_rows = {(int(u), int(x) // dc.DAY - 1) for u, x in zip(f_code[vel], sec(F["flagged_at"])[vel])}
    every = dc._rule_days(m_code, sec(M["ts"]))
    Md = M.drop_duplicates()
    once = dc._rule_days(pd.Index(uniq).get_indexer(Md["user_id"]), sec(Md["ts"]))
    ident = M[M.duplicated(keep=False)]
    ok.append((f"DICT module_clicks: identical rows ({len(ident)}) are all nav: taps; the velocity rule over every "
               f"row = the {len(v_rows)} velocity rows (over de-duplicated rows: {len(once ^ v_rows)} user-days "
               f"differ)", bool(ident["target"].str.startswith("nav:").all()) and every == v_rows))
    if name == "visible":
        ov = A1[A1["method"] == "override"]
        ok.append(("LAUNCH: 100 override accounts, all in B, assigned from 2026-09-03 00:00Z", len(ov) == 100
                   and set(ov["variant"]) == {"B"} and bool((ts(ov["assigned_at"]) >= pd.Timestamp(
                       "2026-09-03T00:00:00Z")).all())))
        ok.append(("LAUNCH: start 2026-09-01 00:00Z, end 2026-09-15 00:00Z: every assigned_at inside",
                   bool(((at >= pd.Timestamp("2026-09-01T00:00:00Z")) & (at < END)).all())))
    for what, good in ok:
        check(bool(good), f"{name}: {what}")

say("")
say(f"Result: {'all checks passed' if not FAIL else str(len(FAIL)) + ' check(s) failed'}.")
with open(os.path.join(HERE, "app_checks.out.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(OUT) + "\n")
print("\n".join(x for x in OUT if x.startswith("- FAIL")) or "all checks passed")
sys.exit(1 if FAIL else 0)

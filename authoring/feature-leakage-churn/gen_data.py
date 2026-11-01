"""Synthetic meal-kit warehouse for task feature-leakage-churn (authoring only; never shipped to the agent).

python gen_data.py [--check | --out DIR]
  Simulates two brands of the company, their customers, the warehouse jobs that wrote every row and the scheduler's
  records of those jobs, runs every build assert (any failure stops before a file is written), then writes
  - the visible brand (seed 11, customer ids 100001+): its extract at 2026-03-05T00:00:00Z, seven plain CSV files and
    the scheduler's records in _ops/, into the task's environment/app/data/, and the live service's January log
    sample into environment/app/logs/;
  - the hidden brand "North" (seed 12, customer ids 200001+): its extract, seven gzip CSV files and the gzip _ops/
    records (mtime 0), into tests/hidden/H/.
  With --check nothing is written; the asserts and the report still run.
  With --out DIR nothing in the task is written: DIR/visible and DIR/H get each brand's extract as plain files (seven
  CSV files and _ops/), and DIR/<brand>/truth.parquet the live values at its scoring points (ref_truth.compute). This
  mode skips the per-mechanism floors and the log sample, so it needs only extract_io, ops_log and ref_truth.
Determinism: numpy PCG64 streams, one per purpose: [seed] the brand's districts and analytics outages, [seed, cid] a
customer's core events (as before the revision), [seed, cid, 1] plan changes, [seed, cid, 2] logins, [seed, 101-106]
the loaders (legacy runs, hourly runs, exports, label job, CRM sync, ticket capture), so a knob of one part re-draws
only that part. Inside Python every timestamp is int64 epoch seconds (UTC).
Since 2026-10-31 three more streams time the scheduler's records. Each is drawn in a fixed order and count per
simulated run (never per extract row), so the streams above and every row's true commit time stay as they were:
  [seed, 107] legacy_orders, per run in run-date order the draws s (1 to 20 s, the send before the commit), a (1 to
    10 s, the commit to the analyze; a failed run ends 1 + (a - 1) mod 5 s after its rollback), u (uniform: the
    analyze length is u scaled to 300 to 2400 s, or to 10800 to 18000 s on a long night) and long (a long night when
    it is below L["analyze_long_p"]);
  [seed, 108] the order loaders' migration: the backfill's start lag, send lag, s and end lag; per hourly top from the
    first dual-run top to 23:00 of the move day a commit offset and an ok draw; then per top s, a start lag and an end
    lag; the parity check's start lag; the cutover's lead before the first hourly run and its s; the drop's send time
    and commit lag;
  [seed, 109] the runs the loaders had before, per run: the hourly runs into `orders` (s, start lag, end lag), then
    label_job (s, end lag), billing_export (s, start lag, end lag) and crm_sync (s, end lag).
  Integer draws are inclusive ranges; every new commit is moved off scoring seconds as before (_away).

Other build scripts use brand_world(name) (the simulator's true state, with each row's true `visible_at`, the CRM
writes, the run tables and the scheduler's records) and extract_tables(world) (the seven tables the warehouse held at
the extract time, plus "_ops": the scheduler's records written before it, see scheduler_runs).
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"  # the model behind the logged scores runs single-threaded
import bisect, json, sys, time
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "feature-leakage-churn"))
APP = os.path.join(TASK, "environment", "app")
sys.path.insert(0, HERE)
import extract_io  # noqa: E402

DAY, HOUR = 86400, 3600
def ts(s): return int(pd.Timestamp(s, tz="UTC").timestamp())
def iso(sec): return pd.Timestamp(int(sec), unit="s").strftime("%Y-%m-%dT%H:%M:%SZ")
T0 = ts("2024-01-01")              # simulation start
SIGNUP_TO = ts("2025-10-31")
SCORING_FROM = ts("2024-07-01")
EXTRACT_AT = ts("2026-03-05")       # the extract: what the warehouse held at this moment
HORIZON = ts("2026-03-15")          # simulated past the extract, so January 2026 outcomes are known
LIVE_FROM, LIVE_TO = ts("2026-01-01"), ts("2026-02-01")          # first live month (the January sample)
SHADOW_FROM, SHADOW_TO = ts("2025-03-10"), ts("2025-03-15")      # task v2's shadow week (no sample now; see line 370)
N_CUSTOMERS = 3000
PLANS = ["basic", "plus", "family"]
PRICES = {"basic": 4990, "plus": 6990, "family": 8990}
PLAN_P = [0.45, 0.40, 0.15]
PLAN_EFF = {"basic": 0.25, "plus": 0.0, "family": -0.3}
AREAS = ["B", "BS", "CF", "E", "EH", "G", "L", "LS", "M", "N", "NE", "NG", "NW", "OX", "S", "SE", "SW", "W", "CB", "BN"]
BOX_AT = 5 * HOUR + 30 * 60         # billing charges boxes at 05:30 UTC on the billing weekday
BATCH_AT = 6 * HOUR                 # batch scoring runs at 06:00 UTC
NEVER = 2 ** 62                     # a load time after every simulated moment
STRIDE = 10 ** 10                   # composite key customer_id * STRIDE + seconds

# Customer behaviour (calibration knobs: see calibrate_auc.py). The first block is the pre-revision simulator.
P = dict(h0=1 / 520, beta_b=0.75, district_sd=0.45, decline_min=10, decline_max=45, dip_every=110,
         dip_depth=(0.3, 0.9), dip_half=(4, 16), skip_base=0.06, skip_x=0.45, pf_base=0.012, pf_x=0.12,
         pause_base=0.0015, pause_x=0.02, addon_rate=0.035, ticket_base=0.012, ticket_x=0.05, ticket_pf=0.25,
         ticket_score_p=0.4, app_scale=70.0, app_missing=0.25, outage_frac=0.07, n_districts=600, zipf=0.5,
         cancel_on_box_day=0.6, cancel_ticket_p=0.7, app_decline=0.85,
         # plan changes: a churner above basic downgrades 5-40 days before cancelling with probability downgrade_p;
         # everyone changes plan at random about once per 400 days, at most one change in any 7 days
         downgrade_p=0.35, downgrade_lead=(5.0, 40.0), plan_change_rate=1 / 400, plan_gap_days=7,
         # logins per day: login_rate x engagement level x (1 - login_decline x disengagement)
         login_rate=0.8, login_decline=0.9)
# Loaders (rates of the design's section 9 step 1 and section 5).
# late_month_n: month-start export partitions per brand that land month_late_days (5 to 9) days after their normal
# 06:30 landing on D+1, after later days' partitions (the design's "one at a month start" gave 87-91 cells for
# status_latest_loaded, under the 100-cell floor; raised to 2).
# analyze_long_p (added 2026-10-31): the share of legacy_orders nights whose analyze after the commit runs 3 to 5 h.
L = dict(legacy_fail=0.03, legacy_late=0.03, legacy_outage=(9, 11), hourly_fail=0.02, export_late=0.02,
         export_ooo=0.02, month_late_days=(5, 9), late_month_n=2, label_fail=0.03, sync_late=1 / 15,
         ticket_lag=(1, 30), analyze_long_p=0.10)
# d0 (added 2026-10-31): the first day of the order loaders' dual run, 56 days before the move day (scheduler_runs);
# txn0: the first transaction number of the brand's scheduler. The move day's backfill of the earlier build is gone:
# the backfill now runs on d0 and its times are drawn (stream [seed, 108]).
BRANDS = {
    "visible": dict(seed=11, label="visible brand", cust0=100001, order0=5000001, ticket0=700001, run0=30001,
                    move="2025-06-01", d0="2025-04-06", txn0=7000001, first_hourly_run="2025-06-01T10:20:00Z",
                    late_month_starts=["2026-01-01"], shadow=True),
    "H": dict(seed=12, label="North", cust0=200001, order0=6000001, ticket0=800001, run0=70001,
              move="2025-04-15", d0="2025-02-18", txn0=9000001, first_hourly_run="2025-04-15T14:20:00Z",
              late_month_starts=[], shadow=False),
}
MIGRATION_DAYS = 56                 # the dual run: d0 = the move day - 56 days
DOC_DATE = "2025-02-14"             # the date of docs/WAREHOUSE.md; d0 is after it


# ----------------------------------------------------------------------------------------------- customers
def districts(rng, n_d, zipf):
    names, seen = [], set()
    while len(names) < n_d:
        n = f"{AREAS[rng.integers(len(AREAS))]}{rng.integers(1, 60)}"
        if n not in seen:
            seen.add(n)
            names.append(n)
    w = 1.0 / np.arange(1, n_d + 1) ** zipf
    return names, w / w.sum()


def plan_timeline(rp, signup, C, churns, plan0, p):
    """The customer's plan changes in the CRM, [(changed_at, old_plan, new_plan)] in time order."""
    end = min(C, HORIZON)
    u_dg, lead, u_to = rp.random(), rp.uniform(*p["downgrade_lead"]), rp.random()
    dg_t = None
    if churns:
        t = C - int(lead * DAY)
        if t > signup + DAY and u_dg < p["downgrade_p"]:
            dg_t = t
    lo = signup + DAY
    n = int(rp.poisson(p["plan_change_rate"] * max(end - lo, 0) / DAY))
    times = np.sort(rp.integers(lo, max(end, lo + 1), n)) if n else np.zeros(0, np.int64)
    picks = rp.random(n)
    gap = int(p["plan_gap_days"] * DAY)
    events, last_kept = [], None
    if dg_t is not None:
        events.append((dg_t, 0, u_to))
    for t, u in zip(times.tolist(), picks.tolist()):
        if dg_t is not None and abs(t - dg_t) < gap:
            continue
        if last_kept is not None and t - last_kept < gap:
            continue
        events.append((t, 1, u))
        last_kept = t
    events.sort()
    plan, out = plan0, []
    for t, kind, u in events:
        if kind == 0:                        # the churner's downgrade
            if plan == "basic":
                continue
            new = "plus" if (plan == "family" and u < 0.7) else "basic"
        else:
            others = [q for q in PLANS if q != plan]
            new = others[int(u * 2)]
        out.append((int(t), plan, new))
        plan = new
    return out


def login_times(rl, signup, C, days, x, level, p):
    """Login times (sorted): the sign-up session, then Poisson logins per day that fall with disengagement."""
    rate = np.clip(p["login_rate"] * level * (1 - p["login_decline"] * x), 0, None)
    k = rl.poisson(rate)
    t = np.repeat(days.astype(np.int64) * DAY, k) + rl.integers(0, DAY, int(k.sum()))
    t = t[(t > signup) & (t < C)]
    return np.sort(np.concatenate([[signup], t]).astype(np.int64))


def _sod(t):
    """Event seconds never fall on the 05:30:00 charge or the 06:00:00 batch second (no planted edge ties)."""
    return t + 1 if t % DAY in (BOX_AT, BATCH_AT) else t


def _fix_edges(my_orders, my_tickets, cpts):
    """No add-on order exactly at t - 7 or t - 30 days and no ticket exactly at t - 30 days of a point of the same
    customer: move such an event by one second (a scored ticket moves with its point) and look again."""
    for _ in range(100):
        pts = {c[0] for c in cpts}
        moved = False
        for o in my_orders:
            if o[1] == "addon":
                while (o[0] + 7 * DAY) in pts or (o[0] + 30 * DAY) in pts or o[0] % DAY in (BOX_AT, BATCH_AT):
                    o[0] += 1
                    moved = True
        for j, tk in enumerate(my_tickets):
            if (tk[0] + 30 * DAY) in pts or tk[0] % DAY in (BOX_AT, BATCH_AT):
                tk[0] += 1
                for cp in cpts:
                    if cp[2] == j:
                        cp[0] = tk[0]
                moved = True
                break
        if not moved:
            return
    raise AssertionError("edge fix did not converge")


def simulate(seed, cust0, p, sync_start, n_customers=N_CUSTOMERS):
    """Customers and their events (no loaders yet). CRM writes and plan changes refer to syncs by index."""
    rng = np.random.default_rng(seed)
    dnames, dweights = districts(rng, p["n_districts"], p["zipf"])
    deff = rng.normal(0, p["district_sd"], len(dnames))
    n_days = (HORIZON - T0) // DAY + 1
    outage = rng.random(n_days) < p["outage_frac"]
    month_first = {int(d) for d in range(T0 // DAY, T0 // DAY + n_days) if pd.Timestamp(d * DAY, unit="s").day == 1}
    cust, orders, tickets, snaps, points, labels, changes, writes = [], [], [], [], [], [], [], []
    for i in range(n_customers):
        cid = cust0 + i
        r = np.random.default_rng([seed, cid])
        signup = int(r.integers(T0, SIGNUP_TO))
        plan0 = str(r.choice(PLANS, p=PLAN_P))
        k = int(r.choice(len(dnames), p=dweights))
        b = r.normal()
        h = p["h0"] * np.exp(p["beta_b"] * b + deff[k] + PLAN_EFF[plan0])
        C = signup + int(r.exponential(1 / h) * DAY)
        first_box = signup // DAY + int(r.integers(1, 8))
        if C < HORIZON and r.random() < p["cancel_on_box_day"]:
            # many customers cancel on a billing day, after that morning's charge and batch run
            cday = max(first_box, first_box + 7 * ((C // DAY - first_box) // 7))
            C = cday * DAY + int(r.integers(6 * HOUR + 60, DAY))
        churns = C < HORIZON
        if not churns:
            C = HORIZON + 10 * DAY
        cust.append((cid, signup, plan0, dnames[k], C if churns else -1))
        chg = plan_timeline(np.random.default_rng([seed, cid, 1]), signup, C, churns, plan0, p)
        ch_t = [c[0] for c in chg]

        def plan_at(x):
            j = bisect.bisect_left(ch_t, x) - 1
            return chg[j][2] if j >= 0 else plan0

        sday = signup // DAY
        last_day = min(C, HORIZON) // DAY
        days = np.arange(sday, last_day + 1)
        # disengagement intensity x(day): decline before churn plus temporary dips that recover
        x = np.zeros(len(days))
        if churns:
            D = r.uniform(p["decline_min"], p["decline_max"])
            x = np.clip((days * DAY + DAY / 2 - (C - D * DAY)) / (D * DAY), 0, 1)
        for _ in range(r.poisson(len(days) / p["dip_every"])):
            c0 = r.uniform(days[0], days[-1] + 1)
            hw = r.uniform(*p["dip_half"])
            dep = r.uniform(*p["dip_depth"])
            x = np.maximum(x, dep * np.clip(1 - np.abs(days + 0.5 - c0) / hw, 0, 1))
        g0 = np.exp(r.normal(0, 0.4) - 0.3 * b)
        g = g0 * (1 - p["app_decline"] * x)
        state, until, prev = "active", -1, None
        my_o, my_t, cpts, my_s = [], [], [], []
        for j, d in enumerate(days):
            day_start = int(d) * DAY
            if state != "active" and d >= until:
                state = "active"
            pf_today = False
            if state == "active" and r.random() < p["pause_base"] + p["pause_x"] * x[j]:
                state, until = "paused", d + int(r.integers(7, 29))
            if d >= first_box and (d - first_box) % 7 == 0 and day_start + BOX_AT < C:
                if state == "active":
                    if r.random() < p["pf_base"] + p["pf_x"] * x[j]:
                        state, until, pf_today = "payment_failed", d + int(r.integers(1, 7)), True
                    elif r.random() >= p["skip_base"] + p["skip_x"] * x[j]:
                        # the box price follows the plan in force at the charge (billing reads the CRM's plan)
                        amt = PRICES[plan_at(day_start + BOX_AT)] - (1000 if r.random() < 0.1 else 0)
                        my_o.append([day_start + BOX_AT, "box", amt])
            if state == "active":
                for _ in range(r.poisson(p["addon_rate"] * g[j])):
                    t = _sod(day_start + int(r.integers(0, DAY)))
                    if signup < t < C:
                        my_o.append([t, "addon", int(r.integers(499, 3000))])
            for _ in range(r.poisson(p["ticket_base"] + p["ticket_x"] * x[j] + (p["ticket_pf"] if pf_today else 0))):
                t = _sod(day_start + int(r.integers(0, DAY)))
                if signup < t < C:
                    topic = "billing" if pf_today else str(r.choice(["delivery", "quality", "account", "billing"]))
                    my_t.append([t, topic])
                    if t >= SCORING_FROM and r.random() < p["ticket_score_p"]:
                        cpts.append([t, "ticket", len(my_t) - 1])
            # batch scoring every second billing day at 06:00, from two weeks after signup
            t = day_start + BATCH_AT
            if (d >= first_box and (d - first_box) % 14 == 0 and t >= SCORING_FROM and t >= signup + 14 * DAY
                    and t < C):
                cpts.append([t, "batch", -1])
            if churns and d == C // DAY and r.random() < p["cancel_ticket_p"]:
                t = _sod(max(signup + 1, C - int(r.integers(60, 2 * HOUR))))
                my_t.append([t, "account"])
                if t >= SCORING_FROM and r.random() < p["ticket_score_p"]:
                    cpts.append([t, "ticket", len(my_t) - 1])
            st = "cancelled" if (churns and d == C // DAY) else state
            if st != prev or int(d) in month_first:
                my_s.append((cid, day_start, st))
            prev = st
            if st == "cancelled":
                break
        _fix_edges(my_o, my_t, cpts)
        orders.extend((cid, o[0], o[1], o[2]) for o in my_o)
        tickets.extend((cid, tk[0], tk[1]) for tk in my_t)
        snaps.extend(my_s)
        # app minutes and labels for this customer's points ((customer_id, as_of) unique; batch wins a tie)
        seen = set()
        for (t, trig, _) in sorted((c[0], c[1], c[2]) for c in cpts):
            if t in seen:
                continue
            seen.add(t)
            dnow = t // DAY
            m = (days >= dnow - 7) & (days < dnow)
            level = g[m].mean() if m.any() else g[0]
            mins = float(r.poisson(p["app_scale"] * level))
            if outage[dnow - T0 // DAY] or r.random() < p["app_missing"]:
                mins = np.nan
            points.append((cid, t, trig, mins))
            y = 1 if (churns and t < C <= t + 30 * DAY) else 0
            labels.append((cid, t, y, C if y else t + 30 * DAY))   # the outcome is known at C, else at t + 30 days
        # logins and the CRM sync's view of the customer
        lg = login_times(np.random.default_rng([seed, cid, 2]), signup, C, days, x, g0, p)
        k0 = int(np.searchsorted(sync_start, signup, side="right"))
        S = sync_start[k0:]
        li = np.searchsorted(lg, S, side="left") - 1
        ci = np.searchsorted(np.array(ch_t, dtype=np.int64), S, side="left") - 1
        cur = (plan0, None)
        for jj in range(len(S)):
            pl = chg[ci[jj]][2] if ci[jj] >= 0 else plan0
            ll = int(lg[li[jj]]) if li[jj] >= 0 else None
            if (pl, ll) != cur:
                writes.append((cid, k0 + jj, pl, ll))
                cur = (pl, ll)
        for (t, old, new) in chg:
            changes.append((cid, t, old, new, int(np.searchsorted(sync_start, t, side="right"))))
    t = {
        "customers": pd.DataFrame(cust, columns=["customer_id", "signup_at", "plan0", "postcode_district",
                                                 "cancelled_at"]),
        "orders": pd.DataFrame(orders, columns=["customer_id", "ordered_at", "kind", "amount_cents"]),
        "tickets": pd.DataFrame(tickets, columns=["customer_id", "opened_at", "topic"]),
        "snapshots": pd.DataFrame(snaps, columns=["customer_id", "snapshot_date", "status"]),
        "points": pd.DataFrame(points, columns=["customer_id", "as_of", "trigger", "app_minutes_7d"]),
        "labels": pd.DataFrame(labels, columns=["customer_id", "as_of", "churned_30d", "known_at"]),
        "plan_changes": pd.DataFrame(changes, columns=["customer_id", "changed_at", "old_plan", "new_plan", "sync"]),
        "crm_writes": pd.DataFrame(writes, columns=["customer_id", "sync", "plan", "last_login_at"]),
    }
    t["crm_writes"]["last_login_at"] = pd.array(
        [pd.NA if v is None or (isinstance(v, float) and np.isnan(v)) else int(v)
         for v in t["crm_writes"]["last_login_at"].tolist()], dtype="Int64")
    t["points"]["app_minutes_7d"] = t["points"]["app_minutes_7d"].astype("float64")
    for name in ("orders", "tickets"):
        col = "ordered_at" if name == "orders" else "opened_at"
        t[name] = t[name].sort_values([col, "customer_id"], kind="mergesort").reset_index(drop=True)
    return t


# ------------------------------------------------------------------------------------------------ loaders
def sync_schedule(seed, l):
    """crm_sync: Sundays 23:00 UTC, one in 15 late by 3-30 h; commit 4-20 min after its start."""
    rb = np.random.default_rng([seed, 105])
    first_sunday = T0 // DAY + (6 - pd.Timestamp(T0, unit="s").weekday()) % 7
    sundays = np.arange(first_sunday, HORIZON // DAY + 8, 7, dtype=np.int64)
    n = len(sundays)
    start = sundays * DAY + 23 * HOUR + rb.integers(0, 61, n)
    late = rb.random(n) < l["sync_late"]
    start = np.where(late, start + rb.integers(3 * HOUR, 30 * HOUR, n), start)
    commit = start + rb.integers(4 * 60, 20 * 60 + 1, n)
    return pd.DataFrame({"start": start, "commit": commit, "late": late})


def legacy_schedule(seed, cfg, l):
    """legacy_orders: a run at 02:30 each night up to the move day, watermark 00:00 of its run date."""
    rb = np.random.default_rng([seed, 101])
    move_day = ts(cfg["move"]) // DAY
    days = np.arange(T0 // DAY + 1, move_day + 1, dtype=np.int64)
    n = len(days)
    u_fail, u_late = rb.random(n), rb.random(n)
    jit = rb.integers(0, 46, n)
    dur_ok = rb.integers(15 * 60, 55 * 60 + 1, n)
    dur_late = rb.integers(int(3.6 * HOUR), 8 * HOUR + 1, n)      # finishes 06:06-10:30, after the 06:00 batch
    dur_fail = rb.integers(4 * 60, 40 * 60 + 1, n)
    out_len = int(rb.integers(l["legacy_outage"][0], l["legacy_outage"][1] + 1))
    protect = np.zeros(n, bool)
    protect[-1] = True                                             # the last run (the move night) is ok
    if cfg["shadow"]:
        protect |= (days >= SHADOW_FROM // DAY - 2) & (days < SHADOW_TO // DAY)
    lo = int(np.searchsorted(days, SCORING_FROM // DAY + 30))
    hi = n - 30 - out_len
    cand = [s for s in range(lo, hi) if not protect[max(0, s - 10): s + out_len + 10].any()]
    s0 = cand[int(rb.integers(0, len(cand)))]
    fail = u_fail < l["legacy_fail"]
    late = (~fail) & (u_late < l["legacy_late"])
    fail[s0:s0 + out_len] = True
    late[s0:s0 + out_len] = False
    fail[protect] = False
    late[protect] = False
    started = days * DAY + 2 * HOUR + 30 * 60 + jit
    finished = started + np.where(fail, dur_fail, np.where(late, dur_late, dur_ok))
    runs = pd.DataFrame({"run_id": cfg["run0"] + np.arange(n), "run_date": days * DAY, "started_at": started,
                         "finished_at": finished, "status": np.where(fail, "failed", "ok"), "watermark": days * DAY})
    return runs, {"start": int(days[s0] * DAY), "nights": out_len, "late": late, "fail": fail}


def hourly_schedule(seed, cfg, l):
    """orders_hourly: a run at about :20 each hour from the first run on the move day; it loads the orders with
    ordered_at before the top of its hour not yet loaded; 2% fail (the next ok run catches up)."""
    rb = np.random.default_rng([seed, 102])
    first = ts(cfg["first_hourly_run"])
    tops = np.arange(first - 20 * 60, HORIZON + 2 * DAY, HOUR, dtype=np.int64)
    n = len(tops)
    commit = tops + 20 * 60 + rb.integers(-120, 301, n)
    commit[0] = first + int(rb.integers(0, 60))
    ok = rb.random(n) >= l["hourly_fail"]
    ok[0] = True
    return pd.DataFrame({"top": tops, "commit": commit, "ok": ok})


def export_schedule(seed, cfg, l):
    """billing_export: the partition of snapshots dated D commits at about 06:30 on D+1; some land late (before the
    next day's partition), some after the next day's (out of order); late_month_n month-start partitions (the brand's
    fixed ones first, then random ones) land 5 to 9 days after their normal 06:30 landing on D+1."""
    rb = np.random.default_rng([seed, 103])
    dates = np.arange(T0 // DAY, HORIZON // DAY + 1, dtype=np.int64)
    n = len(dates)
    base = (dates + 1) * DAY + 6 * HOUR + 30 * 60 + rb.integers(-180, 901, n)
    u = rb.random(n)
    late_in = (dates + 1) * DAY + rb.integers(9 * HOUR, 29 * HOUR, n)
    late_ooo = (dates + 2) * DAY + rb.integers(7 * HOUR, 36 * HOUR, n)
    kind = np.where(u < l["export_late"], 1, np.where(u < l["export_late"] + l["export_ooo"], 2, 0))
    commit = np.where(kind == 1, late_in, np.where(kind == 2, late_ooo, base))
    month_starts = [int(d) for d in dates if pd.Timestamp(int(d) * DAY, unit="s").day == 1
                    and ts("2024-09-01") // DAY <= d <= ts("2026-02-01") // DAY]
    order = rb.permutation(len(month_starts))
    delay = rb.integers(l["month_late_days"][0] * DAY, l["month_late_days"][1] * DAY, 8)   # [5 days, 9 days)
    chosen = [ts(s) // DAY for s in cfg["late_month_starts"]]
    for i in order.tolist():
        if len(chosen) >= l["late_month_n"]:
            break
        if month_starts[i] not in chosen:
            chosen.append(month_starts[i])
    for j, d in enumerate(chosen):
        i = int(d - dates[0])
        commit[i] = (d + 1) * DAY + 6 * HOUR + 30 * 60 + int(delay[j])
        kind[i] = 3
    return pd.DataFrame({"partition": dates * DAY, "commit": commit, "kind": kind}), chosen


def label_schedule(seed, l):
    """label_job: a run at 03:30 each night commits the labels whose outcome became known before its start; 3% of
    nights fail (the next ok run catches up)."""
    rb = np.random.default_rng([seed, 104])
    days = np.arange(T0 // DAY, HORIZON // DAY + 45, dtype=np.int64)
    n = len(days)
    start = days * DAY + 3 * HOUR + 30 * 60
    commit = start + rb.integers(3 * 60, 25 * 60 + 1, n)
    ok = rb.random(n) >= l["label_fail"]
    return pd.DataFrame({"start": start, "commit": commit, "ok": ok})


def _away(arr, as_of):
    """Move commit times that fall on the second of a scoring point by one second until none does."""
    arr = np.asarray(arr, dtype=np.int64).copy()
    for _ in range(100):
        bad = np.isin(arr, as_of)
        if not bad.any():
            return arr
        arr[bad] += 1
    raise AssertionError("commit nudge did not converge")


# ------------------------------------------------------------------------------------- the scheduler's records
# Added 2026-10-31. Every scheduled job writes each task run to the scheduler's log and each transaction it sends to
# the commit log; ops_log.py renders both files of an extract's _ops/ folder from the two frames built here
# (tasks: one row per task run; parity: one row per dq_checks line) and parses them back.
# The order loaders' migration: from d0, 56 days before the move day C, orders_hourly commits every hour into
# `orders_new` while legacy_orders keeps committing every night into `orders`. On d0, after that night's legacy run,
# legacy_backfill copies the rows of `orders` with ordered_at < d0 into `orders_new`. On C, after C's legacy run,
# dq_checks compares both tables for every order day d0 to C - 1 day; then one schema_migrations transaction renames
# `orders` to `orders_legacy` and `orders_new` to `orders`, 5 to 60 s before the start of the first hourly run into
# `orders` (the first run of hourly_schedule, which is as before the revision); a second one drops `orders_legacy` on
# C + 7 days. A query reads a table by the name it has when the query starts, so an order placed
# before C is visible from the legacy commit of the range holding it (as before), an order that the dual run
# committed into `orders_new` from the rename, and every later order from its own commit. No scoring point lies
# between the rename task's start and the first hourly commit (asserted), so no live value changes.
CUTOVER_SQL = "ALTER TABLE orders RENAME TO orders_legacy; ALTER TABLE orders_new RENAME TO orders"
DROP_SQL = "DROP TABLE orders_legacy"
TASK_COLS = ["job", "run", "started_at", "end_at", "state", "lo", "hi", "source", "statements", "table", "rows",
             "txn", "sent_at", "at", "outcome", "analyze_at"]
TASK_STR = ["job", "run", "state", "source", "statements", "table", "outcome"]
TASK_NULLABLE = ["lo", "hi", "rows", "txn", "sent_at", "at", "analyze_at"]
PARITY_COLS = ["run", "at", "day", "table_a", "rows_a", "table_b", "rows_b"]
NA = -(2 ** 63)                     # a field that does not apply, inside the builder (NA or "" in the frames)


def _dates(sec):
    return np.asarray(pd.to_datetime(np.asarray(sec, dtype=np.int64), unit="s").strftime("%Y-%m-%d"), dtype=object)


def _tops(sec):
    return np.asarray(pd.to_datetime(np.asarray(sec, dtype=np.int64), unit="s").strftime("%Y-%m-%dT%H:%M:%SZ"),
                      dtype=object)


def _sent(at, s, as_of):
    """Send times: s seconds before each commit, or the latest scoring second before the commit when that is later,
    so no scoring point lies strictly between a transaction's send and its commit (as_of sorted and unique)."""
    at = np.asarray(at, dtype=np.int64)
    j = np.searchsorted(as_of, at, side="left") - 1
    prev = np.where(j >= 0, as_of[np.maximum(j, 0)], NA)
    return np.maximum(at - np.asarray(s, dtype=np.int64), prev)


def _per_row(rng, n, spec):
    """n rows of draws, row by row and within a row in the order of spec: (a, b) an integer in a..b, None a uniform
    float in [0, 1). Returns one array per spec entry."""
    out = [np.empty(n, dtype=np.int64 if c is not None else np.float64) for c in spec]
    for i in range(n):
        for k, c in enumerate(spec):
            out[k][i] = rng.integers(c[0], c[1] + 1) if c is not None else rng.random()
    return out


def _chain(hi, ok, lo0):
    """lo of each load task: the hi of the same job's last committed task before it (lo0 before the first commit)."""
    lo, cur = np.empty(len(hi), dtype=np.int64), int(lo0)
    for i, (h, k) in enumerate(zip(np.asarray(hi).tolist(), np.asarray(ok).tolist())):
        lo[i] = cur
        if k:
            cur = int(h)
    return lo


def _part(job, run, started, end, ok=None, **given):
    """One job's task runs as builder columns: scalars are broadcast, a field not given is NA ("" for strings);
    ok (per task, or None for a task that sends no transaction) sets state and outcome."""
    n = len(run)
    out = {}
    for c in TASK_COLS:
        if c in TASK_STR:
            v = given.get(c, "")
            out[c] = np.array([v] * n, dtype=object) if isinstance(v, str) else np.asarray(v, dtype=object)
        else:
            v = given.get(c, NA)
            out[c] = np.full(n, v, dtype=np.int64) if np.ndim(v) == 0 else np.asarray(v, dtype=np.int64)
    out["job"][:] = job
    out["run"] = np.asarray(run, dtype=object)
    out["started_at"], out["end_at"] = np.asarray(started, np.int64), np.asarray(end, np.int64)
    ok = np.ones(n, bool) if ok is None else np.asarray(ok, bool)
    out["state"] = np.where(ok, "success", "failed").astype(object)
    sends = out["sent_at"] != NA
    out["outcome"] = np.where(sends, np.where(ok, "commit", "rollback"), "").astype(object)
    for c in TASK_COLS:
        assert len(out[c]) == n, (job, c)
    return out


def scheduler_runs(seed, cfg, l, runs, hourly, exports, lab_runs, syncs, as_of, move0):
    """Every task run of the scheduled jobs, with its record times (int64 seconds) and its ranges, as builder columns
    per job; counts and transaction numbers are added from the extract by ops_frames. Uses streams [seed, 107-109]
    (module docstring). Returns the parts and the times the orders' loads need."""
    d0 = ts(cfg["d0"])
    f_top, f_commit = int(hourly["top"].iloc[0]), int(hourly["commit"].iloc[0])
    parts = {}
    # legacy_orders: the run table's runs. An ok run commits at its finished_at (its commit as before the revision),
    # then analyzes the table and ends; a failed run rolls back at its finished_at and ends 1 to 5 s later. Each run
    # loads [lo, its watermark).
    rl = np.random.default_rng([seed, 107])
    n = len(runs)
    s, a, u, u_long = _per_row(rl, n, [(1, 20), (1, 10), None, None])
    at = runs["finished_at"].to_numpy(dtype=np.int64)
    ok = (runs["status"] == "ok").to_numpy()
    span = np.where(u_long < l["analyze_long_p"], 10800 + np.floor(u * 7201), 300 + np.floor(u * 2101))
    hi = runs["watermark"].to_numpy(dtype=np.int64)
    leg_end = np.where(ok, at + a + span.astype(np.int64), at + 1 + (a - 1) % 5)
    parts["legacy_orders"] = _part("legacy_orders", _dates(runs["run_date"]), runs["started_at"], leg_end, ok,
                                   lo=_chain(hi, ok, T0), hi=hi, table="orders", sent_at=_sent(at, s, as_of), at=at,
                                   analyze_at=np.where(ok, at + a, NA))
    i_d0, i_c = int(np.searchsorted(hi, d0)), len(hi) - 1
    assert hi[i_d0] == d0 and hi[i_c] == move0, "the d0 or move-day legacy run is missing"
    # legacy_backfill on d0, after that night's legacy run
    rm = np.random.default_rng([seed, 108])
    b_lag0 = int(rm.integers(60, 601))
    b_lag1 = int(rm.integers(600, 2401))
    b_s = int(rm.integers(1, 21))
    b_lag2 = int(rm.integers(1, 6))
    b_start = int(leg_end[i_d0]) + b_lag0
    b_at = int(_away([b_start + b_lag1 + b_s], as_of)[0])
    b_sent = int(_sent([b_at], [b_s], as_of)[0])
    b_end = b_at + b_lag2
    parts["legacy_backfill"] = _part("legacy_backfill", _dates([d0]), [b_start], [b_end], [True], hi=d0,
                                     source="orders", table="orders_new", sent_at=[b_sent], at=[b_at])
    # orders_hourly into orders_new (the dual run): every top from the hour after the backfill ends to the hour before
    # the first hourly run into orders; draws for every top to 23:00 of the move day, so their count is fixed
    top0 = (b_end // HOUR + 1) * HOUR
    tops = np.arange(top0, move0 + 23 * HOUR + 1, HOUR, dtype=np.int64)
    k = len(tops)
    off, u_ok = _per_row(rm, k, [(-120, 300), None])
    d_s, d_lag0, d_lag2 = _per_row(rm, k, [(1, 20), (10, 80), (1, 5)])
    q_lag = int(rm.integers(60, 601))
    x_lead = int(rm.integers(5, 61))
    x_s = int(rm.integers(1, 6))
    dr_send = int(rm.integers(0, 3601))
    dr_lag = int(rm.integers(1, 6))
    keep = tops <= f_top - HOUR
    tops, off, u_ok, d_s, d_lag0, d_lag2 = (v[keep] for v in (tops, off, u_ok, d_s, d_lag0, d_lag2))
    d_ok = u_ok >= l["hourly_fail"]
    d_ok[tops == move0] = True                     # the move day's 00:00 top commits: orders_new holds [d0, C)
    d_at = _away(tops + 20 * 60 + off, as_of)
    d_sent = _sent(d_at, d_s, as_of)
    # orders_hourly into orders: the hourly runs as before, their record times from stream [seed, 109]
    rr = np.random.default_rng([seed, 109])
    h_s, h_lag0, h_lag2 = _per_row(rr, len(hourly), [(1, 20), (10, 80), (1, 5)])
    l_s, l_lag2 = _per_row(rr, len(lab_runs), [(1, 20), (1, 5)])
    e_s, e_lag0, e_lag2 = _per_row(rr, len(exports), [(1, 20), (60, 300), (1, 5)])
    s_s, s_lag2 = _per_row(rr, len(syncs), [(1, 20), (1, 5)])
    h_at = hourly["commit"].to_numpy(dtype=np.int64)
    h_ok = hourly["ok"].to_numpy(dtype=bool)
    h_sent = _sent(h_at, h_s, as_of)
    c_hi = np.concatenate([tops, hourly["top"].to_numpy(dtype=np.int64)])
    c_ok = np.concatenate([d_ok, h_ok])
    c_at = np.concatenate([d_at, h_at])
    c_sent = np.concatenate([d_sent, h_sent])
    c_start = c_sent - np.concatenate([d_lag0, h_lag0])
    c_end = c_at + np.concatenate([d_lag2, h_lag2])
    c_lo = _chain(c_hi, c_ok, d0)
    assert (np.diff(c_hi) == HOUR).all(), "the hourly tops are not consecutive"
    n_dual = len(tops)
    c_sel = np.concatenate([np.ones(n_dual, bool), h_at < EXTRACT_AT])
    assert (c_start[~c_sel] >= EXTRACT_AT).all(), "an hourly run starts before the extract but commits after it"
    parts["orders_hourly"] = _part(
        "orders_hourly", _tops(c_hi[c_sel]), c_start[c_sel], c_end[c_sel], c_ok[c_sel], lo=c_lo[c_sel],
        hi=c_hi[c_sel], table=np.array(["orders_new"] * n_dual + ["orders"] * int(c_sel[n_dual:].sum()), object),
        sent_at=c_sent[c_sel], at=c_at[c_sel])
    fh_start = int(c_start[n_dual])
    # dq_checks on C, after C's legacy run: one parity line per order day d0 .. C - 1 day, a second apart
    n_days = (move0 - d0) // DAY
    q_start = int(leg_end[i_c]) + q_lag
    q_end = q_start + 1 + n_days
    parts["dq_checks"] = _part("dq_checks", _dates([move0]), [q_start], [q_end])
    par_at, par_day = q_start + 1 + np.arange(n_days, dtype=np.int64), d0 + DAY * np.arange(n_days, dtype=np.int64)
    # the cutover (two statements, then the send) and the drop (one statement): statement k at started_at + k
    x_at = int(_away([fh_start - x_lead], as_of)[0])
    for _ in range(3600):
        x_sent = int(_sent([x_at], [x_s], as_of)[0])
        if not ((as_of >= x_sent - 3) & (as_of <= f_commit)).any():
            break
        x_at = int(_away([x_at + 1], as_of)[0])    # a scoring point at or after the cutover's start: move it later
    else:
        raise AssertionError("no cutover second without a scoring point before the first hourly commit")
    assert x_at < fh_start, "the cutover does not commit before the first hourly run into orders starts"
    dr_at = int(_away([move0 + 7 * DAY + 3 * HOUR + dr_send + dr_lag], as_of)[0])
    dr_sent = int(_sent([dr_at], [dr_lag], as_of)[0])
    parts["schema_migrations"] = _part(
        "schema_migrations", _dates([move0, move0 + 7 * DAY]), [x_sent - 3, dr_sent - 2], [x_at + 1, dr_at + 1],
        [True, True], statements=np.array([CUTOVER_SQL, DROP_SQL], object), sent_at=[x_sent, dr_sent],
        at=[x_at, dr_at])
    # label_job: the runs started before the extract; a failed run sends no transaction and ends at its finish
    l_sel = (lab_runs["start"] < EXTRACT_AT).to_numpy()
    l_ok = lab_runs["ok"].to_numpy(dtype=bool)
    l_at = lab_runs["commit"].to_numpy(dtype=np.int64)
    l_start = lab_runs["start"].to_numpy(dtype=np.int64)
    l_sent = np.where(l_ok, _sent(l_at, l_s, as_of), NA)
    parts["label_job"] = _part("label_job", _dates(l_start[l_sel]), l_start[l_sel],
                               np.where(l_ok, l_at + l_lag2, l_at)[l_sel], l_ok[l_sel],
                               table=np.where(l_ok, "labels", "")[l_sel].astype(object), sent_at=l_sent[l_sel],
                               at=np.where(l_ok, l_at, NA)[l_sel])
    # billing_export: one partition (snapshot date) per run, the runs that committed before the extract
    e_at = exports["commit"].to_numpy(dtype=np.int64)
    e_sent = _sent(e_at, e_s, as_of)
    e_start, e_end = e_sent - e_lag0, e_at + e_lag2
    e_sel = e_at < EXTRACT_AT
    assert (e_start[~e_sel] >= EXTRACT_AT).all(), "an export starts before the extract but commits after it"
    parts["billing_export"] = _part("billing_export", _dates(exports["partition"].to_numpy()[e_sel]), e_start[e_sel],
                                    e_end[e_sel], table="status_snapshots", sent_at=e_sent[e_sel], at=e_at[e_sel])
    # crm_sync: run = its Sunday (a late sync starts a day or two later), the syncs that committed before the extract
    first_sunday = T0 // DAY + (6 - pd.Timestamp(T0, unit="s").weekday()) % 7
    sundays = np.arange(first_sunday, HORIZON // DAY + 8, 7, dtype=np.int64)
    assert len(sundays) == len(syncs), "sync schedule changed"
    s_at = syncs["commit"].to_numpy(dtype=np.int64)
    s_start = syncs["start"].to_numpy(dtype=np.int64)
    s_sent = _sent(s_at, s_s, as_of)
    s_sel = s_at < EXTRACT_AT
    assert (s_start[~s_sel] >= EXTRACT_AT).all(), "a sync starts before the extract but commits after it"
    parts["crm_sync"] = _part("crm_sync", _dates(sundays[s_sel] * DAY), s_start[s_sel], (s_at + s_lag2)[s_sel],
                              table="plan_changes", sent_at=s_sent[s_sel], at=s_at[s_sel])
    return dict(parts=parts, d0=d0, backfill_at=b_at, cutover_at=x_at, hourly_hi=c_hi, hourly_ok=c_ok,
                hourly_at=c_at, n_dual=n_dual, parity_at=par_at, parity_day=par_day)


def order_loads(oa, rec):
    """Per order (ordered_at sorted): the job that wrote its row and that job's commit (the audit columns), and
    whether the dual run committed it into orders_new before the rename."""
    d0, ok = rec["d0"], rec["hourly_ok"]
    hi, at = rec["hourly_hi"][ok], rec["hourly_at"][ok]
    nd = int(ok[:rec["n_dual"]].sum())             # committed dual-run tasks (they come first)
    j = np.searchsorted(hi, oa, side="right")      # the first committed hourly run whose hi is above the order
    loaded = np.where(j < len(at), at[np.minimum(j, len(at) - 1)], NEVER)
    backfill = oa < d0
    loaded = np.where(backfill, rec["backfill_at"], loaded)
    return np.where(backfill, "legacy_backfill", "orders_hourly"), loaded, (~backfill) & (j < nd)


def ops_frames(rec, tabs, cfg):
    """The tasks and parity frames of the extract's _ops/ records: every count recounted from the extract's tables
    (tabs), transaction numbers txn0 + rank of (sent_at, job, run), the column order and dtypes of the records."""
    parts = rec["parts"]
    x = np.sort(tabs["orders"]["ordered_at"].to_numpy(dtype=np.int64))

    def between(lo, hi):
        return np.searchsorted(x, hi, side="left") - np.searchsorted(x, lo, side="left")

    for job in ("legacy_orders", "orders_hourly"):
        parts[job]["rows"] = between(parts[job]["lo"], parts[job]["hi"])
    parts["legacy_backfill"]["rows"] = np.searchsorted(x, parts["legacy_backfill"]["hi"], side="left")
    for job, table, col in (("label_job", "labels", "_loaded_at"), ("crm_sync", "plan_changes", "_loaded_at"),
                            ("billing_export", "status_snapshots", "snapshot_date")):
        keys, counts = np.unique(tabs[table][col].to_numpy(dtype=np.int64), return_counts=True)
        p = parts[job]
        q = p["at"] if job != "billing_export" else ts_dates(p["run"])
        jj = np.minimum(np.searchsorted(keys, q), len(keys) - 1)
        p["rows"] = np.where(p["sent_at"] != NA, np.where(keys[jj] == q, counts[jj], 0), NA)
    cols = {c: np.concatenate([parts[j][c] for j in parts]) for c in TASK_COLS}
    sends = np.flatnonzero(cols["sent_at"] != NA)
    rank = np.lexsort((cols["run"][sends].astype(str), cols["job"][sends].astype(str), cols["sent_at"][sends]))
    cols["txn"] = np.full(len(cols["job"]), NA, dtype=np.int64)
    cols["txn"][sends[rank]] = cfg["txn0"] + np.arange(len(sends), dtype=np.int64)
    order = np.lexsort((cols["run"].astype(str), cols["job"].astype(str), cols["started_at"]))
    tasks = pd.DataFrame(index=pd.RangeIndex(len(order)))
    for c in TASK_COLS:
        v = cols[c][order]
        if c in TASK_STR:
            tasks[c] = pd.array(v.tolist(), dtype="str")
        elif c in TASK_NULLABLE:
            tasks[c] = pd.arrays.IntegerArray(np.where(v == NA, 0, v).astype(np.int64), v == NA)
        else:
            tasks[c] = v.astype(np.int64)
    day = rec["parity_day"]
    n = between(day, day + DAY)
    parity = pd.DataFrame({"run": pd.array([_dates([day[-1] + DAY])[0]] * len(day), dtype="str"),
                           "at": rec["parity_at"].astype(np.int64), "day": day.astype(np.int64),
                           "table_a": pd.array(["orders"] * len(day), dtype="str"), "rows_a": n.astype(np.int64),
                           "table_b": pd.array(["orders_new"] * len(day), dtype="str"),
                           "rows_b": n.astype(np.int64).copy()})
    return {"tasks": tasks, "parity": parity}


def ts_dates(run):
    """`YYYY-MM-DD` strings -> epoch seconds of 00:00 UTC."""
    return np.array([ts(r) for r in np.asarray(run, dtype=object).tolist()], dtype=np.int64)


def brand_world(name, p=None, l=None, n_customers=N_CUSTOMERS):
    """The simulator's true state for one brand: every row with its true commit time `visible_at`, and (since
    2026-10-31) the scheduler's records of the extract, w["ops"], with d0 and cutover_at."""
    p = P if p is None else p
    l = L if l is None else l
    cfg = BRANDS[name]
    seed = cfg["seed"]
    syncs = sync_schedule(seed, l)
    sim = simulate(seed, cfg["cust0"], p, syncs["start"].to_numpy(), n_customers)
    as_of = np.unique(sim["points"]["as_of"].to_numpy())
    move0, first_hourly = ts(cfg["move"]), ts(cfg["first_hourly_run"])
    runs, outage = legacy_schedule(seed, cfg, l)
    hourly = hourly_schedule(seed, cfg, l)
    exports, late_month = export_schedule(seed, cfg, l)
    lab_runs = label_schedule(seed, l)
    # no commit falls on the second of any scoring point, so `<` against `<=` never decides a value
    runs["finished_at"] = _away(runs["finished_at"], as_of)
    hourly["commit"] = _away(hourly["commit"], as_of)
    exports["commit"] = _away(exports["commit"], as_of)
    lab_runs["commit"] = _away(lab_runs["commit"], as_of)
    syncs["commit"] = _away(syncs["commit"], as_of)

    # orders: the loader that really committed each row
    o = sim["orders"]
    o.insert(0, "order_id", np.arange(cfg["order0"], cfg["order0"] + len(o), dtype=np.int64))
    oa = o["ordered_at"].to_numpy()
    vis = np.full(len(o), NEVER, dtype=np.int64)
    n_leg = int(np.searchsorted(oa, move0, side="left"))
    ptr = 0
    for wm, fin, st in zip(runs["watermark"].tolist(), runs["finished_at"].tolist(), runs["status"].tolist()):
        if st == "ok":       # an ok run commits every order before its watermark that no earlier run committed
            hi = int(np.searchsorted(oa, wm, side="left"))
            if hi > ptr:
                vis[ptr:hi] = fin
                ptr = hi
    assert ptr == n_leg, "legacy runs left orders before the move uncommitted"
    ptr = n_leg
    for top, cm, ok in zip(hourly["top"].tolist(), hourly["commit"].tolist(), hourly["ok"].tolist()):
        if ok:               # an ok hourly run commits every order before the top of its hour not yet loaded
            hi = int(np.searchsorted(oa, top, side="left"))
            if hi > ptr:
                vis[ptr:hi] = cm
                ptr = hi
    o["visible_at"] = vis              # the dual run's orders of the move day are set below, from the records

    # tickets: change data capture 1-30 s after opened_at, always before the customer's next scoring point
    k = sim["tickets"]
    k.insert(0, "ticket_id", np.arange(cfg["ticket0"], cfg["ticket0"] + len(k), dtype=np.int64))
    lag = np.random.default_rng([seed, 106]).integers(l["ticket_lag"][0], l["ticket_lag"][1] + 1, len(k))
    pkeys = np.sort(sim["points"]["customer_id"].to_numpy() * STRIDE + sim["points"]["as_of"].to_numpy())
    tkey = k["customer_id"].to_numpy() * STRIDE + k["opened_at"].to_numpy()
    j = np.searchsorted(pkeys, tkey, side="right")
    nxt = pkeys[np.minimum(j, len(pkeys) - 1)]
    same = (j < len(pkeys)) & (nxt // STRIDE == k["customer_id"].to_numpy())
    gap = np.where(same, nxt - tkey, 10 ** 9)
    assert (gap >= 2).all(), "a scoring point one second after a ticket"
    lag = np.minimum(lag, gap - 1)
    for _ in range(100):
        bad = np.isin(k["opened_at"].to_numpy() + lag, as_of)
        if not bad.any():
            break
        lag[bad] -= 1
    assert (lag >= 1).all() and not np.isin(k["opened_at"].to_numpy() + lag, as_of).any()
    k["visible_at"] = k["opened_at"].to_numpy() + lag
    k["_loaded_at"] = k["visible_at"]

    # status snapshots: the partition of their date
    s = sim["snapshots"]
    s["visible_at"] = exports["commit"].to_numpy()[(s["snapshot_date"].to_numpy() // DAY - T0 // DAY)]
    s["_loaded_at"] = s["visible_at"]

    # labels: the first ok label_job run that starts after the outcome became known
    lb = sim["labels"]
    okr = lab_runs[lab_runs["ok"]]
    kk = np.searchsorted(okr["start"].to_numpy(), lb["known_at"].to_numpy(), side="right")
    commits = np.concatenate([okr["commit"].to_numpy(), [NEVER]])
    lb["visible_at"] = commits[kk]
    lb["_loaded_at"] = lb["visible_at"]

    # plan changes and the customer record: the sync that applied or wrote them
    sc = np.concatenate([syncs["commit"].to_numpy(), [NEVER]])
    pcg = sim["plan_changes"]
    pcg["_loaded_at"] = sc[pcg["sync"].to_numpy()]
    wr = sim["crm_writes"]
    wr["commit"] = sc[wr["sync"].to_numpy()]

    # the scheduler's records (added 2026-10-31): every job's task runs and transactions, the orders' audit columns
    # from the loads they describe, and the rename's effect on the dual run's orders of the move day
    rec = scheduler_runs(seed, cfg, l, runs, hourly, exports, lab_runs, syncs, as_of, move0)
    job, loaded, dual = order_loads(oa, rec)
    o["_load_job"] = job
    o["_loaded_at"] = loaded
    moved = dual & (oa >= move0)                     # in orders_new at the rename, placed on the move day
    o["visible_at"] = np.where(moved, rec["cutover_at"], vis)
    w = dict(name=name, cfg=cfg, seed=seed, customers=sim["customers"], orders=o, tickets=k, snapshots=s,
             labels=lb, points=sim["points"], plan_changes=pcg, crm_writes=wr, legacy_runs=runs, hourly=hourly,
             exports=exports, label_runs=lab_runs, syncs=syncs, move0=move0, backfill_at=rec["backfill_at"],
             first_hourly=first_hourly, outage=outage, late_month=late_month, d0=rec["d0"],
             cutover_at=rec["cutover_at"])
    tabs = _tables_at(w, EXTRACT_AT)
    w["ops"] = ops_frames(rec, tabs, cfg)
    # every order that a load task selected is in the extract (none waits behind a rolled-back last task), so each
    # count is the world's
    t = w["ops"]["tasks"]
    m = t["job"].isin(["legacy_orders", "orders_hourly"]).to_numpy()
    lo, hi = t.loc[m, "lo"].to_numpy(dtype=np.int64), t.loc[m, "hi"].to_numpy(dtype=np.int64)
    world_rows = np.searchsorted(oa, hi, side="left") - np.searchsorted(oa, lo, side="left")
    assert (world_rows == t.loc[m, "rows"].to_numpy(dtype=np.int64)).all(), (name, "a load's rows not all extracted")
    return w


def _tables_at(w, at):
    """The seven tables as the warehouse held them at `at` (int64 seconds; the layout of extract_io.TABLES)."""
    cu = w["customers"][w["customers"]["signup_at"] < at]
    wr = w["crm_writes"][w["crm_writes"]["commit"] < at].sort_values(["customer_id", "commit"], kind="mergesort")
    last = wr.groupby("customer_id", sort=False).tail(1)[["customer_id", "plan", "last_login_at", "commit"]]
    cur = cu.merge(last, on="customer_id", how="left")
    has = cur["commit"].notna().to_numpy()
    customers = pd.DataFrame({
        "customer_id": cur["customer_id"].to_numpy(),
        "signup_at": cur["signup_at"].to_numpy(),
        "plan": np.where(has, cur["plan"].astype(object), cur["plan0"].astype(object)),
        "postcode_district": cur["postcode_district"].to_numpy(),
        "last_login_at": pd.array(cur["last_login_at"], dtype="Int64"),
        "_updated_at": np.where(has, cur["commit"].fillna(0).astype(np.int64), cur["signup_at"]).astype(np.int64),
    })
    pcg = w["plan_changes"]
    o, k, s, lb = w["orders"], w["tickets"], w["snapshots"], w["labels"]
    return {
        "customers": customers,
        "plan_changes": pcg[pcg["_loaded_at"] < at][extract_io.TABLES["plan_changes"]].reset_index(drop=True),
        "scoring_points": w["points"][w["points"]["as_of"] < at].reset_index(drop=True),
        "orders": o[o["_loaded_at"] < at][extract_io.TABLES["orders"]].reset_index(drop=True),
        "tickets": k[k["_loaded_at"] < at][extract_io.TABLES["tickets"]].reset_index(drop=True),
        "status_snapshots": s[s["_loaded_at"] < at][extract_io.TABLES["status_snapshots"]].reset_index(drop=True),
        "labels": lb[lb["_loaded_at"] < at][extract_io.TABLES["labels"]].reset_index(drop=True),
    }


def extract_tables(w, at=EXTRACT_AT):
    """The seven tables as the warehouse held them at `at`, plus "_ops", the scheduler's records written before the
    extract time (w["ops"], counted on the extract), when `at` is the extract time."""
    out = _tables_at(w, at)
    if at == EXTRACT_AT:
        out["_ops"] = w["ops"]
    return out


# ------------------------------------------------------------------------------------------------ asserts
def plan_rule(ext):
    """The plan at each scoring point by the design's H4 rule, from the extract alone (an assert, not the canonical):
    new_plan of the change with the greatest changed_at among changes loaded before t; none loaded: old_plan of the
    customer's earliest change; no change: customers.plan."""
    pc = ext["plan_changes"].sort_values(["customer_id", "changed_at"], kind="mergesort")
    by = {c: (g["changed_at"].tolist(), g["_loaded_at"].tolist(), g["old_plan"].tolist(), g["new_plan"].tolist())
          for c, g in pc.groupby("customer_id", sort=False)}
    cur = dict(zip(ext["customers"]["customer_id"].tolist(), ext["customers"]["plan"].tolist()))
    out = []
    for c, t in zip(ext["scoring_points"]["customer_id"].tolist(), ext["scoring_points"]["as_of"].tolist()):
        if c not in by:
            out.append(cur[c])
            continue
        ca, la, old, new = by[c]
        best, val = None, None
        for x, y, v in zip(ca, la, new):
            if y < t and (best is None or x > best):
                best, val = x, v
        out.append(val if best is not None else old[0])
    return out


def check_world(w, ext):
    """Every structural assert of the build plan on one brand; returns facts for the report."""
    name, cfg = w["name"], w["cfg"]
    sp = ext["scoring_points"]
    as_of = np.unique(sp["as_of"].to_numpy())
    f = {}
    # layout and keys
    for tname, key in (("customers", ["customer_id"]), ("orders", ["order_id"]), ("tickets", ["ticket_id"]),
                       ("scoring_points", ["customer_id", "as_of"]),
                       ("status_snapshots", ["customer_id", "snapshot_date"]), ("labels", ["customer_id", "as_of"]),
                       ("plan_changes", ["customer_id", "changed_at"])):
        assert not ext[tname].duplicated(key).any(), (name, tname, "duplicate keys")
    cu = ext["customers"].set_index("customer_id")
    n_c = len(w["customers"])
    assert cu.index.min() == cfg["cust0"] and cu.index.max() == cfg["cust0"] + n_c - 1, (name, "customer ids")
    for tname, col in (("orders", "ordered_at"), ("tickets", "opened_at"), ("scoring_points", "as_of"),
                       ("plan_changes", "changed_at")):
        su = ext[tname]["customer_id"].map(cu["signup_at"])
        assert su.notna().all() and (ext[tname][col] > su).all(), (name, tname, "at or before signup")
    lk = ext["labels"].merge(sp[["customer_id", "as_of"]], on=["customer_id", "as_of"], how="left", indicator=True)
    assert (lk["_merge"] == "both").all(), (name, "label without its scoring point")
    tp = sp[sp["trigger"] == "ticket"][["customer_id", "as_of"]]
    tk = ext["tickets"][["customer_id", "opened_at"]].rename(columns={"opened_at": "as_of"}).drop_duplicates()
    assert len(tp.merge(tk, on=["customer_id", "as_of"])) == len(tp), (name, "ticket point without its ticket")
    assert (ext["orders"].loc[ext["orders"]["_load_job"] == "orders_hourly", "_loaded_at"]
            > ext["orders"].loc[ext["orders"]["_load_job"] == "orders_hourly", "ordered_at"]).all()
    assert (ext["tickets"]["_loaded_at"] > ext["tickets"]["opened_at"]).all()
    assert (ext["status_snapshots"]["_loaded_at"] > ext["status_snapshots"]["snapshot_date"] + DAY + BATCH_AT).all()
    # no commit at the second of any scoring point (global: te reads every customer's labels)
    commits = [ext["orders"]["_loaded_at"], ext["tickets"]["_loaded_at"], ext["status_snapshots"]["_loaded_at"],
               ext["labels"]["_loaded_at"], ext["plan_changes"]["_loaded_at"], ext["customers"]["_updated_at"],
               pd.Series(w["orders"]["visible_at"])]
    for c in commits:
        assert not np.isin(c.to_numpy(dtype=np.int64), as_of).any(), (name, "a commit on a scoring second")
    # no event exactly at t - 7 days or t - 30 days of a point of the same customer
    pk = set((sp["customer_id"].to_numpy() * STRIDE + sp["as_of"].to_numpy()).tolist())
    ok_ = ext["orders"]["customer_id"].to_numpy() * STRIDE + ext["orders"]["ordered_at"].to_numpy()
    tk_ = ext["tickets"]["customer_id"].to_numpy() * STRIDE + ext["tickets"]["opened_at"].to_numpy()
    assert not any((v + 7 * DAY) in pk or (v + 30 * DAY) in pk for v in ok_.tolist()), (name, "order on an edge")
    assert not any((v + 30 * DAY) in pk for v in tk_.tolist()), (name, "ticket on an edge")
    # the ticket lag never decides: no point of the customer in (opened_at, _loaded_at]
    pks = np.sort(np.array(list(pk), dtype=np.int64))
    lo = np.searchsorted(pks, tk_, side="right")
    hi = np.searchsorted(pks, ext["tickets"]["customer_id"].to_numpy() * STRIDE + ext["tickets"]["_loaded_at"]
                         .to_numpy(), side="right")
    assert (lo == hi).all(), (name, "ticket capture lag decides a value")
    # the move and the order loads: the scheduler's records against the world (replaces the run-table asserts)
    f.update(check_ops(w, ext))
    od = ext["orders"]
    runs = w["legacy_runs"]
    h = w["hourly"]
    assert h["ok"].iloc[0] and h["commit"].iloc[0] // 60 == w["first_hourly"] // 60
    # every other audit column is the true commit
    for tname, wname in (("tickets", "tickets"), ("status_snapshots", "snapshots"), ("labels", "labels")):
        m = ext[tname].merge(w[wname], on=[c for c in ext[tname].columns if c != "_loaded_at"], suffixes=("", "_w"))
        assert len(m) == len(ext[tname]) and (m["_loaded_at"] == m["visible_at"]).all(), (name, tname)
    # the plan chain and the H4 rule reproduce the true customer record at every point
    pc = ext["plan_changes"].sort_values(["customer_id", "changed_at"], kind="mergesort")
    for c, g in pc.groupby("customer_id", sort=False):
        old, new = g["old_plan"].tolist(), g["new_plan"].tolist()
        assert all(old[i + 1] == new[i] for i in range(len(g) - 1)), (name, c, "plan chain")
        assert cu.loc[c, "plan"] == new[-1], (name, c, "customers.plan is not the last applied change")
    import ref_truth
    writes = ref_truth.crm_lists(w["crm_writes"])
    plan0 = dict(zip(w["customers"]["customer_id"].tolist(), w["customers"]["plan0"].tolist()))
    truth_plan = ref_truth.customer_record_features(sp["customer_id"].tolist(), sp["as_of"].tolist(), writes,
                                                    plan0)["plan"]
    rule = plan_rule(ext)
    assert list(truth_plan) == rule, (name, "plan rule differs from the true record",
                                      sum(a != b for a, b in zip(truth_plan, rule)))
    # facts
    f["move"] = iso(w["move0"])
    f["backfill_at"] = iso(w["backfill_at"])
    f["first_hourly_commit"] = iso(h["commit"].iloc[0])
    f["outage"] = f"{iso(w['outage']['start'])[:10]} + {w['outage']['nights']} nights"
    st = runs["status"].to_numpy()
    f["legacy_runs"] = len(runs)
    f["legacy_failed"] = int((st == "failed").sum())
    f["legacy_failed_outside_outage"] = f["legacy_failed"] - w["outage"]["nights"]
    f["legacy_ok_finished_after_0600"] = int(((st == "ok") & ((runs["finished_at"] % DAY) > BATCH_AT)).sum())
    f["hourly_runs_to_extract"] = int((h["commit"] < EXTRACT_AT).sum())
    f["hourly_failed_to_extract"] = int(((~h["ok"]) & (h["commit"] < EXTRACT_AT)).sum())
    ex = w["exports"][w["exports"]["partition"] < EXTRACT_AT - DAY]
    f["export_late_in_order"] = int((ex["kind"] == 1).sum())
    f["export_out_of_order"] = int((ex["kind"] == 2).sum())
    f["export_late_month_start"] = [iso(d * DAY)[:10] + " lands " + iso(w["exports"]["commit"].iloc[int(d - T0 // DAY)])
                                    for d in w["late_month"]]
    lr = w["label_runs"]
    f["label_runs_failed_to_extract"] = int(((~lr["ok"]) & (lr["start"] < EXTRACT_AT)).sum())
    sy = w["syncs"]
    f["syncs_to_extract"] = int((sy["commit"] < EXTRACT_AT).sum())
    f["syncs_late_to_extract"] = int((sy["late"] & (sy["commit"] < EXTRACT_AT)).sum())
    f["pre_move_share_of_points"] = round(float((sp["as_of"] < w["move0"]).mean()), 4)
    tx = ext["_ops"]["tasks"]["txn"].dropna()
    f["ids"] = {"customer": [int(cu.index.min()), int(cu.index.max())],
                "order": [int(od["order_id"].min()), int(od["order_id"].max())],
                "ticket": [int(ext["tickets"]["ticket_id"].min()), int(ext["tickets"]["ticket_id"].max())],
                "txn": [int(tx.min()), int(tx.max())]}
    return f


def check_ops(w, ext):
    """The scheduler's records of one brand against its world and extract (every record assert that needs no
    parser; check_round_trip has the rest); returns facts for the report. Times are int64 seconds; L = legacy_orders
    tasks by hi, B the backfill, H the orders_hourly tasks by hi (the dual run into orders_new first), Fh the first
    hourly task into orders, Q dq_checks, X the cutover, Dr the drop, O the extract's orders."""
    name = w["name"]
    t, par = ext["_ops"]["tasks"], ext["_ops"]["parity"]
    C, d0, F = w["move0"], w["d0"], int(w["hourly"]["commit"].iloc[0])
    pts = np.unique(w["points"]["as_of"].to_numpy())             # every scoring second of the world
    O = ext["orders"]
    x = np.sort(O["ordered_at"].to_numpy(dtype=np.int64))

    def i64(df, c):
        return df[c].to_numpy(dtype=np.int64)

    def one(m, what):
        assert int(m.sum()) == 1, (name, what, int(m.sum()))
        return t[m].iloc[0]

    L = t[t["job"] == "legacy_orders"].sort_values("hi", kind="mergesort")
    lhi, llo, lat = i64(L, "hi"), i64(L, "lo"), i64(L, "at")
    lc = (L["outcome"] == "commit").to_numpy()
    # the dual run's first day: after the doc date, on a night whose legacy run committed before 06:00, far from the
    # outage
    assert d0 == C - MIGRATION_DAYS * DAY and d0 > ts(DOC_DATE), (name, "d0")
    L0 = L[L["hi"] == d0]
    assert len(L0) == 1 and L0["outcome"].iloc[0] == "commit" and int(L0["at"].iloc[0]) % DAY < BATCH_AT, \
        (name, "the d0 legacy run did not commit before 06:00")
    o0, o1 = w["outage"]["start"], w["outage"]["start"] + w["outage"]["nights"] * DAY
    assert not (o0 - 10 * DAY <= d0 <= o1 + 10 * DAY), (name, "d0 near the legacy outage")
    # legacy ranges: one task per run date, each lo the hi of the last committed task before it; C commits
    assert (lhi == np.arange(T0 + DAY, C + 1, DAY)).all(), (name, "legacy run dates")
    assert (llo == _chain(lhi, lc, T0)).all() and lhi[-1] == C and lc[-1], (name, "legacy lo chain")
    rt = w["legacy_runs"]
    assert (i64(L, "started_at") == rt["started_at"].to_numpy()).all() and (lat == rt["finished_at"].to_numpy()).all()
    assert (lc == (rt["status"] == "ok").to_numpy()).all(), (name, "legacy outcomes differ from the run table")
    # the committed ranges partition [T0, C) and their rows are every order placed before C
    clo, chi = llo[lc], lhi[lc]
    assert clo[0] == T0 and (clo[1:] == chi[:-1]).all() and chi[-1] == C, (name, "committed legacy ranges")
    assert int(L.loc[lc, "rows"].sum()) == int((x < C).sum()), (name, "legacy rows")
    # the backfill: after the d0 legacy run, a copy of every order placed before d0
    B = one(t["job"] == "legacy_backfill", "backfill tasks")
    assert B["started_at"] > int(L0["end_at"].iloc[0]), (name, "backfill before the d0 legacy run ended")
    assert (B["hi"] == d0 and pd.isna(B["lo"]) and B["source"] == "orders" and B["table"] == "orders_new"
            and B["outcome"] == "commit"), (name, "backfill fields")
    assert B["rows"] == int((x < d0).sum()) == int(L.loc[lc & (lhi <= d0), "rows"].sum()), (name, "backfill rows")
    # the hourly chain: dual run first (from d0), then the runs into orders as before
    H = t[t["job"] == "orders_hourly"].sort_values("hi", kind="mergesort")
    hhi, hlo, hat = i64(H, "hi"), i64(H, "lo"), i64(H, "at")
    hc = (H["outcome"] == "commit").to_numpy()
    dual = (H["table"] == "orders_new").to_numpy()
    nd = int(dual.sum())
    assert dual[:nd].all() and not dual[nd:].any(), (name, "dual-run tasks are not first")
    assert hlo[0] == d0 and int(H["started_at"].iloc[0]) > B["end_at"], (name, "first dual-run task")
    assert (np.diff(hhi) == HOUR).all() and (hlo == _chain(hhi, hc, d0)).all(), (name, "hourly lo chain")
    Fh = H.iloc[nd]
    X = one((t["job"] == "schema_migrations") & (t["statements"] == CUTOVER_SQL), "cutover tasks")
    Dr = one((t["job"] == "schema_migrations") & (t["statements"] == DROP_SQL), "drop tasks")
    assert (hhi[:nd] < Fh["hi"]).all() and (i64(H, "end_at")[:nd] < X["started_at"]).all(), (name, "dual run end")
    hv = w["hourly"][w["hourly"]["commit"] < EXTRACT_AT]
    assert len(hv) == len(H) - nd and (hhi[nd:] == hv["top"].to_numpy()).all() and \
        (hat[nd:] == hv["commit"].to_numpy()).all() and (hc[nd:] == hv["ok"].to_numpy()).all(), \
        (name, "hourly runs into orders differ from the hourly schedule")
    assert Fh["at"] == F and Fh["outcome"] == "commit", (name, "first hourly commit")
    # the move day's order of events
    Q = one(t["job"] == "dq_checks", "dq_checks tasks")
    LC = L.iloc[-1]
    assert LC["end_at"] < Q["started_at"] and Q["end_at"] < X["started_at"] and X["at"] < Fh["started_at"], \
        (name, "move day order")
    assert X["end_at"] < Dr["started_at"] and Dr["end_at"] < EXTRACT_AT, (name, "drop")
    assert X["run"] == iso(C)[:10] and Dr["run"] == iso(C + 7 * DAY)[:10] and X["outcome"] == Dr["outcome"] == "commit"
    assert X["at"] == w["cutover_at"], (name, "cutover time")
    # parity: each order day d0 .. C - 1 day once, equal counts, inside dq_checks; the dual run covered them
    days = np.arange(d0, C, DAY, dtype=np.int64)
    n_day = np.searchsorted(x, days + DAY, side="left") - np.searchsorted(x, days, side="left")
    assert len(par) == len(days) and (i64(par, "day") == days).all(), (name, "parity days")
    assert (i64(par, "rows_a") == n_day).all() and (i64(par, "rows_b") == n_day).all(), (name, "parity rows")
    assert (par["table_a"] == "orders").all() and (par["table_b"] == "orders_new").all() and \
        (par["run"] == Q["run"]).all(), (name, "parity tables")
    assert (i64(par, "at") == Q["started_at"] + 1 + np.arange(len(days))).all() and \
        Q["end_at"] == Q["started_at"] + 1 + len(days), (name, "parity times")
    cov = dual & hc & (hat < Q["started_at"])
    assert cov.any() and hhi[cov].max() >= C, (name, "the dual run did not cover [d0, C) before the parity check")
    # the orders' audit columns are the loads the records describe
    oa, lj, la = i64(O, "ordered_at"), O["_load_job"].to_numpy(dtype=object), i64(O, "_loaded_at")
    back = lj == "legacy_backfill"
    assert (back == (oa < d0)).all() and (la[back] == B["at"]).all(), (name, "backfill rows")
    k = np.searchsorted(hhi[hc], oa[~back], side="right")
    assert (k < hc.sum()).all() and (hlo[hc][k] <= oa[~back]).all() and (la[~back] == hat[hc][k]).all(), \
        (name, "an hourly row's _loaded_at is not the commit of the task holding it")
    # the records rule gives every order's true visibility
    j = np.searchsorted(chi, oa, side="right")
    rule = np.where(oa < C, lat[lc][np.minimum(j, len(chi) - 1)], np.maximum(la, X["at"]))
    true_vis = w["orders"].set_index("order_id")["visible_at"].loc[O["order_id"]].to_numpy()
    assert (rule == true_vis).all(), (name, "records rule differs from the true visibility", int((rule != true_vis)
                                                                                                .sum()))
    assert not ((pts >= X["started_at"]) & (pts <= F)).any(), (name, "a scoring point between cutover and F")
    # no scoring point strictly between a transaction's send and its commit; no commit on a scoring second
    sends = t["txn"].notna().to_numpy()
    s_at, s_sent = i64(t[sends], "at"), i64(t[sends], "sent_at")
    assert (np.searchsorted(pts, s_sent, side="right") == np.searchsorted(pts, s_at, side="left")).all(), \
        (name, "a scoring point between a send and its commit")
    assert not np.isin(s_at, pts).any(), (name, "a commit on a scoring second")
    # a transaction commits if and only if its task succeeded; a failed label_job sends none
    st, oc, jb = t["state"].to_numpy(dtype=object), t["outcome"].to_numpy(dtype=object), t["job"].to_numpy(dtype=object)
    assert ((oc[sends] == "commit") == (st[sends] == "success")).all(), (name, "a commit and a failed task")
    assert set(jb[~sends].tolist()) <= {"dq_checks", "label_job"} and \
        (st[~sends & (jb == "label_job")] == "failed").all(), (name, "a task without a transaction")
    # the other audit columns are commits of their jobs' tasks
    com = t[sends & (oc == "commit")]
    for job, table in (("label_job", "labels"), ("crm_sync", "plan_changes")):
        ats = set(com.loc[com["job"] == job, "at"].astype("int64").tolist())
        assert ext[table]["_loaded_at"].isin(ats).all(), (name, table, "a _loaded_at that no task committed")
    ex = com[com["job"] == "billing_export"]
    assert not ex["run"].duplicated().any(), (name, "two exports of one partition")
    part = dict(zip(ts_dates(ex["run"]).tolist(), ex["at"].astype("int64").tolist()))
    ss = ext["status_snapshots"]
    assert (ss["snapshot_date"].map(part).to_numpy(dtype=np.int64) == i64(ss, "_loaded_at")).all(), \
        (name, "a partition's _loaded_at is not its export's commit")
    cu = ext["customers"]
    upd = cu.loc[cu["_updated_at"] != cu["signup_at"], "_updated_at"]
    assert upd.isin(set(com.loc[com["job"] == "crm_sync", "at"].astype("int64").tolist())).all(), \
        (name, "a customer _updated_at that no crm_sync committed")
    # without the parser: keys, transaction numbers, the records' order and times
    assert not t.duplicated(["job", "run"]).any() and not t["txn"].dropna().duplicated().any(), (name, "keys")
    srt = t[sends].sort_values(["sent_at", "job", "run"], kind="mergesort")
    assert (i64(srt, "txn") == w["cfg"]["txn0"] + np.arange(len(srt))).all(), (name, "txn order")
    key = t[["started_at", "job", "run"]]
    assert key.equals(key.sort_values(["started_at", "job", "run"], kind="mergesort")) and \
        isinstance(t.index, pd.RangeIndex) and t.index.start == 0, (name, "tasks order")
    times = [t[c].dropna().to_numpy(dtype=np.int64) for c in ("started_at", "end_at", "sent_at", "at", "analyze_at")]
    assert max(int(v.max()) for v in times) < EXTRACT_AT and int(par["at"].max()) < EXTRACT_AT, (name, "a late record")
    order_ok = np.ones(len(t), bool)
    prev = np.full(len(t), -1, dtype=np.int64)
    for c in ("started_at", "sent_at", "at", "analyze_at", "end_at"):
        v = t[c].to_numpy(dtype=np.int64, na_value=NA) if c in TASK_NULLABLE else i64(t, c)
        has = v != NA
        order_ok &= ~has | (v > prev)
        prev = np.where(has, v, prev)
    assert order_ok.all(), (name, "times not in the order started < sent < at < analyze < end")
    lo_, hi_ = t["lo"].to_numpy(dtype=np.int64, na_value=NA), t["hi"].to_numpy(dtype=np.int64, na_value=NA)
    assert ((lo_ == NA) | (hi_ == NA) | (lo_ < hi_)).all(), (name, "lo not below hi")
    f = {}
    an = L[lc]
    f["d0"] = iso(d0)[:10]
    f["d0_legacy_commit"] = iso(int(L0["at"].iloc[0]))
    f["backfill"] = {c: iso(int(B[c])) for c in ("started_at", "sent_at", "at", "end_at")} | {"rows": int(B["rows"])}
    f["dual_run"] = {"first_top": iso(int(hhi[0])), "last_top": iso(int(hhi[nd - 1])), "tasks": nd,
                     "failed": int((~hc[:nd]).sum())}
    f["dq_checks"] = {"started_at": iso(int(Q["started_at"])), "end_at": iso(int(Q["end_at"])), "lines": len(par)}
    f["cutover"] = {c: iso(int(X[c])) for c in ("started_at", "sent_at", "at", "end_at")}
    f["first_hourly_task_into_orders"] = {c: iso(int(Fh[c])) for c in ("started_at", "sent_at", "at")}
    f["drop"] = {c: iso(int(Dr[c])) for c in ("started_at", "at")}
    f["legacy_analyze_long"] = int(((an["end_at"] - an["analyze_at"]) >= 10800).sum())
    f["legacy_end_after_0600_commit_before"] = int((((an["at"] % DAY) < BATCH_AT) & (an["end_at"] - an["at"] // DAY
                                                                                     * DAY > BATCH_AT)).sum())
    f["tasks"] = {j: int((jb == j).sum()) for j in ("legacy_orders", "legacy_backfill", "orders_hourly", "dq_checks",
                                                    "schema_migrations", "label_job", "billing_export", "crm_sync")}
    f["transactions"] = int(sends.sum())
    f["rollbacks"] = int((oc == "rollback").sum())
    f["moved_to_cutover"] = int((w["orders"]["visible_at"] == X["at"]).sum())
    return f


def check_round_trip(ext, name):
    """The records module on one brand's records: the frames have the records' layout, render and parse are exact
    inverses on them, every count is what the extract's tables give, and validate finds no problem."""
    import ops_log as OPS
    x = ext["_ops"]
    for k in ("tasks", "parity"):
        pd.testing.assert_frame_equal(OPS.typed(x)[k], x[k], check_exact=True)
    files = OPS.render(x)
    for fname, text in files.items():
        assert text.isascii() and text.endswith("\n") and "\r" not in text, (name, fname)
    y = OPS.parse(files)
    for k in ("tasks", "parity"):
        pd.testing.assert_frame_equal(y[k], x[k], check_exact=True)
    assert OPS.render(y) == files, (name, "render(parse(files)) is not the same bytes")
    z = OPS.recount(x, {k: v for k, v in ext.items() if k != "_ops"})
    for k in ("tasks", "parity"):
        pd.testing.assert_frame_equal(z[k], x[k], check_exact=True)
    bad = OPS.validate(x)
    assert bad == [], (name, bad[:5])
    return {"scheduler_log_lines": files[OPS.SCHEDULER].count("\n"),
            "commits_jsonl_lines": files[OPS.COMMITS].count("\n"),
            "bytes": {k: len(v) for k, v in files.items()}}


def table_counts(ext):
    out = {k: int(len(v)) for k, v in ext.items() if k != "_ops"}
    if "_ops" in ext:
        out["_ops"] = {k: int(len(v)) for k, v in ext["_ops"].items()}
    return out


# ------------------------------------------------------------------------------------------------ main
def main(argv):
    check_only = "--check" in argv
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv) or check_only:
            raise SystemExit("usage: gen_data.py [--check | --out DIR]")
        out = os.path.abspath(argv[i + 1])
    import ref_truth  # noqa: E402  (authoring modules next to this file)
    if out is None:
        import mechanisms, samples  # noqa: E402
    t_start = time.time()
    report = {"knobs": {k: v for k, v in P.items()}, "loaders": dict(L)}
    worlds, exts, truths = {}, {}, {}
    for b in ("visible", "H"):
        t1 = time.time()
        worlds[b] = brand_world(b)
        exts[b] = extract_tables(worlds[b])
        report[b] = {"facts": check_world(worlds[b], exts[b]), "rows": table_counts(exts[b]),
                     "records": check_round_trip(exts[b], b), "seconds_simulate": round(time.time() - t1, 1)}
        t2 = time.time()
        truths[b] = ref_truth.compute(worlds[b], exts[b]["scoring_points"])
        report[b]["seconds_ref_truth"] = round(time.time() - t2, 1)
    if out is None:
        for b in ("visible", "H"):
            report[b]["mechanisms"] = mechanisms.report(worlds[b], exts[b], truths[b])
        mechanisms.assert_targets(report)
        ev = samples.build(worlds["visible"], exts["visible"], truths["visible"], worlds["H"], exts["H"],
                           truths["H"])
        report["samples"] = ev["report"]
        report["cut_candidates_H"] = mechanisms.cut_candidates(worlds["H"], exts["H"])
    if out is not None:
        for b in ("visible", "H"):
            extract_io.write_dataset(exts[b], os.path.join(out, b))
            truths[b].to_parquet(os.path.join(out, b, "truth.parquet"), index=False)
    elif not check_only:
        extract_io.write_dataset(exts["visible"], os.path.join(APP, "data"))
        extract_io.write_dataset(exts["H"], os.path.join(TASK, "tests", "hidden", "H"), gzip=True)
        samples.write(ev, os.path.join(APP, "logs"))
    report["seconds_total"] = round(time.time() - t_start, 1)
    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])

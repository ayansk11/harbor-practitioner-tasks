"""Synthetic meal-kit subscription data for task feature-leakage-churn (authoring only; never shipped to the agent).

python gen_data.py            -> writes the visible extract (seed 1) into the task's environment/app/data/ and the
                                 hidden extract H (seed 2, then plant_boundary_ties) into tests/hidden/H/ (gzipped
                                 CSV, fixed mtime)
Everything is deterministic for a given seed (numpy PCG64). Timestamps are int64 epoch seconds until written.
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "feature-leakage-churn"))
sys.path.insert(0, os.path.join(TASK, "tests"))
import dataset_io  # noqa: E402

DAY = 86400
def ts(s): return int(pd.Timestamp(s, tz="UTC").timestamp())
T0 = ts("2024-01-01")              # simulation start (day index 0)
SIGNUP_TO = ts("2025-10-31")
SCORING_FROM = ts("2024-07-01")
EXTRACT_END = ts("2026-01-01")
HORIZON = ts("2026-03-15")          # simulated past the extract so the live month (Jan 2026) has labels
N_CUSTOMERS = 3000
PRICES = {"basic": 4990, "plus": 6990, "family": 8990}
PLAN_P = [0.45, 0.40, 0.15]
PLAN_EFF = {"basic": 0.25, "plus": 0.0, "family": -0.3}
AREAS = ["B", "BS", "CF", "E", "EH", "G", "L", "LS", "M", "N", "NE", "NG", "NW", "OX", "S", "SE", "SW", "W", "CB", "BN"]

# calibration knobs (see calibrate_auc.py and DESIGN.md)
P = dict(h0=1 / 520, beta_b=0.75, district_sd=0.45, decline_min=10, decline_max=45, dip_every=110,
         dip_depth=(0.3, 0.9), dip_half=(4, 16), skip_base=0.06, skip_x=0.45, pf_base=0.012, pf_x=0.12,
         pause_base=0.0015, pause_x=0.02, addon_rate=0.035, ticket_base=0.012, ticket_x=0.05, ticket_pf=0.25,
         ticket_score_p=0.4, app_scale=70.0, app_missing=0.25, outage_frac=0.07, n_districts=600, zipf=0.5,
         cancel_on_box_day=0.6, cancel_ticket_p=0.7, app_decline=0.85)


def districts(rng, n_d, zipf):
    names, seen = [], set()
    while len(names) < n_d:
        n = f"{AREAS[rng.integers(len(AREAS))]}{rng.integers(1, 60)}"
        if n not in seen:
            seen.add(n)
            names.append(n)
    w = 1.0 / np.arange(1, n_d + 1) ** zipf
    return names, w / w.sum()


def simulate(seed, n_customers=N_CUSTOMERS, p=P):
    rng = np.random.default_rng(seed)
    dnames, dweights = districts(rng, p["n_districts"], p["zipf"])
    deff = rng.normal(0, p["district_sd"], len(dnames))
    n_days = (HORIZON - T0) // DAY + 1
    outage = rng.random(n_days) < p["outage_frac"]
    MONTH_FIRST = {int(d) for d in range(T0 // DAY, T0 // DAY + n_days) if pd.Timestamp(d * DAY, unit="s").day == 1}
    cust, orders, tickets, snaps, points, labels = [], [], [], [], [], []
    for i in range(n_customers):
        cid = 100001 + i
        r = np.random.default_rng([seed, cid])
        signup = int(r.integers(T0, SIGNUP_TO))
        plan = str(r.choice(list(PRICES), p=PLAN_P))
        k = int(r.choice(len(dnames), p=dweights))
        b = r.normal()
        h = p["h0"] * np.exp(p["beta_b"] * b + deff[k] + PLAN_EFF[plan])
        C = signup + int(r.exponential(1 / h) * DAY)
        first_box = signup // DAY + int(r.integers(1, 8))
        if C < HORIZON and r.random() < p["cancel_on_box_day"]:
            # many customers cancel on a billing day, after that morning's charge
            cday = max(first_box, first_box + 7 * ((C // DAY - first_box) // 7))
            C = cday * DAY + int(r.integers(6 * 3600 + 60, DAY))
        churns = C < HORIZON
        if not churns:
            C = HORIZON + 10 * DAY
        cust.append((cid, signup, plan, dnames[k]))
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
        state, until = "active", -1
        prev = None
        cpts = []
        for j, d in enumerate(days):
            day_start = d * DAY
            if state != "active" and d >= until:
                state = "active"
            pf_today = False
            if state == "active" and r.random() < p["pause_base"] + p["pause_x"] * x[j]:
                state, until = "paused", d + int(r.integers(7, 29))
            if d >= first_box and (d - first_box) % 7 == 0 and day_start + 6 * 3600 < C:
                if state == "active":
                    if r.random() < p["pf_base"] + p["pf_x"] * x[j]:
                        state, until, pf_today = "payment_failed", d + int(r.integers(1, 7)), True
                    elif r.random() >= p["skip_base"] + p["skip_x"] * x[j]:
                        amt = PRICES[plan] - (1000 if r.random() < 0.1 else 0)
                        orders.append((cid, day_start + 6 * 3600, "box", amt))
            if state == "active":
                for _ in range(r.poisson(p["addon_rate"] * g[j])):
                    t = day_start + int(r.integers(0, DAY))
                    if signup < t < C:
                        orders.append((cid, t, "addon", int(r.integers(499, 3000))))
            for _ in range(r.poisson(p["ticket_base"] + p["ticket_x"] * x[j] + (p["ticket_pf"] if pf_today else 0))):
                t = day_start + int(r.integers(0, DAY))
                if signup < t < C:
                    topic = "billing" if pf_today else str(r.choice(["delivery", "quality", "account", "billing"]))
                    tickets.append((cid, t, topic))
                    if t >= SCORING_FROM and r.random() < p["ticket_score_p"]:
                        cpts.append((t, "ticket"))
            # batch scoring every second billing day at 06:00, from two weeks after signup
            t = day_start + 6 * 3600
            if (d >= first_box and (d - first_box) % 14 == 0 and t >= SCORING_FROM and t >= signup + 14 * DAY
                    and t < C):
                cpts.append((t, "batch"))
            if churns and d == C // DAY and r.random() < p["cancel_ticket_p"]:
                t = max(signup + 1, C - int(r.integers(60, 2 * 3600)))
                tickets.append((cid, t, "account"))
                if t >= SCORING_FROM and r.random() < p["ticket_score_p"]:
                    cpts.append((t, "ticket"))
            st = "cancelled" if (churns and d == C // DAY) else state
            if st != prev or d in MONTH_FIRST:
                snaps.append((cid, day_start, st))
            prev = st
            if st == "cancelled":
                break
        # app minutes and labels for this customer's points ((customer_id, as_of) unique)
        seen = set()
        for (t, trig) in sorted(cpts):
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
            avail = (C if y else t + 30 * DAY) + int(r.integers(2 * 3600, 72 * 3600))
            labels.append((cid, t, y, avail))
    t = {
        "customers": pd.DataFrame(cust, columns=["customer_id", "signup_at", "plan", "postcode_district"]),
        "orders": pd.DataFrame(orders, columns=["customer_id", "ordered_at", "kind", "amount_cents"]),
        "tickets": pd.DataFrame(tickets, columns=["customer_id", "opened_at", "topic"]),
        "status_snapshots": pd.DataFrame(snaps, columns=["customer_id", "snapshot_date", "status"]),
        "scoring_points": pd.DataFrame(points, columns=["customer_id", "as_of", "trigger", "app_minutes_7d"]),
        "labels": pd.DataFrame(labels, columns=["customer_id", "as_of", "churned_30d", "label_available_at"]),
    }
    t["orders"] = t["orders"].sort_values(["ordered_at", "customer_id"], kind="mergesort").reset_index(drop=True)
    t["orders"].insert(0, "order_id", np.arange(5000001, 5000001 + len(t["orders"])))
    t["tickets"] = t["tickets"].sort_values(["opened_at", "customer_id"], kind="mergesort").reset_index(drop=True)
    t["tickets"].insert(0, "ticket_id", np.arange(700001, 700001 + len(t["tickets"])))
    t["scoring_points"]["app_minutes_7d"] = t["scoring_points"]["app_minutes_7d"].astype("float64")
    return t


def extract(full, end=EXTRACT_END):
    """What the warehouse held at `end`: rows stamped before it; labels that had landed before it."""
    out = dict(full)
    out["customers"] = full["customers"][full["customers"].signup_at < end]
    out["orders"] = full["orders"][full["orders"].ordered_at < end]
    out["tickets"] = full["tickets"][full["tickets"].opened_at < end]
    out["status_snapshots"] = full["status_snapshots"][full["status_snapshots"].snapshot_date < end]
    out["scoring_points"] = full["scoring_points"][full["scoring_points"].as_of < end]
    out["labels"] = full["labels"][full["labels"].label_available_at < end]
    return {k: v.reset_index(drop=True) for k, v in out.items()}


N_PLANT = 300          # boundary ties planted per kind in the hidden extract H (DESIGN.md section 3)
TOPICS = ["delivery", "quality", "account", "billing"]


def plant_boundary_ties(t, seed, n=N_PLANT):
    """Hidden extract only: make three edges FEATURES.md states decide some values (the simulation never hits them).

    The weekly 06:00 box charges land exactly on t - 7 days of a 06:00 batch point but never on t - 30 days, and label
    lags are random seconds, so without this a 30-day window open on the left, or district counts that use
    label_available_at <= t, would match the reference on H. For `n` scoring points each (sampled separately):
    - an add-on order stamped exactly at as_of - 30 days (strictly after the customer's signup);
    - a ticket stamped exactly at as_of - 30 days (strictly after signup; not itself scored);
    - one churned_30d = 0 label row of the same postcode district whose label_available_at is moved onto that scoring
      point's as_of; the new value stays inside the generator's own lag band, as_of + 30 days + [2 h, 72 h).
    Works on the extract (every planted time is before EXTRACT_END), keeps all row counts of scoring points and labels,
    and renumbers order_id / ticket_id in time order, as simulate() does. Deterministic for a given seed.
    """
    rng = np.random.default_rng([seed, 30])
    t = {k: v.copy() for k, v in t.items()}
    cu = t["customers"].set_index("customer_id")
    sp = t["scoring_points"]
    edge = sp["as_of"].to_numpy() - 30 * DAY
    cand = np.flatnonzero(edge > sp["customer_id"].map(cu["signup_at"]).to_numpy())

    def plant_events(name, ts_col, id_col, first_id, extra):
        pick = np.sort(rng.choice(cand, n, replace=False))
        new = pd.DataFrame({"customer_id": sp["customer_id"].to_numpy()[pick], ts_col: edge[pick]})
        for col, fn in extra.items():
            new[col] = fn(n)
        df = pd.concat([t[name].drop(columns=id_col), new], ignore_index=True)
        df = df.sort_values([ts_col, "customer_id"], kind="mergesort").reset_index(drop=True)
        df.insert(0, id_col, np.arange(first_id, first_id + len(df)))
        t[name] = df

    plant_events("orders", "ordered_at", "order_id", 5000001,
                 {"kind": lambda k: np.array(["addon"] * k), "amount_cents": lambda k: rng.integers(499, 3000, k)})
    plant_events("tickets", "opened_at", "ticket_id", 700001, {"topic": lambda k: rng.choice(TOPICS, k)})

    # same-district label rows landing exactly at a scoring point's as_of
    codes, _ = pd.factorize(pd.concat([cu["postcode_district"], sp["customer_id"].map(cu["postcode_district"]),
                                       t["labels"]["customer_id"].map(cu["postcode_district"])], ignore_index=True))
    pt_code = codes[len(cu):len(cu) + len(sp)].astype("int64")
    lb_code = codes[len(cu) + len(sp):].astype("int64")
    STRIDE = 10 ** 10
    keys = np.unique(pt_code * STRIDE + sp["as_of"].to_numpy())
    lb = t["labels"]
    base = lb["as_of"].to_numpy() + 30 * DAY
    lo = np.searchsorted(keys, lb_code * STRIDE + base + 2 * 3600, side="left")
    hi = np.searchsorted(keys, lb_code * STRIDE + base + 72 * 3600, side="left")
    ok = np.flatnonzero((lb["churned_30d"].to_numpy() == 0) & (hi > lo))
    pick = np.sort(rng.choice(ok, n, replace=False))
    choice = lo[pick] + (rng.random(n) * (hi[pick] - lo[pick])).astype("int64")
    new_avail = keys[choice] - lb_code[pick] * STRIDE
    col = lb.columns.get_loc("label_available_at")
    lb.iloc[pick, col] = new_avail
    assert (new_avail < EXTRACT_END).all()
    t["labels"] = lb
    return t


def main():
    vis = extract(simulate(1))
    dataset_io.write_dataset(vis, os.path.join(TASK, "environment", "app", "data"))
    hid = plant_boundary_ties(extract(simulate(2)), 2)
    dataset_io.write_dataset(hid, os.path.join(TASK, "tests", "hidden", "H"), gzip=True)
    for name, d in (("visible", vis), ("hidden H", hid)):
        print(name, {k: len(v) for k, v in d.items()},
              "churn rate per label row", round(d["labels"].churned_30d.mean(), 4))


if __name__ == "__main__":
    main()

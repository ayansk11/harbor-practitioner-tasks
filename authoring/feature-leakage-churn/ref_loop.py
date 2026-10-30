"""Reference 2 (per row, standard library only: csv, bisect, calendar), written from churn/FEATURES.md alone.

compute(data_dir) -> list of dicts with customer_id (int), as_of (int epoch seconds) and the nine features.
"""
import bisect, calendar, csv, os
from collections import defaultdict

DAY = 86400
M, P0 = 20, 0.05


def sec(s):
    # "YYYY-MM-DDTHH:MM:SSZ" or "YYYY-MM-DD"
    y, mo, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
    if len(s) > 10:
        return calendar.timegm((y, mo, d, int(s[11:13]), int(s[14:16]), int(s[17:19])))
    return calendar.timegm((y, mo, d, 0, 0, 0))


def rows(d, name):
    with open(os.path.join(d, name + ".csv"), newline="") as f:
        return list(csv.DictReader(f))


def compute(data_dir):
    signup, district = {}, {}
    for r in rows(data_dir, "customers"):
        signup[int(r["customer_id"])] = sec(r["signup_at"])
        district[int(r["customer_id"])] = r["postcode_district"]
    orders = defaultdict(list)
    for r in rows(data_dir, "orders"):
        orders[int(r["customer_id"])].append((sec(r["ordered_at"]), int(r["amount_cents"])))
    tickets = defaultdict(list)
    for r in rows(data_dir, "tickets"):
        tickets[int(r["customer_id"])].append(sec(r["opened_at"]))
    snaps = defaultdict(list)
    for r in rows(data_dir, "status_snapshots"):
        snaps[int(r["customer_id"])].append((sec(r["snapshot_date"]), r["status"]))
    labels = []
    for r in rows(data_dir, "labels"):
        labels.append((sec(r["label_available_at"]), int(r["churned_30d"]), district[int(r["customer_id"])]))
    points = [(int(r["customer_id"]), sec(r["as_of"]), r["app_minutes_7d"]) for r in rows(data_dir, "scoring_points")]

    # sorted lists and prefix sums
    o_t, o_pref = {}, {}
    for c, lst in orders.items():
        lst.sort()
        o_t[c] = [x[0] for x in lst]
        pref = [0]
        for x in lst:
            pref.append(pref[-1] + x[1])
        o_pref[c] = pref
    for c in tickets:
        tickets[c].sort()
    s_d, s_v = {}, {}
    for c, lst in snaps.items():
        lst.sort()
        s_d[c] = [x[0] for x in lst]
        s_v[c] = [x[1] for x in lst]
    labels.sort(key=lambda x: x[0])
    g_t = [x[0] for x in labels]
    g_pref = [0]
    for x in labels:
        g_pref.append(g_pref[-1] + x[1])
    d_t, d_pref = defaultdict(list), defaultdict(lambda: [0])
    for (a, y, k) in labels:
        d_t[k].append(a)
        d_pref[k].append(d_pref[k][-1] + y)

    # app minutes: carry the last earlier non-empty reading per customer
    by_c = defaultdict(list)
    for (c, t, a) in points:
        by_c[c].append((t, a))
    app = {}
    for c, lst in by_c.items():
        lst.sort()
        last = None
        for (t, a) in lst:
            if a != "":
                last = float(a)
            app[(c, t)] = last

    out = []
    for (c, t, _) in points:
        ot = o_t.get(c, [])
        i_now = bisect.bisect_left(ot, t)
        i7 = bisect.bisect_left(ot, t - 7 * DAY)
        i30 = bisect.bisect_left(ot, t - 30 * DAY)
        pref = o_pref.get(c, [0])
        tk = tickets.get(c, [])
        k_now = bisect.bisect_left(tk, t)
        k30 = bisect.bisect_left(tk, t - 30 * DAY)
        day0 = (t // DAY) * DAY
        sd = s_d.get(c, [])
        j = bisect.bisect_left(sd, day0) - 1
        status = s_v[c][j] if j >= 0 else None
        N = bisect.bisect_left(g_t, t)
        S = g_pref[N]
        p = S / N if N > 0 else P0
        k = district[c]
        n = bisect.bisect_left(d_t.get(k, []), t)
        s = d_pref[k][n] if k in d_pref else 0
        out.append({
            "customer_id": c, "as_of": t,
            "orders_7d": i_now - i7, "orders_30d": i_now - i30, "spend_30d_cents": pref[i_now] - pref[i30],
            "tickets_30d": k_now - k30,
            "days_since_last_order": (t - ot[i_now - 1]) / DAY if i_now > 0 else None,
            "tenure_days": (t - signup[c]) / DAY,
            "status": status,
            "app_minutes_7d": app[(c, t)],
            "te_district": (s + M * p) / (n + M),
        })
    return out


if __name__ == "__main__":
    import sys
    print(compute(sys.argv[1])[:3])

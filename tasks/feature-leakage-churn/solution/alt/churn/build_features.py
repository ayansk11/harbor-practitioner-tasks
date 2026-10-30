"""Point-in-time churn features, computed one prediction at a time (second valid solution).

python -m churn.build_features --data <dir> --out <file.parquet>

Materially different from the canonical fix: no pandas; per-customer sorted lists and bisect for the windows and the
last order, the standard library's sqlite3 for the as-of lookups (status snapshots, district labels), a plain loop for
the gap filling, and pyarrow for the output with its own column order, dtypes, row order and an extra column.
"""
import argparse
import bisect
import csv
import datetime as dt
import os
import sqlite3
from collections import defaultdict

import pyarrow as pa
import pyarrow.parquet as pq

DAY = 86400
UTC = dt.timezone.utc


def epoch(s):
    d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return int(d.timestamp())


def read(data_dir, name):
    with open(os.path.join(data_dir, name + ".csv"), newline="") as f:
        yield from csv.DictReader(f)


class Extract:
    def __init__(self, data_dir):
        self.signup, self.district = {}, {}
        for r in read(data_dir, "customers"):
            c = int(r["customer_id"])
            self.signup[c], self.district[c] = epoch(r["signup_at"]), r["postcode_district"]
        orders = defaultdict(list)
        for r in read(data_dir, "orders"):
            orders[int(r["customer_id"])].append((epoch(r["ordered_at"]), int(r["amount_cents"])))
        self.order_t, self.order_cum = {}, {}
        for c, lst in orders.items():
            lst.sort()
            self.order_t[c] = [a for a, _ in lst]
            cum, run = [0], 0
            for _, amt in lst:
                run += amt
                cum.append(run)
            self.order_cum[c] = cum
        self.ticket_t = defaultdict(list)
        for r in read(data_dir, "tickets"):
            self.ticket_t[int(r["customer_id"])].append(epoch(r["opened_at"]))
        for lst in self.ticket_t.values():
            lst.sort()
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE snap (customer_id INTEGER, day INTEGER, status TEXT)")
        self.db.executemany("INSERT INTO snap VALUES (?, ?, ?)",
                            ((int(r["customer_id"]), epoch(r["snapshot_date"]), r["status"])
                             for r in read(data_dir, "status_snapshots")))
        self.db.execute("CREATE INDEX snap_i ON snap (customer_id, day)")
        self.db.execute("CREATE TABLE lab (district TEXT, avail INTEGER, y INTEGER)")
        labs = [(self.district[int(r["customer_id"])], epoch(r["label_available_at"]), int(r["churned_30d"]))
                for r in read(data_dir, "labels")]
        self.db.executemany("INSERT INTO lab VALUES (?, ?, ?)", labs)
        self.db.execute("CREATE INDEX lab_i ON lab (district, avail)")
        labs.sort(key=lambda x: x[1])
        self.lab_t = [a for _, a, _ in labs]
        self.lab_cum = [0]
        for _, _, y in labs:
            self.lab_cum.append(self.lab_cum[-1] + y)
        self.points = [(int(r["customer_id"]), epoch(r["as_of"]), r["trigger"],
                        float(r["app_minutes_7d"]) if r["app_minutes_7d"] != "" else None)
                       for r in read(data_dir, "scoring_points")]


def window(times, t, days):
    return bisect.bisect_left(times, t) - bisect.bisect_left(times, t - days * DAY)


def features(x):
    # gap filling: walk each customer's predictions in time order, carrying the last earlier reading
    carried = {}
    by_customer = defaultdict(list)
    for c, t, _, v in x.points:
        by_customer[c].append((t, v))
    for c, lst in by_customer.items():
        last = None
        for t, v in sorted(lst):
            if v is not None:
                last = v
            carried[(c, t)] = last
    rows = []
    for c, t, trig, _ in x.points:
        ot, cum = x.order_t.get(c, []), x.order_cum.get(c, [0])
        now = bisect.bisect_left(ot, t)
        lo30 = bisect.bisect_left(ot, t - 30 * DAY)
        status = x.db.execute("SELECT status FROM snap WHERE customer_id = ? AND day < ? ORDER BY day DESC LIMIT 1",
                              (c, t - t % DAY)).fetchone()
        N = bisect.bisect_left(x.lab_t, t)
        p = x.lab_cum[N] / N if N else 0.05
        n, s = x.db.execute("SELECT COUNT(*), COALESCE(SUM(y), 0) FROM lab WHERE district = ? AND avail < ?",
                            (x.district[c], t)).fetchone()
        rows.append({
            "customer_id": c, "as_of": t, "trigger": trig,
            "orders_7d": window(ot, t, 7), "orders_30d": now - lo30, "spend_30d_cents": cum[now] - cum[lo30],
            "tickets_30d": window(x.ticket_t.get(c, []), t, 30),
            "days_since_last_order": (t - ot[now - 1]) / DAY if now else None,
            "tenure_days": (t - x.signup[c]) / DAY,
            "status": status[0] if status else None,
            "app_minutes_7d": carried[(c, t)],
            "te_district": (s + 20 * p) / (n + 20),
        })
    rows.sort(key=lambda r: (-r["as_of"], r["customer_id"]))
    return rows


def write(rows, out):
    cols = {
        "as_of": pa.array([dt.datetime.fromtimestamp(r["as_of"], UTC).replace(tzinfo=None) for r in rows],
                          pa.timestamp("us")),
        "customer_id": pa.array([r["customer_id"] for r in rows], pa.int64()),
        "trigger": pa.array([r["trigger"] for r in rows], pa.string()),
    }
    for name, typ in [("app_minutes_7d", pa.float64()), ("days_since_last_order", pa.float64()),
                      ("orders_30d", pa.int32()), ("orders_7d", pa.int32()), ("spend_30d_cents", pa.int64()),
                      ("status", pa.string()), ("te_district", pa.float64()), ("tenure_days", pa.float64()),
                      ("tickets_30d", pa.int32())]:
        cols[name] = pa.array([r[name] for r in rows], typ)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    pq.write_table(pa.table(cols), out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = features(Extract(a.data))
    write(rows, a.out)
    print(f"wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()

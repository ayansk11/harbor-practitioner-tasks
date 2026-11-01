"""Point-in-time churn features by replaying the warehouse's commits (second valid solution).

python -m churn.build_features --data <dir> --out <file.parquet>

The scoring points are merged in time order into the stream of the warehouse's commits (docs/WAREHOUSE.md), so each
point is computed from exactly what the warehouse held before its as_of, as the live service read it
(live/features.py):
- the order tables are replayed as tables. The commit log of the scheduled jobs (`_ops/commits.jsonl`) is joined on
  the txn to the scheduler line that sent each transaction (`_ops/scheduler.log`), and every committed transaction is
  applied at its `at`: a load adds the orders with lo <= ordered_at < hi to the table it names, a copy adds the rows
  of its source table below its bound to its target, and schema statements rename or drop tables; a rolled-back
  transaction changes nothing. A table keeps its rows when a rename moves its name, and each point reads the table
  that bears the name `orders` at that moment. The rows a load selected are the extract's orders in its range (the
  backfill copied the legacy rows, and dq_checks found the two tables equal, rows and values, on every order day in
  between), so neither `_loaded_at` nor `_load_job` of an order is read. After the last commit the table named
  `orders` must hold exactly the extract's orders, or the run stops;
- every other row (tickets, status snapshots, labels, plan changes) commits at its _loaded_at;
- at the same second a point comes before any commit, so a row committed at that very second is not seen.
Each point then reads per-customer state: the orders of the table named `orders` and the committed tickets (sorted
event times, bisect windows on ordered_at and opened_at), the committed snapshot with the greatest snapshot_date, the
committed plan change with the greatest changed_at (none yet: the plan chosen at signup), the point's own app reading
(else the last reading of the customer's earlier points), and the counts of the committed labels.
days_since_last_login cannot be rebuilt (the warehouse keeps no history of last_login_at), so it is written as an
all-null column.

Materially different from the canonical fix: no pandas or numpy; csv, json, heapq and bisect from the standard
library, pyarrow only to write the output, which has its own dtypes (int32 counts, naive microsecond as_of), row order
(newest first), column order (alphabetical) and an extra column (trigger).
"""
import argparse
import bisect
import csv
import datetime as dt
import gzip
import heapq
import json
import operator
import os
from collections import defaultdict

import pyarrow as pa
import pyarrow.parquet as pq

DAY = 86400
M, P0 = 20, 0.05  # district encoding: prior weight, and the prior when no label is committed yet
UTC = dt.timezone.utc
# event kinds, in the order they are applied within one second: points first, then the commits
POINT, TXN, TICKET, SNAPSHOT, LABEL, PLAN = range(6)
NONE = ()
# the scheduled jobs whose transactions write an order table or move a table's name, and the lines they write
ORDER_JOBS = ("legacy_orders", "legacy_backfill", "orders_hourly", "schema_migrations")
LOAD = ("selected orders where ordered_at >= {lo} and ordered_at < {hi}: {rows} rows; sent txn {txn} to commit "
        "into {table}")
COPY = "copied table {source} where ordered_at < {hi}: {rows} rows; sent txn {txn} to commit into {table}"
SENT = "sent txn {txn} to commit"


def epoch(text):
    """UTC ISO 8601 text (a date, or a time with Z or an offset; naive means UTC) as integer epoch seconds."""
    d = dt.datetime.fromisoformat(text)
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return int(d.timestamp())


def opened(path):
    """A text file of the extract, plain, or gzip if only the .gz exists."""
    if not os.path.exists(path) and os.path.exists(path + ".gz"):
        return gzip.open(path + ".gz", "rt", newline="")
    return open(path, newline="")


def table(data_dir, name, *cols):
    """The named columns of one extract table, row by row, as text (a .csv, or a .csv.gz if only that exists)."""
    with opened(os.path.join(data_dir, name + ".csv")) as f:
        reader = csv.reader(f)
        head = next(reader)
        pick = operator.itemgetter(*[head.index(c) for c in cols])
        for row in reader:
            yield pick(row)


def fields(template, text):
    """The {name} fields of text when it has the template's words, else None ({name} may end in ':' or ';')."""
    t, w = template.split(" "), text.split(" ")
    if len(t) != len(w):
        return None
    out = {}
    for a, b in zip(t, w):
        if a.startswith("{"):
            name, _, tail = a[1:].partition("}")
            if len(b) <= len(tail) or not b.endswith(tail):
                return None
            out[name] = b[:len(b) - len(tail)]
        elif a != b:
            return None
    return out


def order_transactions(data_dir):
    """The committed transactions of ORDER_JOBS in commit order, [(at, txn, action)]: ("load", table, lo, hi),
    ("copy", source, table, hi) or ("ddl", statements). Every transaction a line names must be in the commit log."""
    outcome = {}
    with opened(os.path.join(data_dir, "_ops", "commits.jsonl")) as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                outcome[int(rec["txn"])] = (rec["outcome"], rec["at"])
    actions, ddl = {}, {}
    with opened(os.path.join(data_dir, "_ops", "scheduler.log")) as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            parts = line.split(" ", 3)
            if len(parts) < 4 or not parts[2].startswith("run="):
                raise ValueError(f"_ops/scheduler.log line {n} does not read '<time> <job> run=<run> <event>'")
            if parts[1] not in ORDER_JOBS:
                continue
            _, job, run, event = parts
            if event.startswith("state=") or event == "analyze orders":
                continue
            if job == "schema_migrations":
                task = ddl.setdefault(run, {"statements": [], "txn": []})
                if event.startswith("statement: "):
                    task["statements"].append(event[len("statement: "):])
                    continue
                f_ = fields(SENT, event)
                if f_ is None:
                    raise ValueError(f"_ops/scheduler.log line {n}: unknown schema_migrations event")
                task["txn"].append(int(f_["txn"]))
                continue
            f_ = fields(LOAD, event)
            if f_ is not None:
                actions[int(f_["txn"])] = ("load", f_["table"], epoch(f_["lo"]), epoch(f_["hi"]))
                continue
            f_ = fields(COPY, event)
            if f_ is not None:
                actions[int(f_["txn"])] = ("copy", f_["source"], f_["table"], epoch(f_["hi"]))
                continue
            raise ValueError(f"_ops/scheduler.log line {n}: unknown {job} event")
    for run, task in ddl.items():
        if len(task["txn"]) != 1:
            raise ValueError(f"schema_migrations run={run} sends {len(task['txn'])} transactions, not one")
        actions[task["txn"][0]] = ("ddl", tuple(task["statements"]))
    out = []
    for txn, action in actions.items():
        if txn not in outcome:
            raise ValueError(f"_ops/commits.jsonl has no transaction {txn}")
        result, at = outcome[txn]
        if result == "commit":
            out.append((epoch(at), txn, action))
        elif result != "rollback":
            raise ValueError(f"transaction {txn}: outcome {result!r} is neither commit nor rollback")
    out.sort(key=operator.itemgetter(0, 1))
    return out


def load(data_dir):
    """The extract as plain lists, plus one time-sorted event stream per kind of commit and one for the points."""
    x = {"signup": {}, "district": {}, "plan_now": {}}
    for c, signup, plan, district in table(data_dir, "customers", "customer_id", "signup_at", "plan",
                                           "postcode_district"):
        c = int(c)
        x["signup"][c], x["district"][c], x["plan_now"][c] = epoch(signup), district, plan

    x["points"] = [(int(c), epoch(t), trig, float(app) if app != "" else None)
                   for c, t, trig, app in table(data_dir, "scoring_points", "customer_id", "as_of", "trigger",
                                                "app_minutes_7d")]
    # the order system: every order of the extract, by ordered_at (a load selects a range of it)
    x["orders"] = sorted((epoch(ordered), int(c), int(amount)) for c, ordered, amount in
                         table(data_dir, "orders", "customer_id", "ordered_at", "amount_cents"))
    x["txns"] = order_transactions(data_dir)
    x["tickets"] = [(epoch(loaded), int(c), epoch(opened_at)) for c, opened_at, loaded in
                    table(data_dir, "tickets", "customer_id", "opened_at", "_loaded_at")]
    x["snapshots"] = [(epoch(loaded), int(c), epoch(day), status) for c, day, status, loaded in
                      table(data_dir, "status_snapshots", "customer_id", "snapshot_date", "status", "_loaded_at")]
    x["labels"] = [(epoch(loaded), int(c), int(y)) for c, y, loaded in
                   table(data_dir, "labels", "customer_id", "churned_30d", "_loaded_at")]
    changes = [(epoch(loaded), int(c), epoch(changed), old, new) for c, changed, old, new, loaded in
               table(data_dir, "plan_changes", "customer_id", "changed_at", "old_plan", "new_plan", "_loaded_at")]
    x["plan_changes"] = changes
    # the plan chosen at signup: old_plan of the customer's earliest change, else the record's plan (never changed)
    first = {}
    for _, c, changed, old, _ in changes:
        if c not in first or changed < first[c][0]:
            first[c] = (changed, old)
    x["signup_plan"] = {c: (first[c][1] if c in first else plan) for c, plan in x["plan_now"].items()}

    def stream(rows, kind, at=0):
        return sorted((r[at], kind, i) for i, r in enumerate(rows))
    x["streams"] = [stream(x["points"], POINT, 1), stream(x["txns"], TXN), stream(x["tickets"], TICKET),
                    stream(x["snapshots"], SNAPSHOT), stream(x["labels"], LABEL), stream(changes, PLAN)]
    return x


def replay(x):
    """Apply the commits and compute each point from the state committed before it; one output dict of lists."""
    tables, names = [], {}                       # each table: per customer, ordered_at and amount, by ordered_at
    ticket_t = defaultdict(list)                 # per customer, sorted opened_at
    snapshot, plan, last_app = {}, {}, {}
    lab_n = lab_s = 0
    dist_n, dist_s = defaultdict(int), defaultdict(int)
    signup, district, signup_plan = x["signup"], x["district"], x["signup_plan"]
    points, txns = x["points"], x["txns"]
    order_t = [o[0] for o in x["orders"]]
    tickets, snapshots, labels, changes = x["tickets"], x["snapshots"], x["labels"], x["plan_changes"]
    out = {k: [] for k in ("customer_id", "as_of", "trigger", "orders_7d", "orders_30d", "spend_30d_cents",
                           "tickets_30d", "days_since_last_order", "tenure_days", "status", "plan",
                           "app_minutes_7d", "te_district")}

    def named(name, create=False):
        """The table that bears the name now (a load or copy into a free name creates an empty table)."""
        if name not in names:
            if not create:
                raise ValueError(f"no table is named {name}")
            names[name] = len(tables)
            tables.append((defaultdict(list), defaultdict(list)))
        return tables[names[name]]

    def insert(tab, c, ordered, amount):
        times = tab[0][c]
        j = bisect.bisect_right(times, ordered)
        times.insert(j, ordered)
        tab[1][c].insert(j, amount)

    named("orders", create=True)                 # the legacy table bore the name from the first load on
    for t, kind, i in heapq.merge(*x["streams"]):
        if kind == POINT:
            c, _, trig, app = points[i]
            o_t, o_a = named("orders")           # the table the name meant when the request's queries started
            times = o_t.get(c, NONE)
            hi = bisect.bisect_left(times, t)
            lo7 = bisect.bisect_left(times, t - 7 * DAY, 0, hi)
            lo30 = bisect.bisect_left(times, t - 30 * DAY, 0, hi)
            opened_at = ticket_t.get(c, NONE)
            if app is not None:
                last_app[c] = app
            else:
                app = last_app.get(c)
            st, pl = snapshot.get(c), plan.get(c)
            p = lab_s / lab_n if lab_n else P0
            d = district[c]
            out["customer_id"].append(c)
            out["as_of"].append(t)
            out["trigger"].append(trig)
            out["orders_7d"].append(hi - lo7)
            out["orders_30d"].append(hi - lo30)
            out["spend_30d_cents"].append(sum(o_a[c][lo30:hi]) if hi > lo30 else 0)
            out["tickets_30d"].append(bisect.bisect_left(opened_at, t) - bisect.bisect_left(opened_at, t - 30 * DAY))
            out["days_since_last_order"].append((t - times[hi - 1]) / DAY if hi else None)
            out["tenure_days"].append((t - signup[c]) / DAY)
            out["status"].append(st[1] if st is not None else None)
            out["plan"].append(pl[1] if pl is not None else signup_plan[c])
            out["app_minutes_7d"].append(app)
            out["te_district"].append((dist_s[d] + M * p) / (dist_n[d] + M))
        elif kind == TXN:
            action = txns[i][2]
            if action[0] == "load":
                _, name, lo, hi = action
                tab = named(name, create=True)
                for j in range(bisect.bisect_left(order_t, lo), bisect.bisect_left(order_t, hi)):
                    ordered, c, amount = x["orders"][j]
                    insert(tab, c, ordered, amount)
            elif action[0] == "copy":
                _, source, name, hi = action
                src, tab = named(source), named(name, create=True)
                for c in sorted(src[0]):
                    times, amounts = src[0][c], src[1][c]
                    for j in range(bisect.bisect_left(times, hi)):
                        insert(tab, c, times[j], amounts[j])
            else:
                for sql in action[1]:
                    w = sql.split(" ")
                    if len(w) == 6 and w[:2] == ["ALTER", "TABLE"] and w[3:5] == ["RENAME", "TO"]:
                        if w[2] not in names or w[5] in names:
                            raise ValueError(f"cannot apply {sql!r}")
                        names[w[5]] = names.pop(w[2])
                    elif len(w) == 3 and w[:2] == ["DROP", "TABLE"] and w[2] in names:
                        del names[w[2]]
                    else:
                        raise ValueError(f"cannot apply {sql!r}")
        elif kind == TICKET:
            _, c, opened_at = tickets[i]
            bisect.insort(ticket_t[c], opened_at)
        elif kind == SNAPSHOT:
            _, c, day, status = snapshots[i]
            cur = snapshot.get(c)
            if cur is None or day > cur[0]:
                snapshot[c] = (day, status)
        elif kind == LABEL:
            _, c, y = labels[i]
            lab_n += 1
            lab_s += y
            dist_n[district[c]] += 1
            dist_s[district[c]] += y
        else:
            _, c, changed, _, new = changes[i]
            cur = plan.get(c)
            if cur is None or changed > cur[0]:
                plan[c] = (changed, new)
    # the replayed `orders` table must be the extract's own
    o_t, o_a = named("orders")
    held = sorted((ordered, c, amount) for c in o_t for ordered, amount in zip(o_t[c], o_a[c]))
    if held != x["orders"]:
        raise ValueError(f"the replayed commits leave {len(held)} rows in the table named orders, not the extract's "
                         f"{len(x['orders'])} orders")
    return out


def write(out, path):
    """Newest rows first, columns in alphabetical order, the dropped feature present and all null."""
    n = len(out["as_of"])
    order = sorted(range(n), key=lambda i: (-out["as_of"][i], out["customer_id"][i]))

    def col(name, typ):
        v = out[name]
        return pa.array([v[i] for i in order], typ)
    cols = {
        "app_minutes_7d": col("app_minutes_7d", pa.float64()),
        "as_of": pa.array([out["as_of"][i] * 1_000_000 for i in order], pa.timestamp("us")),
        "customer_id": col("customer_id", pa.int64()),
        "days_since_last_login": pa.nulls(n, pa.float64()),
        "days_since_last_order": col("days_since_last_order", pa.float64()),
        "orders_30d": col("orders_30d", pa.int32()),
        "orders_7d": col("orders_7d", pa.int32()),
        "plan": col("plan", pa.string()),
        "spend_30d_cents": col("spend_30d_cents", pa.int64()),
        "status": col("status", pa.string()),
        "te_district": col("te_district", pa.float64()),
        "tenure_days": col("tenure_days", pa.float64()),
        "tickets_30d": col("tickets_30d", pa.int32()),
        "trigger": col("trigger", pa.string()),
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    pq.write_table(pa.table(cols), path)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, help="folder with the extract CSVs and _ops/")
    ap.add_argument("--out", required=True, help="output parquet file")
    a = ap.parse_args()
    n = write(replay(load(a.data)), a.out)
    print(f"wrote {n} rows to {a.out}")


if __name__ == "__main__":
    main()

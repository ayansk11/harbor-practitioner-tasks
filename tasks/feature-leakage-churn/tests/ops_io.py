"""The scheduler's records of a churn extract, `_ops/scheduler.log` and `_ops/commits.jsonl` (the grader's copy of the
authoring ops_log.py, with only this docstring changed): dataset_io.py reads H's records and writes those of check B's
perturbed copies with it, so the copies' records have the byte format of H's.

In Python the records are two frames, ops = {"tasks": ..., "parity": ...}, every time int64 epoch seconds (UTC):
  tasks   one row per scheduler task run, key (job, run), sorted by (started_at, job, run), index 0..n-1, with the
          columns and dtypes of TASK_COLUMNS; a field that none of the task's lines carries is NA ("" in a str column)
  parity  one row per dq_checks line, sorted by (at, day), with the columns and dtypes of PARITY_COLUMNS
In the files (ASCII, LF line ends, a final LF):
  scheduler.log  one UTC event per line, `<time> <job> run=<run> <event>`, each event one of EVENTS: a task's start
                 (`state=running`), the lines its job writes (ALLOWED) and its end (`state=success` or `state=failed`)
  commits.jsonl  one JSON object per transaction a task sent: txn, at, outcome (commit or rollback), table and rows
                 (both null for schema statements), sorted by (at, txn)

render(ops)          -> {"scheduler.log": text, "commits.jsonl": text}, formatting only. Lines are sorted by (time,
                        job, run, rank): the start 0, statement k 10 + k, the line that sends the transaction 20, a
                        parity line 30 (then by day), analyze 40, the end 50. Statement k is written at started_at + k.
parse(files)         -> ops, the exact inverse of render: a ValueError for a line or event that no pattern fully
                        matches, an event its job may not write, a (job, run) without exactly one start and one end
                        line, a txn in one file only, rows or table that differ between the files, or any text that
                        render would not write back byte for byte.
recount(ops, tables) -> ops with every count recomputed from the extract's tables (rows of each LOAD, COPY and WRITE,
                        rows_a and rows_b of each parity line), nothing else changed.
validate(ops)        -> problems, [] when sound: the fields each job's lines carry, started_at < sent_at < at <
                        analyze_at < end_at where present, lo < hi, analyze if and only if a legacy_orders transaction
                        commits, statements and parity lines inside their task, (job, run) and txn unique.
typed(ops)           -> ops with the columns, dtypes, sort and index that parse returns.
"""
import json
import re

import numpy as np
import pandas as pd

SCHEDULER, COMMITS = "scheduler.log", "commits.jsonl"
DAY = 86400
JOBS = ("legacy_orders", "legacy_backfill", "orders_hourly", "dq_checks", "schema_migrations", "label_job",
        "billing_export", "crm_sync")
TASK_COLUMNS = {"job": "str", "run": "str", "started_at": "int64", "end_at": "int64", "state": "str", "lo": "Int64",
                "hi": "Int64", "source": "str", "statements": "str", "table": "str", "rows": "Int64", "txn": "Int64",
                "sent_at": "Int64", "at": "Int64", "outcome": "str", "analyze_at": "Int64"}
PARITY_COLUMNS = {"run": "str", "at": "int64", "day": "int64", "table_a": "str", "rows_a": "int64", "table_b": "str",
                  "rows_b": "int64"}
TIME_COLUMNS = ("started_at", "end_at", "lo", "hi", "sent_at", "at", "analyze_at")

TS = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
D = r"\d{4}-\d{2}-\d{2}"
RUN = r"\d{4}-\d{2}-\d{2}(T\d{2}:00:00Z)?"
SQL = r"ALTER TABLE [a-z_]+ RENAME TO [a-z_]+|DROP TABLE [a-z_]+"
NAME = r"[a-z_]+"
LINE = re.compile(r"^(?P<ts>" + TS + r") (?P<job>[a-z_]+) run=(?P<run>" + RUN + r") (?P<event>.+)$")
EVENTS = {
    "STATE": re.compile(r"state=(?P<state>running|success|failed)"),
    "LOAD": re.compile(r"selected orders where ordered_at >= (?P<lo>" + TS + r") and ordered_at < (?P<hi>" + TS
                       + r"): (?P<rows>\d+) rows; sent txn (?P<txn>\d+) to commit into (?P<table>orders|orders_new)"),
    "WRITE": re.compile(r"wrote (?P<rows>\d+) rows into (?P<table>labels|status_snapshots|plan_changes)"
                        r"(?P<also> and updated customers)?; sent txn (?P<txn>\d+) to commit"),
    "COPY": re.compile(r"copied table (?P<source>[a-z_]+) where ordered_at < (?P<hi>" + TS + r"): (?P<rows>\d+) rows; "
                       r"sent txn (?P<txn>\d+) to commit into (?P<table>[a-z_]+)"),
    "ANALYZE": re.compile(r"analyze (?P<table>orders)"),
    "PARITY": re.compile(r"order day (?P<day>" + D + r"): (?P<table_a>[a-z_]+) (?P<rows_a>\d+) rows, "
                         r"(?P<table_b>[a-z_]+) (?P<rows_b>\d+) rows, rows and values equal"),
    "STATEMENT": re.compile(r"statement: (?P<sql>" + SQL + r")"),
    "SENT": re.compile(r"sent txn (?P<txn>\d+) to commit"),
}
# the events each job writes between its start and end lines
ALLOWED = {"legacy_orders": ("LOAD", "ANALYZE"), "legacy_backfill": ("COPY",), "orders_hourly": ("LOAD",),
           "dq_checks": ("PARITY",), "schema_migrations": ("STATEMENT", "SENT"), "label_job": ("WRITE",),
           "billing_export": ("WRITE",), "crm_sync": ("WRITE",)}
# the line that sends the job's transaction (a label_job run that fails sends none; dq_checks sends none)
SENDS = {"legacy_orders": "LOAD", "orders_hourly": "LOAD", "legacy_backfill": "COPY", "label_job": "WRITE",
         "billing_export": "WRITE", "crm_sync": "WRITE", "schema_migrations": "SENT"}
WRITE_TABLE = {"label_job": "labels", "billing_export": "status_snapshots", "crm_sync": "plan_changes"}
TXN_FIELDS = ("txn", "sent_at", "at", "outcome")
# the task fields that each job's lines carry; OPTIONAL ones may be NA (label_job: all of its fields or none)
CARRIES = {"legacy_orders": ("lo", "hi", "rows", "table") + TXN_FIELDS,
           "orders_hourly": ("lo", "hi", "rows", "table") + TXN_FIELDS,
           "legacy_backfill": ("hi", "source", "rows", "table") + TXN_FIELDS,
           "label_job": ("rows", "table") + TXN_FIELDS,
           "billing_export": ("rows", "table") + TXN_FIELDS,
           "crm_sync": ("rows", "table") + TXN_FIELDS,
           "dq_checks": (),
           "schema_migrations": ("statements",) + TXN_FIELDS}
OPTIONAL = {"legacy_orders": ("analyze_at",), "label_job": CARRIES["label_job"]}
FIELDS = ("lo", "hi", "source", "statements", "table", "rows", "txn", "sent_at", "at", "outcome", "analyze_at")
LIMIT = 20  # problems listed per check; the rest are counted


# ------------------------------------------------------------------------------------------------ conversions
def _iso(col):
    """Epoch seconds (int64 or Int64) -> ISO 8601 UTC strings with a Z suffix, None for NA."""
    v = pd.array(col, dtype="Int64")
    ok = ~np.asarray(v.isna(), dtype=bool)
    out = [None] * len(v)
    if ok.any():
        txt = np.datetime_as_string(np.asarray(v[ok], dtype="int64").astype("datetime64[s]"), unit="s")
        for k, s in zip(np.flatnonzero(ok).tolist(), txt.tolist()):
            out[k] = s + "Z"
    return out


def _iso1(sec):
    return str(np.datetime64(int(sec), "s")) + "Z"


def _dates(col):
    """Epoch seconds of 00:00 UTC -> `YYYY-MM-DD`."""
    return np.datetime_as_string((np.asarray(col, dtype="int64") // DAY).astype("datetime64[D]"), unit="D").tolist()


def _secs(values):
    """`YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DD` strings (None for NA) -> pandas Int64 epoch seconds."""
    out = pd.array([pd.NA] * len(values), dtype="Int64")
    idx = [k for k, v in enumerate(values) if v is not None]
    if idx:
        sec = np.array([values[k].rstrip("Z") for k in idx], dtype="datetime64[s]").astype("int64")
        out[np.array(idx, dtype=np.int64)] = sec
    return out


def _ints(col):
    """Integers (int64 or Int64) -> Python ints, None for NA."""
    return [None if x is None else int(x) for x in pd.array(col, dtype="Int64").to_numpy(dtype=object,
                                                                                       na_value=None).tolist()]


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _lines(text, name):
    if not isinstance(text, str):
        raise ValueError(f"{name}: not text")
    if text == "":
        return []
    if not text.isascii():
        raise ValueError(f"{name}: not ASCII")
    if not text.endswith("\n"):
        raise ValueError(f"{name}: no line end after the last line")
    return text[:-1].split("\n")


# ------------------------------------------------------------------------------------------------ layout
def _frame(df, columns, keys):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"columns missing: {missing}")
    out = {}
    for c, dt in columns.items():
        s = df[c]
        if dt == "str":
            v = s.astype(object)
            out[c] = v.where(v.notna(), "").astype("str")
        else:
            out[c] = s.astype(dt)
    return pd.DataFrame(out).sort_values(keys, kind="mergesort").reset_index(drop=True)


def typed(ops):
    """ops with the record layout's columns (in that order), dtypes, sort and index: what parse returns."""
    return {"tasks": _frame(ops["tasks"], TASK_COLUMNS, ["started_at", "job", "run"]),
            "parity": _frame(ops["parity"], PARITY_COLUMNS, ["at", "day"])}


def _reporter(out, labels):
    def report(mask, what):
        idx = np.flatnonzero(mask)
        out.extend(f"{labels[i]}: {what}" for i in idx[:LIMIT].tolist())
        if len(idx) > LIMIT:
            out.append(f"{len(idx) - LIMIT} more: {what}")
    return report


def _shape_problems(ops):
    """What the files cannot hold, on typed frames: job, run, state, outcome, table, source and statement values, the
    fields each job's lines carry (set) and those they do not (NA), parity lines without their dq_checks task."""
    t, par = ops["tasks"], ops["parity"]
    out = []
    report = _reporter(out, (t["job"] + " run=" + t["run"]).tolist())
    job = t["job"].to_numpy(dtype=object)
    report(~np.isin(job, JOBS), "not a scheduled job")
    report(~t["run"].str.fullmatch(RUN).to_numpy(dtype=bool), "run is not YYYY-MM-DD or YYYY-MM-DDTHH:00:00Z")
    report(~np.isin(t["state"].to_numpy(dtype=object), ("success", "failed")), "state is not success or failed")
    pres = {c: (t[c] != "").to_numpy(dtype=bool) if TASK_COLUMNS[c] == "str" else t[c].notna().to_numpy(dtype=bool)
            for c in FIELDS}
    for j in JOBS:
        m = job == j
        if not m.any():
            continue
        opt = OPTIONAL.get(j, ())
        for c in FIELDS:
            if c in CARRIES[j] and c not in opt:
                report(m & ~pres[c], f"{c} missing")
            elif c not in CARRIES[j] and c not in opt:
                report(m & pres[c], f"{c} set, but no line of {j} carries it")
        if j == "label_job":
            g = np.column_stack([pres[c] for c in CARRIES[j]])
            report(m & g.any(axis=1) & ~g.all(axis=1), "its write fields are set in part")
    report(pres["outcome"] & ~np.isin(t["outcome"].to_numpy(dtype=object), ("commit", "rollback")),
           "outcome is not commit or rollback")
    table = t["table"].to_numpy(dtype=object)
    report((job == "legacy_orders") & pres["table"] & (table != "orders"), "legacy_orders loads into orders only")
    report((job == "orders_hourly") & pres["table"] & ~np.isin(table, ("orders", "orders_new")),
           "orders_hourly loads into orders or orders_new only")
    for j, name in WRITE_TABLE.items():
        report((job == j) & pres["table"] & (table != name), f"{j} writes into {name} only")
    for c in ("table", "source"):
        report(pres[c] & ~t[c].str.fullmatch(NAME).to_numpy(dtype=bool), f"{c} is not a table name")
    sql = re.compile(SQL)
    report(pres["statements"] & ~np.array([all(sql.fullmatch(s) for s in v.split("; ")) for v in
                                            t["statements"].tolist()], dtype=bool),
           "a statement is not ALTER TABLE <a> RENAME TO <b> or DROP TABLE <a>")
    for c in ("rows", "txn"):
        report(pres[c] & (t[c].fillna(0).to_numpy(dtype="int64") < 0), f"{c} is negative")
    if len(par):
        prep = _reporter(out, ("dq_checks run=" + par["run"] + " order day " + pd.Series(_dates(par["day"]),
                                                                                        dtype="str")).tolist())
        dq = set(t.loc[job == "dq_checks", "run"].tolist())
        prep(~par["run"].isin(dq).to_numpy(dtype=bool), "a parity line without its dq_checks task")
        prep(par["day"].to_numpy(dtype="int64") % DAY != 0, "day is not 00:00 UTC")
        for c in ("table_a", "table_b"):
            prep(~par[c].str.fullmatch(NAME).to_numpy(dtype=bool), f"{c} is not a table name")
        for c in ("rows_a", "rows_b"):
            prep(par[c].to_numpy(dtype="int64") < 0, f"{c} is negative")
    return out


# ------------------------------------------------------------------------------------------------ render, parse
def render(ops):
    """The two files' text from the frames (formatting only); a ValueError for records the files cannot hold."""
    ops = typed(ops)
    bad = _shape_problems(ops)
    if bad:
        raise ValueError("records the files cannot hold: " + "; ".join(bad[:5]))
    t, par = ops["tasks"], ops["parity"]
    job, run, state = t["job"].tolist(), t["run"].tolist(), t["state"].tolist()
    table, source, statements, outcome = (t[c].tolist() for c in ("table", "source", "statements", "outcome"))
    iso = {c: _iso(t[c]) for c in TIME_COLUMNS}
    started, ended = t["started_at"].tolist(), t["end_at"].tolist()
    sent, at, analyze = _ints(t["sent_at"]), _ints(t["at"]), _ints(t["analyze_at"])
    rows, txn = _ints(t["rows"]), _ints(t["txn"])
    lines = []
    for i in range(len(t)):
        j, r = job[i], run[i]
        head = f" {j} run={r} "
        lines.append((started[i], j, r, 0, 0, iso["started_at"][i] + head + "state=running"))
        lines.append((ended[i], j, r, 50, 0, iso["end_at"][i] + head + "state=" + state[i]))
        if txn[i] is None:
            continue
        if j in ("legacy_orders", "orders_hourly"):
            ev = (f"selected orders where ordered_at >= {iso['lo'][i]} and ordered_at < {iso['hi'][i]}: {rows[i]} "
                  f"rows; sent txn {txn[i]} to commit into {table[i]}")
        elif j == "legacy_backfill":
            ev = (f"copied table {source[i]} where ordered_at < {iso['hi'][i]}: {rows[i]} rows; sent txn {txn[i]} to "
                  f"commit into {table[i]}")
        elif j == "schema_migrations":
            for k, sql in enumerate(statements[i].split("; "), 1):
                lines.append((started[i] + k, j, r, 10 + k, 0, _iso1(started[i] + k) + head + "statement: " + sql))
            ev = f"sent txn {txn[i]} to commit"
        else:
            also = " and updated customers" if j == "crm_sync" else ""
            ev = f"wrote {rows[i]} rows into {table[i]}{also}; sent txn {txn[i]} to commit"
        lines.append((sent[i], j, r, 20, 0, iso["sent_at"][i] + head + ev))
        if analyze[i] is not None:
            lines.append((analyze[i], j, r, 40, 0, iso["analyze_at"][i] + head + "analyze orders"))
    p_iso, p_day = _iso(par["at"]), _dates(par["day"])
    for i, (r, a, d, ta, ra, tb, rb) in enumerate(zip(*(par[c].tolist() for c in PARITY_COLUMNS))):
        lines.append((a, "dq_checks", r, 30, d, f"{p_iso[i]} dq_checks run={r} order day {p_day[i]}: {ta} {ra} rows, "
                                                f"{tb} {rb} rows, rows and values equal"))
    lines.sort()
    objs = sorted((at[i], txn[i], i) for i in range(len(t)) if txn[i] is not None)
    commits = [json.dumps({"txn": txn[i], "at": iso["at"][i], "outcome": outcome[i], "table": table[i] or None,
                           "rows": rows[i]}) for _, _, i in objs]
    return {SCHEDULER: "".join(x[5] + "\n" for x in lines), COMMITS: "".join(c + "\n" for c in commits)}


def parse(files):
    """The frames from the two files' text (the exact inverse of render; see the module docstring)."""
    log, com = files[SCHEDULER], files[COMMITS]
    tasks, parity = {}, []
    for n, line in enumerate(_lines(log, SCHEDULER), 1):
        m, kind, e = LINE.fullmatch(line), None, None
        if m:
            for kind, pat in EVENTS.items():
                e = pat.fullmatch(m["event"])
                if e:
                    break
        if e is None:
            raise ValueError(f"{SCHEDULER} line {n}: no pattern fully matches {line!r}")
        ts, job, run = m["ts"], m["job"], m["run"]
        where = f"{SCHEDULER} line {n} ({job} run={run})"
        if job not in ALLOWED or (kind != "STATE" and kind not in ALLOWED[job]):
            raise ValueError(f"{where}: an event this job may not write: {line!r}")
        rec = tasks.setdefault((job, run), {"job": job, "run": run, "statements": []})
        if kind == "STATE":
            key = "started_at" if e["state"] == "running" else "end_at"
            if key in rec:
                raise ValueError(f"{where}: a second {'start' if key == 'started_at' else 'end'} line")
            rec[key] = ts
            if key == "end_at":
                rec["state"] = e["state"]
        elif kind == "PARITY":
            parity.append({"run": run, "at": ts, "day": e["day"], "table_a": e["table_a"], "rows_a": int(e["rows_a"]),
                           "table_b": e["table_b"], "rows_b": int(e["rows_b"])})
        elif kind == "STATEMENT":
            rec["statements"].append(e["sql"])
        elif kind == "ANALYZE":
            if "analyze_at" in rec:
                raise ValueError(f"{where}: a second analyze line")
            rec["analyze_at"] = ts
        else:  # LOAD, COPY, WRITE or SENT: the line that sends the task's transaction
            if "txn" in rec:
                raise ValueError(f"{where}: a second line that sends a transaction")
            g = e.groupdict()
            if kind == "LOAD" and job == "legacy_orders" and g["table"] != "orders":
                raise ValueError(f"{where}: legacy_orders loads into orders only")
            if kind == "WRITE":
                if g["table"] != WRITE_TABLE[job]:
                    raise ValueError(f"{where}: {job} writes into {WRITE_TABLE[job]} only")
                if (g["also"] is not None) != (job == "crm_sync"):
                    raise ValueError(f"{where}: crm_sync, and only crm_sync, also updates customers")
            rec["sent_at"], rec["txn"] = ts, int(g["txn"])
            for c in ("lo", "hi", "source", "table"):
                if g.get(c) is not None:
                    rec[c] = g[c]
            if g.get("rows") is not None:
                rec["rows"] = int(g["rows"])
    for (job, run), rec in tasks.items():
        where = f"{SCHEDULER} ({job} run={run})"
        if "started_at" not in rec or "end_at" not in rec:
            raise ValueError(f"{where}: not exactly one start (state=running) and one end (state=success or "
                             f"state=failed) line")
        if job in SENDS and job != "label_job" and "txn" not in rec:
            raise ValueError(f"{where}: no line that sends its transaction")
        if job == "schema_migrations" and not rec["statements"]:
            raise ValueError(f"{where}: no statement line")
        rec["statements"] = "; ".join(rec["statements"])

    commits = {}
    for n, line in enumerate(_lines(com, COMMITS), 1):
        where = f"{COMMITS} line {n}"
        try:
            o = json.loads(line)
        except ValueError:
            raise ValueError(f"{where}: not JSON: {line!r}") from None
        if not isinstance(o, dict) or list(o) != ["txn", "at", "outcome", "table", "rows"]:
            raise ValueError(f"{where}: not an object with the keys txn, at, outcome, table, rows: {line!r}")
        if not (_is_int(o["txn"]) and isinstance(o["at"], str) and re.fullmatch(TS, o["at"])
                and o["outcome"] in ("commit", "rollback") and (o["table"] is None or isinstance(o["table"], str))
                and (o["rows"] is None or _is_int(o["rows"]))):
            raise ValueError(f"{where}: a value of the wrong type or form: {line!r}")
        if o["txn"] in commits:
            raise ValueError(f"{where}: txn {o['txn']} twice")
        commits[o["txn"]] = o
    senders = {}
    for (job, run), rec in tasks.items():
        if "txn" not in rec:
            continue
        x, where = rec["txn"], f"{job} run={run}"
        if x in senders:
            raise ValueError(f"{SCHEDULER}: txn {x} sent by two tasks, {senders[x]} and {where}")
        senders[x] = where
        o = commits.pop(x, None)
        if o is None:
            raise ValueError(f"{where}: txn {x} is in {SCHEDULER} only")
        if job == "schema_migrations":
            if o["table"] is not None or o["rows"] is not None:
                raise ValueError(f"{where}: txn {x} of a schema statement has a table or rows in {COMMITS}")
        elif o["table"] != rec["table"] or o["rows"] != rec["rows"]:
            raise ValueError(f"{where}: txn {x} has table {o['table']} and rows {o['rows']} in {COMMITS}, but "
                             f"{rec['table']} and {rec['rows']} in {SCHEDULER}")
        rec["at"], rec["outcome"] = o["at"], o["outcome"]
    if commits:
        raise ValueError(f"{COMMITS}: txn {min(commits)} is in {COMMITS} only")

    recs = list(tasks.values())
    t = pd.DataFrame({c: (_secs([r.get(c) for r in recs]) if c in TIME_COLUMNS else
                          pd.array([r.get(c) for r in recs], dtype="Int64") if TASK_COLUMNS[c] == "Int64" else
                          [r.get(c) for r in recs]) for c in TASK_COLUMNS})
    p = pd.DataFrame({c: (_secs([r[c] for r in parity]) if c in ("at", "day") else [r[c] for r in parity])
                      for c in PARITY_COLUMNS})
    ops = typed({"tasks": t, "parity": p})
    again = render(ops)
    for name, text in ((SCHEDULER, log), (COMMITS, com)):
        if again[name] != text:
            a, b = text.split("\n"), again[name].split("\n")
            k = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
            raise ValueError(f"{name} line {k + 1} is not as render writes it: {a[k] if k < len(a) else '(end)'!r}, "
                             f"render writes {b[k] if k < len(b) else '(end)'!r}")
    return ops


# ------------------------------------------------------------------------------------------------ counts, checks
def _lookup(keys, counts, q):
    """counts[k] where keys[k] == q, else 0 (keys sorted and unique)."""
    q = np.asarray(q, dtype="int64")
    if len(keys) == 0:
        return np.zeros(len(q), dtype="int64")
    j = np.minimum(np.searchsorted(keys, q), len(keys) - 1)
    return np.where(keys[j] == q, counts[j], 0).astype("int64")


def recount(ops, tables):
    """ops with every count recomputed from the extract's tables, nothing else changed: a LOAD's rows are the orders
    with lo <= ordered_at < hi, a COPY's the orders with ordered_at < hi, a WRITE's the rows of its table with
    `_loaded_at` equal to its `at` (billing_export: the rows of its partition, snapshot_date = its run date), and a
    parity line's rows_a and rows_b are the orders of its UTC day."""
    ops = typed(ops)
    t, par = ops["tasks"], ops["parity"]
    job = t["job"].to_numpy(dtype=object)
    oa = np.sort(np.asarray(tables["orders"]["ordered_at"], dtype="int64"))

    def need(col, m):
        v = t.loc[m, col]
        if v.isna().any():
            raise ValueError(f"recount: {col} missing on {int(v.isna().sum())} task(s)")
        return v.to_numpy(dtype="int64")

    new, done = np.zeros(len(t), dtype="int64"), np.zeros(len(t), dtype=bool)
    load = np.isin(job, ("legacy_orders", "orders_hourly"))
    if load.any():
        new[load] = np.searchsorted(oa, need("hi", load), "left") - np.searchsorted(oa, need("lo", load), "left")
        done |= load
    copy = job == "legacy_backfill"
    if copy.any():
        new[copy] = np.searchsorted(oa, need("hi", copy), "left")
        done |= copy
    sends = t["txn"].notna().to_numpy(dtype=bool)
    table = t["table"].to_numpy(dtype=object)
    for name in ("labels", "plan_changes"):
        m = np.isin(job, ("label_job", "crm_sync")) & sends & (table == name)
        if m.any():
            keys, counts = np.unique(np.asarray(tables[name]["_loaded_at"], dtype="int64"), return_counts=True)
            new[m] = _lookup(keys, counts, need("at", m))
            done |= m
    bill = (job == "billing_export") & sends
    if bill.any():
        keys, counts = np.unique(np.asarray(tables["status_snapshots"]["snapshot_date"], dtype="int64"),
                                 return_counts=True)
        new[bill] = _lookup(keys, counts, _secs(t.loc[bill, "run"].tolist()).to_numpy(dtype="int64"))
        done |= bill
    rows = t["rows"].copy()
    rows[done] = new[done]
    t = t.assign(rows=rows)
    if len(par):
        keys, counts = np.unique(oa // DAY * DAY, return_counts=True)
        c = _lookup(keys, counts, par["day"].to_numpy(dtype="int64"))
        par = par.assign(rows_a=c, rows_b=c.copy())
    return {"tasks": t, "parity": par}


def validate(ops):
    """Problems of the records (see the module docstring); [] when sound."""
    try:
        ops = typed(ops)
    except (KeyError, TypeError, ValueError) as e:
        return [f"not in the record layout: {e}"]
    t, par = ops["tasks"], ops["parity"]
    out = _shape_problems(ops)
    report = _reporter(out, (t["job"] + " run=" + t["run"]).tolist())
    prev, bad = np.full(len(t), -np.inf), np.zeros(len(t), dtype=bool)
    for c in ("started_at", "sent_at", "at", "analyze_at", "end_at"):
        v = t[c].to_numpy(dtype="float64", na_value=np.nan)
        p = ~np.isnan(v)
        bad |= p & (v <= prev)
        prev = np.where(p, v, prev)
    report(bad, "times not in the order started_at < sent_at < at < analyze_at < end_at")
    lo, hi = (t[c].to_numpy(dtype="float64", na_value=np.nan) for c in ("lo", "hi"))
    report(~np.isnan(lo) & ~np.isnan(hi) & (lo >= hi), "lo is not below hi")
    job = t["job"].to_numpy(dtype=object)
    commit = (job == "legacy_orders") & (t["outcome"].to_numpy(dtype=object) == "commit")
    report(commit != t["analyze_at"].notna().to_numpy(dtype=bool),
           "analyze orders is written if and only if a legacy_orders transaction commits")
    k = np.array([len(s.split("; ")) if s else 0 for s in t["statements"].tolist()], dtype="float64")
    sent = t["sent_at"].to_numpy(dtype="float64", na_value=np.nan)
    report((job == "schema_migrations") & (k > 0) & ~(t["started_at"].to_numpy(dtype="float64") + k < sent),
           "a statement at or after the line that sends its transaction")
    report(t.duplicated(["job", "run"], keep=False).to_numpy(dtype=bool), "(job, run) not unique")
    tx = t["txn"]
    report((tx.notna() & tx.duplicated(keep=False)).to_numpy(dtype=bool), "txn not unique")
    if len(par):
        dq = t[job == "dq_checks"].drop_duplicates("run").set_index("run")
        s = par["run"].map(dq["started_at"]).to_numpy(dtype="float64", na_value=np.nan)
        e = par["run"].map(dq["end_at"]).to_numpy(dtype="float64", na_value=np.nan)
        a = par["at"].to_numpy(dtype="float64")
        prep = _reporter(out, ("dq_checks run=" + par["run"] + " order day " + pd.Series(_dates(par["day"]),
                                                                                        dtype="str")).tolist())
        prep(~np.isnan(s) & ~((s < a) & (a < e)), "a parity line outside its dq_checks task")
    return out

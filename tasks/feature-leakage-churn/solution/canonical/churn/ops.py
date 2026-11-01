"""The scheduler's records of an extract (`_ops/`, docs/WAREHOUSE.md): the runs of the nightly `legacy_orders` loader
and the cutover that gave the name `orders` to the table that the backfill and the hourly loader filled.

`_ops/scheduler.log` has one UTC event per line, `<time> <job> run=<run> <event>`: each task's start (`state=running`)
and end (`state=success` or `state=failed`), and between them the lines the task writes. `_ops/commits.jsonl` is the
commit log of the scheduled jobs, one JSON object per transaction: a transaction is committed if and only if its
outcome is `commit`, and it is committed at its `at`. A task's state lines say when the task started and ended, not
when its rows were committed: a legacy run sends its rows in one transaction and then analyzes the table, so its end
line comes after its commit, and a rolled-back run committed nothing. The two files are joined on the transaction
number of the `sent txn <n> to commit` text.

Every time here is int64 epoch seconds (UTC).
"""
import datetime as dt
import json
import os
import re

import pandas as pd

TS = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
RUN = r"\d{4}-\d{2}-\d{2}(T\d{2}:00:00Z)?"
LINE = re.compile(rf"(?P<ts>{TS}) (?P<job>[a-z_]+) run=(?P<run>{RUN}) (?P<event>.+)")
STATE = re.compile(r"state=(?P<state>running|success|failed)")
LOAD = re.compile(rf"selected orders where ordered_at >= (?P<lo>{TS}) and ordered_at < (?P<hi>{TS}): (?P<rows>\d+) "
                  rf"rows; sent txn (?P<txn>\d+) to commit into (?P<table>orders|orders_new)")
ANALYZE = re.compile(r"analyze (?P<table>orders)")
STATEMENT = re.compile(r"statement: (?P<sql>ALTER TABLE [a-z_]+ RENAME TO [a-z_]+|DROP TABLE [a-z_]+)")
SENT = re.compile(r"sent txn (?P<txn>\d+) to commit")
CUTOVER = "ALTER TABLE orders_new RENAME TO orders"
LEGACY_COLUMNS = ["run", "lo", "hi", "started_at", "end_at", "txn", "at", "outcome", "state"]


def epoch(text):
    """UTC ISO 8601 text with a Z suffix (`2025-04-20T03:02:11Z`) as integer epoch seconds."""
    return int(dt.datetime.fromisoformat(text).timestamp())


def _path(data_dir, name):
    return os.path.join(data_dir, "_ops", name)


def _tasks(data_dir, job):
    """{run: task} for the tasks of one scheduled job in scheduler.log. A task holds its started_at and end_at (the
    times of its state lines), its state (success or failed) and its other lines, [(line number, time, event)] in
    file order. Every line of the log must read `<time> <job> run=<run> <event>`."""
    tasks = {}
    with open(_path(data_dir, "scheduler.log"), encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            m = LINE.fullmatch(line)
            if m is None:
                raise ValueError(f"_ops/scheduler.log line {n} does not read '<time> <job> run=<run> <event>'")
            if m["job"] != job:
                continue
            run, t, event = m["run"], epoch(m["ts"]), m["event"]
            task = tasks.setdefault(run, {"lines": []})
            s = STATE.fullmatch(event)
            if s is None:
                task["lines"].append((n, t, event))
            elif s["state"] == "running":
                if "started_at" in task:
                    raise ValueError(f"_ops/scheduler.log line {n}: {job} run={run} starts twice")
                task["started_at"] = t
            else:
                if "end_at" in task:
                    raise ValueError(f"_ops/scheduler.log line {n}: {job} run={run} ends twice")
                task["end_at"], task["state"] = t, s["state"]
    for run, task in tasks.items():
        if "started_at" not in task or "end_at" not in task:
            raise ValueError(f"_ops/scheduler.log: {job} run={run} lacks its state=running or its end line")
    return tasks


def _commits(data_dir):
    """{txn: (at text, outcome)} from commits.jsonl."""
    out = {}
    with open(_path(data_dir, "commits.jsonl"), encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            rec = json.loads(line)
            txn, outcome = int(rec["txn"]), rec["outcome"]
            if outcome not in ("commit", "rollback"):
                raise ValueError(f"_ops/commits.jsonl line {n}: outcome {outcome!r} is neither commit nor rollback")
            if txn in out:
                raise ValueError(f"_ops/commits.jsonl line {n}: txn {txn} occurs twice")
            out[txn] = (rec["at"], outcome)
    return out


def _transaction(commits, txn, what):
    if txn not in commits:
        raise ValueError(f"_ops/commits.jsonl has no transaction {txn} ({what} sent it)")
    at, outcome = commits[txn]
    return epoch(at), outcome


def legacy_runs(data_dir):
    """One row per `legacy_orders` task, in start order: run (its run date), lo and hi (it selected the orders with
    lo <= ordered_at < hi), started_at and end_at (its state lines), txn, at and outcome (its transaction in the
    commit log: committed at `at` if the outcome is `commit`, nothing committed if `rollback`) and state (success or
    failed, from its end line). Times are int64 epoch seconds."""
    commits = _commits(data_dir)
    rows = []
    for run, task in _tasks(data_dir, "legacy_orders").items():
        loads = []
        for n, _, event in task["lines"]:
            m = LOAD.fullmatch(event)
            if m is not None:
                loads.append(m)
            elif ANALYZE.fullmatch(event) is None:
                raise ValueError(f"_ops/scheduler.log line {n}: legacy_orders run={run} writes an unknown event")
        if len(loads) != 1:
            raise ValueError(f"_ops/scheduler.log: legacy_orders run={run} selects orders {len(loads)} times, "
                             f"not once")
        m = loads[0]
        txn = int(m["txn"])
        at, outcome = _transaction(commits, txn, f"legacy_orders run={run}")
        rows.append((run, epoch(m["lo"]), epoch(m["hi"]), task["started_at"], task["end_at"], txn, at, outcome,
                     task["state"]))
    if not rows:
        raise ValueError("_ops/scheduler.log has no legacy_orders task")
    runs = pd.DataFrame(rows, columns=LEGACY_COLUMNS)
    for c in ("lo", "hi", "started_at", "end_at", "txn", "at"):
        runs[c] = runs[c].astype("int64")
    return runs.sort_values(["started_at", "run"], kind="mergesort").reset_index(drop=True)


def cutover_at(data_dir):
    """The commit time (epoch seconds) of the schema_migrations transaction that renamed `orders_new` to `orders`.
    From that commit on, a query on `orders` read the table that the backfill and the hourly loader had filled; before
    it, the legacy table. A rename that was rolled back moved no name."""
    commits = _commits(data_dir)
    found = []
    for run, task in _tasks(data_dir, "schema_migrations").items():
        statements, sent = [], []
        for n, _, event in task["lines"]:
            m = STATEMENT.fullmatch(event)
            if m is not None:
                statements.append(m["sql"])
                continue
            m = SENT.fullmatch(event)
            if m is None:
                raise ValueError(f"_ops/scheduler.log line {n}: schema_migrations run={run} writes an unknown event")
            sent.append(int(m["txn"]))
        if CUTOVER not in statements:
            continue
        if len(sent) != 1:
            raise ValueError(f"_ops/scheduler.log: schema_migrations run={run} sends {len(sent)} transactions, "
                             f"not one")
        at, outcome = _transaction(commits, sent[0], f"schema_migrations run={run}")
        if outcome == "commit":
            found.append(at)
    if len(found) != 1:
        raise ValueError(f"{len(found)} committed schema_migrations transactions rename orders_new to orders, "
                         f"not one")
    return found[0]

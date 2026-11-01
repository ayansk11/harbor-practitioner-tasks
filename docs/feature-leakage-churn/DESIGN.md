# feature-leakage-churn: design and build record (task v3, the operations-log revision)

**What this file is.** The authoring record of the task in `tasks/feature-leakage-churn/` as revised on 2026-10-31
(task v3): the task (section 1), what changed from task v2 and why (2), what the agent sees (3), the mechanisms and the
evidence that pins each (4), why the task is fair (5), the data and the build asserts (6), the AUC calibration (7), the
grader and the independence fix (8), the solutions and attempts (9), timings and caps (10), the local matrix (11), the
hit report (12), where the build departs from the approved design, the two approved changes included (13), the blind
read (14), the Daytona proof (15), the agent trials with their pre-registration and outcome (16), the gate record
against `docs/QUALITY_GATE.md` (17), the limitations and open issues (18) and the earlier versions (19). The approved
design was written before the build and is not part of this repository. Paths are relative to the repository root:
`T/x` = `tasks/feature-leakage-churn/x`, `app/x` = `T/environment/app/x` (the agent's `/app/x`), `auth/x` =
`authoring/feature-leakage-churn/x`.

Last updated: 2026-10-31, 23:03 MST (Mac clock): fixes after a pre-commit check: gate G8 names both hints of the blind
read, G20 and G21 are scored as at this commit, and the canary's time is the run's own. Before that, 2026-10-31, 22:01
MST (Mac clock): fixes after an independent check of the churn commit parts: 30 of the 31 proof trials equal their local
variant (sections 15 and 17), the naive build's second timing (10, 17 and 18), the proof command and where some FACTs
are recorded (15 and 16), and wording in sections 14 and 18. Before that, 20:59 MST: the blind read's result (section
14), the Daytona proof v3 (15) and the three Claude Code trials of task v3 (16) recorded; the gate record (17), the
limitations (18) and the pointers to task v2's shipped evidence (sections 2 and 19) brought up to date; wording fixed
after an independent check of this record. Before that, 19:07 MST: edited after an independent check of the package
(sections 3, 13 and 14). Before that, 18:24 MST (by the file's time): written for task v3 after the build's local checks
(sections 6 to 12), before the blind read was graded, the Daytona proof and any agent trial of task v3.

Versions. Task v3 is this package. Task v2 is the revision built, proven on Daytona and tried with Claude Code on
2026-10-31 just before it; it was never committed or pushed (section 19). The first version is the package of commit
`495c9f5`. The pipeline that the agent fixes is called v3 in the agent's own files (`app/CHANGELOG.md`); here it is
"the shipped pipeline", and run as shipped it is the nop (`original` in the local matrix).

Labels: FACT (a command's output or a file, with the Mac time of the command), INFERENCE (reasoned; the basis named),
RECOMMENDATION, UNVERIFIED. "Mac" = the authoring machine, an Apple M4 with 10 cores and 16 GiB of memory (FACT,
`sysctl`, 2026-10-31 18:07 MST), using `.venv` (Python 3.12.13 with the image's pins: numpy 2.5.4, pandas 3.1.0, pyarrow
26.0.0, scikit-learn 1.9.1, scipy 1.18.1). Task v3 has run in containers only on Daytona (section 15): the Mac has no
container engine. "The build" is the parallel build of 2026-10-31, 16:25 to 17:57 MST: its stages (data, records,
grader, invariants, solutions, attempts and docs) and its integration step, which ran the checks of sections 6 to 12.
Some FACTs cite records kept outside this repository (task v2's job folders, and the build's reviews, checks and scratch
runs); each is named where it is cited.

## 1. The task in one paragraph
A meal-kit subscription company's churn model `churn-hgb-v3` scored offline validation AUC 0.805 but 0.656 in its
first live month (FACT, section 7). Its feature pipeline (`app/churn`) uses only events stamped before each prediction,
so it is right by the old standard, yet the live scoring service computed other values: at each prediction the
warehouse held less, or held it differently, than the later extract shows. The agent must fix `python -m
churn.build_features --data <dir> --out <file.parquet>` so that every kept feature equals what `app/live/features.py`
(the contract) would have computed at each scoring point against the warehouse as it stood then, and must leave out
the one feature that no extract determines (`days_since_last_login`: no history of `last_login_at` is kept). What task
v3 changes is where the loading facts live. `app/docs/WAREHOUSE.md` is a table reference written on 2025-02-14,
before this brand's order-loader migration, with no loader timing; the warehouse's own records, `_ops/scheduler.log`
and `_ops/commits.jsonl`, are the only account of which commit put each order into the table named `orders` and which
table bore that name at each moment. For 8 weeks the new hourly loader filled a second table, `orders_new`, that no
live query read until a recorded rename, and the scheduler marks each nightly legacy run done well after its commit.
The verifier runs the agent's CLI on another brand's extract H and compares the ten kept features with values from the
simulator's true warehouse state (check A), then changes everything the warehouse did not yet hold at two cut times,
the records included, and checks that no earlier prediction moves (check B). The output contract, the tolerances, the
60 s cap, the shared kit, the pins, the 2 vCPU / 4 GiB container, the agent network line and the shared closing
sentence are task v2's.

## 2. What changed from task v2, and why
Task v2's three Claude Code trials (Harbor's `claude-code` agent, `claude-opus-5-5`, web search off, 20 dollars a
trial, run on 2026-10-31 on the proven copy without the agent network line) all passed, in about three to four minutes
each (FACT: each trial's `result.json`, `agent_execution`, and `agent/trajectory.json`, read 2026-10-31 18:00 MST;
cost is Claude Code's `total_cost_usd`):

| Trial | Reward (A, B cut1, B cut2) | Agent time | Tool calls | Cost |
|---|---|---|---|---|
| `feature-leakage-churn__MAANsaN` | 1.0 (1, 1, 1) | 182.5 s | 11 | 0.603 dollars |
| `feature-leakage-churn__PqYpM4P` | 1.0 (1, 1, 1) | 221.2 s | 12 | 0.678 dollars |
| `feature-leakage-churn__aFqLESN` | 1.0 (1, 1, 1) | 181.8 s | 10 | 0.575 dollars |

How the trials got there (FACT: the tool calls of the three trajectories, listed 2026-10-31 18:09 MST, and string
counts in them, 18:00 MST):
- Each trial's first command printed the file list and ran `cat INCIDENT.md CHANGELOG.md docs/WAREHOUSE.md`. Task
  v2's WAREHOUSE.md (107 lines) stated each loader's commit timing, the schedule and a History of the move to the
  hourly loader with this brand's dates: every loading rule was one read away.
- The run table's name `legacy_order_loads` appears 40, 43 and 41 times in the three trajectories (with `.csv`: 14, 10
  and 18); `legacy_backfill` 36, 20 and 37 times; `np.minimum` 4, 20 and 8 times. The trials keyed an order's visibility
  on `_load_job == legacy_backfill` (legacy commit for those rows, `_loaded_at` for the rest) or took the earlier of
  `_loaded_at` and the legacy commit over all orders (the design's reading of the trajectories; attempts `v2_rule` and
  `min_commit` of section 9 are those two rules on task v3's records).
- Each trial compared its output with the logged rows of the two samples (a comparison script in each trajectory;
  the shadow sample's file name appears 18, 18 and 28 times) and wrote its own cut test (`/tmp/cut.py`); a self-made
  check B is consistent with the trial's own rule, so it cannot show that the rule is wrong.

The three trials ship, redacted, in `validation/feature-leakage-churn/second-version/traces/agent-claude-code/`, beside
task v2's proof traces; their agent times, costs and tool calls, the first commands and the string counts above are the
same there (FACT: recounted in the shipped copies, 2026-10-31, by 20:50 MST).

The review of the first version asked for tasks that current agents cannot reliably complete, with deeper
investigation and practitioner judgment. At 3 of 3 in about three to four minutes, task v2 was not that, so task v3
moves the evidence and adds two real migration patterns, and keeps the truth:

| Part | Task v3 |
|---|---|
| truth (`auth/ref_truth.py` reads only the simulator's commit times), seeds 11 and 12, every loader stream of task v2, both cuts | KEPT |
| `T/tests/expected/H_features.parquet` | KEPT byte for byte (sha256 `c888c32554a73aa51bac63a299abf7caec9c2c617fbaa38375f9d020da1180b5`; FACT, `make_expected.py` at 17:37 MST and `cmp` with task v2's file): the regression gate of the build |
| `app/docs/WAREHOUSE.md` | 87 lines (task v2: 107): dated 2025-02-14, "not updated since"; keeps the reading rule, the column and table meanings; adds the name rule and the `_ops/` section; drops the schedule, every scheduled job's commit timing and failure sentence, the run table's rule and the History (the ticket capture's 1 to 30 s, line 73, stays) |
| `app/data/` | seven CSV files (the run table `legacy_order_loads.csv` removed) plus `_ops/scheduler.log` and `_ops/commits.jsonl` |
| `app/logs/` | the January sample kept (365 requests, byte-identical); the 42-request shadow-week sample removed |
| orders | an 8-week dual run before the move (M5) and the legacy runs' end after their commits (M4), both described by the records; of `orders.csv` only the two audit columns changed: it differs from task v2's in `_load_job` (11,494 visible / 11,392 H rows) and `_loaded_at` (64,962 / 56,157 rows) and in no other column; the six other tables are byte-identical (FACT, `cmp` and a column comparison, 2026-10-31 18:02 to 18:03 MST) |
| `instruction.md` | five sentences changed (section 3) |
| `T/tests/grade.py`, `perturb.py`, `invariants.py`, `dataset_io.py`; new `T/tests/ops_io.py` | the records read and rewritten in every check B copy; the independence fix (section 8) |
| solutions | canonical gains `churn/ops.py`; the alt replays the commit log; 4 new attempts, 1 renamed, a probe (section 9) |
| `live/features.py`, the shipped pipeline's feature modules, `kit.py`, `test.sh`, `compare.py`, `convert.py`, both Dockerfiles | KEPT (`churn/extract.py` loads seven tables) |
| `task.toml` | the verifier timeout 278 s -> 279 s and its comment (section 10); nothing else |

Only 193 (visible) and 180 (H) orders change their true visibility: those placed on the move day before the last
dual-run hour, now visible at the rename's commit instead of task v2's first hourly commit (FACT, the generator's
report, `moved_to_cutover`, 17:35 MST). No scoring point lies between the rename's start and that first hourly commit
(asserted, section 6), so no live value changes, and the expected parquet stays the same bytes.

## 3. What the agent sees (`instruction.md`, `environment/app/`)
The instruction (FACT, `T/instruction.md`, diff with task v2's, 2026-10-31 18:01 MST) changed in five places:
- lines 6-8: "The tables are described in `/app/docs/WAREHOUSE.md`, the warehouse's own records of its job runs and
  transactions are in `/app/data/_ops/`, and samples of what the live service computed are in `/app/logs/`." (task
  v2: "The tables and how each one is loaded are described in ...");
- lines 12-13: "(exactly the rows and values committed to it before that moment, in the tables its queries name)";
- lines 19-21: "the same seven CSV files, `_ops/` folder and layout as `/app/data`, ... (their own job runs, failures
  and migrations)" (task v2: eight CSV files, and "their own date for the move to the hourly order loader");
- lines 35-36 (check B): the changed copy's `_ops/` records match it: every record dated before the cut is unchanged,
  and the later records describe the changed extract;
- lines 38-39: "Graded runs set `OMP_NUM_THREADS=1`." (FACT, `T/tests/kit.py:48-49`).
It names no feature to drop and no mechanism.

| Path in `/app` | What it holds |
|---|---|
| `INCIDENT.md` | INC-2077: offline AUC 0.805, live 0.656 on the 3,415 predictions of January 2026; `--l2 50 --max-depth 2` gave 0.813; a hand check of 200 requests; one sample (lines 20-22); the model team's plan (v4 on a table that matches live; a feature that cannot match is dropped) |
| `CHANGELOG.md` | the shipped pipeline (INC-2041): four event-time fixes; `plan` and `days_since_last_login` from the customer record; `extract.py` loads the seven tables (line 18) |
| `live/features.py` | the contract, unchanged: one PostgreSQL query per feature, run at the request's moment; every order query reads `orders` by name (lines 27, 35, 43, 59) |
| `docs/WAREHOUSE.md` | header (lines 3-5): written 2025-02-14 for the warehouse and its nightly loaders as they were then, not updated since, the scheduler's records of every job run and transaction in `_ops/`; the reading rule (12-14), the name rule (15), `_loaded_at` (16), the extract (17-18), formats (19-21); the records (23-34); the seven tables and their writing jobs (36-87), with no timing of the scheduled jobs |
| `churn/` | the shipped pipeline: `extract.py` (seven tables), `windows.py`, `status.py`, `impute.py`, `encoding.py`, `attributes.py`, `build_features.py` (11 features), `train.py` |
| `data/` | this brand's extract at 2026-03-05T00:00:00Z: seven CSV files, 18,700,401 bytes; `_ops/scheduler.log` 3,410,213 bytes (31,146 lines) and `_ops/commits.jsonl` 1,015,126 bytes (10,179 lines) (FACT, `stat` and `wc -l`, 18:00 MST); dropped from the artifact at grading |
| `logs/live_2026-01_sample.jsonl` | 365 requests of January 2026 (about 10%): keys, trigger, the 11 values the service computed, the score |
| `README.md` | layout (lines 10 and 13 name the seven files and `_ops/`) and the two commands |

The doc sentences that graded values rest on (FACT, `app/docs/WAREHOUSE.md`, never cut by the build):
- S1 (line 15): "A query reads each table by the name it has when the query starts."
- S2 (lines 31-32): "`_ops/commits.jsonl` is the commit log of the scheduled jobs: a transaction is committed if and
  only if its outcome is `commit`, and it is committed at its `at`; the scheduler's task states describe tasks, not
  commits."
- S3 (lines 33-34): change data capture (`tickets`), the sign-up service and the scoring service write without the
  scheduler and are not in `_ops/`.
- S4 (line 16, task v2's, still true): "`_loaded_at` is the commit time of the load that wrote the row; in `orders`,
  `_load_job` names that load." A dual-run row's `_loaded_at` is a real commit, into `orders_new`.
- S5 (`instruction.md:13`): "in the tables its queries name".

What the records look like (FACT, literal lines of `app/data/_ops/`, 2026-10-31 18:06 MST): the dual run's first day,
the rename and the first hourly load into `orders` of the visible brand.
```
2025-04-06T02:30:29Z legacy_orders run=2025-04-06 state=running
2025-04-06T03:24:08Z legacy_orders run=2025-04-06 selected orders where ordered_at >= 2025-04-05T00:00:00Z and ordered_at < 2025-04-06T00:00:00Z: 192 rows; sent txn 7001428 to commit into orders
2025-04-06T03:24:18Z legacy_orders run=2025-04-06 analyze orders
2025-04-06T03:35:51Z legacy_orders run=2025-04-06 state=success
2025-04-06T04:12:33Z legacy_backfill run=2025-04-06 copied table orders where ordered_at < 2025-04-06T00:00:00Z: 53275 rows; sent txn 7001430 to commit into orders_new
2025-04-06T05:22:46Z orders_hourly run=2025-04-06T05:00:00Z selected orders where ordered_at >= 2025-04-06T00:00:00Z and ordered_at < 2025-04-06T05:00:00Z: 4 rows; sent txn 7001431 to commit into orders_new
2025-06-01T03:46:23Z dq_checks run=2025-06-01 order day 2025-04-06: orders 202 rows, orders_new 202 rows, rows and values equal
2025-06-01T10:18:50Z schema_migrations run=2025-06-01 statement: ALTER TABLE orders RENAME TO orders_legacy
2025-06-01T10:18:51Z schema_migrations run=2025-06-01 statement: ALTER TABLE orders_new RENAME TO orders
2025-06-01T10:18:52Z schema_migrations run=2025-06-01 sent txn 7002955 to commit
2025-06-01T10:20:11Z orders_hourly run=2025-06-01T10:00:00Z selected orders where ordered_at >= 2025-06-01T09:00:00Z and ordered_at < 2025-06-01T10:00:00Z: 4 rows; sent txn 7002956 to commit into orders
```
and in `commits.jsonl`, for example `{"txn": 7002955, "at": "2025-06-01T10:18:55Z", "outcome": "commit", "table":
null, "rows": null}` (the rename; `table` and `rows` are null exactly for schema statements).

Package files (FACT, `find` and `stat`, 2026-10-31 19:04 MST): 81 files, 27,856,922 bytes: the visible extract
23,125,740 (seven CSV files 18,700,401, `_ops/` 4,425,339), H 2,759,089 (gzip, mtime 0; `_ops/` 463,601), the expected
parquet 1,549,294, the January sample 147,700. Under `T/tests/`: `grade.py`, `perturb.py`, `invariants.py`,
`dataset_io.py` and `ops_io.py` (generated from `auth/extract_io.py` and `auth/ops_log.py`; `diff` shows the docstring
and the import line only), `compare.py`, `convert.py`, the shared kit (`kit.py`, `test.sh`, synced unchanged from
`base/verifier_kit/`), `SHA256SUMS` (10 files), `hidden/H/` (seven `.csv.gz` and `_ops/*.gz`) and
`expected/H_features.parquet`. Under `T/solution/`: `solve.sh`, `canonical/churn/` (seven modules), `alt/churn/`
(one module), `attempts/` (`_common.py`, 22 attempts and one probe).

## 4. The mechanisms and the evidence that pins each
Cells: graded value cells that the wrong rule moves, visible / H (FACT, the generator's report, `mechanisms.report`,
17:35 MST; equal in every field to the run of `gen_data.py --check` at 18:07 MST apart from timings; the same counts as
the hit report, section 12). C = the move day (00:00 UTC of the day the last legacy range ends); D0 = C - 56 days.

| # | Mechanism | Evidence in every extract | Natural wrong rule (attempt) | Cells, visible / H | Kill |
|---|---|---|---|---|---|
| M1 | a row is visible only from its commit: hourly orders after the rename, tickets, status partitions, labels, plan changes | `_loaded_at` (S4), equal to its job's commit `at` in `commits.jsonl` (asserted); the reading rule (WAREHOUSE.md:12-14) | the shipped pipeline's event time (`original`); windows on load time; the most recently loaded snapshot; the shipped status rule; the label proxy | orders by event time 179,502 / 179,370; window_on_loaded_at 47,216 / 47,173; status_latest_loaded 194 / 113; status_event_date 483 / 484; labels_matured 57,854 / 57,833 | A (`original`, the whole shipped pipeline: A, B1, B2) |
| M2 | an order placed before D0 carries the backfill's `_loaded_at` (a commit into `orders_new`), but it was visible from the commit of the committed legacy range holding it | each legacy run's LOAD line (a half-open range of `ordered_at`, its rows and txn, target `orders`) and its outcome; the backfill's COPY line (source `orders`, `ordered_at` below D0, 53,275 / 44,585 rows); S1 and the rename | trust `_loaded_at` (`loaded_at_everywhere`); the order's own time (`backfill_event_time`) | 67,430 / 53,362; 82,006 / 68,098 | A; A, B1 |
| M3 | failed, late and catch-up legacy runs | rollbacks (25 / 24 legacy runs, an outage of 11 / 10 nights among them), commits after 06:00 (18 / 15), one catch-up range after the outage | the nightly schedule (`legacy_schedule`); a rollback taken as a commit (`rollback_as_commit`) | 1,633 / 1,522; 1,541 / 1,381 | A, B1 |
| M4 | NEW: each legacy run analyzes the table after its commit and is marked done (`state=success`) 5 to 40 minutes later, 3 to 5 hours on 47 / 48 nights | the commit's `at` in `commits.jsonl` against the task's state lines; S2 | the task's end as the commit (`scheduler_end`); its start (`scheduler_start`) | 372 / 296; 108 / 156 | A |
| M5 | NEW: the dual run. From D0 `orders_hourly` commits into `orders_new` (1,349 / 1,353 tasks, 34 / 24 rolled back) while `legacy_orders` keeps committing into `orders` up to C; on C `dq_checks` writes one "rows and values equal" line per order day D0 to C - 1 (56 lines), then one transaction renames `orders` to `orders_legacy` and `orders_new` to `orders`, 78 s / 83 s before the first hourly commit into `orders`; `orders_legacy` is dropped 7 days later | the hourly LOAD lines naming `orders_new`; legacy ranges up to C over rows that `_load_job` calls `orders_hourly`; the parity lines; the two RENAME statements and their commit; S1, S5, and `live/features.py` reading `orders` by name | the task v2 trials' rules: legacy commits for `legacy_backfill` rows only (`v2_rule`), or the earlier of `_loaded_at` and the legacy commit (`min_commit`) | 356 / 492 (89 / 123 rows); 356 / 492 | A only: cut1 (2024-11-27) is before both D0s, cut2 (2025-11-14) after both moves |
| M7 | `plan` from `plan_changes` visible at t (greatest `changed_at`; none: the sign-up plan) | `plan_changes` and its `_loaded_at`; WAREHOUSE.md:43-54 | the current plan (`current_plan`); plan by `changed_at` (`plan_changed_at`) | 19,627 / 19,228; 584 / 518 | A, B2 |
| M8 | leave out `days_since_last_login` (no history of `last_login_at`) | WAREHOUSE.md:43-46; the instruction's drop criterion | the shipped clip (`clip_last_login`); exact where known (`last_login_where_known`) | non-null values 1,953 / 1,898; 1,246 / 1,212 | A, B1, B2; A |

Also counted: orders at or above the last legacy watermark by the hourly schedule (`hourly_schedule`) 12 / 12 cells,
killed by check A alone (approved change (a), section 13). M6 (a billing export-file stamp on status partitions) was
designed and cut before the build, with a third cut; the numbering keeps the design's. The shipped pipeline is right
on `tickets_30d`, `tenure_days` and `app_minutes_7d` (0 cells on both extracts; FACT, the same report,
`samples.nop_mismatched_cells_*`).

## 5. Why the task is fair
- One truth, three derivations. Every graded value is the live service's value from the simulator's true state
  (`auth/ref_truth.py`; it never reads an extract's audit columns or records). The extract-only canonical equals it
  with 0 mismatched cells and bit-identical floats on both extracts (FACT, `make_expected.py`, 17:37 MST, and its
  `--check`, 18:08 MST), and the alt, a replay of the commit log by another method, equals the canonical on both
  (section 9). So every graded value is derivable from an extract.
- Each graded rule rests on a stated sentence and a record. Which table bore the name `orders` at t: S1, S5 and the
  RENAME statements with their commit. Which commit made an order visible: S2 and the LOAD lines joined to
  `commits.jsonl` on the txn. That the legacy table and `orders_new` held the same rows and values: the parity lines.
  That the records cover every scheduled writer: S3 (approved change (d), section 13). The doc's header says it
  predates the migration and points to `_ops/` for every later change.
- The build asserts (section 6) close the gaps, overlaps and ties through which two careful readings could differ on a
  graded cell: the committed legacy ranges partition [2024-01-01, C) (so each order before C has exactly one legacy
  commit); the backfill copies exactly the orders before D0; the parity lines cover each order day D0 to C - 1 once;
  every order's `_loaded_at` is the commit of the committed task whose range holds it; the records' rule equals every
  order's true visibility; no scoring point lies between the rename's start and the first hourly commit into `orders`,
  or strictly between any transaction's `sent txn` line and its commit, and no commit falls on a scoring second; a
  transaction commits if and only if its task succeeded. Whether any other careful reading differs is what the blind
  read tests (section 14). INFERENCE (from these asserts): "the sent line's time as the commit" and "the next N order
  ids by a range's row count" give the graded values on these extracts too, so they would score 1 and are not attempts.
- Task v2's rules for the other tables and features are unchanged and stay stated (WAREHOUSE.md:36-87); every
  mechanism of section 4 that check A grades moves at least 100 cells on both extracts, hourly_schedule excepted
  (section 12), so each shows in the agent's own data.
- Not a trap: the dual run moves no live value, and every commit the agent needs is an explicit record. No difficulty is
  added only to lower the pass rate (G29), and nothing is added because of a trial (section 16).
- What the agent cannot check against a log: the January sample is after both moves, so it is silent on how orders
  before C became visible (section 18); the rules for M2 to M5 come from the doc and the records alone.

## 6. Data and build asserts
FACT (`auth/gen_data.py`, run twice in place at 17:35 and 17:36 MST by the build's integration step, exit 0, the first
run 20.7 s by `time`, the reports' own `seconds_total` 20.1 and 19.8 s; all 19 written files byte-identical between the
runs, and the printed reports equal apart from their `seconds_*` fields; `gen_data.py --check` again at 18:07 MST,
exit 0, 26.0 s, report equal to the 17:35 run apart from timings).
Its printed report is the source of this section's numbers. The simulator is task v2's (each part on its own numpy
PCG64 stream, `gen_data.py` docstring): 3,000 customers per brand signing up between 2024-01-01 and 2025-10-31;
weekly boxes charged at 05:30 on the billing weekday; add-ons; support tickets; status snapshots on the sign-up day, on
every change and on the first of each month; batch scoring at 06:00 every 14 days, and some tickets scored at their
`opened_at`; app readings missing for some requests; plan changes, with 35% of the churners above basic downgrading 5 to
40 days before cancelling; logins that fall with disengagement. The loaders (`gen_data.L`): the nightly legacy job (3%
failed nights, one outage of 9 to 11 nights, 3% committing late), hourly commits (2% failed), exports on D+1 (2% late,
2% out of order, two month-start partitions 5 to 9 days late), the label job (3% failed nights), the CRM sync on Sundays
(1 in 15 late), ticket capture 1 to 30 s; new in task v3, `analyze_long_p` 0.10. Three new streams time the records
only: [seed, 107] the legacy runs' send, analyze and end; [seed, 108] the migration (backfill, dual run, parity, rename,
drop); [seed, 109] the record times of the runs task v2 already had. Each is drawn per simulated run in a fixed order,
so every earlier stream and every row's true commit time stay as in task v2 (FACT: the build's data stage, 2026-10-31
17:00 to 17:12 MST: every world frame equal to task v2's generator's, apart from the true visibility of the 193 / 180
orders of section 2, and `ref_truth.compute` bit for bit equal on both brands).

| Table | visible (seed 11) | H, brand "North" (seed 12) |
|---|---|---|
| customers (ids) | 3,000 (100001-103000) | 3,000 (200001-203000) |
| plan_changes | 2,339 | 2,266 |
| scoring_points (batch / ticket) | 57,909 (52,379 / 5,530) | 57,896 (52,432 / 5,464) |
| orders (`legacy_backfill` / `orders_hourly`) | 130,003 (53,275 / 76,728) | 132,227 (44,585 / 87,642) |
| tickets | 14,905 | 14,631 |
| status_snapshots | 40,316 | 40,051 |
| labels | 54,800 | 54,825 |
| records: tasks; `scheduler.log` lines; transactions (txn ids); parity lines | 10,208; 31,146; 10,179 (7000001-7010179); 56 | 11,289; 34,350; 11,267 (9000001-9011267); 56 |
| tasks by job: legacy_orders, legacy_backfill, orders_hourly, dq_checks, schema_migrations, label_job, billing_export, crm_sync | 517, 1, 7,987, 1, 2, 794, 793, 113 | 470, 1, 9,115, 1, 2, 794, 793, 113 |

| Load history | visible | H |
|---|---|---|
| D0; its legacy commit | 2025-04-06; 03:24:12Z | 2025-02-18 (4 days after the doc date); 03:16:08Z |
| backfill into `orders_new` (commit; rows) | 2025-04-06T04:12:42Z; 53,275 | 2025-02-18T04:02:00Z; 44,585 |
| dual run (hourly tops; tasks; rolled back) | 2025-04-06T05:00:00Z to 2025-06-01T09:00:00Z; 1,349; 34 | 2025-02-18T05:00:00Z to 2025-04-15T13:00:00Z; 1,353; 24 |
| move day C (the last legacy range ends; that run committed) | 2025-06-01 | 2025-04-15 |
| parity check (`dq_checks`, 56 lines) | 03:46:22Z to 03:47:19Z | 03:34:32Z to 03:35:29Z |
| rename (its commit); first hourly commit into `orders` | 2025-06-01T10:18:55Z; 10:20:13Z | 2025-04-15T14:19:31Z; 14:20:54Z |
| drop of `orders_legacy` (commit) | 2025-06-08T03:39:27Z | 2025-04-22T03:07:30Z |
| orders visible at the rename (placed on C before the last dual-run top) | 193 | 180 |
| legacy outage | 2024-11-08, 11 nights | 2024-11-20, 10 nights |
| legacy runs rolled back (outside the outage); committed after 06:00; analyze of 3 to 5 h | 25 (14); 18; 47 | 24 (14); 15; 48 |
| hourly runs into `orders` to the extract (rolled back) | 6,638 (143) | 7,762 (154) |
| all rollbacks in the records | 202 | 202 |
| scoring points before C; during the dual run | 26,407 (45.6%); 5,600 | 21,721 (37.5%); 5,371 |
| export partitions late in order; out of order | 12; 17 | 11; 10 |
| month-start partitions landing late | 2026-01-01 (2026-01-09T23:02:02Z), 2026-02-01 (2026-02-09T04:12:31Z) | 2025-01-01 (2025-01-08T00:17:46Z), 2024-12-01 (2024-12-09T06:50:36Z) |
| failed label nights; CRM syncs (late) | 28; 113 (10) | 21; 113 (10) |

Build asserts (FACT, `auth/gen_data.py`: `check_world` lines 908-1006, `check_ops` 1009-1170, `check_round_trip`
1173-1194, and `auth/mechanisms.py` `assert_targets` 278-296; any failure stops before a file is written; all held at
17:35, 17:36 and 18:07 MST), on both brands:
1. D0 = C - 56 days, after the doc date 2025-02-14; D0's legacy run committed before 06:00; D0 at least 10 days
   from the legacy outage (lines 1033-1038).
2. One legacy task per run date from 2024-01-02 to C; each range starts where the last committed range ended; C's
   run committed (1040-1044).
3. The committed legacy ranges partition [2024-01-01, C), and their rows are every order placed before C (1046-1048).
4. The backfill starts after D0's legacy run ended and copies exactly the orders placed before D0 into `orders_new`,
   committed; its rows equal the committed legacy rows below D0 (1050-1054).
5. The hourly chain: every dual-run task (into `orders_new`) comes first, from D0, ending before the rename starts;
   the hourly tasks into `orders` are task v2's hourly runs (top, commit, outcome), and the first commit is task
   v2's (1056-1072).
6. The move day's order: C's legacy run ends before `dq_checks` starts, `dq_checks` ends before the rename starts,
   the rename commits before the first hourly task into `orders` starts, and the drop follows (1074-1080).
7. Parity: each order day D0 to C - 1 once, both counts the orders of that day; committed dual-run ranges before the
   parity check cover [D0, C) (1082-1091).
8. `_load_job` is `legacy_backfill` iff `ordered_at` < D0, with the backfill's commit; every other order's
   `_loaded_at` is the commit of the committed hourly task whose range holds it (1093-1098).
9. The records' rule (an order before C at the commit of its committed legacy range; a later order at the later of
   `_loaded_at` and the rename's commit) equals every order's true visibility; no scoring point lies between the
   rename's start and the first hourly commit into `orders` (1100-1105).
10. No scoring point strictly between a transaction's send and its commit; no commit on a scoring second, in the
    records (1107-1111) and in every table (936-941).
11. A transaction commits iff its task succeeded; a failed label_job sends none (1113-1116).
12. Labels, plan changes, status partitions (one export per partition) and every customer record a sync wrote carry
    the commit of their job's task (1118-1131).
13. Unique (job, run) and txn; txn rising in (sent_at, job, run) order from the brand's base; tasks in start order;
    every record before the extract moment; each task's times in the order start, send, commit, analyze, end; every
    range's lo below its hi (1133-1150); render and parse are exact inverses, byte for byte, every count is what the
    extract's tables give, and the records validate (1173-1194).
14. The floors: the derived checks move 0 cells; every check-A kill of section 4 other than the two login attempts moves
    at least 100 cells on both extracts and `hourly_schedule` more than 0 (`mechanisms.py:278-296`, which asserts the
    login attempts' wrong rows and non-null values instead; `hit_report.py` checks them at 100 cells, section 12). The
    design's target of 300 cells for M4 and M5 is reported, not asserted: met by `v2_rule` and `min_commit` (356 / 492)
    and by `scheduler_end` on the visible extract (372), not by `scheduler_end` on H (296).
Task v2's asserts are kept (lines 914-977): no order at exactly t - 7 or t - 30 days of a point of its customer and no
ticket at t - 30 days; the ticket capture lag never decides a value; the plan chains hold and the plan rule equals the
true customer record; the audit columns of tickets, snapshots and labels are their true commits. Task v2's asserts on
the run table and on the shadow sample are gone with them.

Determinism and the regression gate (FACT, the build's integration step, 17:35 to 17:38 MST, and the checks of 18:07
to 18:08 MST): regeneration byte-identical; `make_expected.py`: canonical against `ref_truth` 0 mismatched cells on
the ten kept features, visible 57,909 rows and H 57,896, no duplicate, missing or extra row, the four float features
bit-identical on every row; the expected parquet the same bytes as task v2's; `make_expected.py --check` (17:38 and
18:08 MST): both extracts on disk equal the generator's output, the parquet and `SHA256SUMS` current.

## 7. AUC calibration
FACT (`auth/calibrate_auc.py` without `--write`, 2026-10-31 17:50 MST; equal to `auth/auc_calibration.json` and to
INCIDENT.md's figures): AUC_OFF 0.805 (the shipped `train.py` model on the shipped pipeline's features of the visible
extract: 36,490 labelled predictions before 2025-09-01, validated on 11,107, churn rate 0.0723); AUC_LIVE 0.656 (the
same model on the live values of the 3,415 predictions of January 2026, churn rate 0.0755); gap 0.149; AUC_TRUE_context
0.768 (the model class on the ten kept live features). Unchanged from task v2: the order rows' values and times and the
six other tables are the same (section 2), and so is the truth. `auth/v3_model.py` runs the shipped pipeline for this
calibration; `auth/samples.py` draws the January sample (stream [seed, 77]) and asserts that its logged values equal
`ref_truth` cell for cell (the 365 lines are byte-identical to task v2's file).

## 8. The grader and the independence fix
`T/tests/grade.py` (separate verifier, root, cwd `/tests`; the kit's rules for graders, `base/verifier_kit/README.md`):
1. Verifies `SHA256SUMS` (lines 57-63), then copies `/app` into the root-only scratch folder before any agent code
   runs (`snapshot_app`, lines 88-96).
2. Check A: H, unzipped into the scratch folder with its `_ops/` folder (lines 66-85), is staged for uid 1001; the CLI
   runs once (cap 60 s, line 44); `convert.py` turns the output into JSON as uid 1001 (cap 20 s), which root reads and
   checks: one row per scoring point, the ten kept features equal `expected/H_features.parquet` (the four integer
   features exactly, the other numbers within 1e-6 + 1e-9 x |expected|, `status` and `plan` exactly, nulls alike), a
   `days_since_last_login` column, if present, all null (lines 315-325).
3. Check B per cut (lines 326-349): `perturb.perturb(H, cut, seed)`, then `invariants.check(H, copy, cut)` (a problem
   fails that cut closed and is logged as a grader defect), then the CLI on the copy: every row with `as_of <= cut`
   must equal the agent's own H output (same tolerances), one row per scoring point of the copy, the left-out column
   null. The cuts (line 51): cut1 = 2024-11-27T06:00:00Z (seed 101), the 06:00 batch run 8 nights into H's 10-night
   legacy outage, before H's dual run; cut2 = 2025-11-14T08:13:16Z (seed 202), a ticket point after H's move, in an
   hour whose hourly run rolled back, with plan changes waiting for that week's late sync and the 2025-11-13 export
   partition not landed (the generator's `cut_candidates_H` still lists both, 17:35 MST). Neither cut falls on a
   commit, send or start second of H, and both copies have 3,060 customers (FACT, the build's integration step,
   17:41 MST).
4. Reward 1 only if A, B cut1 and B cut2 all pass (line 350). `reward.json` carries `check_A`, `A_mismatched_cells`,
   `A_mismatch_<feature>`, `check_B_<cut>`, `B_<cut>_changed_cells`, `B_<cut>_mismatch_<feature>`,
   `B_<cut>_invariant_problems`, `<run>_days_since_last_login_nonnull`, row counts, `seconds_<run>`,
   `seconds_convert_<run>`, `seconds_grade_total`, `net_private_<run>`, the sweep metrics below and the container's
   resources where readable.

What a check B copy changes (`T/tests/perturb.py` docstring, lines 1-50): everything the warehouse did not yet hold at
the cut, in every table, with the loaders' rules kept for every changed or added row: legacy runs that sent at or
after the cut (except the D0 and C runs) get 30% of outcomes flipped and their commits re-timed after the cut; orders
not yet visible get new amounts, 25% are dropped where no task that sent before the cut selected them, and orders are
added where none had; tickets, unlanded partitions, labels and plan changes are changed with their jobs' commits;
half of the last logins are rewritten by a later sync; 60 customers sign up after the cut; later scoring points
change. The records are edited per record time and their counts recomputed from the copy's own tables
(`ops_io.recount`): every record dated before the cut is unchanged, a task that sent its transaction before the cut
is unchanged in every field and keeps the rows it selected, copied or wrote, and the later records describe the copy.
Never changed: every row visible before the cut, the move, `signup_at`, districts and sign-up plans.
`T/tests/invariants.py` (docstring, lines 1-44) derives every rule again from WAREHOUSE.md and the records, importing
nothing from `perturb.py`, and checks layout, the records' rules, the loaders, the plan chains, the move and that
nothing visible before the cut changed.

Robustness of the copies (FACT, the build's grader and invariants stages and its integration step, 2026-10-31 17:07 to
17:41 MST, on extracts byte-identical to the shipped ones): `auth/cut_check.py --random 20` (17:39 MST): 35 cuts (the
2 graded; 13 targeted: inside three legacy runs (before D0, in the dual run, on a rolled-back night), at D0 and inside
its legacy run, inside the backfill, at C and inside its legacy run, inside the parity check, just after the rename,
after a dual-run commit, after a rolled-back hourly run, inside the drop; 20 seeded random cuts) in 88 s, all clean:
invariant problems 0, and the canonical and the alt keep every row at or before each cut and agree on every row; the
graded copies' digests `2e10c9ffcd33` and `024668ccd414`, the same in three separate processes; 17 hand-made
corruptions of a copy reported at each graded cut; the two graded copies byte-identical under two hash seeds.

The independence fix. Task v2's grader was not independent between its three runs: one package copy, handed to uid
1001, served all three; the H run's staged input, output and converter folders stayed in place through the cut runs;
and their names told a run which one it was (FACT, an independent review of task v2 on 2026-10-31, 02:09 MST: a
cache written into the package folder by the H run, or a read of the H run's output, turned `hourly_schedule`'s
B cut2 from 0 to 1). Check A, the first run, stayed independent and every wrong rule tried failed it, so no reward
changed; but task v2's record said that hidden inputs could not change the score, which was false for check B. Task
v3 fixes it in `grade.py` only (the kit stays synced unchanged):
- before any agent code: `/app` is copied into the root-only `kit.SCRATCH` and `kit.APP_DIR` points at the copy, so
  every package copy comes from `/app` as handed in (lines 88-96; `kit.prepare_submission` reads `kit.APP_DIR` when
  called, `kit.py:458-471`);
- before each run (`sweep`, lines 193-222): every uid-1001 process is killed; the whole file system is walked from
  `/` without following links, not entering `/proc`, `/sys`, `/dev` (but walking `/dev/shm` and `/dev/mqueue`) or the
  scratch folder, and every entry owned by uid 1001 is removed, not entered (lines 99-138); every SysV shared-memory
  segment, semaphore set and message queue whose owner or creator is uid 1001 is removed (`ipcrm`, else the
  `IPC_RMID` call through ctypes; lines 141-190); then the walk runs again and counts what is left;
- a run after a sweep that left anything of uid 1001 is not graded and scores 0 (lines 267-270);
- each run gets a fresh package copy and the same staging names, `sub`, `in`, `out`, `conv` (lines 271-286), so no
  path tells a run which one it is; the H output stays in root's memory;
- metrics `swept_runner_paths_<run>`, `residual_runner_paths_<run>` (must be 0), `seconds_sweep_<run>`,
  `sweep_errors_<run>`.
In `KIT_LOCAL` mode (the Mac, no uid split) the sweep clears the kit's work folder's top level instead (lines 199-205):
the local matrix shows 0, 5 and 5 entries swept before the H, cut1 and cut2 runs and 0 left on every three-run variant
(section 11). The real-mode walk is proved only on Daytona, and run v3 proved it: no sweep left an entry of uid 1001
(section 15).

The probe `cache_in_work` (`T/solution/attempts/cache_in_work.py`): the canonical, which on an extract with exactly
3,000 customers (H, or this brand's; every check B copy has 3,060) also writes its output to `/work`, `/tmp`,
`/dev/shm`, `$HOME`, `/home/runner` and its own package folder, and on any other extract replays a cache found there on
matching keys, else writes `orders_7d + 1`. Locally it scores 1 by construction (the `/tmp` cache survives the local
sweep; FACT, `local_check.py cache_in_work`, 17:45 MST: A 1, B1 1, B2 1, swept 0 / 5 / 5, residual 0; the check removes
`/tmp/churn_cache_in_work.parquet` before and after). Expected on Daytona: check A 1, both B checks 0 (no cache left, so
`orders_7d` is off by one on every kept row), reward 0, swept paths above 0 before each cut, residual 0. Run v3 gave
exactly that (section 15).

Grading needs no network, and agent runs get the kit's private loopback-only network where the kernel allows it
(`net_private_<run>`).

## 9. Solutions and attempts
Canonical (`T/solution/canonical/churn/`, seven modules copied over the shipped pipeline, 446 lines; FACT `wc -l`,
18:07 MST): `ops.py` (new, 160 lines) parses `scheduler.log` with regular expressions (every line must match the
`<time> <job> run=<run> <event>` envelope) and `commits.jsonl` with `json`, joined on the txn: `legacy_runs` (one row
per legacy task: range, times, txn, commit `at`, outcome, state) and `cutover_at` (the `at` of the one committed
transaction holding `ALTER TABLE orders_new RENAME TO orders`; a rolled-back rename is skipped).
`visibility.order_visible_at` (`visibility.py:41-49`): an order placed before the end of the last committed legacy
range is visible at the commit of the committed range holding it (a searchsorted on the ranges' ends); a later order
at the later of its `_loaded_at` and the rename's commit. `build_features.py` changes its imports and its orders line
only. The rest is task v2's: exact window pairs over (customer, `ordered_at`) filtered on visibility; one "greatest key
among rows that arrived before t" helper for `status` (key `snapshot_date`) and `plan` (key `changed_at`, the sign-up
plan as fallback); the shipped forward fill for `app_minutes_7d`; the district encoding on the labels' `_loaded_at`;
no last-login column.

Alt (`SOLUTION=alt`, `T/solution/alt/churn/build_features.py`, 350 lines, the standard library plus pyarrow for the
write): `commits.jsonl` is joined to each transaction's sending line, and every committed transaction is replayed at
its `at` in (at, txn) order into tables and a name map (a load adds the extract's orders in its range to the table it
names, a copy adds its source's rows below its bound, a rename moves a name, a drop removes a table); each point reads
the table named `orders`; no order's `_loaded_at` or `_load_job` is read, and the run stops unless the final `orders`
table equals the extract's orders. Other tables as task v2's alt (every row commits at its `_loaded_at`; a point
before any commit of the same second; per-customer state with `bisect` windows). Output with int32 counts, naive
microsecond `as_of`, rows newest first, alphabetical columns, an extra `trigger` column and `days_since_last_login`
present and all null. FACT (the build's solutions stage, 17:01 MST, on extracts byte-identical to the shipped ones):
the alt equals the canonical with 0 mismatched cells and bit-identical floats on both brands, and each solution's
output sha256 was the same across two runs.

The attempts (`T/solution/attempts/`; each is the canonical with one rule swapped unless noted; the named kill is the
check `local_check.py` requires to fail; A cells on H from the matrix of section 11):

| Attempt | The realistic mistake | Named kill | A cells (H) |
|---|---|---|---|
| (nop) `original` | the shipped pipeline: event time, current plan, clipped last login, label proxy | A, B1, B2 | 256,915 |
| `v2_rule` (new) | task v2's trials' key: the legacy commit for `legacy_backfill` rows only, `_loaded_at` for the rest, the rename not read | A | 492 |
| `min_commit` (new) | the earlier of `_loaded_at` and the legacy commit, over all orders | A | 492 |
| `scheduler_end` (new) | a legacy range visible at its task's `state=success` line, not at its commit | A | 296 |
| `scheduler_start` (new) | a legacy range visible at its task's `state=running` line | A | 156 |
| `rollback_as_commit` (task v2's `legacy_ignore_status`) | the outcome in `commits.jsonl` not read: a rolled-back range taken as committed | A, B1 | 1,381 |
| `loaded_at_everywhere` | `_loaded_at` trusted in every table, the orders included | A | 53,362 |
| `backfill_event_time` | an order below the last legacy watermark visible at its `ordered_at` | A, B1 | 68,098 |
| `legacy_schedule` | an order below the watermark visible at 02:30 the next night | A, B1 | 1,522 |
| `hourly_schedule` | a later order visible at the first :20 after the next top of the hour | A (12 cells, approved change (a)) | 12 |
| `window_on_loaded_at` | order windows on the visible time instead of `ordered_at` | A | 47,173 |
| `status_latest_loaded` | the most recently loaded snapshot | A | 113 |
| `status_event_date` | the shipped status rule, `snapshot_date < date(t)` | A | 484 |
| `current_plan` | the plan on the customer record now | A, B2 | 19,228 |
| `plan_changed_at` | the plan from changes with `changed_at < t` | A, B2 | 518 |
| `drop_plan` | `plan` left out too | A (output rejected) | - |
| `clip_last_login` | `days_since_last_login` kept with the shipped clip | A, B1, B2 | 0 (1,898 non-null) |
| `last_login_where_known` | exact where the extract determines it, null elsewhere | A | 0 (1,212 non-null) |
| `labels_matured` | the shipped label proxy `as_of + 30 days < t` | A | 57,833 |
| `log_lookup` (on the shipped pipeline) | the logged values copied into the rows they match | A | 256,915 |
| `cache_visible` | the visible extract's right table returned for any input | A | 0 (57,896 rows missing) |
| `zero_features` | every kept feature a constant | A | 422,145 |
| `tune_model` (on the shipped pipeline) | stronger regularisation, features untouched | A | 256,915 |
| `cache_in_work` (probe) | state kept from the H run (section 8) | B1, B2 on Daytona; scores 1 locally by construction | 0 |

Why check B passes some wrong attempts: B compares an output with the same program's output under a changed future; a
wrong rule that uses only what was visible before t (the trusted `_loaded_at`, the dual-run commits, a task's end line,
windows on load time, a constant) is consistent with itself, so only A sees it. That is the designed split. Not
attempts, since they would score 1 on these extracts (section 5): the next N order ids by a range's row count; the sent
line's time as the commit.

## 10. Timings and caps (Mac)
FACT (`auth/timing.py`, 2026-10-31 17:49 MST, load average 3.14 before and 2.75 after; a fresh `python -m
churn.build_features` process per run, with the environment the grader gives agent code, `OMP_NUM_THREADS=1`):

| Program | H, 5 runs (s) | median / max | visible, 5 runs (s) | median / max |
|---|---|---|---|---|
| canonical | 0.53, 0.49, 0.46, 0.47, 0.47 | 0.47 / 0.53 | 0.48, 0.46, 0.47, 0.46, 0.46 | 0.46 / 0.48 |
| alt (commit replay) | 0.91, 0.91, 0.90, 0.91, 0.91 | 0.91 / 0.91 | 0.90, 0.90, 0.90, 0.90, 0.93 | 0.90 / 0.93 |
| original (the shipped pipeline) | 0.40, 0.40, 0.40, 0.40, 0.40 | 0.40 / 0.40 | 0.40, 0.40, 0.41, 0.41, 0.41 | 0.41 / 0.41 |
| naive valid per-row approach (order visibility from `_ops/`) | 1.3 s per 600 predictions of H, 0 mismatched cells against `tests/expected` | about 123 s for all 57,896 (linear extrapolation); about 159 s in a second run of the script at 18:17 MST, in the independent check of section 13, item 10 (recorded outside this repository) | | |

**Per-run cap: 60 s** (`T/tests/grade.py:44`, the instruction's sentence; task v2's). FACT (task v2's Daytona proof
rev1, the 26 trials' `reward.json`, read 2026-10-31 18:08 MST): runs took 0.373 to 1.574 s, the canonical 0.573 to
0.679 s and the alt 1.431 to 1.574 s, against task v2's Mac medians of 0.43 s and 0.85 s (task v2's `timing.py`,
2026-10-31 00:54 MST), a ratio of about 1.3 to 1.9. INFERENCE: at that ratio task v3's alt takes about 1.2 to 1.7 s on
Daytona, about 1/35 of the cap; run v3 measured more, 1.83 to 1.99 s (2.0 to 2.2 times the Mac's H median, about 1/30 of
the cap; section 15). The cap still bites: a naive per-row build needs about 123 to 159 s on the Mac (table above).

**Verifier timeout: 279 s** = (3 runs x 60 s + 5.59 s) x 1.5 = 278.4, rounded up (`T/task.toml:23-28`). The grading time
outside the three runs (process time minus `seconds_H`, `seconds_cut1`, `seconds_cut2`; FACT, `local_check.py --json`,
computed per variant at 17:59 MST): 5.22 to 5.41 s in the checkpoint run of 17:38 to 17:39 MST, 4.98 to 5.38 s in the
full matrix of 17:41 to 17:44 MST (load average 2.8 to 3.7, as `task.toml` records), 5.59 s for the probe at 17:45 MST,
the worst measured when the timeout was set. Later runs of the matrix beside other checks measured more (FACT, computed
the same way): up to 7.52 s at 18:06 to 18:10 MST (the independent check of section 13, item 10), 6.35 s at 18:55 to
18:58 MST and 5.73 s at 19:04 to 19:07 MST (section 14); with 7.52 s the formula gives 281.3 s. 279 s is kept: with
every run at its 60 s cap and all three conversions at their 20 s cap, 180 + 60 + 7.52 = 247.5 s, under 279 s. Grading
returns right after a failed or rejected H run. UNVERIFIED: the time `test.sh` spends before `grade.py` and the
real-mode sweeps' walks of the file system (`seconds_sweep_<run>`) do not run on the Mac; the margin, about 91 s
(279 - 180 - 7.52), must cover them. Task v2's Harbor verifier phases took 18.1 to 55.6 s on Daytona (FACT, rev1
`result.json`, read 18:08 MST). Measured in run v3 (section 15): sweeps of 0.638 to 1.193 s, and each Harbor verifier
phase minus its three runs 11.9 to 50.3 s, inside that margin; task v3's verifier phases took 12.6 to 52.5 s.

**The Daytona proof must read the alt's `seconds_H`, `seconds_cut1` and `seconds_cut2` (if any exceeds 20 s, cap / 3,
raise `RUN_CAP_SEC`, the instruction's sentence and `timeout_sec` together) and every `seconds_sweep_<run>`.** Read in
run v3: the alt's three runs took 1.83 to 1.99 s and each sweep 0.638 to 1.193 s, so nothing was raised (section 15).

## 11. Local matrix (FACT)
Command, from the repository root: `.venv/bin/python -I -B authoring/feature-leakage-churn/local_check.py --json
<file>` (the build's integration step, 2026-10-31 17:41 to 17:44 MST, 166 s; output "ALL AS EXPECTED", 25 variants;
the probe run by name at 17:45 MST, since its real result needs Daytona). Each row: a fresh copy of
`environment/app`, `solution/solve.sh` with that `SOLUTION` (none for `original`, the nop), the artifact excludes,
`tests/grade.py` in `KIT_LOCAL=1` mode with the task's `tests/`. A, B1, B2: the checks (1 pass, 0 fail, "-" not run
because the H output was rejected). A cells: mismatched value cells of the ten kept features on H. B cells: cells of
rows at or before the cut that moved. Login: non-null `days_since_last_login` values on H. Runs: the three CLI runs
(s). Grade: the whole grading process (s). On all 24 three-run variants: invariant problems 0 / 0, swept 0 / 5 / 5,
residual 0.

| Variant | Exp. | Got | Named kill | A | B1 | B2 | A cells | B cells (cut1 / cut2) | Login | Runs (s) | Grade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| canonical | 1 | 1 | - | 1 | 1 | 1 | 0 | 0 / 0 | 0 | 0.54 / 0.50 / 0.55 | 6.9 |
| alt | 1 | 1 | - | 1 | 1 | 1 | 0 | 0 / 0 | 0 | 0.94 / 1.03 / 0.96 | 8.3 |
| original (nop) | 0 | 0 | A, B1, B2 | 0 | 0 | 0 | 256,915 | 4,005 / 8,933 | 1,898 | 0.49 / 0.50 / 0.45 | 6.7 |
| loaded_at_everywhere | 0 | 0 | A | 0 | 1 | 1 | 53,362 | 0 / 0 | 0 | 0.48 / 0.50 / 0.49 | 6.6 |
| v2_rule | 0 | 0 | A | 0 | 1 | 1 | 492 | 0 / 0 | 0 | 0.49 / 0.55 / 0.56 | 6.7 |
| min_commit | 0 | 0 | A | 0 | 1 | 1 | 492 | 0 / 0 | 0 | 0.49 / 0.53 / 0.55 | 6.6 |
| scheduler_end | 0 | 0 | A | 0 | 1 | 1 | 296 | 0 / 0 | 0 | 0.49 / 0.51 / 0.51 | 6.6 |
| scheduler_start | 0 | 0 | A | 0 | 1 | 1 | 156 | 0 / 0 | 0 | 0.50 / 0.50 / 0.51 | 6.6 |
| rollback_as_commit | 0 | 0 | A, B1 | 0 | 0 | 1 | 1,381 | 214 / 0 | 0 | 0.50 / 0.55 / 0.55 | 6.8 |
| backfill_event_time | 0 | 0 | A, B1 | 0 | 0 | 1 | 68,098 | 790 / 0 | 0 | 0.49 / 0.49 / 0.49 | 6.5 |
| legacy_schedule | 0 | 0 | A, B1 | 0 | 0 | 1 | 1,522 | 214 / 0 | 0 | 0.48 / 0.60 / 0.50 | 6.8 |
| hourly_schedule | 0 | 0 | A | 0 | 1 | 1 | 12 | 0 / 0 | 0 | 0.49 / 0.50 / 0.56 | 6.7 |
| window_on_loaded_at | 0 | 0 | A | 0 | 1 | 1 | 47,173 | 0 / 0 | 0 | 0.53 / 0.49 / 0.54 | 6.6 |
| status_latest_loaded | 0 | 0 | A | 0 | 1 | 1 | 113 | 0 / 0 | 0 | 0.49 / 0.54 / 0.54 | 6.7 |
| status_event_date | 0 | 0 | A | 0 | 1 | 1 | 484 | 0 / 0 | 0 | 0.50 / 0.50 / 0.60 | 6.7 |
| current_plan | 0 | 0 | A, B2 | 0 | 0 | 0 | 19,228 | 3,063 / 8,923 | 0 | 0.47 / 0.50 / 0.49 | 6.5 |
| plan_changed_at | 0 | 0 | A, B2 | 0 | 0 | 0 | 518 | 112 / 291 | 0 | 0.54 / 0.50 / 0.55 | 6.6 |
| drop_plan | 0 | 0 | A | 0 (output rejected: no `plan`) | - | - | - | - | - | 0.48 / - / - | 1.1 |
| clip_last_login | 0 | 0 | A, B1, B2 | 0 | 0 | 0 | 0 | 0 / 0 | 1,898 | 0.49 / 0.49 / 0.50 | 6.6 |
| last_login_where_known | 0 | 0 | A | 0 | 0 | 0 | 0 | 0 / 0 | 1,212 | 0.53 / 0.49 / 0.49 | 6.7 |
| labels_matured | 0 | 0 | A | 0 | 0 | 0 | 57,833 | 152 / 2 | 0 | 0.48 / 0.50 / 0.54 | 6.5 |
| log_lookup | 0 | 0 | A | 0 | 0 | 0 | 256,915 | 4,005 / 8,933 | 1,898 | 0.61 / 0.49 / 0.48 | 6.8 |
| cache_visible | 0 | 0 | A | 0 | 0 | 0 | 0 (57,896 H rows missing) | 0 / 0 | 0 | 0.33 / 0.32 / 0.33 | 6.3 |
| zero_features | 0 | 0 | A | 0 | 1 | 1 | 422,145 | 0 / 0 | 0 | 0.39 / 0.38 / 0.38 | 6.1 |
| tune_model | 0 | 0 | A | 0 | 0 | 0 | 256,915 | 4,005 / 8,933 | 1,898 | 0.43 / 0.49 / 0.44 | 6.6 |
| cache_in_work (probe, by name, 17:45) | 1 locally | 1 | none locally (B1, B2 on Daytona) | 1 | 1 | 1 | 0 | 0 / 0 | 0 | 0.66 / 0.56 / 0.55 | 7.4 |

The checkpoint run of 17:38 MST (canonical, alt, original) and its re-run of 17:56 MST after comment-only edits of
`local_check.py` were also all as expected. Check B cell counts differ from task v2's (task v2's nop: 5,944 / 8,506)
because the copies are now rewritten with their records (section 8).

## 12. Hit report (FACT)
`auth/hit_report.py` (the build's integration step, 2026-10-31 17:45 to 17:48 MST): "HIT REPORT OK", problems [];
run again 17:52 to 17:55 MST, it wrote the same `hit_report.json` bytes (sha256
`e9eb23c13fdd30a3b46bc3b77105f2059c537ea8c33d65e1af1f91b4db94e3ad`, also read 18:11 MST). The rule: every attempt
killed by check A moves at least 100 graded cells on H and on the visible extract, so each mechanism shows in the
agent's own data; an attempt whose named kill includes a check-B cut moves more than 0 cells at that cut. Cells count
value cells, 10 per missing row, every row of a missing column and the non-null values of the left-out column; at a
cut, `grade.py`'s changed cells plus that run's non-null left-out values. Twin: the same mistake counted by
`mechanisms.report` in `ref_truth`'s own loop; every rule-swap attempt equals its twin.

| Attempt | Named | H | visible | cut1 | cut2 | Twin H / visible |
|---|---|---|---|---|---|---|
| original (nop) | A, B1, B2 | 258,813 | 259,419 | 27,305 | 14,996 | 256,915 / 257,466 (mechanisms summed, value cells only) |
| loaded_at_everywhere | A | 53,362 | 67,430 | 0 | 0 | equal |
| v2_rule | A | 492 | 356 | 0 | 0 | equal |
| min_commit | A | 492 | 356 | 0 | 0 | equal |
| scheduler_end | A | 296 | 372 | 0 | 0 | equal |
| scheduler_start | A | 156 | 108 | 0 | 0 | equal |
| rollback_as_commit | A, B1 | 1,381 | 1,541 | 214 | 0 | equal |
| backfill_event_time | A, B1 | 68,098 | 82,006 | 790 | 0 | equal |
| legacy_schedule | A, B1 | 1,522 | 1,633 | 214 | 0 | equal |
| hourly_schedule | A | 12 | 12 | 0 | 0 | equal (stated exception: floor 1 on each extract) |
| window_on_loaded_at | A | 47,173 | 47,216 | 0 | 0 | equal |
| status_latest_loaded | A | 113 | 194 | 0 | 0 | equal |
| status_event_date | A | 484 | 483 | 0 | 0 | equal |
| current_plan | A, B2 | 19,228 | 19,627 | 3,063 | 8,923 | equal |
| plan_changed_at | A, B2 | 518 | 584 | 112 | 291 | equal |
| drop_plan | A | 57,896 | 57,909 | - | - | - |
| clip_last_login | A, B1, B2 | 1,898 | 1,953 | 23,300 | 6,063 | equal |
| last_login_where_known | A | 1,212 | 1,246 | 3,407 | 1,493 | equal |
| labels_matured | A | 57,833 | 57,854 | 152 | 2 | equal |
| log_lookup | A | 258,813 | 258,255 | 27,305 | 14,996 | - |
| cache_visible | A | 578,960 | 0 (stated exception: right on the visible extract by construction) | 0 | 0 | - |
| zero_features | A | 422,145 | 422,094 | 0 | 0 | - |
| tune_model | A | 258,813 | 259,419 | 27,305 | 14,996 | - |

`scheduler_start` moves 108 cells on the visible extract and `status_latest_loaded` 113 on H: both clear the floor by
little (section 18). Not graded on purpose (asserted, section 6): a commit at an `as_of`, an event at exactly t - 7 or
t - 30 days, the ticket capture lag, a scoring point between a send and its commit; `<` against `<=` never decides a
value.

## 13. Where the build departs from the approved design
The two changes approved with the design (two of the points in which the interface specification, which like the
approved design is not part of this repository, found the design could not be built as written; its letters are kept):
- (a) **Check B can no longer kill `hourly_schedule`; check A kills it on 12 cells on each extract, a stated exception
  to the 100-cell floor** (floor 1 per extract, `auth/hit_report.py` lines 7-8 and 65-67). A consistent check B copy
  keeps the row counts of every selection line written before its cut, so it cannot change the rows of the hour this
  rule misreads at cut2 (task v2 named B cut2 as its kill, on 4 cells). FACT: B cells 0 / 0, A 12 cells (17:41 MST).
- (d) **`label_job`, `billing_export` and `crm_sync` are in `_ops/` too**, so that S2 and S3 hold word for word for
  every scheduled job: about one hour of build work the design's plan did not count. `crm_sync`'s write line counts
  `plan_changes` rows only (an extract cannot say how many customer records an old sync overwrote); a failed
  `label_job` run sends no transaction; a failed order load rolls back.
Other departures, none of which changes what the agent must find or what the grader checks:
1. Every load line names its target table (`into orders` or `into orders_new`), and the parity lines end "rows and
   values equal" (design: "equal"), so a parity line pins the values too.
2. Stream [seed, 107] holds every legacy record time (send, analyze, end), not only the analyze ends; D0 = C - 56
   days on both brands, with no move of the doc date; `analyze_long_p` 0.10, since 0.05 left `scheduler_end` short of
   the 300-cell target (a scratch run of the interface specification, 2026-10-31 15:23 to 15:40 MST).
3. The dual run continues on C until the rename, which commits 5 to 60 s before the first hourly task into `orders`
   starts (78 s / 83 s before its commit, section 4); the drop is on C + 7 days; txn numbers follow the global send
   order (in copies, the tasks that sent at or after the cut get new numbers after the kept ones).
4. `scheduler_end` moves 296 cells on H, under the 300-cell target and over the 100-cell floor; accepted, since a
   longer analyze tail would change the data.
5. The sweep walks all of `/` (the design named folders), the real-mode runner home is `/tmp/runner-home`
   (`T/tests/kit.py:48`) besides `/home/runner` (`T/tests/Dockerfile:5`), and a residual above 0 fails that run
   closed (section 8).
6. Not built: the third cut and M6 (cut at design time); the two optional grafts (a legacy run marked failed after its
   commit, and a rolled-back rename before C): the hour-3 checkpoint made them optional, and assert 11 keeps "commits
   iff succeeded" in the base data (both variants are counted in `mechanisms.report` at 0 cells).
7. WAREHOUSE.md is 87 lines (design: about 45 unwrapped).
8. The verifier timeout is 279 s (task v2: 278 s), re-derived from task v3's grading times (section 10).
9. The design's "B keeps task v2's kills" holds for B cut1 with fewer cells: `legacy_schedule` and
   `rollback_as_commit` move 214 cells each there (task v2: 2,443 and 2,437) and `backfill_event_time` 790 (task v2:
   2,321; FACT, task v2's local matrix of 2026-10-31 00:46 MST); INFERENCE (from the copy rules of section 8): fewer,
   since a copy now keeps the rows of every selection line sent before the cut. M5 is an A-only kill.
10. Two clauses that the design kept from task v2's WAREHOUSE.md (its lines 9-17) changed at 18:53 MST, after an
    independent check of task v3 (2026-10-31, 17:57 to 18:31 MST): the extract bullet no longer names `data/` at
    2026-03-05, and the timestamp example is `2025-02-04T06:00:00Z` (task v2: `2025-03-04T06:00:00Z`), so nothing in
    the page postdates its 2025-02-14 header (section 14). The extract's moment is still stated in `instruction.md`
    (lines 5-6), `app/README.md:13` and `app/INCIDENT.md:7`.
The hour-3 checkpoint's gates 1 to 4 (the generator's asserts, the regression gate, the checkpoint matrix, the cut
check) passed at 17:37 to 17:39 MST; its gate 5, the mini blind read, was not run as its own step (section 14).

## 14. Blind read
The acceptance test of the design: a fresh Opus 5.5 reader gets only `instruction.md` and a copy of
`environment/app` (a prompt that forbids every other path and the network) and writes its own fix; the fix is graded
with task v3's grader in `KIT_LOCAL` mode (check A on H and check B at both cuts) and must score 1 before the Daytona
proof. Recorded: wall time, tool calls, whether the reader found the dual run unprompted, and each ambiguity it
reported. A second valid reading is fixed in the docs, never kept as a trap, and a new reader then reads. An
independent check lists each sentence a graded value rests on. The hour-3 checkpoint's mini blind read (gate 5) is a
shorter form of the same test: a reader's order visibility, written from the doc, the instruction and the visible
extract as one `order_id,visible_at` row per order, must give the true visible set at every scoring point of both
extracts (`auth/mechanisms.py --visibility <csv> --brand visible`, then `--brand H`: 0 differing pairs); it was not run
as its own step (below). Items the build left to it, settled after the read and an independent check by edits that
change no graded value (2026-10-31, 18:53 MST): WAREHOUSE.md's header says the page was not updated since 2025-02-14,
yet its extract bullet (lines 17-18) named `data/` at 2026-03-05; that clause is gone and the timestamp example
(line 19) is dated before the header (section 13, item 10), while the `_ops/` section stays, as the header announces it.
`app/README.md:8` said that WAREHOUSE.md tells when rows are committed and now says where each table's commit times are
recorded (`_loaded_at` and the commit log, WAREHOUSE.md lines 16 and 31-32); `app/live/features.py:19-20`, the contract,
is unchanged, and its pointer to WAREHOUSE.md for commit times holds through those two sentences. `app/README.md:14` now
names one sample, the one file in `logs/`. After the edits (FACT, 2026-10-31, 18:55 to 19:07 MST): the 25-variant local
matrix gave every reward, check and cell count of section 11 again (timings aside), the cut check's 15 graded and
targeted cuts were all clean, the graded copies carrying the digests of section 8, and the generator and
`make_expected.py` passed in `--check` mode.

Result (FACT: the reader's report and the grade of its copy, 2026-10-31; neither is shipped). An Opus 5.5 reader worked
from 17:58:13 to 18:26:01 MST (about 28 min by its report; its copy's file times agree: first code edit 18:19:31, output
18:26:00) in 35 tool calls. Its fix, graded at 18:30 MST with task v3's grader in `KIT_LOCAL` mode on the Mac (its copy
of `/app` without `data/`, `__pycache__` and `.venv`, as the artifact rule drops them), scored reward 1.0: check A,
B_cut1 and B_cut2 all 1, 0 mismatched cells in every one of the ten features in each check, `days_since_last_login` left
out, invariant problems 0 at both cuts; a second grading gave the same `reward.json` apart from timings. Controls: the
shipped pipeline, graded the same way, scored 0 (the `original` row of section 11), and three other careful readings of
points the reader found unclear, each built on the reader's fix, scored 1.0 with 0 cells: a load resolves its target
table at its task's start, not at its log line; a schema statement takes effect at its log line (on H 1 s before the
rename's commit); status partitions are visible from `_loaded_at` alone. Beyond the grade, the reader's command matched
the simulator's live values on both extracts with 0 mismatched cells and kept every row at or before the cut at 35 cuts
made as in the cut check of section 8 (2 graded, 13 targeted, 20 random).

It was not a blind read. The reader's task text named the migration ("a second table filled before a rename") before it
opened any data, and its context also held the authors' design notes, which describe task v3's design; the reader
reported the hint itself. So the read shows that the agent's files settle every graded value for a reader who knows
where to look; it does not show that an agent finds the migration unprompted, and whether the reader found the dual run
unprompted cannot be answered from it (its code rebuilds the migration from `_ops/`, but the prompt came first). The
unprompted test is the three Claude Code trials, which had only `/app` and the instruction (section 16). The reader also
read the package before the four clause edits above (WAREHOUSE.md lines 18 and 19, `app/README.md` lines 8 and 14); they
reword text and change no graded value (FACT: a diff of the package against the reader's copy, and the matrix re-run
above). No reading that changes a graded value was found (the grade's verdict), so no doc fix was needed for one and no
second reader read; the four clause edits answer the independent check's notes.

What the reader found unclear, and how each is settled:
- The interpreter flag `-I` (the reader's own harness, not the task): under Python 3.12 it drops the current folder from
  the module path, so `python -I -m churn.build_features` fails; the grader runs `python3 -m` from the package folder
  (instruction line 18), which the reader also ran (exit 0).
- The drop rule read per extract (instruction lines 14-15): by the reader's count `days_since_last_login` is
  determinable for 2.2% of the visible extract's predictions, and it left the feature out. Settled: a feature that the
  extract cannot determine for some rows is left out, and a column named after it fails unless all its values are null
  (line 25), so filling the determinable rows fails (`last_login_where_known`, section 9).
- WAREHOUSE.md predates the migration and names none of its parts: by design; its header points to `_ops/` (lines 3-5),
  and S2 makes the commit log, not the scheduler's task states, the account of commits.
- How a load resolves a table name (S1 speaks of queries): every load line names its target table (section 13, item 1);
  the other readings of load and schema timing scored 1, and no scoring point lies between the rename's start and the
  first hourly commit into `orders`, or between a send and its commit (asserts 9 and 10, section 6).
- When the backfill read its source: it copies exactly the orders placed before D0 (assert 4), so the moment changes no
  row.
- Overlapping legacy windows ("sends them to `orders`", WAREHOUSE.md:68-69, read as an append): none; the committed
  ranges partition [2024-01-01, C) (assert 3; 492 committed ranges on the visible extract and 446 on H, with 0 overlaps
  and 0 gaps).
- A status partition exported twice: none; each partition is exported once (assert 12; 793 `billing_export` tasks with
  793 run dates on both extracts).
- No table named `orders` at some moment: never; one transaction holds both RENAME statements (section 3).
- A scoring point exactly at the cut: kept, as the instruction's "at or before the cut" needs (lines 31-33); the
  grader's copies keep every scoring point at or before the cut (`T/tests/perturb.py` docstring).
- `plan_changes` as the complete log of applied changes, the sign-up plan being the earliest `old_plan`: as stated
  (WAREHOUSE.md:49-54); task v2's plan-chain asserts hold on both extracts (section 6), and the copies re-derive every
  chain and never change a sign-up plan (section 8).

The sentences the graded values rest on are S1 to S5 of section 3; the independent check of task v3 (2026-10-31,
17:57 to 18:31 MST) read the doc against the data of each extract (57 checks pass on each) and found S1 to S4 and the
instruction's phrase S5 once each. Gate 5 of the hour-3 checkpoint, the mini blind read, was not run as its own step
(the build's records name gates 1 to 4 only). The nearest evidence is that check's own replay of the name rule from the
records into one `order_id,visible_at` row per order: `auth/mechanisms.py --visibility` found 0 differing orders and 0
differing pairs on both extracts. That check had the whole package, so it is not a blind read either.

## 15. Daytona proof (run v3)
Run on a copy of the package without the `[agent] network_mode` line (section 18), one trial at a time, from the
repository root. `tools/proof_matrix.py` makes that copy at
`jobs/feature-leakage-churn/package-<tag>/feature-leakage-churn` (lines 31-45: it checks that the copy differs from
`task.toml` by that one line only, and skips `__pycache__`, `.DS_Store` and `.claude-flow`), runs Harbor on it and names
it in the results. Its rows (lines 46-53): canonical (oracle x k), every `alt*` folder, nop, every attempt under
`solution/attempts/` (the probe included, expected 0 like every attempt) and one force-build: 27 rows here, 31 trials at
`--oracle-k 5` (FACT, the tool's enumeration applied to `T/solution/`, 18:07 MST). Run v3 ran all 27 rows, the whole
enumeration (`run_v3.log`), so its command needs no `--only` (no shipped file records whether the run passed one); its
tag is `v3` (task v2's proof was `rev1`; its files are in `validation/feature-leakage-churn/second-version/`):
```
python tools/proof_matrix.py feature-leakage-churn --env daytona --env-file <keys file> --n 1 --oracle-k 5 --without-agent-network-line --tag v3
```
Harbor ran with `--environment-build-timeout-multiplier 3` (`environment_build_timeout_multiplier` 3.0 in every trial's
`config.json`), as in task v2's proof and trials: the authors adopted it on 2026-10-30, while Daytona's service was
degraded, so that a slow image build cannot leave a sandbox that Harbor never received, and `tools/proof_matrix.py` has
no option for it.

Result, 2026-10-31, 19:12:31 to 19:31:31 MST (the first row's `started` in `proof_results_v3.json`, and the time the
run's three files were written): ALL AS EXPECTED, 27 rows and 31 trials (FACT: `PROOF_RESULTS_v3.md`,
`proof_results_v3.json` and `run_v3.log` in `validation/feature-leakage-churn/`; each trial's `result.json`,
`config.json`, `verifier/reward.json` and `verifier/test-stdout.txt`, read 2026-10-31 by 20:50 MST):
- canonical 5 of 5 at 1.0; alt and force-build 1.0; nop and the 23 attempts, the probe among them, 0.0; no exception,
  and Harbor returned 0 on every row.
- Against the local matrix of 19:04:10 to 19:06:58 MST on the final package (section 14; nop against the local
  `original`, force-build against `canonical`): 30 of the 31 trials, all but the probe, equal their local variant field
  by field outside the timing, environment and sweep fields (`drop_plan` among them: it stops after its run on H in
  both, its output rejected, `bad_output_H` 1, check A 0, no cut run); the probe is not in that matrix and differs from
  its local run of section 8 by design (below).
- Real mode: the sweep before H removed 1 entry of uid 1001 and each sweep before a cut 5 (the probe's before cut1: 8),
  with 0 left and 0 unreadable (`sweep_errors_*` 0) in all 91 sweeps; no run failed for a sweep. INFERENCE (the log
  gives counts, not paths): the counts the plan inferred from the code, the runner's home before H and the earlier run's
  four staging folders with a runner home before each cut. Each sweep took 0.638 to 1.193 s.
- The probe `cache_in_work`: check A 1; check B cut1 and cut2 0, with 9,451 and 45,706 changed cells, every row compared
  at each cut and all in `orders_7d` (no cache was left, so it wrote `orders_7d + 1`); residual 0; reward 0, as
  designed.
- Invariant problems 0 at both cuts on every trial that ran check B (30 of 31).
- Times: the graded runs took 0.42 to 1.99 s, the alt's 1.83, 1.89 and 1.99 s, each under section 10's 20 s; grading
  (`seconds_grade_total`) 11.5 to 16.5 s on the 30 trials that ran all three checks and 1.9 s on `drop_plan`; Harbor's
  verifier phases 20.5 to 26.6 s, 12.6 s on `drop_plan` and 52.5 s on the run's first trial; each phase minus its three
  runs 11.9 to 50.3 s, under the plan's 99 s (279 - 180), so `timeout_sec` stays.
- Every `reward.json` has `verifier_cpu_quota` 2.0, `verifier_memory_limit_mib` 4096.0 and `net_private_*` 1, and every
  `test-stdout.txt` holds `[test.sh] lock ok`, `setid files left: 0`, `network isolation: ON` and
  `killed 0 runner processes`.
- Not shown: whether the image has `ipcrm`. No sweep found an IPC object of uid 1001: each sweep line names the removal
  method of every IPC object it removed (`ipcrm` or ctypes; `T/tests/grade.py` lines 207-221), and that field is empty
  in all 91. The rule that a residual above 0 fails a run never fired either (section 18).
- Harbor 0.25.0 content hashes: the shipped package
  `sha256:274a6896d00585702123292d2377480bab7ec0829da8594f2c9502e486700091` (Harbor's `Packager`, 81 files, computed by
  19:17 MST; no package file is newer than 19:03:40 MST), the proof's copy
  `sha256:b042a2c9540522bfbb76e91c81eae76b77d9f8f34df7d550a8314a25b24c0de5` (the same 81 files; the digest in every v3
  job's `lock.json`, shipped as each trace's `job_lock.json`, the Claude Code job's of section 16 included). Both
  differ from task v2's (`sha256:580f945d63a9540624b8362b9865224c2bd1c9d8f02fb72532048641f5f184c5` and
  `sha256:5f7e542b9c3c131bd0a0cdb2b7e1c1d7f6a8202429f0aaf2f1431a7fd9d0d63f`), since `task.toml`, `instruction.md`,
  `environment/`, `tests/` and `solution/` all changed (section 2). `diff -rq` of the package and the copy lists
  `task.toml` only, and its diff is the `network_mode` line (2026-10-31, by 20:50 MST).
- Daytona listed 0 sandboxes before and after the run (the authors' listings, recorded outside this repository).

Files: the proof matrix in `validation/feature-leakage-churn/` (`PROOF_RESULTS_v3.md`, `proof_results_v3.json` and
`run_v3.log`, the console output) and one redacted trial per row in `traces/<variant>/` (27 folders; for canonical the
trial with the earliest `started_at`, `feature-leakage-churn__57KkDQi`, whose `job_result.json` holds the rewards of all
five). The job folders under `jobs/` are git-ignored and stay outside the repository; the trace folders are the shipped
copy.

## 16. Agent trials and pre-registration
Settings (the authors' defaults for the revised tasks): Harbor's `claude-code` agent with `claude-opus-5-5`, web
search off, a spend cap of 20 dollars per trial (`max_budget_usd`), three trials, one at a time (`-n 1`), on the copy
the proof used; the model key stays outside the repository; every trajectory is read for fetches from GitHub hosts and
every trace scanned for the key before shipping.

Pre-registration, copied unchanged from the approved design (written before any trial of task v3):
1. Prediction (INFERENCE): 1 to 2 passes of 3, 3 of 3 about one chance in four, 5 to 15 minutes of agent time each.
2. Reported as measured: the pass count, agent seconds and cost per trial, A's mismatches per feature, B per cut.
3. Each failure is classed against M2 to M5, M7, M8 and the v2 feature work; one outside them (an unclear sentence, a
   verifier error, a second valid reading) is a defect: fixed and the proof re-run, or v2 ships if past the cutoff.
4. Fixed now: v3 ships if its proof is all as expected and its blind read scored 1, whatever the count (3 of 3
   included: a high pass rate is not a defect, G29); no change to the package after the trials start except a fix.
5. A trial whose trajectory fetches the public tests is excluded and reported.

In the copied text, v2 and v3 are task v2 and task v3, and "the cutoff" is the authors' cutoff of 2026-10-31: task v3
locally green with its blind read at 1 by 22:00 MST and its Daytona proof all as expected by 23:30 MST, else task v2
ships as built with its 3 of 3 stated. Both were met: task v3 was green locally by 17:57 MST (sections 6 to 12), its
blind read was graded 1 at 18:30 MST (section 14) and its proof was all as expected at 19:31:31 MST (section 15).

Outcome (FACT: each trial's `result.json`, `config.json`, `trial.log`, `agent/trajectory.json`, `agent/claude-code.txt`
and `verifier/reward.json`, and the job's `result.json` and `lock.json`, shipped in each trace as `job_result.json` and
`job_lock.json`; read 2026-10-31 by 20:50 MST, and the `trial.log` files at 21:54 MST; Harbor's return code from the
authors' run log, recorded outside this repository). Job `feature-leakage-churn-claudecode-opus55-v3-cc1`, 19:32:41 to
19:59:05 MST, Harbor's return code 0: Claude Code 2.1.316 with `claude-opus-5-5`, `max_budget_usd` 20 and
`disable_web_search` true, so Harbor passed Claude Code `--disallowedTools WebSearch,WebFetch` (each trial's
`trial.log`); every trial on the proof's copy (section 15), one at a time. Because the copy lacks the agent network
line, the agent phase had the sandbox's own network (Harbor's default, public, under the limits of the authors' Daytona
Tier 1 account, which by Daytona's documentation keep GitHub's hosts reachable); the shipped package denies the agent
network.

| Trial | Ran (MST) | Reward (A, B cut1, B cut2) | Agent time | Tool calls | Cost |
|---|---|---|---|---|---|
| `feature-leakage-churn__qthVz4g` | 19:32:41 to 19:41:37 | 1.0 (1, 1, 1) | 448.2 s | 24 (Bash 23, Write 1) | 1.362 dollars |
| `feature-leakage-churn__58R6Roz` | 19:41:37 to 19:50:07 | 1.0 (1, 1, 1) | 426.8 s | 22 (Bash 19, Write 2, Edit 1) | 1.470 dollars |
| `feature-leakage-churn__oYkSBpm` | 19:50:07 to 19:59:05 | 1.0 (1, 1, 1) | 454.9 s | 27 (Bash 25, Write 2) | 1.549 dollars |

The "Ran" times are the Mac clock; `result.json` gives them in UTC (7 hours ahead). Agent time is the `agent_execution`
phase; tool calls are counted in `agent/trajectory.json`; cost is Claude Code's `total_cost_usd`
(`agent/claude-code.txt`), 4.382 dollars for the three, each far under its 20-dollar cap.
- As item 2 asks: 3 of 3 passed. In each trial check A had 0 mismatches in every one of the ten features and 0 missing,
  extra or duplicate rows; check B moved 0 cells at cut1 (9,451 rows compared) and at cut2 (45,706);
  `days_since_last_login` was left out (0 non-null values in all three runs); the graded runs took 0.87 to 1.13 s and
  Harbor's verifier phases 21.9 to 23.6 s.
- Against the prediction (item 1): the agent time, 7.1 to 7.6 minutes, fell inside 5 to 15 minutes; the count, 3 of 3,
  is above 1 to 2 passes, the outcome given about one chance in four.
- Against task v2's three trials (section 2): 426.8 to 454.9 s of agent time against 181.8 to 221.2 s, 22 to 27 tool
  calls against 10 to 12, and 1.362 to 1.549 dollars against 0.575 to 0.678; for the three together about 2.3 times the
  agent time, 2.2 times the tool calls and 2.4 times the cost.
- What each trajectory worked from (`agent/trajectory.json`): each first printed the file list and ran
  `cat INCIDENT.md CHANGELOG.md docs/WAREHOUSE.md`, as task v2's did, then read `live/` and `churn/`; from its third
  tool call each read the `_ops/` records (the jobs in `scheduler.log`, the backfill, migration and parity lines, the
  outcomes in `commits.jsonl`), wrote a parser of the two logs (`churn/ops.py` in all three), compared its output with
  the January sample, built its own check B copy at a cut of its choosing, and ran the command on a copy as an
  unprivileged user (`su nobody`). Strings in the tool calls' arguments, in start order (FACT: counted 2026-10-31,
  20:00 MST): `_ops` 26, 36 and 23; `commits.jsonl` 14, 13 and 10; `scheduler` 21, 19 and 17; `RENAME` 3, 4 and 4;
  `dq_checks` 3, 3 and 1; `orders_new` 1, 3 and 1. Passing check A on H needs the dual run and the commit times:
  `v2_rule` and `min_commit`, task v2's trials' rules, fail it by 492 cells (section 11).
- Network and answer key: no tool call, observation or message of the three trajectories holds a network command (curl,
  wget, nc, ssh, pip install, git clone), an http or https URL, a GitHub host, or a path under `/tests`, `/solution` or
  `/logs/verifier` (two scans of 2026-10-31, the second by 20:50 MST; every hit of the first was read, and none was a
  network command or a path); the run's key scan found the model key in none of the job's files. The traces in
  `validation/feature-leakage-churn/traces/agent-claude-code/<trial>/` ship `agent/trajectory.json`,
  `agent/claude-code.txt` and the trial and job records, redacted; Claude Code's raw session files (`agent/sessions/`,
  which hold its full requests) are not shipped.
- Items 3 to 5 applied: no trial failed, so none was there to class (item 3); task v3 ships, with its 3 of 3 stated,
  since its proof was all as expected and its blind read scored 1 (hinted, section 14), and the package was not changed
  after the trials started (no package file is newer than 19:03:40 MST; the first trial started at 19:32:41 MST)
  (item 4); no trajectory fetched the public tests, so no trial is excluded (item 5).
- INFERENCE (from the 3 of 3 and the agent times): the hardening doubled the investigation Claude Code on Opus 5.5
  needs, but did not make the task one this agent cannot reliably complete. Three trials show that this agent can solve
  the task, not its pass rate (3 of 3 has a Wilson 95% interval of 0.44 to 1.00). How other agents, the external
  reviewer's among them, fare on task v3 is UNVERIFIED. Nothing was added to the task after the trials (G29).

## 17. Gate record
Scored against the checks G1 to G30 of `docs/QUALITY_GATE.md`.
```
Gate record: feature-leakage-churn, task v3 as built (2026-10-31; local, the blind read, the Daytona proof v3 and three Claude Code trials)
Applies to: task feature-leakage-churn
G1  PASS - code, docs, the January sample, the visible extract with its _ops/ records, H, expected values and pinned packages are in the package; neither the work nor grading needs network
G2  PASS - a training table that matches what the live service computed decides whether churn-hgb-v4 can ship; the drop tells the model team what v4 must do without
G3  PASS - seven warehouse tables with audit columns, a scheduler log and a commit log as a warehouse keeps them, the live queries, a reference doc written before a migration, incident, changelog, a log sample and a multi-module pipeline
G4  PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - a script decides: values against the simulator's true state (A) and causality on what the warehouse held, records included (B); reward 1 only if all pass; 25 of 25 as expected locally and the probe as expected locally (section 11); on Daytona all 27 rows as expected, 30 of 31 trials (all but the probe) equal to their local variant field by field outside timing, environment and sweep fields, the probe as designed (section 15)
G5  PASS - still the only point-in-time ML task of the five; orders-export-missing-rows also has late rows, but its cause is a cursor key and its fix keyset pagination
G6  PASS - expected values from the simulator's true state, unchanged from task v2 byte for byte; the extract-only canonical matches with 0 mismatches and bit-identical floats on both extracts, and the commit-replay alt matches the canonical (sections 6 and 9)
G7  PASS - rebuilding what a live service read across a table migration is everyday ML platform work
G8  PASS (run) - principle, drop criterion, null-column rule, formats, the integer features, tolerances, check B with the copy's records, cap, resources and OMP_NUM_THREADS are stated; the name rule, the commit-log sentence and its scope in WAREHOUSE.md; every graded value from /app (section 5); an Opus 5.5 reader's fix scored 1, but its prompt named the migration and its context held the authors' design notes, so it shows the files settle every graded value, not unprompted discovery (section 14); three Claude Code trials with only /app and the instruction passed (section 16)
G9  PASS - dual runs with a rename cutover, maintenance after a commit, backfills that restamp load metadata, failed nightly jobs, attributes overwritten in place and late labels are real warehouse behaviour
G10 PASS - a feature table train.py can use for v4, and a documented drop of the feature that cannot be rebuilt
G11 PASS - black-box CLI runs; only output values are compared; two very different methods pass
G12 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - the shipped pipeline, task v2's trials' rules (v2_rule, min_commit), the scheduler's state lines, schedules, the trusted restamped column, a cache of the visible answer, a log lookup, constants and tuning all score 0, locally and on Daytona; the cache probe failed both check B cuts on Daytona, reward 0 (section 15); limitation: hidden files public after the push
G13 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - the commit-replay alt (no pandas; other dtypes, row and column order, an extra column, the left-out column present and all null) scores 1, locally and on Daytona; a copy's records are recounted from the copy, never stale (section 8)
G14 PASS - difficulty is investigation (which table bore the name orders at t, which commit put each order there, from two logs) and judgment (the commit log over the scheduler's states, drop over approximate) plus an exact as-of build; measured: 3 of 3 Claude Code trials passed, each working from _ops/, in about twice task v2's agent time (section 16)
G15 PASS (run) - every commit an explicit record; parity coverage; the name rule and the commit-log sentence; no planted ties and no point between a send and its commit (asserted); lenient formats; the cap is about 65 x the Mac alt median and about 30 x the alt's slowest run on Daytona (1.99 s), a naive per-row build needs about 123 to 159 s on the Mac (section 10); each A-killed attempt moves >= 100 cells on both extracts, except hourly_schedule (12, approved) and cache_visible on the visible extract (0 by construction); the points the blind reader found unclear change no graded value (section 14)
G16 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - seeded simulator and perturbation, new streams for the new parts only, committed H, expected and SHA256SUMS, pinned image; regeneration byte-identical twice; graded copies byte-identical across processes; timeout from measured grading time; canonical 5 of 5 and the clean rebuild (force-build) 1.0 on Daytona (section 15)
G17 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - tests/ only in the verifier image (/tests 0700); /app holds the visible brand's data, records and sample only; check B runs now independent of the H run (section 8): on Daytona no sweep left an entry of uid 1001 and the probe's cache did not reach check B (section 15); no Claude Code trial's command touched /tests (section 16)
G18 PASS - the Harbor layout; harbor lint clean; Harbor's TaskConfig accepts task.toml (no-network 3600 s; separate verifier 279 s; 2 cpus; 4096 MB); tools/check_task.py prints OK feature-leakage-churn
G19 PASS - its own copy of the kit (sync_kit.py --check clean for all five tasks); no other task needed
G20 PASS - the row is in the repository README (README.md, the feature-leakage-churn row of the table "The tasks"); its validation cell gives run v3 and the three Claude Code trials as sections 15 and 16 record them
G21 PASS - limitations in section 18 and in the repository README (this task's row, "The agent network line" under Setup, and the task's entries under "Known limitations")
G22 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - canonical 1 on A and both cuts locally; oracle 5 of 5 at 1.0 on Daytona (section 15)
G23 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - the nop (the shipped pipeline) 0, failing A and both cuts, locally and on Daytona
G24 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - 22 attempts 0, each failing its named check, locally and on Daytona; the probe 0 on Daytona, failing both cuts (section 15)
G25 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_v3.md) - alt 1 on A and both cuts, locally and on Daytona
G26 PASS - grader commented; per-check, per-feature and sweep sub-metrics in reward.json; in the repository at the revision commit: one redacted trial per row of run v3 (validation/feature-leakage-churn/traces/<variant>/), the three Claude Code trials (traces/agent-claude-code/<trial>/), task v2's proof traces and trials (second-version/) and the first version's evidence (first-version/)
G27 PASS (plan; part UNVERIFIED) - CPU only, no keys; whether a reviewer's harness enforces the [agent] network_mode line is UNVERIFIED; Daytona Tier 1 refuses it, so a runner there removes the line (section 18)
G28 PASS (run) - a failure is a wrong account of what the warehouse held at t: the table behind a name, the commit behind a row, a task state taken for a commit, current-value attributes, label timing; measured: 3 of 3 Claude Code trials passed, so no failure was there to classify (section 16)
G29 PASS - no live value changes: the truth is task v2's, the records replace stated rules, the dual run is a real migration pattern; nothing was added after the 3 of 3, as the pre-registration requires (section 16)
G30 PASS (plan) - delivered in the existing public repository; commit and push only on the authors' word
Result: PASS, no FAIL. The Daytona proof v3 (2026-10-31) covers G4, G12, G13, G16, G17 and G22 to G25; the blind read,
hinted (section 14), and the three Claude Code trials (section 16) back G8 and G15; the trials give G14, G28 and G29
their measured part. G30 is completed by the revision commit and its push; G27's network part is UNVERIFIED.
```

## 18. Limitations and open issues
- Three Claude Code trials, 3 of 3 passed (section 16), in about twice task v2's agent time. They show that this agent
  can solve the task, not its pass rate (3 of 3 has a Wilson 95% interval of 0.44 to 1.00); they ran with the sandbox's
  network, and how other agents, the external reviewer's among them, fare is UNVERIFIED. INFERENCE: the hardening did
  not make the task one this agent cannot reliably complete. `difficulty = "hard"` (`task.toml:10`) is the authors'
  estimate, written before any trial; with 3 of 3 passes it overstates the task for this agent (INFERENCE), and it
  stays, since an edit to `task.toml` would change the proven package's digest. A high pass rate would not by itself be
  a defect: G29 rules out difficulty added only to lower it.
- The blind read scored 1 but was hinted (its prompt named the migration), so it is evidence of fairness, not of
  unprompted discovery; the Claude Code trials are the unprompted test. Its context also held the authors' design
  notes (section 14).
- Synthetic data: two simulated brands; the live AUC is computed from simulated live values (section 7).
- The hidden tests (H, the expected values, the grader) are public in this repository once this revision is pushed; an
  agent with network access could fetch them. Hence the network line below; where it cannot be enforced, read each
  trajectory for fetches from GitHub hosts and exclude and report any trial that made one. By Daytona's documentation,
  its Tier 1 and 2 keep GitHub's hosts reachable (the repository README's limitation "The hidden tests are public").
- The network line. `task.toml` ships `[agent] network_mode = "no-network"` (no line for the verifier). FACT (Harbor
  0.25.0 source, `harbor/trial/trial.py:312-321` and `:692-694`): where Harbor applies it, an installed agent's model
  host is added to the agent phase's allowlist and the agent's web tools are turned off. FACT (the authors' Daytona
  canary of 2026-10-30, 17:43 to 17:47 MST, recorded outside this repository): the authors' Daytona Tier 1 account
  refuses Harbor's runtime network switch for the agent phase, on the block-all path (oracle) and the domain-allowlist
  path (claude-code): "Failed to update network settings: Network access is restricted and cannot be overridden at the
  sandbox level." So where the line cannot be enforced, Harbor rejects the trial: on Daytona Tier 1 (the canary), and on
  Tier 2 by Daytona's documentation (INFERENCE; not tried). A runner there removes the line and reads each trajectory as
  above. The Daytona proof and the trials of this task ran such a copy; it differs from the shipped package by that line
  only, so its Harbor digest differs (section 15).
- `hourly_schedule` is under the floor: check A kills it on 12 cells per extract (3 predictions on each), and check B
  cannot (approved change (a)). Deterministic, but a thin kill.
- The January sample is silent on orders before the move: its 365 requests are of January 2026, months after both
  moves, so matching it says nothing about M2 to M5; only the doc and the records decide those rules. Task v2's
  shadow-week sample, all 42 of whose rows contradicted "trust `_loaded_at`" (task v2's generator report), is gone;
  check A kills that reading by 53,362 cells on H.
- Thin margins: `scheduler_end` 296 cells on H (under the design's 300 target), `scheduler_start` 108 on the visible
  extract and `status_latest_loaded` 113 on H, each over the 100-cell floor. If the generator is ever re-run with
  other knobs, `mechanisms.assert_targets` stops a regeneration under the floor.
- The independence fix is proved only on Daytona: on the Mac there is no uid split, so the probe scores 1 by
  construction. Run v3 proved the real-mode walk (0.638 to 1.193 s per sweep, 0 entries left in every trial) and the
  probe's failure of check B (section 15). Still UNVERIFIED: `ipcrm` in the image (else the ctypes call; no trial left
  an IPC object to remove), and the rule that a residual above 0 fails a run closed, which never fired (a uid-1001 path
  that root cannot remove, for example on a read-only mount, would score every run 0; the remedy would be to add it to
  `SWEEP_SKIP`). Not swept: kernel keyrings (Docker's default seccomp profile blocks `add_key` and `keyctl`; UNVERIFIED
  on Daytona).
- The documented rule for several plan changes applied by one sync (WAREHOUSE.md:52-54) is never graded: no (customer,
  sync) group has more than one change on either extract (FACT, an independent review of 2026-10-31, 01:56 MST, on
  `plan_changes.csv` files that task v3 keeps byte for byte).
- A valid naive per-row build (about 123 to 159 s on the Mac, two runs, section 10) fails the 60 s cap; the
  instruction says to time a run on `/app/data`, which is about the size of H.
- Check B's invariants run at grade time, and a problem fails that cut closed (logged as a grader defect); the graded
  copies were checked byte-identical across processes on the Mac only. On Daytona the invariant problems were 0 at both
  cuts on every trial that ran check B (section 15).
- `test.sh`'s own setup time is not measured on the Mac (section 10); on Daytona each verifier phase minus its three
  runs, `test.sh` included, took 11.9 to 50.3 s (section 15). The image size and build time are not measured.
- Hidden inputs are readable by agent code while it runs in the verifier (they must be, to be processed); it cannot
  change check A's verdict (the expected values stay in `/tests`, 0700), and since task v3 the grader's sweep kills
  every uid-1001 process and removes every uid-1001 file and IPC object it finds before the next run (section 8; the
  Daytona proof checked it in real mode, section 15; kernel keyrings are not swept, as above).
- `solve.sh` rebuilds `/app/output/features.parquet` for the canonical and the alt (a smoke test; the artifact keeps
  that file, about 1.5 MB for the canonical); the attempts skip it.
- The shipped package's Harbor digest is new, since `task.toml` (the timeout), `instruction.md`, `environment/`,
  `tests/` and `solution/` all changed (section 2); the proof records it (section 15).

## 19. Earlier versions: task v2 and the first version
**Task v2** (built 2026-10-30 to 2026-10-31): the same simulated world, truth, H scoring points, cuts and expected
parquet as task v3. Its WAREHOUSE.md (107 lines) stated each loader's commit timing, the schedule and a History of the
move from the nightly `legacy_orders` job to `orders_hourly` with this brand's dates; `data/` had eight CSV files,
among them the run table `legacy_order_loads.csv` (one row per legacy run: its date, start, finish, status and
watermark; 43,067 bytes on the visible brand); every order placed before the move carried `_load_job`
`legacy_backfill` and the backfill's `_loaded_at` (64,769 visible / 55,977 H rows; FACT, task v2's `orders.csv` files,
18:03 MST); `logs/` also held a 42-request sample of a pre-launch shadow week. Its grader served the three runs from
one package copy (section 8). Proof rev1 on Daytona (2026-10-31, 01:54:40 to 02:12:04 MST, on the copy without the
network line): ALL AS EXPECTED, 26 trials: canonical oracle 5 of 5 at 1.0, alt and force-build 1.0, nop and 18 attempts
0.0, B invariant problems 0 on every trial that reached check B (25 of 26; the `drop_plan` output was rejected before
it) (FACT: `validation/feature-leakage-churn/second-version/PROOF_RESULTS_rev1.md`, `proof_results_rev1.json`,
`run_rev1.log`; the trials' `reward.json` and `result.json`, read 18:08 MST). Claude Code: 3 of 3 (section 2). Task v2
was never committed or pushed: on 2026-10-31 at 17:59 MST `main` and `origin/main` were at `495c9f5` (FACT, `git log`
and `git rev-parse`), and task v3 replaced task v2 in place before any commit, so git history holds the first version
and task v3, not task v2. Task v2's record is this section and section 2, its rev1 proof files and redacted traces (one
trial per proof row and its three Claude Code trials) in `validation/feature-leakage-churn/second-version/`, and its job
folders, which are git-ignored and stay outside the repository.

**The first version** (commit `495c9f5`): four event-time leaks against a written spec, `churn/FEATURES.md`, nine
features, hidden seed 2; proven on Daytona on 2026-10-28 (runs full1 and full1b) and run again from a fresh clone on
2026-10-30; its evidence is in `validation/feature-leakage-churn/first-version/` and its design record in git (`git
show 495c9f5:docs/feature-leakage-churn/DESIGN.md`). Its three agent trials of 2026-10-30 (Harbor's `terminus-2` agent
with `openai/gpt-oss-120b`) passed 0 of 3. Its results do not apply to task v2 or task v3: the data, the agent's
files, the grader and the solutions all changed.

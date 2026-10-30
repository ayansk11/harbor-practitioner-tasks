# feature-leakage-churn: design and local validation

**What this file is.** The authoring notes for the task in `tasks/feature-leakage-churn/`: its design, the deviations
from our original design (written before the build and not part of this repository; section 9), the local checks, the
quality-gate record against `docs/QUALITY_GATE.md` (gate ids G1-G30; section 10), the Daytona proof results
(section 13) and the known limitations (section 11). Paths are relative to the repository root; short names such as
`tests/grade.py` are inside the task folder `tasks/feature-leakage-churn/`.

Last updated: 2026-10-29 (Mac clock, MST): wording edited for outside readers, pointers fixed, and the kit's version
note in section 2 corrected (no measurement, verdict or limitation changed). Before that, also 2026-10-29: section 13
adds the Daytona proof results of 2026-10-28, the gate record
(section 10) is re-scored from them, and the notes of sections 5, 7, 11 and 12 that were written before those runs now
point to their results. Before that: 2026-10-28 19:24 MST, after the review fixes (section 12). Labels: FACT (a command
output or file named), INFERENCE (reasoned; basis named), UNVERIFIED. "Mac" = the authoring machine, an Apple M4 with
10 cores, using `.venv` (Python 3.12.13, pins in `tools/dev-requirements.lock`). The task has not run on a local
container engine (the Mac has none; our check of 2026-10-28); the Daytona runs full1 and full1b of 2026-10-28 are in
section 13.

## 1. The task in one paragraph
A meal-kit subscription company's churn model scored offline AUC 0.981 but 0.613 in its first live month. The feature
pipeline `/app/churn` leaks future information in four places, in four files. The agent must find them and fix
`python -m churn.build_features --data <dir> --out <file.parquet>` so every feature follows `/app/churn/FEATURES.md`
exactly, keeping all nine features. The verifier runs the agent's CLI on a hidden extract and checks values against a
reference (check A), then changes everything that becomes known after two cut times and checks that no earlier
prediction moves (check B, which needs no reference).

| Leak (file) | What the original does | What FEATURES.md says |
|---|---|---|
| windows (`churn/windows.py`) | daily buckets with `rolling("7D"/"30D", closed="both")`, joined on the prediction's day: the whole day of t counts (including the 06:00 box charge stamped exactly at t, and the rest of the day), plus one extra day at the left edge | half-open `[t - W days, t)` on exact timestamps |
| target encoding (`churn/encoding.py`) | district churn rate over all labels, the row's own and later ones included | smoothed mean (m = 20) over labels with `label_available_at < t`; prior from the same set, 0.05 if none |
| status (`churn/status.py`) | `drop_duplicates("customer_id", keep="last")`: every row gets the customer's final snapshot (`cancelled` for churners) | latest snapshot dated before `date(t)` (a snapshot dated D describes the end of day D) |
| imputation (`churn/impute.py`) | `bfill().ffill()` per customer: gaps take the next reading | own reading, else the last earlier reading, else null |

Two features (`days_since_last_order`, `tenure_days`) are already correct, as in a real codebase. The design's fallback
(drop the imputation leak if the oracle could not pass with four) was not needed: all four leaks are in.

## 2. File map
| Path (from the repository root) | What |
|---|---|
| `tasks/feature-leakage-churn/task.toml` | schema 1.4, the shared `/app` artifact, separate verifier (281 s), agent 3600 s, 2 vCPU, 4096 MB |
| `tasks/.../instruction.md` | the request, every enforced rule, the 60 s limit, the shared closing line |
| `tasks/.../environment/Dockerfile` | pinned base image digest, 12 exact pins (all transitive deps), `COPY app/ /app/` only |
| `tasks/.../environment/app/churn/` | the leaky pipeline: `extract.py`, `windows.py`, `encoding.py`, `status.py`, `impute.py`, `build_features.py`, `train.py`, `FEATURES.md` |
| `tasks/.../environment/app/{INCIDENT.md,README.md}` | incident note (numbers from section 4) and layout |
| `tasks/.../environment/app/data/` | visible extract, seed 1, 10 MB (dropped from the artifact at grading) |
| `tasks/.../tests/Dockerfile` | same base and pins, `COPY . /tests/`, uid 1001 `runner`, `/tests` 0700 |
| `tasks/.../tests/{test.sh,kit.py}` | the shared kit from `base/verifier_kit/` (with `stage_for_runner` and `SCRATCH`; `kit.py` unchanged since 2026-10-28 18:46 MST and `test.sh` since 18:52 MST, section 12), copied in by `tools/sync_kit.py`, never edited in the task |
| `tasks/.../tests/grade.py` | stages inputs, runs the CLI as uid 1001 three times, converts each output as uid 1001, checks A and B, records the container's CPUs, memory and network mode, writes the reward |
| `tasks/.../tests/{compare.py,convert.py,dataset_io.py,perturb.py}` | normalisation and comparison; the parquet-to-JSON converter run as uid 1001; CSV read/write; check B's perturbation |
| `tasks/.../tests/hidden/H/*.csv.gz`, `tests/expected/H_features.parquet`, `tests/SHA256SUMS` | hidden extract H (seed 2, gzip with fixed mtime), its reference features, checksums (grade.py verifies them first) |
| `tasks/.../solution/solve.sh` | canonical by default; `SOLUTION=alt`; `SOLUTION=<attempt>`; `APP_DIR` for local use |
| `tasks/.../solution/canonical/churn/` | the four fixed modules |
| `tasks/.../solution/alt/churn/build_features.py` | second valid solution (section 6) |
| `tasks/.../solution/attempts/*.py` | ten wrong or shortcut attempts (section 8) |
| `authoring/feature-leakage-churn/gen_data.py` | seeded generator (visible seed 1, hidden seed 2); `plant_boundary_ties` adds the boundary rows of section 3 to H only |
| `authoring/.../ref_vectorized.py`, `ref_loop.py` | the two independent references, both written from FEATURES.md |
| `authoring/.../make_expected.py` | regenerates data, cross-checks the references, prints the boundary counts of section 3 (events at t, at t - 7 and t - 30 days, label ties), writes expected output and SHA256SUMS |
| `authoring/.../calibrate_auc.py`, `timing.py`, `local_check.py` | AUC calibration, run-time measurements, local proof matrix |

Package size: 16 MB (FACT, `du -sh`, 19:19 MST after the review fixes). Image size: UNVERIFIED (not built on the Mac; the Daytona runs did not record it, section 13); INFERENCE:
the slim base plus about 300 MB of packages (pandas 45M, numpy 22M, pyarrow 125M, scikit-learn 32M, scipy 75M in the
Mac venv, `du -sh`). No torch.

## 3. Data
Synthetic, from `gen_data.py` (FACT, `make_expected.py` output): 3,000 customers who sign up 2024-01-01..2025-10-31;
weekly box charges at 06:00:00 UTC on each customer's billing weekday, add-ons at random times; support tickets;
status snapshots (on change and on the 1st of each month); a scoring point every second billing day at 06:00:00 (the
batch run) and 40% of tickets scored at their `opened_at` (the support desk); `app_minutes_7d` missing for 25% of rows
plus 7% of days (export outages); labels `churned_30d` landing at the cancellation (or `as_of` + 30 days) plus a 2-72 h
warehouse lag. Churners decline for 10-45 days before cancelling; everyone has temporary dips that recover, so the
honest signal is moderate. 60% of churners cancel on a billing day after the 06:00 charge, 70% with an `account`
ticket up to 2 h before (that is what makes the same-day window leak matter).

| Extract | customers | orders | tickets | snapshots | scoring points | labels | label rate |
|---|---|---|---|---|---|---|---|
| visible (seed 1) | 3,000 | 112,612 | 12,997 | 34,147 | 48,966 | 45,737 | 0.0885 |
| hidden H (seed 2) | 3,000 | 119,884 | 13,631 | 35,684 | 52,075 | 48,474 | 0.0776 |

**Planted boundary rows (H only; added for review finding 1, section 12).** The simulation never hits two of the edges
FEATURES.md states: weekly 06:00 box charges land exactly on `t - 7 days` of a 06:00 batch point but never on
`t - 30 days`, and label lags are random seconds, so no same-district label landed exactly at a scoring point. An
independent review showed that four wrong solutions scored 1 on the old H because of this (30-day windows open on the
left; the tickets window alone open on the left; the 30-day lower edge 1 s late; district counts with
`label_available_at <= t`). `gen_data.plant_boundary_ties` (seed `[2, 30]`, applied to the extract of H only) now adds,
for 300 scoring points each (sampled separately): an add-on order (499-2,999 cents, the generator's add-on range)
stamped exactly at `as_of - 30 days`; a ticket stamped exactly at `as_of - 30 days` (not itself scored); and it moves
the `label_available_at` of 300 `churned_30d = 0` label rows onto a same-district scoring point's `as_of`, inside the
generator's own lag band (`as_of + 30 days` + 2 h to 72 h). Every planted time is strictly after the customer's signup
and before the extract time; `order_id` and `ticket_id` are renumbered in time order as `simulate()` does; no scoring
point or label row is added or removed. The visible extract is not touched (FACT: the six visible CSV files have the
same SHA-256 before the change and after each regeneration, last checked 19:20 MST), so the incident numbers of
section 4 stand.

Boundary facts (FACT, `make_expected.py`, 2026-10-28 19:20 MST):

| Fact | visible | hidden H |
|---|---|---|
| events (orders + tickets) stamped exactly at a row's `as_of` (excluded; the design asked for at least 200) | 42,287 | 45,066 |
| orders exactly at `as_of - 7 days` (included) | 37,901 | 40,511 |
| orders / tickets exactly at `as_of - 30 days` (included) | 0 / 0 | 300 / 300 |
| rows with a same-district label landing exactly at `as_of` (not available) | 0 | 376 (383 row-label pairs) |
| rows with any label landing exactly at `as_of` (not in the prior) | 11 | 18,733 |
| rows with labels landing both before and after them | 48,936 of 48,966 | 51,933 of 52,075 |
| rows with no label landed yet (prior 0.05) | 30 | 141 |

Layout checks on the new H (FACT, ad-hoc checks on these bytes, not shipped, last run 19:20 MST): ticket-trigger points
4,821, all with a ticket at their `as_of`; orders and tickets at or before signup 0; order and ticket ids unique and in
time order; `churned_30d = 0` lag 2.0-72.0 h; add-on amounts 499-2,999. Regeneration is byte-identical (FACT:
`make_expected.py` run three times, the last at 19:20 MST, same `SHA256SUMS` each time).

## 4. AUC calibration (FACT, `calibrate_auc.py 1` and `2`)
Offline = trained on predictions before 2025-09-01, validated 2025-09-01..2025-11-30, both on the original features
(what `train.py` prints). Leak-free = the same on reference features. Live = the leaky model trained on everything
before 2025-12-01, scored on point-in-time features of January 2026 (simulated past the extract). INFERENCE: in
production only the past exists, so live features equal point-in-time features; the original's `bfill` would leave
gaps empty live instead of carrying them, an approximation not modelled.

| Seed | offline (leaky) | leak-free | live (Jan 2026) |
|---|---|---|---|
| 1 (visible; the incident's numbers) | 0.981 | 0.767 | 0.613 (3,151 rows) |
| 2 (hidden H, before the planted rows) | 0.986 | 0.788 | 0.509 (3,479 rows) |

The seed-2 row was measured before the boundary rows of section 3 were planted (`calibrate_auc.py` calls
`simulate` and `extract` directly) and was not re-measured: 600 added events and 300 moved label times out of about
182,000 rows (INFERENCE: too few to move these AUCs visibly; UNVERIFIED). Seed 1 is unchanged (same files).

Per leak, seed 1 (offline AUC): only this leak left in / only this leak fixed: windows 0.786 / 0.979; target encoding
0.831 / 0.981; status 0.977 / 0.860; imputation 0.799 / 0.979. The status leak dominates; fixing only it still leaves
0.860, so an agent that stops there still sees an inflated number. `train.py` itself (FACT): original 0.981; with
`--l2 50 --max-depth 2` still 0.981; after the canonical fix 0.767.

## 5. Verifier
`grade.py` (separate verifier, root, cwd `/tests`), following the kit's rules for graders (`base/verifier_kit/README.md`):
1. Verifies `SHA256SUMS`; `kit.prepare_submission()` copies the artifact to `/work/sub` for uid 1001.
2. Writes each extract (H unzipped, or a perturbed copy) into the root-only `kit.SCRATCH`, then gives uid 1001 its own
   copy with `kit.stage_for_runner`, plus an empty output folder. Root reads extracts only from `SCRATCH` (the
   perturbation starts from root's copy of H, never from the runner's).
3. Runs `python3 -m churn.build_features --data <dir> --out <file>` with `kit.run_as_runner` (cwd `/work/sub`, cap
   60 s); the kit kills every leftover uid-1001 process after each run. Agent code is never imported.
4. The agent's parquet is parsed only by `convert.py`, run as uid 1001 (`python3 -I`, cap 20 s, files over 100 MB
   refused); it normalises the table (`compare.normalise`) and writes JSON. Root reads that JSON with
   `kit.read_as_runner` and checks its shape and types (`compare.from_json`): root never deserializes the agent's file.
5. **Check A:** normalisation maps customer_id to int; `as_of` to UTC epoch seconds from any timestamp unit, aware or
   naive, or ISO strings (whole seconds required); numbers to float; every null form alike. Then one row per scoring
   point is required, and every value must equal `expected/H_features.parquet`: counts exactly, floats within
   1e-6 + 1e-9 x |expected|, status exact.
6. **Check B:** for cut1 = 2025-01-15T06:00:00Z (87 rows exactly at the cut, a batch time) and cut2 =
   2025-08-20T14:54:24Z (a ticket-scored row; 96 batch rows earlier that day), `perturb.py` (fixed seeds 101, 202)
   rewrites everything that becomes known at or after the cut (list in its docstring); the agent's output must have one
   row per new scoring point, and every row with `as_of <= cut` must equal the agent's own H output (same tolerances as
   A; the instruction now says so, a review fix: section 12, finding 4). Since the review, the perturbed extracts keep the
   extract's layout (section 12, finding 5): the 40 events placed exactly at the cut go only to customers who signed up
   before it, and every ticket-trigger point at or after the cut gets a ticket at its `as_of`. FACT (ad-hoc invariant
   check, not shipped, 19:20 MST, both cuts): keys unique, references intact, no order, ticket or point at or before its
   customer's signup, every ticket-trigger point (cut1 6,692, cut2 5,552) has its ticket, every label has its point,
   and every row known before the cut is unchanged.
7. Reward 1 only if A, B cut1 and B cut2 all pass; `reward.json` carries sub-metrics (`check_A`, `A_mismatch_<feature>`,
   `check_B_cut<n>`, `B_cut<n>_changed_cells`, `seconds_H`, `seconds_cut1`, `seconds_cut2`, `run_failed_*`,
   `bad_output_*`) and, since the review (section 12, finding 3), what the container has: `verifier_cpus_visible`
   (`sched_getaffinity`), `verifier_cpu_quota` (cgroup v2 `cpu.max` or v1 CFS quota), `verifier_memory_limit_mib`
   (cgroup `memory.max` / `memory.limit_in_bytes`), `verifier_memtotal_mib` (`/proc/meminfo`), and `net_private_<run>`
   (1 = the run had the kit's private loopback-only network, 0 = host network). They never change the verdict.

No service is started; agent runs get the kit's private loopback-only network where the kernel allows it (the first run
logs `network isolation: ON|OFF`; on Daytona it logged ON in all 32 graded trials, section 13). The instruction no
longer promises "without network access"; it says "Do not rely on network access", which is true either way. It still
says the grading container is set up with the agent's resources. The basis is Harbor's rule that a separate verifier
with no `[verifier.environment]` runs on a fresh copy of `[environment]`
(https://docs.harborframework.com/tasks/separate-verifier); the new metrics are the run-time proof (section 13:
`verifier_cpu_quota` 2.0 and `verifier_memory_limit_mib` 4096.0 in all 32 graded trials).

Sensitivity (FACT, ad-hoc check on the canonical output with `compare.py`): ISO-string `as_of`, string `customer_id`,
float counts, categorical status, shuffled rows and reversed columns: pass; `as_of` in America/Denver at ns: pass;
`te_district` + 5e-7: pass; + 2e-6: fail; one count + 1: fail; one duplicated row: fail.

## 6. References and the second solution
`ref_vectorized.py` (pandas `merge_asof` on cumulative integer counts) and `ref_loop.py` (csv, bisect, calendar; no
pandas) were each written from FEATURES.md. All arithmetic is integer counting and cent sums followed by one division
chain, so they can agree bit for bit. FACT (`make_expected.py`): they agree on all 48,966 visible and 52,075 hidden rows
with max float difference 0 (the design asked for 1e-9). The canonical fix (searchsorted on composite keys,
`merge_asof` for status, `ffill`) and the alt both match `expected/H_features.parquet` with 0 mismatched cells.

The alt (`SOLUTION=alt`) replaces `build_features.py` with a per-row implementation: no pandas, per-customer sorted
lists and `bisect` for windows and the last order, `sqlite3` as-of queries for status and the district counts, a plain
loop for gap filling, pyarrow output with naive microsecond `as_of`, int32 counts, alphabetical column order, rows in
descending time, and an extra `trigger` column. It scores 1 (section 8).

## 7. Timings and the caps (Mac; the Daytona timings are in section 13)
FACT (`timing.py`, 2026-10-28 18:43 MST: a fresh `python -m churn.build_features` process each time, on H, with the
grader's environment variables `kit.RUNNER_ENV`, which include `OMP_NUM_THREADS=1`; 5 runs):

| Program | runs (s) | median | max |
|---|---|---|---|
| canonical | 0.39, 0.36, 0.37, 0.37, 0.36 | 0.37 | 0.39 |
| alt (loop) | 1.52, 1.59, 1.58, 1.58, 1.58 | 1.58 | 1.59 |
| original | 0.59, 0.59, 0.58, 0.57, 0.57 | 0.58 | 0.59 |
| naive per-row pandas filtering (filter the full frames once per prediction) | 1.0 s for 600 rows | about 85 s for 52,075 (linear extrapolation) | |

Re-measured on the new H after the review fixes (FACT, `timing.py`, 19:17 MST, with other jobs running on the Mac:
`uptime` load average 6.2-7.0 just before and after):

| Program | runs (s) | median | max |
|---|---|---|---|
| canonical | 0.41, 0.40, 0.41, 0.41, 0.41 | 0.41 | 0.41 |
| alt (loop) | 1.91, 1.91, 1.76, 1.82, 1.83 | 1.83 | 1.91 |
| original | 0.68, 0.74, 0.92, 0.73, 0.90 | 0.74 | 0.92 |
| naive per-row pandas filtering | 1.6 s for 600 rows | about 143 s for 52,075 (linear extrapolation) | |

An earlier run without `OMP_NUM_THREADS=1` gave canonical 0.89 s and alt 2.00 s (thread-pool start-up on 10 cores).
Grading time outside the three CLI runs: about 2.8 s before the review (FACT, `local_check.py` at 18:42 MST: canonical
total 4.1 s minus runs 1.28 s; alt 7.2 s minus 4.51 s; this includes the three converter runs, about 0.4 s each).
After the fixes, on the loaded Mac (FACT, `local_check.py`): 6.9 s in the full matrix at 19:14 MST (canonical 9.9 s
minus runs 3.02 s; load average about 7-9), and 2.9-3.8 s in two canonical + alt runs at 19:17-19:18 MST (canonical
4.3 s minus 1.38 s and 5.0 s minus 1.65 s; alt 8.9 s minus 5.66 s and 10.1 s minus 6.32 s). A run over the cap is
stopped and scores 0, not `verifier_failed` (FACT: a copy of the canonical with `time.sleep(65)` gave
`rc=-9 timed_out=True 60.057s`, reward 0.0, `run_failed_H` 1, with the 18:39 kit).

**Per-run cap: 60 s (a deviation, see section 9).** The literal rule, 3 x the loop alt = 3 x 1.58 s = 4.7 s, was not
used. Checks for the 60 s value:
1. It is 38 x the Mac alt, so the alt stays under a third of the cap on a runner up to 12 x slower than the M4
   (INFERENCE, made before the Daytona runs; cold imports in a fresh sandbox add an unmeasured amount). On Daytona the
   alt took 2.18-2.425 s per run (section 13).
2. `verifier.timeout_sec` = (3 runs x 60 + 6.9) x 1.5 = 280.35, set to 281 s (it was 275 s from the 2.8 s figure; the
   worst grading time measured since, 6.9 s, is used); inside the design's 3-6 min band. Even the worst case with all
   three conversions at their 20 s cap, 180 + 60 + 6.9 = 246.9 s, stays under it.
   Grading returns right after a failed or over-cap H run, so three full caps happen only when H passes and both
   cut runs hit the cap. UNVERIFIED: the time `test.sh` spends before `grade.py` (its `find / -xdev -perm /6000` walk
   over the image, and Python start-up) was not measured, because `test.sh` does not run on the Mac; the 50% margin,
   about 93 s, is what covers it. On Daytona the whole Harbor verifier phase of a graded trial took at most 111.7 s and
   no trial ended `verifier_failed` (section 13); `test.sh`'s own share of that phase is still not measured.
3. It still bites: the naive per-row approach needs about 85 s on the Mac (143 s under load; more on a slower runner),
   and a per-row pandas solution written during the independent review hit the cap (`run_failed_H`, 60.5 s, reward 0),
   so the design's rule that "a run on a fresh extract must stay under the stated time limit" still means something.

**The Daytona proof run must read `seconds_H`, `seconds_cut1`, `seconds_cut2` of the alt from `reward.json`: if any
exceeds 20 s (cap / 3), raise `RUN_CAP_SEC` in `grade.py`, the sentence in `instruction.md` and `timeout_sec` in
`task.toml` together.** Met (section 13): the alt's runs took 2.425 s, 2.18 s and 2.381 s, so none of the three needed
a change.

## 8. LOCAL RESULTS (FACT)
Command, from the repository root: `.venv/bin/python authoring/feature-leakage-churn/local_check.py` (2026-10-28,
19:21:15 to 19:22:30 MST, after the review fixes: planted H, new `perturb.py`, two new attempts, resource metrics; kit
unchanged since 18:46, `tools/sync_kit.py` re-run at 19:19; the 19:14 run gave the same verdicts and cell counts). Each
row: fresh copy of `environment/app`, `solution/solve.sh` with that `SOLUTION` (none for `original`), the artifact
excludes applied, `tests/grade.py` in `KIT_LOCAL=1` mode with `GRADE_TESTS_DIR` = the task's `tests/`. "cells" =
mismatched feature cells; "B changed" = cells of rows at or before the cut that moved.

| Variant | Expected | Got | A | B cut1 | B cut2 | A cells | B changed (cut1 / cut2) | What kills it |
|---|---|---|---|---|---|---|---|---|
| canonical | 1 | 1 | 1 | 1 | 1 | 0 | 0 / 0 | - |
| alt | 1 | 1 | 1 | 1 | 1 | 0 | 0 / 0 | - |
| original (no-op) | 0 | 0 | 0 | 0 | 0 | 215,719 | 20,464 / 51,992 | A and B |
| zero_features | 0 | 0 | 0 | 1 | 1 | 378,892 | 0 / 0 | A only (B cannot see a constant: why A is needed) |
| drop_leaky | 0 | 0 | 0 | 0 | 0 | - | - | A: columns missing (`bad_output_H`) |
| cache_visible | 0 | 0 | 0 | 0 | 0 | 11,189 | 0 / 0 | A (wrong rows); B (row set) |
| loo_encoding | 0 | 0 | 0 | 0 | 0 | 52,073 | 13,498 / 35,906 | A and B (later labels still used) |
| closed_right | 0 | 0 | 0 | 0 | 1 | 94,717 | 125 / 0 | A; B at cut1 (events exactly at the cut) |
| tune_model | 0 | 0 | 0 | 0 | 0 | 215,719 | 20,464 / 51,992 | A and B (features untouched) |
| miss_imputation | 0 | 0 | 0 | 0 | 0 | 14,693 | 427 / 559 | A and B (the backward fill) |
| status_same_day | 0 | 0 | 0 | 0 | 0 | 2,190 | 3 / 4 | A and B (the snapshot dated date(t)) |
| open_left_30d (new) | 0 | 0 | 0 | 1 | 1 | 900 | 0 / 0 | A only: the 300 orders and 300 tickets planted at `t - 30 days` (orders_30d, spend_30d_cents, tickets_30d 300 cells each) |
| label_at_t (new) | 0 | 0 | 0 | 1 | 1 | 376 | 0 / 0 | A only: te_district on the 376 rows with a same-district label landing exactly at t |

Run seconds per variant were 0.40-1.09 s (2.02-2.80 s for the alt) on the loaded Mac. Also FACT: `tests/SHA256SUMS`
ok; `python tools/sync_kit.py` then `.venv/bin/python tools/check_task.py tasks/feature-leakage-churn` prints
`OK feature-leakage-churn` (this runs `harbor lint`; section 12 has the final run).

The four boundary mutants from the independent review, re-run as single edits of the canonical against the new H (FACT,
an ad-hoc script `mutants.py` using `local_check`'s helpers and `tests/grade.py` in KIT_LOCAL mode, run between 19:16
and 19:17 MST; not shipped):

| Mutant (one edit on the canonical) | Before the fix | Now | A cells |
|---|---|---|---|
| 30-day windows open on the left (orders_30d, spend_30d_cents, tickets_30d) | 1 | 0 | 900 |
| tickets window alone open on the left | 1 | 0 | 300 |
| orders 30-day lower edge 1 s late | 1 | 0 | 600 |
| district counts with `label_available_at <= t` | 1 | 0 | 376 |
| control: prior with `label_available_at <= t` | 0 (8 cells) | 0 | 8,934 |
| control: 7-day lower edge open | 0 | 0 | 40,511 |

Why B passes the two new attempts: check B compares an output with itself under a changed future; a wrong rule that
uses only the past (an edge one second off, a tie counted) is consistent with itself, so only A sees it. That is the
designed split (zero_features shows the same).

## 9. Deviations from the original design, with reasons
1. **Per-run cap 60 s, not 3 x the loop alt (4.7 s).** With a 1.58 s alt on an M4, 4.7 s would make the alt (the G25
   proof) and possibly the canonical depend on the unmeasured speed of a fresh Daytona sandbox: "a verifier that depends
   on timing" is G16's own failure example, and under our gate a FAIL blocks the task. The design's formula means the
   runner-measured slowest valid solution; the Mac is not the runner, and the design's "verifier 3-6 min" only fits a
   cap in the tens of seconds. Derivation and the proof-run condition: section 7. The gate record's result line flags
   this deviation (section 10).
2. **Ten attempts, not six:** the design's six plus `miss_imputation` (three of four leaks fixed) and
   `status_same_day` (a natural wrong fix of the status join), both plausible half-fixes; and, after the review,
   `open_left_30d` (30-day windows open on the left) and `label_at_t` (district counts with `label_available_at <= t`),
   two plausible boundary errors the old H could not see.
3. **Amounts in integer cents and an integer `spend_30d_cents` feature**, so the two references agree exactly.
4. **Check B's two perturbed extracts are generated at grade time** (deterministic, fixed seeds, pinned numpy/pandas)
   instead of committed: committing them would triple the hidden data. H itself and its expected output are committed.
5. **Spec details added to FEATURES.md** (improvements, same problem): the end-of-day meaning of a snapshot date and
   one snapshot per customer and date; `(customer_id, as_of)` unique; whole-second UTC timestamps; "in days" =
   seconds / 86,400; the prior p = 0.05 when no label has landed; the event at exactly t excluded, with the 06:00
   billing-run example.
6. **Visible data is 10 MB, not about 15 MB** (3,000 customers as designed; the compact schema is smaller).
7. **Calibrated incident numbers 0.981 / 0.613** replace the placeholder 0.96 / 0.71 (they are what the data gives).
8. Image: about 450 MB (INFERENCE, section 2), inside the design's 450-700 MB guess.
9. **H carries planted boundary rows the visible extract does not** (section 3): 300 orders and 300 tickets at exactly
   `as_of - 30 days` and 300 label times moved onto same-district scoring points. Reason: without them three stated
   edges were never tested (review finding 1, section 12). They are ordinary rows of the same layout; the design's
   "same size as the visible set" holds within 6.5% per table (FACT, section 3 counts: scoring points 52,075 / 48,966 =
   +6.35%, orders 119,884 / 112,612 = +6.5%, labels +6.0%, tickets +4.9%, snapshots +4.5%); the instruction now says
   "about the same size". The visible extract stays as it was so the calibrated incident numbers stand.
10. **`verifier.timeout_sec` 281 s** (was 275 s): the same formula with the worst grading time measured since (6.9 s on
    the loaded Mac, section 7).

## 10. Gate record (implementation, after the review fixes)
Scored against the checks G1-G30 of `docs/QUALITY_GATE.md`.
```
Gate record: feature-leakage-churn implementation (2026-10-28, re-scored 19:24 MST after the independent review; the (run) items re-scored 2026-10-29 from the recorded Daytona runs, section 13; paths from the repository root)
Applies to: task feature-leakage-churn
G1  PASS - code, spec, visible and hidden data, pinned packages all in the package; grading needs no network
G2  PASS - honest offline validation decides whether a churn model ships; the fixed pipeline restores it
G3  PASS - six-table warehouse extract, multi-module pipeline, spec, training script, incident note
G4  PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1.md and PROOF_RESULTS_full1b.md) - script-only verdict: values vs reference (A) and a causality test (B); local matrix as expected (13 of 13); on Daytona every row as expected except one full1 oracle trial lost to the Mac's DNS with no reward (validation/feature-leakage-churn/NOTES.md), re-run clean in full1b
G5  PASS - the only leakage / point-in-time task of the five
G6  PASS - two references written separately agree bit for bit on both extracts, now including the planted edges; check B needs no reference
G7  PASS - offline/online AUC gaps from leaky features are everyday ML engineering
G8  PASS (run, recorded for the resources part: verifier/reward.json of the 32 graded trials, raw Harbor output under the git-ignored jobs/; one trial per variant is shipped in validation/feature-leakage-churn/traces/) - FEATURES.md defines every feature, boundary, null and constant; the instruction states CLI, schema, accepted dtypes, tolerances (now also for check B), check B, the 60 s limit, keep all features; it no longer promises "without network access" ("do not rely on network access"); the resources sentence rests on Harbor's separate-verifier rule (section 5), and reward.json shows verifier_cpu_quota 2.0 and verifier_memory_limit_mib 4096.0 in every trial (the task's 2 vCPU and 4096 MB); verifier_cpus_visible 48 and verifier_memtotal_mib about 386,464 look host-wide (INFERENCE, section 13)
G9  PASS - the four leaks are textbook kinds (same-day aggregates, target encoding on all labels, latest-snapshot join, backward fill)
G10 PASS - a fixed pipeline whose output can train a trustworthy model (train.py: 0.981 -> 0.767)
G11 PASS - black-box CLI runs; only output values are checked
G12 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1.md) - ten attempts all 0 locally and on Daytona, each failing the same checks with the same A cell counts in both (sections 8 and 13); the four boundary mutants that scored 1 on the old H now score 0 (local only, not run on Daytona)
G13 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1.md) - alt with different algorithms, dtypes, row and column order and an extra column = 1 locally and 1.0 on Daytona; format variants accepted locally (section 5)
G14 PASS - difficulty is finding four leak kinds in four files and matching an exact spec (status fixed alone still leaves AUC 0.860); the "hard" label is an author estimate until agent trials (section 11)
G15 PASS - every rule stated, and every stated edge (t, t - 7 days, t - 30 days, a label landing at t) is now exercised by H; tolerance covers summation order; 60 s cap is 33 x the Mac alt under load; no fragile formatting
G16 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1b.md and PROOF_RESULTS_full1.md) - committed data + sha256, byte-identical regeneration (three runs), seeded perturbation, pinned image; verifier timeout 281 s from the worst measured grading time; on Daytona the oracle scored 1.0 in all 19 trials that returned a reward (full1 9, full1b 10) and with --force-build; runs took 0.471-0.527 s (canonical) and 2.18-2.425 s (alt), under the section 7 condition of 20 s
G17 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1.md) - tests/ only in the verifier image (/tests 0700); environment Dockerfile copies app/ only; agent code and the parquet parsing run as uid 1001; root reads only /tests, SCRATCH, /proc, /sys and JSON; on Daytona the separate verifier ran in 33 of 33 trials, with lock ok and a private loopback network (net_private_* = 1) in all 32 graded ones
G18 PASS - layout complete; check_task.py OK, harbor lint clean (section 12)
G19 PASS - own copy of the kit and helpers; no other task needed
G20 PASS (plan) - this task's row is in the top-level README.md
G21 PASS (plan) - limitations in section 11
G22 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1b.md) - canonical = 1 locally; Daytona oracle 10 of 10 = 1.0 in full1b (full1: nine trials 1.0, one lost to the Mac's DNS with no reward, validation/feature-leakage-churn/NOTES.md); --force-build 1.0
G23 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1.md) - original (no-op) = 0 locally and nop 0.0 on Daytona (fails A and B)
G24 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1.md) - ten attempts = 0 locally and 0.0 on Daytona, two of them boundary errors (open_left_30d, label_at_t)
G25 PASS (run, recorded: validation/feature-leakage-churn/PROOF_RESULTS_full1.md) - alt = 1 locally and 1.0 on Daytona, on the planted edges too
G26 PASS (plan) - grade.py, compare.py, perturb.py are short and commented; reward.json sub-metrics and kit log explain each verdict
G27 PASS (plan) - CPU only, no keys, no network
G28 PASS - a failure means a missed leak or a wrong boundary, both stated in FEATURES.md
G29 PASS - every check is a FEATURES.md sentence or the request's own time limit; the planted rows test stated edges only (no trap beyond the spec)
G30 PASS (plan) - the delivery is this GitHub repository; the author adds the reviewer named in the brief
Result: PASS, no FAIL and nothing BLOCKED. One deviation to note: the per-run cap is 60 s, not the literal
3 x loop alt (4.7 s), because the literal value would fail G16 (section 9 item 1); on Daytona the alt took 2.18-2.425 s
per run. G4, G8 (resources), G12, G13, G16, G17 and G22-G25 are proven by the recorded Daytona runs of 2026-10-28
(section 13).
```

## 11. Known limitations and open issues
- Before the Daytona runs, build time and image size, the kit's root-only steps (demotion to uid 1001, chown, the
  network namespace, the lock) and run speed were UNVERIFIED. The runs of section 13 recorded run speeds and, in all 32
  graded trials, the kit's log lines `[kit] network isolation: ON`, `[test.sh] lock ok` with `setid files left: 0`, and
  `killed 0 runner processes`. Still not measured: the image size and the build time.
- Synthetic data; the live AUC is simulated with point-in-time features (section 4). The seed-2 AUC row predates the
  planted rows (section 4).
- The status leak dominates the AUC gap; the other three are smaller but each still moves AUC (section 4).
- The instruction says how check B works; that is required by G8 and it does not reveal where the leaks are.
- Hidden inputs are readable by agent code while it runs in the verifier (they must be, to be processed); an earlier
  Daytona infrastructure pilot found the verifier has internet (noted at the top of `base/verifier_kit/kit.py`), so
  agent code could copy them out. It cannot change the current score (expected values stay in `/tests`, 0700). In the
  Daytona runs, `net_private_H`, `net_private_cut1` and `net_private_cut2` were 1 wherever recorded (section 13).
- `solve.sh` rebuilds `/app/output/features.parquet` for the canonical and the alt (a smoke test); the artifact keeps
  that file (about 1.3 MB per oracle trial). The attempts skip it.
- `test.sh` setup time on Daytona is not measured on its own (section 7); the whole Harbor verifier phase of the graded
  trials took 11.3-111.7 s and no trial ended `verifier_failed` (section 13). If the oracle ever ends
  `verifier_failed`, raise `timeout_sec` first.
- A valid but naive per-row implementation (about 85 s on the Mac, 143 s under load) fails the stated 60 s limit; the
  instruction tells the agent to time a run on `/app/data`, which is about the same size.
- `difficulty = "hard"` is the author's estimate (review finding 7, section 12): FEATURES.md states every rule and each
  leak is a short edit, so frontier agents may pass often. Set it from the measured pass rate of agent trials on
  Daytona (and say so in the README); no agent trials have been run (section 13). A high pass rate is not a defect
  (G29).
- Planted rows are in H only; the visible extract has no order or ticket at `t - 30 days` and no same-district label
  landing at a scoring point, so an agent cannot see those edges matter by running on `/app/data`. The spec states
  them; this is the same situation as any hidden test (INFERENCE).

## 12. Review history (2026-10-28)
An independent review of the first build raised seven findings. We checked each one before acting.

| # | Finding | Checked | Action |
|---|---|---|---|
| 1, 2 | Four wrong solutions score 1: H has no order or ticket at `t - 30 days` and no same-district label landing at a scoring point | Confirmed (FACT, ad-hoc count on the old H: orders at t-30d 0, tickets at t-7d / t-30d 0, same-district label ties 0, any-district 11) | Applied: `plant_boundary_ties` (section 3), expected and SHA256SUMS regenerated, two new attempts (section 8); all four mutants now 0 |
| 3 | Instruction promises no network, equal resources, "different customers", "same size" | Partly confirmed: network isolation was UNVERIFIED on Daytona at the time (section 13 now records it); customer ids overlap (both 100001-103000, FACT `gen_data.py`); sizes differ by up to 6.5% per table (section 9 item 9). Rejected in part: the equal-resources sentence has a documented basis (Harbor's separate-verifier rule, section 5), it is not unsupported | Applied: reworded to "Do not rely on network access", "about the same size, but different data", "is set up with the same resources"; grade.py now records CPUs, memory and the network mode |
| 4 | Check B says "exactly" but uses A's tolerance | Confirmed (grade.py calls `C.compare` with ABS_TOL / REL_TOL) | Applied: instruction says "within the tolerances above"; the grader keeps the tolerance (a stricter grader would only add a fragile edge, G15) |
| 5 | Perturbed extracts break the layout (ticket points without tickets; events before signup) | Confirmed by the invariant check before the fix | Applied in `perturb.py`; invariants now hold for both cuts (section 5) |
| 6 | 60 s cap instead of 4.7 s | Agreed with the reviewer | No change; verifier timeout raised to 281 s from a newer grading-time measurement (section 7) |
| 7 | `difficulty = "hard"` has no evidence | Agreed it is unproven; not a gate failure | No value change; marked as an author estimate in `task.toml` and section 11 |

Final checks (FACT, 2026-10-28): `python tools/sync_kit.py` (19:19 MST, all five tasks synced; kit files unchanged
since 18:46 / 18:52) then `.venv/bin/python tools/check_task.py tasks/feature-leakage-churn` prints
`OK feature-leakage-churn`; the full local matrix (section 8) is 13 of 13 as expected.

What we required the Daytona proof run to show for this task (section 13 reports each item):
- oracle x 10 = 1, alt = 1, nop = 0, each of the ten attempts = 0, one `--force-build` oracle = 1;
- in the alt's `reward.json`: `seconds_H`, `seconds_cut1`, `seconds_cut2` each under 20 s (else raise `RUN_CAP_SEC`,
  the instruction sentence and `timeout_sec` together);
- in the oracle's: `verifier_cpus_visible` / `verifier_cpu_quota` about 2 and `verifier_memory_limit_mib` /
  `verifier_memtotal_mib` about 4,096 (else reword the resources sentence), `net_private_H` (record it), and the
  verifier phase duration from `result.json` (if any trial ends `verifier_failed`, raise `timeout_sec` first);
- in `verifier/test-stdout.txt`: the kit lines listed in `base/verifier_kit/README.md` ("What the Daytona proof run must
  show").

## 13. Daytona proof results (2026-10-28)
FACT: `validation/feature-leakage-churn/PROOF_RESULTS_full1.md` and `PROOF_RESULTS_full1b.md` (the same rows are in
`proof_results_full1.json`, `proof_results_full1b.json`, `run_full1.log` and `run_full1b.log` in that folder) and
`validation/feature-leakage-churn/NOTES.md`. Harbor 0.25.0 (`harbor.version` in the `lock.json` of all 15 job
folders); runner Daytona (`environment.type` "daytona" in each job's `config.json`; Daytona Tier 1), one trial at a
time (`n_concurrent_trials` 1); `verifier_environment_mode` "separate" in 33 of 33 trial `result.json` files. Job
folders: `jobs/feature-leakage-churn/feature-leakage-churn-<variant>-full1/` and
`jobs/feature-leakage-churn/feature-leakage-churn-canonical-full1b/` (last column below). `jobs/` is the raw Harbor
output and is git-ignored, so it is not in the repository; one trial per variant is copied to
`validation/feature-leakage-churn/traces/` (see `validation/feature-leakage-churn/README.md`). Run full1 ran from
19:57:07 to 20:56:42 MST and full1b from 20:57:25 to 21:05:48 MST on 2026-10-28 (job `result.json`, Mac clock). The
tables are copied from the two files:

Run full1. Overall: NOT ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, None, 1.0, 1.0, 1.0, 1.0] | ['DaytonaConnectionError'] | FAIL | `jobs/feature-leakage-churn/feature-leakage-churn-canonical-full1` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-alt-full1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-nop-full1` |
| cache_visible | `-a oracle --ae SOLUTION=cache_visible` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-cache_visible-full1` |
| closed_right | `-a oracle --ae SOLUTION=closed_right` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-closed_right-full1` |
| drop_leaky | `-a oracle --ae SOLUTION=drop_leaky` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-drop_leaky-full1` |
| label_at_t | `-a oracle --ae SOLUTION=label_at_t` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-label_at_t-full1` |
| loo_encoding | `-a oracle --ae SOLUTION=loo_encoding` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-loo_encoding-full1` |
| miss_imputation | `-a oracle --ae SOLUTION=miss_imputation` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-miss_imputation-full1` |
| open_left_30d | `-a oracle --ae SOLUTION=open_left_30d` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-open_left_30d-full1` |
| status_same_day | `-a oracle --ae SOLUTION=status_same_day` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-status_same_day-full1` |
| tune_model | `-a oracle --ae SOLUTION=tune_model` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-tune_model-full1` |
| zero_features | `-a oracle --ae SOLUTION=zero_features` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-zero_features-full1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-force-build-full1` |

Run full1b. Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-canonical-full1b` |

The one FAIL row of full1 is not a task verdict (`validation/feature-leakage-churn/NOTES.md`): trial
`feature-leakage-churn__dtTSGvN` ended with `DaytonaConnectionError` and no reward; its `exception.txt` (shipped in
`validation/feature-leakage-churn/traces/canonical_full1_lost/`) shows `socket.gaierror: [Errno 8] nodename nor servname
provided, or not known`, so the Mac running Harbor had lost DNS while polling the verifier. Its Harbor verifier phase
spans 2,636 s in `result.json`, the time the client could not reach Daytona, not grading time. The other nine full1
canonical trials scored 1.0, and full1b re-ran the ten canonical trials for a clean record: 10 of 10 = 1.0.

What section 12 asked the run to show (FACT: the 32 graded trials' `verifier/reward.json`, `verifier/test-stdout.txt`
and `result.json`):
- Alt: `seconds_H` 2.425 s, `seconds_cut1` 2.18 s, `seconds_cut2` 2.381 s, each under the 20 s trigger (cap / 3) of
  section 7, so `RUN_CAP_SEC`, the instruction sentence and `timeout_sec` need no change.
- Resources, in all 32: `verifier_cpu_quota` 2.0 and `verifier_memory_limit_mib` 4096.0, the task's 2 vCPU and
  4096 MB; `verifier_cpus_visible` 48 and `verifier_memtotal_mib` 386,464.3 (386,459.6 in one trial). Section 12 named
  both pairs. INFERENCE: the second pair is what `sched_getaffinity` and `/proc/meminfo` see of the host, while the
  cgroup limits are the task's. Whether the resources sentence needs other wording is left open; it is unchanged in
  `tasks/feature-leakage-churn/instruction.md` (line 26).
- `net_private_H`, `net_private_cut1` and `net_private_cut2` = 1 wherever recorded; `[kit] network isolation: ON`,
  `[test.sh] lock ok` with `setid files left: 0`, and `killed 0 runner processes` in 32 of 32 test-stdout files.
- No trial ended `verifier_failed`; the only exception is the DNS-lost trial above.
- Each attempt's `A_mismatched_cells` and its check A / B cut1 / B cut2 pattern equal the local matrix of section 8 (for
  example `open_left_30d` 900 cells and `label_at_t` 376, both failing A only; `closed_right` 94,717, failing A and B
  cut1; `zero_features` 378,892, A only; `drop_leaky` stops after a bad H output, so only `seconds_H` is recorded). This
  task's `solve.sh` prints no `applied <variant>` line; these equal counts are the evidence that each `SOLUTION`
  reached it.

Timings the runs recorded (FACT: `seconds_H`, `seconds_cut1`, `seconds_cut2` from `verifier/reward.json`; the Harbor
verifier phase from `verifier.started_at` to `verifier.finished_at` in each trial's `result.json`):

| Rows | `seconds_H` | `seconds_cut1` | `seconds_cut2` | Harbor verifier phase |
|---|---|---|---|---|
| canonical (19 graded trials: full1 9, full1b 10) | 0.471-0.476 s | 0.474-0.480 s | 0.475-0.527 s | 15.4-111.7 s |
| alt | 2.425 s | 2.18 s | 2.381 s | 20.9 s |
| force-build | 0.475 s | 0.478 s | 0.476 s | 17.6 s |
| nop and ten attempts | 0.375-0.874 s | 0.327-0.928 s | 0.380-0.931 s | 11.3-19.0 s |

Reading: on Daytona the canonical took 0.47-0.53 s per run and the alt 2.18-2.43 s (section 7 measured medians of 0.41 s
and 1.83 s on the loaded Mac), so the 60 s cap is about 25 x the slowest valid run. The slowest graded Harbor verifier
phase, 111.7 s, is under `verifier.timeout_sec` 281 s; whether that timeout covers the whole phase or only `test.sh` is
UNVERIFIED, and if it covers the whole phase that trial used 40% of it. Not exercised by these runs: the boundary
mutants from the review (local only, section 8), agent trials (the "hard" label stays an author estimate, section 11),
and the image size and build time.

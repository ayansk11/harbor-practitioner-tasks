# Validation: feature-leakage-churn

Last updated: 2026-10-31, 23:03 MST (Mac clock): fixes after a pre-commit check: the blind read's two hints, and Daytona
Tier 2 marked as not tried. Before that, 2026-10-31, 22:05 MST (Mac clock): fixes after an independent check (the
wording of the trajectory scan in section "Agent trials", and why task v2 was hardened, as the design record gives it).
Before that, 21:03 MST: rewritten for task v3, the shipped package (the Daytona proof `v3`, three Claude Code trials,
task v2's evidence in `second-version/` and the first version's in `first-version/`). Before that, 2026-10-29 (Mac
clock, MST): the first version's proof runs `full1` and `full1b`.

This task has had three versions. The first is the package of the repository's commits `79286dc` and `495c9f5`
(section "First version"). Task v2, a revision built on 2026-10-30 and 2026-10-31 and proven on 2026-10-31, was never
committed or pushed (section "Task v2"). Task v3 is the package in `tasks/feature-leakage-churn/`; everything above
the section "Task v2" is about it.

**Final run: `v3`.** Harbor 0.25.0 on Daytona, 2026-10-31 from 19:12:31 to 19:31:31 (Mac clock, MST; the first row's
`started` in `proof_results_v3.json`, and the time the run's three files were written; in the shipped traces, the
canonical job's `started_at` is 19:12:32 and the force-build job's `finished_at` 19:31:28, each in
`job_result.json`). Overall: ALL AS EXPECTED, 27 variants and 31 trials (`PROOF_RESULTS_v3.md`).

The proof ran a copy of the package without its `[agent] network_mode = "no-network"` line, made by
`tools/proof_matrix.py --without-agent-network-line`. The shipped `task.toml` denies the agent network, and Daytona
Tier 1 (the authors' account) refuses Harbor's runtime network switch for the agent phase, so a trial of the shipped
package is expected to fail there (INFERENCE from the network canary of 2026-10-30 and Harbor's code; the comment
above the line in `task.toml`, and the limitations in the design record, `../../docs/feature-leakage-churn/DESIGN.md`).
The copy differs from the shipped package in that one line only: `diff -rq` of the two lists `task.toml` only, whose
diff is the missing line, and both have the same 81 files. Their Harbor 0.25.0 content hashes differ only because
`task.toml` differs (shipped package `sha256:274a6896d00585702123292d2377480bab7ec0829da8594f2c9502e486700091`; proof
copy `sha256:b042a2c9540522bfbb76e91c81eae76b77d9f8f34df7d550a8314a25b24c0de5`, the digest in each trace's
`job_lock.json`).

## Files in this folder

- `PROOF_RESULTS_v3.md`, `proof_results_v3.json`, `run_v3.log`: the proof matrix of run `v3`, written by
  `tools/proof_matrix.py` (`run_v3.log` is its console output).
- `traces/<variant>/`: one Harbor trial per variant of run `v3` (table below).
- `traces/agent-claude-code/<trial>/`: the three Claude Code trials of task v3 (section "Agent trials").
- `second-version/`: the evidence of task v2 (section "Task v2").
- `first-version/`: the evidence of the first version (section "First version").

Each traces folder carries a `REDACTIONS.md` that lists what was replaced in its copies; no reward, count or timing
was changed. The "Job folder" column of `PROOF_RESULTS_v3.md` points into `jobs/`, the raw Harbor output, which is
git-ignored and not part of the repository; the trace folders are the shipped copy.

## Results and traces (run `v3`)

One trial per variant is shipped. For canonical (five trials) the shipped trial is the one with the earliest
`started_at` in its `result.json`; its `job_result.json` holds the rewards of all five.

The grader (`tests/grade.py`) runs the agent's command three times. Check A runs it on the hidden extract H
(`tests/hidden/H/`, another brand, 57,896 scoring points) and compares every value of the ten kept features with
`tests/expected/H_features.parquet`; a `days_since_last_login` column, if present, must be all null. Checks B cut1 and
B cut2 change H in everything the warehouse did not yet hold at a cut time (2024-11-27T06:00:00Z and
2025-11-14T08:13:16Z) and run it again; every row with `as_of` at or before the cut (9,451 and 45,706 rows) must keep
its values from the run on H. The reward is 1 only if all three pass. The last column is read from the shipped
trial's `verifier/reward.json` and, for why a check failed, its `verifier/test-stdout.txt`: `A_mismatched_cells` counts
the values of check A that differ (per feature in `A_mismatch_<feature>`), and "B changed cells" the values that moved
between the run on H and the run on each changed copy (`B_cut1_changed_cells` / `B_cut2_changed_cells`). "The order
features" are `orders_7d`, `orders_30d`, `spend_30d_cents` and `days_since_last_order`. "The shipped pipeline" is the
code in `environment/app/churn/` as the agent receives it.

| Variant | What it is | Expected | Rewards (all trials of the job) | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|
| canonical | the reference fix (`solution/canonical/`, pandas and numpy): each feature from the rows the warehouse held at `as_of`; an order below the last legacy watermark visible from the commit of the committed `legacy_orders` range that holds it, any later order from the later of its `_loaded_at` and the rename's commit (both from `_ops/`); the plan rebuilt from `plan_changes`; `days_since_last_login` left out | 1 | 5 of 5 = 1.0 | [`traces/canonical/`](traces/canonical/) | `feature-leakage-churn__57KkDQi` | check A 1, B cut1 1, B cut2 1; `A_mismatched_cells` 0, B changed cells 0 / 0 |
| alt | a different valid route (`solution/alt/`, the standard library and pyarrow, no pandas or numpy): every committed transaction of `_ops/` replayed in time order into tables and table names, each prediction reading the table named `orders` at its moment; no order's `_loaded_at` or `_load_job` read | 1 | 1.0 | [`traces/alt/`](traces/alt/) | `feature-leakage-churn__bZ7F35J` | check A 1, B cut1 1, B cut2 1; `A_mismatched_cells` 0, B changed cells 0 / 0 |
| nop | Harbor's nop agent: the shipped pipeline | 0 | 0.0 | [`traces/nop/`](traces/nop/) | `feature-leakage-churn__WfQpBUs` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 256915 (`te_district` 57833, `plan` 19228, `status` 484, the order features 44826 to 44848 each); B changed cells 4005 / 8933; `days_since_last_login` non-null on 1898 rows of H |
| backfill_event_time | an order the legacy table held taken as visible from its `ordered_at`; the times of the legacy commits in `_ops/` not used | 0 | 0.0 | [`traces/backfill_event_time/`](traces/backfill_event_time/) | `feature-leakage-churn__8NfjLuZ` | check A 0, B cut1 0, B cut2 1; `A_mismatched_cells` 68098 (`orders_7d` 17008, each other order feature 17030); B changed cells 790 / 0 |
| cache_in_work | a probe of the grader's independence between runs: the canonical solution, which on an extract of 3,000 customers (H) also writes its output to a cache file in each writable place it tries, and on any other extract uses a cache file if it finds one (the cached row for every prediction the cache holds) and otherwise adds 1 to `orders_7d` on every row | 0 | 0.0 | [`traces/cache_in_work/`](traces/cache_in_work/) | `feature-leakage-churn__FK7TKJn` | check A 1, B cut1 0, B cut2 0; `A_mismatched_cells` 0; B changed cells 9451 / 45706, all in `orders_7d`; runner paths swept 1 / 8 / 5, none left |
| cache_visible | a shortcut: the right features for the visible extract, computed once, returned for any input | 0 | 0.0 | [`traces/cache_visible/`](traces/cache_visible/) | `feature-leakage-churn__oQATY5u` | check A 0, B cut1 0, B cut2 0; `A_missing_rows` 57896 and `A_extra_rows` 57909 (the visible extract's rows in place of H's), and the same kind of key failure on both copies |
| clip_last_login | keeps `days_since_last_login` with the shipped pipeline's clip (t minus the record's current `last_login_at`), though the extract keeps no history of that column | 0 | 0.0 | [`traces/clip_last_login/`](traces/clip_last_login/) | `feature-leakage-churn__9GTyiwB` | check A 0, B cut1 0, B cut2 0; every compared value right (`A_mismatched_cells` 0, B changed cells 0 / 0), but `days_since_last_login` non-null on 1898 rows of H (23300 and 6063 on the copies), so each check fails |
| current_plan | the plan as the customer record holds it now (`customers.plan`); `plan_changes` not read | 0 | 0.0 | [`traces/current_plan/`](traces/current_plan/) | `feature-leakage-churn__8RtLiGG` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 19228 (`plan`); B changed cells 3063 / 8923 |
| drop_plan | leaves out `plan` as well as `days_since_last_login`, though `plan_changes` determines it for every prediction | 0 | 0.0 | [`traces/drop_plan/`](traces/drop_plan/) | `feature-leakage-churn__7vhhJvH` | check A 0, B cut1 0, B cut2 0; `bad_output_H` 1: the output on H was rejected (missing column `plan`), so grading stopped after that run |
| hourly_schedule | an order at or above the last legacy watermark taken as visible at the hourly loader's schedule, the first :20 after the top of the hour that follows `ordered_at`; its `_loaded_at` and the rename's commit not read | 0 | 0.0 | [`traces/hourly_schedule/`](traces/hourly_schedule/) | `feature-leakage-churn__SvXayAS` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 12 (3 in each order feature) |
| labels_matured | `te_district` from the shipped pipeline's label rule (the labels whose 30-day window closed before t), not from the label rows loaded before t | 0 | 0.0 | [`traces/labels_matured/`](traces/labels_matured/) | `feature-leakage-churn__44oP7M2` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 57833 (`te_district`); B changed cells 152 / 2 |
| last_login_where_known | keeps `days_since_last_login` where the record has not changed since t, null elsewhere | 0 | 0.0 | [`traces/last_login_where_known/`](traces/last_login_where_known/) | `feature-leakage-churn__jAGuQo3` | check A 0, B cut1 0, B cut2 0; every compared value right, but `days_since_last_login` non-null on 1212 rows of H (3407 and 1493 on the copies) |
| legacy_schedule | an order below the last legacy watermark taken as visible at the nightly job's usual start, 02:30 on the night after `ordered_at`; the times and outcomes of the legacy commits not used | 0 | 0.0 | [`traces/legacy_schedule/`](traces/legacy_schedule/) | `feature-leakage-churn__H96thiF` | check A 0, B cut1 0, B cut2 1; `A_mismatched_cells` 1522 (`orders_7d` 253, each other order feature 423); B changed cells 214 / 0 (`spend_30d_cents`) |
| loaded_at_everywhere | `_loaded_at` trusted in every table, the orders included, so the backfill's and the dual run's commits into `orders_new` count as visibility | 0 | 0.0 | [`traces/loaded_at_everywhere/`](traces/loaded_at_everywhere/) | `feature-leakage-churn__sFghHHm` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 53362 (`orders_7d` 4345, `orders_30d` and `spend_30d_cents` 16318 each, `days_since_last_order` 16381) |
| log_lookup | a shortcut: the shipped pipeline with the live service's logged values (the sample in `logs/`) copied into the rows that match a logged request; no rule fixed | 0 | 0.0 | [`traces/log_lookup/`](traces/log_lookup/) | `feature-leakage-churn__W9eGHMb` | check A 0, B cut1 0, B cut2 0; the counts of nop (`A_mismatched_cells` 256915, B changed cells 4005 / 8933, `days_since_last_login` non-null on 1898 rows of H) |
| min_commit | an order visible from the earlier of its `_loaded_at` and the commit of the committed legacy range that holds it; the rename not read | 0 | 0.0 | [`traces/min_commit/`](traces/min_commit/) | `feature-leakage-churn__omNmUA7` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 492 (123 in each order feature) |
| plan_changed_at | the plan rebuilt from `plan_changes` by `changed_at`, not by the `crm_sync` that applied each change (`_loaded_at`) | 0 | 0.0 | [`traces/plan_changed_at/`](traces/plan_changed_at/) | `feature-leakage-churn__aAVwM7z` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 518 (`plan`); B changed cells 112 / 291 |
| rollback_as_commit | every `legacy_orders` transaction taken as committed, the rolled-back ones included (the `outcome` in `_ops/commits.jsonl` not read) | 0 | 0.0 | [`traces/rollback_as_commit/`](traces/rollback_as_commit/) | `feature-leakage-churn__uQsijxD` | check A 0, B cut1 0, B cut2 1; `A_mismatched_cells` 1381 (`orders_7d` 217, each other order feature 388); B changed cells 214 / 0 (`spend_30d_cents`) |
| scheduler_end | a committed legacy range taken as visible at the end of its task (the scheduler's `state=success` line), not at the commit of its transaction | 0 | 0.0 | [`traces/scheduler_end/`](traces/scheduler_end/) | `feature-leakage-churn__KNgNaS8` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 296 (74 in each order feature) |
| scheduler_start | a committed legacy range taken as visible at the start of its task (the scheduler's `state=running` line), before the task had selected or committed its orders | 0 | 0.0 | [`traces/scheduler_start/`](traces/scheduler_start/) | `feature-leakage-churn__6BFpVHA` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 156 (39 in each order feature) |
| status_event_date | the status from the shipped pipeline's rule, the latest snapshot dated before the prediction's UTC date, whether or not its export partition had landed | 0 | 0.0 | [`traces/status_event_date/`](traces/status_event_date/) | `feature-leakage-churn__Tet7qUR` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 484 (`status`) |
| status_latest_loaded | the status of the most recently loaded snapshot, not of the visible snapshot with the greatest `snapshot_date` | 0 | 0.0 | [`traces/status_latest_loaded/`](traces/status_latest_loaded/) | `feature-leakage-churn__48WwXKZ` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 113 (`status`) |
| tune_model | treats the gap as overfitting: stronger regularisation and shallower trees in `churn/train.py`, the features untouched | 0 | 0.0 | [`traces/tune_model/`](traces/tune_model/) | `feature-leakage-churn__yqdNa4U` | check A 0, B cut1 0, B cut2 0; the counts of nop (`A_mismatched_cells` 256915, B changed cells 4005 / 8933) |
| v2_rule | only the orders the backfill copied (`_load_job` = `legacy_backfill`) get the commit of their legacy range; every other order visible from its `_loaded_at`; the rename not read | 0 | 0.0 | [`traces/v2_rule/`](traces/v2_rule/) | `feature-leakage-churn__RSqCYiy` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 492 (123 in each order feature) |
| window_on_loaded_at | the order windows (`orders_7d`, `orders_30d`, `spend_30d_cents`) taken on each order's visible time instead of `ordered_at` | 0 | 0.0 | [`traces/window_on_loaded_at/`](traces/window_on_loaded_at/) | `feature-leakage-churn__8H6vAgr` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 47173 (`orders_7d` 45305, `orders_30d` and `spend_30d_cents` 934 each) |
| zero_features | a shortcut: every kept feature a constant, `days_since_last_login` left out | 0 | 0.0 | [`traces/zero_features/`](traces/zero_features/) | `feature-leakage-churn__WtTXKmi` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 422145 (all ten features) |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | [`traces/force-build/`](traces/force-build/) | `feature-leakage-churn__zdnsFo9` | check A 1, B cut1 1, B cut2 1; `A_mismatched_cells` 0, B changed cells 0 / 0 |

The "What it is" column condenses each variant's own description: the comment at the top of `solution/solve.sh` for
canonical and alt, and the docstring of each attempt in `solution/attempts/`.

## What the proof shows

Read in all 31 trials of the run (each trial's `verifier/reward.json`, `verifier/test-stdout.txt` and `result.json`):

- The verifier's privilege steps: each `verifier/test-stdout.txt` starts with the same lock line (below), and its last
  line reports the reward with `killed 0 runner processes`.

      [test.sh] lock ok: /logs/verifier 0:0 755, /logs 0:0 755, owner before 0:0; protected_symlinks=1 protected_hardlinks=1 protected_regular=2; setid files left: 0

- The answer key: `tests/grade.py` checks the ten files of `tests/SHA256SUMS` (H's nine files and the expected
  parquet) before anything else and stops on the first that changed (`verify_checksums`); it prints nothing when all
  match, and every trial went on to grade.
- Network isolation of the graded runs: `[kit] network isolation: ON (private namespace, loopback only)` before the
  first graded run in every trial. Each of the 91 runs of the agent's command (three per trial, one for `drop_plan`)
  and each of the 91 runs of the grader's parquet converter logged `timed_out=False`, `net=private` and
  `strays_killed=0`. Every run of the agent's command exited 0; one converter run exited 3, `drop_plan`'s, whose
  output lacks the column `plan`.
- Independence of the three runs (the real-mode sweep, which runs only in the verifier container): before every run
  the sweep removed every file, folder and IPC object of the runner's uid and then found none left
  (`residual_runner_paths_*` 0 and `sweep_errors_*` 0 in every trial). It removed 1 entry before H and 5 before each
  cut in every trial, except the probe's 8 before cut1, and took 0.64 to 1.19 s (`seconds_sweep_*`).
- The probe `cache_in_work` behaved as designed: check A 1; the sweep before cut1 removed 8 entries, 3 more than in
  the other trials (INFERENCE: the cache files it wrote during the run on H); then checks B cut1 and cut2 scored 0
  with 9,451 and 45,706 changed cells, every one in `orders_7d`, which is what the probe writes when it finds no
  cache. So none of its cache files reached a later run.
- The changed copies: `B_cut1_invariant_problems` and `B_cut2_invariant_problems` 0 in every trial that ran the cuts
  (`tests/invariants.py` proves that each copy keeps the loaders' rules and every row the warehouse held before the
  cut).
- The verifier's limits: `verifier_cpu_quota` 2.0 and `verifier_memory_limit_mib` 4096.0 in every trial, the 2 vCPUs
  and 4 GiB that the instruction states for the grading container; `verifier_cpus_visible` 48 is the host's count, not
  the limit.
- Times: the slowest run of the agent's command took 1.985 s (`alt` on cut2) against the 60 s cap per run
  (`RUN_CAP_SEC` in `tests/grade.py`, stated in the instruction); grading took 11.5 to 16.5 s in the 30 trials with
  three runs and 1.9 s for `drop_plan` (`seconds_grade_total`); the verifier phases took 12.6 to 52.5 s against the
  279 s verifier timeout (`result.json`; `task.toml`).
- The local matrix: field by field, every trial's `reward.json` but the probe's (30 of 31) equals the result of its
  variant in the grader's local matrix on the final package (`authoring/feature-leakage-churn/local_check.py`, 25
  variants, run 2026-10-31 from 19:04:10 to 19:06:58 MST; nop against the local `original`, the shipped pipeline, and
  force-build against `canonical`), outside the timing, environment and sweep fields; `drop_plan` stops after its run
  on H in both. The probe is not in that matrix: on the Mac the local sweep clears only the work folder, so its cache
  survives in `/tmp` and it scores 1 there by construction (its docstring).
- `agent/oracle.txt` shows what `solution/solve.sh` printed: the two valid solutions' smoke run on the visible
  extract (canonical and force-build `wrote 57909 rows x 12 columns to /app/output/features.parquet`, alt
  `wrote 57909 rows to /app/output/features.parquet`); the attempts print nothing (an empty file), and the nop trial
  has no `agent/` folder.

## How to reproduce

From the repository root, with Harbor 0.25.0 on `PATH`:

    python tools/proof_matrix.py feature-leakage-churn --tag <tag> --n 1 --oracle-k 5

Without `--env` (or `HARBOR_ENV`), the script passes `-e docker`, Harbor's default backend, and runs the shipped
package itself. Only Daytona was run for this task. Run `v3` was the Daytona form on the copy without the agent network
line (the backend, the copy and `-k 5` in `PROOF_RESULTS_v3.md`; one trial at a time in each `job_lock.json`):

    python tools/proof_matrix.py feature-leakage-churn --without-agent-network-line --tag v3 --n 1 --oracle-k 5 --env daytona --env-file <file>

- On a backend that cannot apply the agent network line (Daytona Tier 1 among them; Tier 2 by Daytona's documentation,
  not tried), keep `--without-agent-network-line`: the script copies the task to
  `jobs/feature-leakage-churn/package-<tag>/feature-leakage-churn`, drops that one line, checks that nothing else in
  `task.toml` changed, and runs the copy. On a backend that applies the line, leave the option out.
- The script runs, per variant, the command below followed by the row's arguments in `PROOF_RESULTS_v3.md`
  (`-a oracle -k 5` for canonical, `-a oracle --ae SOLUTION=<variant>` for the others, `-a nop`,
  `-a oracle --force-build`), and writes `PROOF_RESULTS_<tag>.md` and `proof_results_<tag>.json` here. The variants
  come from the package's `solution/` folder.

      harbor run -p <package> -e <env> --env-file <file> -n <n> -o jobs/feature-leakage-churn --job-name feature-leakage-churn-<variant>-<tag>

- The env file is how Harbor gets the provider's key (`DAYTONA_API_KEY` for Daytona); it is not in the repository.
- `--n 1` runs one trial at a time. Harbor 0.25.0 stops the agent sandbox before the separate verifier starts
  (`trial/single_step.py`), and both have 2 vCPUs and 4,096 MB here (`[environment]` in `task.toml`; the verifier's in
  `reward.json`), so a trial holds at most 4 GiB at a time (INFERENCE; Daytona may still count a sandbox that is
  being destroyed). The authors' runs also raised Harbor's wait for the environment build three-fold
  (`environment_build_timeout_multiplier` 3.0 in each trial's `config.json`); the script has no option for it.

## Agent trials

Three trials of task v3 with Harbor's `claude-code` agent (Claude Code 2.1.316, `agent_info` in each `result.json`)
and the model `claude-opus-5-5`, on Daytona, 2026-10-31, one at a time (`n_concurrent_trials` 1 in `job_lock.json`),
in the job `feature-leakage-churn-claudecode-opus55-v3-cc1`, on the same copy as the proof (each trial's
`result.json` carries the `task_checksum` of the proof's 31 trials,
`70baca478cc8a36b2c4b6f2c211a6000643e5da8d429e85ae74fa5808bdece08`). Settings (each trial's `config.json`):
`max_budget_usd` 20 (a spend cap of 20 dollars per trial) and `disable_web_search` true, so Harbor passed Claude Code
`--disallowedTools WebSearch,WebFetch` (each trial's `trial.log`). Because the copy lacks the agent network line, the
agent phase had the sandbox's own network (Harbor's default, public, under the limits of the authors' Daytona Tier 1
account, which keep GitHub's hosts and other essential services reachable); the shipped package denies the agent
network.

| Trial | Ran (MST) | Reward | Checks A, B cut1, B cut2 | Agent time | Tool calls | Cost | Trace folder |
|---|---|---|---|---|---|---|---|
| `feature-leakage-churn__qthVz4g` | 19:32:41 to 19:41:37 | 1.0 | 1, 1, 1 | 448.2 s | 24 | 1.36 dollars | [`traces/agent-claude-code/feature-leakage-churn__qthVz4g/`](traces/agent-claude-code/feature-leakage-churn__qthVz4g/) |
| `feature-leakage-churn__58R6Roz` | 19:41:37 to 19:50:07 | 1.0 | 1, 1, 1 | 426.8 s | 22 | 1.47 dollars | [`traces/agent-claude-code/feature-leakage-churn__58R6Roz/`](traces/agent-claude-code/feature-leakage-churn__58R6Roz/) |
| `feature-leakage-churn__oYkSBpm` | 19:50:07 to 19:59:05 | 1.0 | 1, 1, 1 | 454.9 s | 27 | 1.55 dollars | [`traces/agent-claude-code/feature-leakage-churn__oYkSBpm/`](traces/agent-claude-code/feature-leakage-churn__oYkSBpm/) |

The "Ran" times are the Mac clock (MST, 2026-10-31); each trial's `result.json` gives them in UTC (suffix `Z`, 7 hours
ahead, so dated 2026-11-01). Agent time is the `agent_execution` phase of `result.json`; tool calls are counted in
`agent/trajectory.json` (all Bash apart from 1, 3 and 2 file writes or edits, in the table's order); cost is Claude
Code's `total_cost_usd` (`agent/claude-code.txt`, equal to `cost_usd` in `result.json`), 4.38 dollars for the three.

- Outcome: Claude Code (Opus 5.5, web search off) passed task v3 3 of 3, in 427 to 455 s of agent time each, about
  twice task v2's 182 to 221 s; each trial had 0 mismatched cells in check A, 0 changed cells in both B checks and no
  non-null `days_since_last_login` value. The task's pre-registration (design record, section 16) predicted 1 to 2
  passes of 3 (3 of 3 about one chance in four) and 5 to 15 minutes of agent time; the trials took 7.1 to 7.6 minutes.
  By the pre-registration, task v3 ships with that count stated, and no trap is added to lower it (a low pass rate is
  not itself a sign of quality, gate check G29). Three trials show that this agent can solve the task, not its pass
  rate (3 of 3 has a Wilson 95% interval of 0.44 to 1.00). How the external reviewer's own agent fares on task v3 is
  not known.
- These trials are the unprompted test of the task. The blind read recorded in the design record (section 14) scored
  1 but was hinted (its prompt named the migration, and its context held the authors' design notes, which describe
  task v3's design), so it is evidence of fairness, not of unprompted discovery.
- What the agents did (`agent/trajectory.json`): in its first three commands each read `INCIDENT.md`, `CHANGELOG.md`
  and `docs/WAREHOUSE.md`, the live service's and the pipeline's code, the README and the heads of the data files and
  of `_ops/commits.jsonl`. Each then studied the two `_ops/` records (its tool calls name `orders_new`,
  `orders_hourly`, the `RENAME` statements and the `dq_checks` lines), wrote a new module `churn/ops.py`, compared its
  output with the live service's sample in `logs/`, and tested its command on a cut copy of the extract made by a
  script of its own (`/tmp/cut.py`, `/tmp/an/cut.py`, `/tmp/cuttest/mk.py`). Check A on H needs both the rename and
  the commit times: the attempts that skip the rename (`v2_rule`, `min_commit`) miss 492 cells there, and those that
  take the legacy loads' times from the schedule, the task log or a rolled-back run instead of the committed
  transactions (`legacy_schedule`, `scheduler_start`, `scheduler_end`, `rollback_as_commit`) miss 156 to 1,522 (table
  above).
- Network and answer key: no tool call holds a network command (curl, wget, pip install, apt install, git clone, ssh,
  scp, nc, ncat, ping, an http or https URL, a GitHub host) or a path under `/tests`, `/solution` or `/logs/verifier`,
  and neither `agent/trajectory.json` nor `agent/claude-code.txt` holds one as a command or a path (scans of
  2026-10-31). A plain search of those files does find some of these strings, and each such hit was checked: `ping`
  and `ncat` inside words such as `mapping`, `early_stopping` and `concat`, `ncat` and `nc` after an escaped newline (a
  shell `cat`, a Python variable `c`), and `ssh` and `scp` inside encoded strings of `agent/claude-code.txt`. So no
  trial is excluded. The model key's value is in no file of the job folder (the run's key scan).
- Each trace folder holds the same files as the proof traces except `agent/oracle.txt` (`result.json`, `config.json`,
  `trial.log`, `verifier/`, `artifacts/manifest.json`, `job_result.json`, `job_lock.json`), plus
  `agent/trajectory.json` (Harbor's record of the agent's steps, tool calls and their output) and
  `agent/claude-code.txt` (Claude Code's own output stream, its cost line included). Not shipped: `agent/sessions/`,
  Claude Code's raw session files, which hold its full requests, its system prompt among them, and the downloaded copy
  of `/app`.
- Task v2: Claude Code on Opus 5.5, with the same settings, passed it 3 of 3 on 2026-10-31 (181.8 to 221.2 s of agent
  time, 10 to 12 tool calls, 0.58 to 0.68 dollars each; traces in `second-version/traces/agent-claude-code/`; section
  "Task v2").
- The first version: 0 of 3 with Harbor's `terminus-2` agent and `openai/gpt-oss-120b` on 2026-10-30 (traces in
  `first-version/traces/agent-r3/`; section "First version").

## Task v2 (`second-version/`)

Task v2 was the first revision of this task, built on 2026-10-30 and 2026-10-31, proven on 2026-10-31, and never
committed or pushed; only its evidence is kept here. Its extract held the legacy order loads in a table of their own
(`legacy_order_loads.csv`), and `docs/WAREHOUSE.md` stated the loaders' rules. Claude Code passed task v2 3 of 3, in
about three to four minutes each, with every loading rule one read away (design record, section 2), so the task was
hardened once more. Task v3 drops that table: the commit times of the legacy loads, and the rename that ended the order
table's migration (`ALTER TABLE orders_new RENAME TO orders`), are recorded only in the warehouse's own operations
records (`data/_ops/scheduler.log` and `data/_ops/commits.jsonl`). Its other tables are task v2's, and so are its orders
apart from their two load columns (`_load_job` and `_loaded_at`); the expected answer is the same
(`tests/expected/H_features.parquet` has the same sha256 in both versions).

- `PROOF_RESULTS_rev1.md`, `proof_results_rev1.json`, `run_rev1.log`: task v2's Daytona proof `rev1`, Harbor 0.25.0,
  2026-10-31 from 01:54:40 to 02:12:04 MST (the first row's `started` in `proof_results_rev1.json`, and the time the
  three files were written): ALL AS EXPECTED, 22 variants and 26 trials (canonical 5 of 5 at 1.0, alt and force-build
  1.0, nop and 18 attempts 0.0), on a copy without the agent network line, as for task v3. Harbor 0.25.0 content
  hashes (73 files each, the same file list, only `task.toml` differs): task v2's package
  `sha256:580f945d63a9540624b8362b9865224c2bd1c9d8f02fb72532048641f5f184c5`, its proof copy
  `sha256:5f7e542b9c3c131bd0a0cdb2b7e1c1d7f6a8202429f0aaf2f1431a7fd9d0d63f` (the digest in each of its traces'
  `job_lock.json`).
- `second-version/traces/<variant>/`: one trial per variant of `rev1` (22). Its variants are task v3's without the six
  that came with task v3 (`cache_in_work`, `min_commit`, `rollback_as_commit`, `scheduler_end`, `scheduler_start`,
  `v2_rule`) and with `legacy_ignore_status`, whose place `rollback_as_commit` took. For canonical the shipped trial is
  the earliest-started of its five, as for task v3: `feature-leakage-churn__SW6s555`, started at 01:54:42 MST (its
  `result.json`); its `job_result.json` holds the rewards of all five.
- `second-version/traces/agent-claude-code/<trial>/`: task v2's three Claude Code trials, with the settings of task
  v3's (Claude Code 2.1.316, `claude-opus-5-5`, `max_budget_usd` 20, `disable_web_search` true, one at a time), in the
  job `feature-leakage-churn-claudecode-opus55-cc1`, 2026-10-31 from 02:33:28 to 02:47:27 MST (`job_result.json`), on
  task v2's proof copy (`task_checksum` `94676415bd333dd7e9882213f3868badc229fd3f5932b95ad1b48e694a5471f3` in each
  `result.json`, as in its proof traces). Each passed with checks A, B cut1 and B cut2 at 1 and 0 mismatched cells:

| Trial | Ran (MST) | Reward | Agent time | Tool calls | Cost |
|---|---|---|---|---|---|
| `feature-leakage-churn__PqYpM4P` | 02:33:28 to 02:38:32 | 1.0 | 221.2 s | 12 | 0.68 dollars |
| `feature-leakage-churn__MAANsaN` | 02:38:32 to 02:42:59 | 1.0 | 182.5 s | 11 | 0.60 dollars |
| `feature-leakage-churn__aFqLESN` | 02:42:59 to 02:47:27 | 1.0 | 181.8 s | 10 | 0.58 dollars |

Times, tool calls and costs are read as for task v3's trials. `second-version/traces/REDACTIONS.md` lists what was
replaced in these copies.

## First version (`first-version/`)

The task's first version (commits `79286dc` and `495c9f5`; the package `tasks/feature-leakage-churn/` at `495c9f5`,
Harbor digest `sha256:00371b77162a4c186fbf375f4547c2b4c98f1e238d67304c3ceeef08fee3410a`, the digest in each of its
traces' `job_lock.json`) shipped a pipeline with four leaks to fix in place (time windows, target encoding, status and
imputation); task v2 replaced it. Its evidence, at the top of this folder in `495c9f5`, is now in `first-version/`,
with two additions marked below (its traces' `REDACTIONS.md` lists what was replaced in their copies):

- Proof runs `full1` and `full1b` (`PROOF_RESULTS_full1.md`, `PROOF_RESULTS_full1b.md`, `proof_results_full1.json`,
  `proof_results_full1b.json`, `run_full1.log`, `run_full1b.log`), Harbor 0.25.0 on Daytona, 2026-10-28. `full1`, from
  19:57:07 to 20:56:42 MST, was as expected except for one of its ten canonical trials, lost to a DNS failure on the
  Mac running Harbor (`DaytonaConnectionError`, no reward), so its file says NOT ALL AS EXPECTED; `full1b`, from
  20:57:25 to 21:05:48 MST, re-ran the ten canonical trials: 10 of 10 = 1.0, ALL AS EXPECTED. `NOTES.md` explains the
  lost trial.
- `first-version/traces/<variant>/`: one trial per variant of `full1`, canonical from `full1b` (canonical, alt, nop,
  cache_visible, closed_right, drop_leaky, label_at_t, loo_encoding, miss_imputation, open_left_30d, status_same_day,
  tune_model, zero_features, force-build), and `canonical_full1_lost`, the lost trial with its `exception.txt`; the
  first version's design record is `git show 495c9f5:docs/feature-leakage-churn/DESIGN.md`.
- The fresh-clone run of `495c9f5` (`PROOF_RESULTS_clone2.md`, `proof_results_clone2.json`, added): cloned from GitHub
  and run on Daytona on 2026-10-30 (its two rows started at 07:05:57 and 07:07:19 MST), canonical [1.0] and nop [0.0],
  ALL AS EXPECTED.
- Three agent trials of 2026-10-30, 07:32:32 to 07:57:13 MST (`job_result.json`), with Harbor's `terminus-2` agent and
  `openai/gpt-oss-120b`, one at a time (the first version's `task.toml` sets no network line, so the agent phase had
  the sandbox's network), in `first-version/traces/agent-r3/<trial>/` (added): `feature-leakage-churn__hnGjJbF`
  (265.1 s of agent time), `feature-leakage-churn__ioYjMbS` (520.5 s) and `feature-leakage-churn__JeN8fJg` (427.5 s),
  each 0.0: 0 of 3. A review of 2026-10-30 found each failure a capability gap the task targets, not a task defect; no
  command in them uses the network, and no GitHub host appears in any command, output, pane or recording (a scan of
  every trajectory, 2026-10-30). They ran on the first version, so they say nothing of task v3.

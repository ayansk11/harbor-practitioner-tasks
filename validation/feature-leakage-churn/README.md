# Validation: feature-leakage-churn

Last updated: 2026-10-29 (Mac clock, MST).

**Final record: run `full1` for every variant except canonical, and run `full1b` for canonical.** Harbor 0.25.0 on Daytona. Run `full1` ran on 2026-10-28 from 19:57:07 to 20:56:42 and `full1b` from 20:57:25 to 21:05:48 (Mac clock, MST; job `result.json`). `PROOF_RESULTS_full1.md` says NOT ALL AS EXPECTED because of one lost trial (see the notes); `PROOF_RESULTS_full1b.md` says ALL AS EXPECTED.

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py`.
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below).
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies.
- `NOTES.md`: what the run showed beyond the rewards.

The "Job folder" column of the `PROOF_RESULTS_*.md` files points into `jobs/`, the raw Harbor output. `jobs/` is git-ignored and not part of the repository; the trace folders below are the shipped copy.

## Results and traces

One trial per variant is shipped. Variants with one trial ship that trial. For canonical (ten trials) the shipped trial is the one with the earliest `started_at` in its `result.json`; its `job_result.json` holds the rewards of all ten. The last column is read from the shipped trial's `verifier/reward.json`.

| Variant | What it is | Expected | Rewards (all trials of the job) | Run | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|---|
| canonical | reference fix: the four leaks fixed in place (windows, target encoding, status, imputation) | 1 | 10 of 10 = 1.0 | `full1b` | [`traces/canonical/`](traces/canonical/) | `feature-leakage-churn__vs66nEM` | check A 1, B cut1 1, B cut2 1; `A_mismatched_cells` 0, B changed cells 0 / 0; `seconds_H` 0.471 |
| alt | a different valid fix: a per-row implementation of the CLI (bisect and sqlite3, no pandas) | 1 | 1.0 | `full1` | [`traces/alt/`](traces/alt/) | `feature-leakage-churn__qbRxNMV` | check A 1, B cut1 1, B cut2 1; `A_mismatched_cells` 0, B changed cells 0 / 0; `seconds_H` 2.425 |
| nop | Harbor's nop agent: the four leaks stay | 0 | 0.0 | `full1` | [`traces/nop/`](traces/nop/) | `feature-leakage-churn__Ydh7FGt` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 215719, B changed cells 20464 / 51992; `seconds_H` 0.872 |
| cache_visible | computes correct features for the visible extract once and returns them for any input | 0 | 0.0 | `full1` | [`traces/cache_visible/`](traces/cache_visible/) | `feature-leakage-churn__8Hykb55` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 11189, B changed cells 0 / 0; `seconds_H` 0.375 |
| closed_right | exact-timestamp windows, but closed on the right: the event stamped at t counts | 0 | 0.0 | `full1` | [`traces/closed_right/`](traces/closed_right/) | `feature-leakage-churn__pNBheUW` | check A 0, B cut1 0, B cut2 1; `A_mismatched_cells` 94717, B changed cells 125 / 0; `seconds_H` 0.474 |
| drop_leaky | drops the three features that look leaky instead of fixing them | 0 | 0.0 | `full1` | [`traces/drop_leaky/`](traces/drop_leaky/) | `feature-leakage-churn__GFS2UqZ` | check A 0, B cut1 0, B cut2 0; `bad_output_H` 1 (the run on the hidden extract gave unusable output, so the later checks did not run); `seconds_H` 0.675 |
| label_at_t | target encoding counts labels that land exactly at the prediction time | 0 | 0.0 | `full1` | [`traces/label_at_t/`](traces/label_at_t/) | `feature-leakage-churn__EZZr99P` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 376, B changed cells 0 / 0; `seconds_H` 0.474 |
| loo_encoding | leave-one-out target encoding over all labels (still uses later labels) | 0 | 0.0 | `full1` | [`traces/loo_encoding/`](traces/loo_encoding/) | `feature-leakage-churn__ucGbHmA` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 52073, B changed cells 13498 / 35906; `seconds_H` 0.525 |
| miss_imputation | windows, encoding and status fixed; the backward fill in imputation is missed | 0 | 0.0 | `full1` | [`traces/miss_imputation/`](traces/miss_imputation/) | `feature-leakage-churn__sTvSj6W` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 14693, B changed cells 427 / 559; `seconds_H` 0.675 |
| open_left_30d | 30-day windows open on the left: an event at exactly t - 30 days is dropped | 0 | 0.0 | `full1` | [`traces/open_left_30d/`](traces/open_left_30d/) | `feature-leakage-churn__JexSAvp` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 900, B changed cells 0 / 0; `seconds_H` 0.475 |
| status_same_day | status taken from the snapshot dated on the prediction's own day | 0 | 0.0 | `full1` | [`traces/status_same_day/`](traces/status_same_day/) | `feature-leakage-churn__ceEbW4A` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 2190, B changed cells 3 / 4; `seconds_H` 0.473 |
| tune_model | treats it as overfitting: stronger regularisation, features untouched | 0 | 0.0 | `full1` | [`traces/tune_model/`](traces/tune_model/) | `feature-leakage-churn__uRFXrAp` | check A 0, B cut1 0, B cut2 0; `A_mismatched_cells` 215719, B changed cells 20464 / 51992; `seconds_H` 0.874 |
| zero_features | every feature constant: nothing leaks, nothing follows FEATURES.md | 0 | 0.0 | `full1` | [`traces/zero_features/`](traces/zero_features/) | `feature-leakage-churn__wfMN7Rx` | check A 0, B cut1 1, B cut2 1; `A_mismatched_cells` 378892, B changed cells 0 / 0; `seconds_H` 0.424 |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | `full1` | [`traces/force-build/`](traces/force-build/) | `feature-leakage-churn__DHZxhyB` | check A 1, B cut1 1, B cut2 1; `A_mismatched_cells` 0, B changed cells 0 / 0; `seconds_H` 0.475 |
| canonical_full1_lost | one canonical trial of run full1, lost to a DNS failure on the Mac running Harbor (kept as evidence) | 1 | 9 of 10 = 1.0 (1 with no reward) | `full1` | [`traces/canonical_full1_lost/`](traces/canonical_full1_lost/) | `feature-leakage-churn__dtTSGvN` | no `reward.json` (the trial ended with `DaytonaConnectionError` before a reward was written) |

Command for each row: `harbor run -p tasks/feature-leakage-churn -e daytona --env-file <file> -n <n> -o jobs/feature-leakage-churn --job-name feature-leakage-churn-<variant>-<run>` followed by the row's arguments in `PROOF_RESULTS_<run>.md` (`-a oracle -k 10` for canonical, `-a oracle --ae SOLUTION=<variant>` for the others, `-a nop`, `-a oracle --force-build`). The env file is how Harbor gets the Daytona key (`DAYTONA_API_KEY`); it is not in the repository.

## What each trace folder holds

Each `traces/<variant>/` folder holds the files of one Harbor trial, copied from the job folder of the final run:

| File | What it shows |
|---|---|
| `result.json` | Harbor's trial record: the reward and the grader's metrics, the exception if any, phase start and end times (UTC, ending in `Z`), and the trial config |
| `config.json` | the trial config: task path, agent (`oracle` or `nop`) and, for oracle trials, the `SOLUTION` variable passed with `--ae` |
| `trial.log` | Harbor's trial log (sandbox build and artifact download) |
| `agent/oracle.txt` | what `solution/solve.sh` printed in the sandbox (nop trials have no `agent/` folder; an empty file means `solve.sh` printed nothing) |
| `verifier/reward.txt`, `verifier/reward.json` | the reward Harbor read, and the grader's metrics |
| `verifier/test-stdout.txt` | the verifier's full log (`tests/test.sh` and the grader) |
| `artifacts/manifest.json` | what Harbor downloaded from the agent sandbox for the verifier (the downloaded copy of `/app` itself is not shipped) |
| `job_result.json` | the job-level `result.json`: every trial of that job with its reward (for canonical, all ten), and job start and end times (Mac clock, MST, no zone suffix) |
| `job_lock.json` | the job-level `lock.json`: `harbor.version` (0.25.0), the task digest and the trial settings |

`traces/REDACTIONS.md` lists the machine-specific paths that were replaced in these copies. Nothing else was changed.

## Notes

- Run `full1` is marked NOT ALL AS EXPECTED only because one of its ten canonical trials ended with `DaytonaConnectionError` and no reward. Its `exception.txt` (in `traces/canonical_full1_lost/`) shows `socket.gaierror: [Errno 8] nodename nor servname provided, or not known`: the Mac running Harbor lost DNS while it was polling the verifier. That is a failure of the machine running Harbor, not of the task. The trial's `verifier/` folder was empty in the original (no reward was written), so that trace has no verifier files. Its `job_result.json` is the full1 canonical job: 9 trials with reward 1.0 and one errored trial; Harbor's job-level mean `reward` there is 0.9, which equals 9 of 10 with the lost trial counted as 0 (inferred from the numbers); it is not a grading result.
- Run `full1b` re-ran the ten canonical trials for a clean record: 10 of 10 = 1.0. The shipped canonical trace comes from `full1b`; every other trace comes from `full1`.
- This task's `solve.sh` prints no `applied <variant>` line; `agent/oracle.txt` holds the CLI's own output where `solve.sh` ran the CLI (canonical, alt, force-build and `cache_visible`) and is empty for the other attempts. The evidence that each `SOLUTION` reached `solve.sh` is that each attempt's mismatch counts in `verifier/reward.json` match the local results in `../../docs/feature-leakage-churn/DESIGN.md` section 8.
- Runs here were one trial at a time (`n_concurrent_trials` 1 in `job_lock.json`); the other tasks ran two at a time.
- No agent (model) trials were run for this task; the matrix uses Harbor's `oracle` and `nop` agents only.

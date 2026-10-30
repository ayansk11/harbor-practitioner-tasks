# Validation: ab-test-reanalysis

Last updated: 2026-10-29 (Mac clock, MST).

**Final run: `full2`.** Harbor 0.25.0 on Daytona, 2026-10-29 from 03:38:22 to 03:51:16 (Mac clock, MST; job `result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full2.md`).

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py`.
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below).
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies.

The "Job folder" column of the `PROOF_RESULTS_*.md` files points into `jobs/`, the raw Harbor output. `jobs/` is git-ignored and not part of the repository; the trace folders below are the shipped copy.

## Results and traces

One trial per variant is shipped. Variants with one trial ship that trial. For canonical (ten trials) the shipped trial is the one with the earliest `started_at` in its `result.json`; its `job_result.json` holds the rewards of all ten. The last column is read from the shipped trial's `verifier/reward.json` and, for the names of the failing fields, its `verifier/test-stdout.txt`; CI errors are rounded to three decimals (exact values in the files).

| Variant | What it is | Expected | Rewards (all trials of the job) | Run | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|---|
| canonical | reference fix: bots out of both arms; user-level delta-method CI; SRM chi-square; the plan's decision rule | 1 | 10 of 10 = 1.0 | `full2` | [`traces/canonical/`](traces/canonical/) | `ab-test-reanalysis__qvmVU87` | `sets_passed` 6 of 6 (CI band 0.25 half-widths) |
| alt | a different valid method: user-level bootstrap (5,000 resamples, fixed seed), numpy per-user sums | 1 | 1.0 | `full2` | [`traces/alt/`](traces/alt/) | `ab-test-reanalysis__MGDk7sX` | `sets_passed` 6 of 6 (CI band 0.25 half-widths) |
| alt_cr1 | a third valid method: CR1 cluster-robust errors from a pageview-level regression | 1 | 1.0 | `full2` | [`traces/alt_cr1/`](traces/alt_cr1/) | `ab-test-reanalysis__tz3x2yq` | `sets_passed` 6 of 6 (CI band 0.25 half-widths) |
| nop | Harbor's nop agent: the shipped readout and code | 0 | 0.0 | `full2` | [`traces/nop/`](traces/nop/) | `ab-test-reanalysis__uDDEjGt` | `sets_passed` 0 of 6 (CI band 0.25 half-widths); visible: 9 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.429 half-widths), decision; h_null: 8 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.154 half-widths); h_pos: 8 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.337 half-widths); h_srm: 9 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.197 half-widths), decision; h_bots: 9 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (4.094 half-widths), decision; h_twin: 8 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.288 half-widths) |
| constant_inflation | pageview-level CI times a constant (2.466) fitted on the visible data | 0 | 0.0 | `full2` | [`traces/constant_inflation/`](traces/constant_inflation/) | `ab-test-reanalysis__afgxzi3` | `sets_passed` 5 of 6 (CI band 0.25 half-widths); h_null: 1 problem(s): ci_95 (0.486 half-widths) |
| fix_bots_only | bots, SRM and decision fixed; the CI is still pageview-level | 0 | 0.0 | `full2` | [`traces/fix_bots_only/`](traces/fix_bots_only/) | `ab-test-reanalysis__K7NgMLk` | `sets_passed` 0 of 6 (CI band 0.25 half-widths); visible: 1 problem(s): ci_95 (0.594 half-widths); h_null: 1 problem(s): ci_95 (0.792 half-widths); h_pos: 1 problem(s): ci_95 (0.594 half-widths); h_srm: 1 problem(s): ci_95 (0.617 half-widths); h_bots: 1 problem(s): ci_95 (0.643 half-widths); h_twin: 1 problem(s): ci_95 (0.563 half-widths) |
| fix_ci_only | CI, SRM and decision fixed; the B-only bot filter is kept | 0 | 0.0 | `full2` | [`traces/fix_ci_only/`](traces/fix_ci_only/) | `ab-test-reanalysis__ijwMmdt` | `sets_passed` 0 of 6 (CI band 0.25 half-widths); visible: 7 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, ci_95 (0.845 half-widths); h_null: 7 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, ci_95 (0.373 half-widths); h_pos: 7 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, ci_95 (0.749 half-widths); h_srm: 7 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, ci_95 (0.587 half-widths); h_bots: 9 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (3.501 half-widths), decision; h_twin: 7 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, ci_95 (0.728 half-widths) |
| fix_visible_result_only | a one-off script writes the right visible readout; the pipeline is unchanged | 0 | 0.0 | `full2` | [`traces/fix_visible_result_only/`](traces/fix_visible_result_only/) | `ab-test-reanalysis__ZjGV9oi` | `sets_passed` 1 of 6 (CI band 0.25 half-widths); h_null: 8 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.154 half-widths); h_pos: 8 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.337 half-widths); h_srm: 9 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.197 half-widths), decision; h_bots: 9 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (4.094 half-widths), decision; h_twin: 8 problem(s): n_users, pageviews, clicks, ctr, diff, srm_p, srm_flag, ci_95 (1.288 half-widths) |
| hardcode_no_ship | canonical numbers, but the decision is always `no_ship` | 0 | 0.0 | `full2` | [`traces/hardcode_no_ship/`](traces/hardcode_no_ship/) | `ab-test-reanalysis__3EUBTMa` | `sets_passed` 3 of 6 (CI band 0.25 half-widths); h_pos: 1 problem(s): decision; h_srm: 1 problem(s): decision; h_twin: 1 problem(s): decision |
| icc_tuned | pageview-level CI widened by one intra-user correlation tuned on every graded set | 0 | 0.0 | `full2` | [`traces/icc_tuned/`](traces/icc_tuned/) | `ab-test-reanalysis__9mNkgc7` | `sets_passed` 4 of 6 (CI band 0.25 half-widths); h_null: 1 problem(s): ci_95 (0.359 half-widths); h_twin: 1 problem(s): ci_95 (0.348 half-widths) |
| kish_tuned | pageview-level CI widened by Kish's factor to one exponent tuned on every graded set | 0 | 0.0 | `full2` | [`traces/kish_tuned/`](traces/kish_tuned/) | `ab-test-reanalysis__s9ExD9T` | `sets_passed` 4 of 6 (CI band 0.25 half-widths); h_null: 1 problem(s): ci_95 (0.354 half-widths); h_twin: 1 problem(s): ci_95 (0.360 half-widths) |
| mean_of_ratios | average of per-user CTRs with a user-level Welch CI, not the plan's ratio of sums | 0 | 0.0 | `full2` | [`traces/mean_of_ratios/`](traces/mean_of_ratios/) | `ab-test-reanalysis__4hocD2L` | `sets_passed` 0 of 6 (CI band 0.25 half-widths); visible: 4 problem(s): ctr, diff, ci_95 (0.490 half-widths); h_null: 4 problem(s): ctr, diff, ci_95 (0.670 half-widths); h_pos: 4 problem(s): ctr, diff, ci_95 (0.498 half-widths); h_srm: 4 problem(s): ctr, diff, ci_95 (0.510 half-widths); h_bots: 4 problem(s): ctr, diff, ci_95 (0.589 half-widths); h_twin: 4 problem(s): ctr, diff, ci_95 (0.513 half-widths) |
| no_srm_gate | everything right except that the decision ignores the SRM flag | 0 | 0.0 | `full2` | [`traces/no_srm_gate/`](traces/no_srm_gate/) | `ab-test-reanalysis__9WF82uM` | `sets_passed` 5 of 6 (CI band 0.25 half-widths); h_srm: 1 problem(s): decision |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | `full2` | [`traces/force-build/`](traces/force-build/) | `ab-test-reanalysis__ywxtGS2` | `sets_passed` 6 of 6 (CI band 0.25 half-widths) |

Command for each row: `harbor run -p tasks/ab-test-reanalysis -e daytona --env-file <file> -n <n> -o jobs/ab-test-reanalysis --job-name ab-test-reanalysis-<variant>-<run>` followed by the row's arguments in `PROOF_RESULTS_<run>.md` (`-a oracle -k 10` for canonical, `-a oracle --ae SOLUTION=<variant>` for the others, `-a nop`, `-a oracle --force-build`). The env file is how Harbor gets the Daytona key (`DAYTONA_API_KEY`); it is not in the repository.

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

- Run `full1` (`PROOF_RESULTS_full1.md`, `proof_results_full1.json`, `run_full1.log`) was also all as expected, but it ran before the hidden set `h_twin` was rebuilt as an exact pageview twin of `h_null`. It does not cover the final package, so it is kept here as a dated record only and no traces are shipped from it. Run `full2` is the proof for the final package.
- `icc_tuned` and `kish_tuned` pass four of the six sets and fail the pair `h_null` and `h_twin`: one set needs a wider interval and the other a narrower one, which no multiplier built from pageview counts alone can give. The two sets have the same users, arms, bots and pageviews; only the clicks differ.
- `agent/oracle.txt` shows the readout each variant wrote for the visible data (`decision`, `diff`, `ci`, `srm_p`). Design: `../../docs/ab-test-reanalysis/DESIGN.md` sections 7, 15 and 16.
- No agent (model) trials were run for this task; the matrix uses Harbor's `oracle` and `nop` agents only.

# Validation: tenant-isolation-docshare

Last updated: 2026-10-29 (Mac clock, MST).

**Final run: `full1`.** Harbor 0.25.0 on Daytona, 2026-10-28 from 19:45:27 to 19:56:43 (Mac clock, MST; job `result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full1.md`).

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py`.
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below).
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies.

The "Job folder" column of the `PROOF_RESULTS_*.md` files points into `jobs/`, the raw Harbor output. `jobs/` is git-ignored and not part of the repository; the trace folders below are the shipped copy.

## Results and traces

One trial per variant is shipped. Variants with one trial ship that trial. For canonical (ten trials) the shipped trial is the one with the earliest `started_at` in its `result.json`; its `job_result.json` holds the rewards of all ten. The last column is read from the shipped trial's `verifier/reward.json`.

| Variant | What it is | Expected | Rewards (all trials of the job) | Run | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|---|
| canonical | reference fix: one central access check used by every file endpoint; X-Org-Id checked against memberships | 1 | 10 of 10 = 1.0 | `full1` | [`traces/canonical/`](traces/canonical/) | `tenant-isolation-docshare__rCxcLLy` | `run1_failed` 0 of 2475, `run2_failed` 0 of 1231, `leaking_refusals` 0 |
| alt | a different valid fix: every SQL query scoped by the caller's org and role; refusals are 403 instead of 404 | 1 | 1.0 | `full1` | [`traces/alt/`](traces/alt/) | `tenant-isolation-docshare__e9qFx96` | `run1_failed` 0 of 2475, `run2_failed` 0 of 1231, `leaking_refusals` 0 |
| nop | Harbor's nop agent: all six planted flaws stay | 0 | 0.0 | `full1` | [`traces/nop/`](traces/nop/) | `tenant-isolation-docshare__XmUpF3f` | `run1_failed` 1742 of 2475, `run2_failed` 603 of 1139, `leaking_refusals` 785; largest: `run1_fail_status_thumb_bad_x_org_id` 128, `run1_fail_status_read_bad_x_org_id` 128, `run1_fail_status_download_bad_x_org_id` 128 |
| deny_most | closes every leak by also refusing support users, share links and link creation | 0 | 0.0 | `full1` | [`traces/deny_most/`](traces/deny_most/) | `tenant-isolation-docshare__B4rtEHL` | `run1_failed` 142 of 2475, `run2_failed` 148 of 1119, `leaking_refusals` 0; largest: `run2_fail_permitted_folder_files_support` 24, `run1_fail_permitted_folder_files_support` 24, `run2_fail_permitted_export_support` 20 |
| drop_org_switching | removes org switching instead of checking it | 0 | 0.0 | `full1` | [`traces/drop_org_switching/`](traces/drop_org_switching/) | `tenant-isolation-docshare__5pcy95D` | `run1_failed` 140 of 2475, `run2_failed` 149 of 1127, `leaking_refusals` 0; largest: `run2_fail_permitted_folder_files_support` 24, `run1_fail_permitted_folder_files_support` 24, `run2_fail_permitted_thumb_support` 16 |
| hardcode_visible_orgs | membership check uses a table copied from the visible development data | 0 | 0.0 | `full1` | [`traces/hardcode_visible_orgs/`](traces/hardcode_visible_orgs/) | `tenant-isolation-docshare__NDb4Y6o` | `run1_failed` 555 of 2475, `run2_failed` 229 of 1231, `leaking_refusals` 246; largest: `run1_fail_status_me_bad_x_org_id` 46, `run1_fail_status_list_folders_bad_x_org_id` 46, `run1_fail_status_list_files_bad_x_org_id` 46 |
| membership_plus_get | fixes the header trust and the shared loader only; misses thumbs, export, share and delete | 0 | 0.0 | `full1` | [`traces/membership_plus_get/`](traces/membership_plus_get/) | `tenant-isolation-docshare__pACZ8Qu` | `run1_failed` 251 of 2475, `run2_failed` 103 of 1231, `leaking_refusals` 130; largest: `run1_fail_status_export` 52, `run1_fail_leak_export` 52, `run1_fail_status_thumb` 32 |
| patch_get_only | fixes only the two endpoints the report names | 0 | 0.0 | `full1` | [`traces/patch_get_only/`](traces/patch_get_only/) | `tenant-isolation-docshare__MLvAmEf` | `run1_failed` 1300 of 2475, `run2_failed` 427 of 1139, `leaking_refusals` 516; largest: `run1_fail_status_thumb_bad_x_org_id` 128, `run1_fail_leak_thumb_bad_x_org_id` 128, `run1_fail_status_share_bad_x_org_id` 126 |
| phase_gate | refuses every write on the first start and allows every write on later starts | 0 | 0.0 | `full1` | [`traces/phase_gate/`](traces/phase_gate/) | `tenant-isolation-docshare__G9e8F8p` | `run1_failed` 0 of 2475, `run2_failed` 50 of 1198, `leaking_refusals` 0; largest: `run2_fail_noise_status_revoke` 17, `run2_fail_noise_status_delete` 11, `run2_fail_noise_status_rename` 8 |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | `full1` | [`traces/force-build/`](traces/force-build/) | `tenant-isolation-docshare__JXRGo7G` | `run1_failed` 0 of 2475, `run2_failed` 0 of 1231, `leaking_refusals` 0 |

Command for each row: `harbor run -p tasks/tenant-isolation-docshare -e daytona --env-file <file> -n <n> -o jobs/tenant-isolation-docshare --job-name tenant-isolation-docshare-<variant>-<run>` followed by the row's arguments in `PROOF_RESULTS_<run>.md` (`-a oracle -k 10` for canonical, `-a oracle --ae SOLUTION=<variant>` for the others, `-a nop`, `-a oracle --force-build`). The env file is how Harbor gets the Daytona key (`DAYTONA_API_KEY`); it is not in the repository.

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

- Every oracle trial's `agent/oracle.txt` says `applied <variant> to /app/docshare`, so the `SOLUTION` variable reached `solve.sh` on Daytona.
- `phase_gate` passes the grader's first run (`run1_failed` 0) and fails only the second run, where refused requests are mixed into the write list (the `run2_fail_noise_status_*` counts in its `reward.json`). That second run is what kills it.
- The verifier log (`verifier/test-stdout.txt`) of every trial shows the lock line, `network isolation: ON` and `killed 0 runner processes`. Design and local results: `../../docs/tenant-isolation-docshare/DESIGN.md` sections 7 and 10.
- No agent (model) trials were run for this task; the matrix uses Harbor's `oracle` and `nop` agents only.

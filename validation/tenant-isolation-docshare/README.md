# Validation: tenant-isolation-docshare

Last updated: 2026-10-31 (Mac clock, MST).

**Final run: `full1`.** Harbor 0.25.0 on Daytona, 2026-10-28 from 19:45:27 to 19:56:43 (Mac clock, MST; job `result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full1.md`).

**Fresh-clone run: `clone2`.** The task as published in commit `495c9f5`, run again from a fresh clone of the GitHub repository on 2026-10-30: canonical 1.0, nop 0.0, ALL AS EXPECTED (section "Fresh-clone run").

**Agent trials:** three trials of one model agent, 0 of 3 pass (section "Agent trials").

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py` (for the fresh-clone run `clone2`, the first two only).
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below); `traces/agent-r3/<trial>/`: the agent trials (section "Agent trials").
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies, and the model service's URL in the agent traces' copies.

The "Job folder" column of the `PROOF_RESULTS_*.md` files points into `jobs/`, the raw Harbor output (for `clone2`, the `jobs/` folder of the fresh clone). `jobs/` is git-ignored and not part of the repository; the trace folders below are the shipped copy.

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

Each `traces/<variant>/` folder holds the files of one Harbor trial, copied from the job folder of the final run (each `traces/agent-r3/<trial>/`, from the job folder of the agent trials):

| File | What it shows |
|---|---|
| `result.json` | Harbor's trial record: the reward and the grader's metrics, the exception if any, phase start and end times (UTC, ending in `Z`), and the trial config |
| `config.json` | the trial config: task path, agent (`oracle` or `nop`; `terminus-2` and its model for the agent traces) and, for oracle trials, the `SOLUTION` variable passed with `--ae` |
| `trial.log` | Harbor's trial log (sandbox build and artifact download; in the agent traces also the agent's trajectory saves and parser warnings) |
| `agent/oracle.txt` | what `solution/solve.sh` printed in the sandbox (nop trials have no `agent/` folder; an empty file means `solve.sh` printed nothing; the agent traces have no `oracle.txt`: their `agent/` holds `trajectory.json`, `terminus_2.pane` and `recording.cast`) |
| `verifier/reward.txt`, `verifier/reward.json` | the reward Harbor read, and the grader's metrics |
| `verifier/test-stdout.txt` | the verifier's full log (`tests/test.sh` and the grader) |
| `artifacts/manifest.json` | what Harbor downloaded from the agent sandbox for the verifier (the downloaded copy of `/app` itself is not shipped) |
| `job_result.json` | the job-level `result.json`: every trial of that job with its reward (for canonical, all ten), and job start and end times (Mac clock, MST, no zone suffix) |
| `job_lock.json` | the job-level `lock.json`: `harbor.version` (0.25.0), the task digest and the trial settings |

`traces/REDACTIONS.md` lists the machine-specific paths that were replaced in these copies, and the model service's URL in `traces/agent-r3/`. Nothing else was changed.

## Fresh-clone run

Run `clone2` ([`PROOF_RESULTS_clone2.md`](PROOF_RESULTS_clone2.md), `proof_results_clone2.json`) checks the published
package. On 2026-10-30 this repository was cloned from GitHub at commit `495c9f5` (06:18, Mac clock, MST), and
`tools/proof_matrix.py` ran this task from the clone on Daytona with Harbor 0.25.0, from 07:01:08 to 07:02:39 (Mac clock,
MST): canonical once (`-a oracle -k 1`) and nop once (`-a nop`), one trial at a time. Rewards: canonical [1.0], nop
[0.0]; overall ALL AS EXPECTED. The task digest in both jobs' `lock.json` is the one in this folder's `job_lock.json`
files (`sha256:8295aff32904e8b26a5d2f49369b5a160473f8f5c99367ae5488799f0e87bd3b`), so the clone graded the same package
as `full1`. Harbor waited up to three times its default image-build time (`--environment-build-timeout-multiplier 3`)
because Daytona's status page reported degraded performance for a subset of US runners that morning; task, agent and
verifier timeouts were those of `task.toml`. Only the two results files are shipped from this run (no traces, no run
log).

## Agent trials

Three trials of a model agent have run on this task, outside the proof matrix, on 2026-10-30: Harbor's `terminus-2`
agent with the model `openai/gpt-oss-120b`, served by an OpenAI-compatible model service (its URL is `<model-endpoint>`
in the traces), on Daytona and on the same task package as `full1` (the task digest in each agent trace's
`job_lock.json` equals the one in the other traces). They are one job, `tenant-isolation-docshare-terminus2-gptoss-r3` (`-k 3`, two trials at a
time, from 07:13:20 to 07:19:28, Mac clock, MST; job `result.json`); agent and verifier timeouts were those of
`task.toml` (agent 1,800 s), and Harbor waited up to three times its default image-build time
(`--environment-build-timeout-multiplier 3`). Every trial finished without an exception (`result.json`). None passed:
0 of 3. Flaw numbers are those of the six planted flaws in `../../docs/tenant-isolation-docshare/DESIGN.md` section 3.

| Trial | Episodes | Agent phase | Reward | What the trial's files show | Trace |
|---|---|---|---|---|---|
| `tenant-isolation-docshare__U5her8X` | 11 | 162 s | 0.0 | `files.py`, `thumbs.py`, `export.py` and `share.py` edited: flaws 1, 3, 4 and 5 closed unless the request names another org in `X-Org-Id`; flaw 2 (`X-Org-Id` trusted without a membership check) and flaw 6 (delete not limited to org_admin) open. Run 1: 643 of 2,475 checks failed; run 2: 246 of 1,231; 257 leaking refusals | [`traces/agent-r3/tenant-isolation-docshare__U5her8X/`](traces/agent-r3/tenant-isolation-docshare__U5her8X/) |
| `tenant-isolation-docshare__9n7yLqH` | 12 | 151 s | 0.0 | no source file changed: both edit commands called `apply_patch`, which is not in the image (`command not found`), and no later command edited a file. `reward.json` equals the nop trace's except `grading_seconds` (run 1: 1,742 of 2,475 failed; run 2: 603 of 1,139; 785 leaking refusals) | [`traces/agent-r3/tenant-isolation-docshare__9n7yLqH/`](traces/agent-r3/tenant-isolation-docshare__9n7yLqH/) |
| `tenant-isolation-docshare__5JS5qnC` | 15 | 140 s | 0.0 | `thumbs.py`, `export.py` and `share.py` edited: flaws 3, 4 and 5 closed as above; the reported flaw 1, flaw 2 and flaw 6 open; support users' thumbnail and export requests now refused (400 instead of 200). Run 1: 1,246 of 2,475 failed; run 2: 433 of 1,139; 515 leaking refusals | [`traces/agent-r3/tenant-isolation-docshare__5JS5qnC/`](traces/agent-r3/tenant-isolation-docshare__5JS5qnC/) |

Episodes are `n_episodes` and the agent phase runs from `agent_execution.started_at` to `finished_at`, both in each
trial's `result.json`; the check counts are from `verifier/reward.json`. The edited files are under `docshare/routes/`.

What the trials show:
- In every trial most failed run-1 checks are requests whose `X-Org-Id` names an org the caller may not use (the
  `*_bad_x_org_id` keys of `verifier/reward.json`: 577 of 643, 1,309 of 1,742 and 1,007 of 1,246, in the order of the
  table).
- All three agents read `/app/docs/PERMISSIONS.md`, which states the membership rule (section 2) and that only org_admin
  deletes (section 3), and each marked the task complete after the 9 visible tests passed; those tests pass on the
  unfixed service too (`../../docs/tenant-isolation-docshare/DESIGN.md` section 2).
- Reading (INFERENCE, from these files): capability gaps the task targets (a complete audit of every code path and of
  the identity layer, follow-through on the rules read, checking the result), not a task defect. In `9n7yLqH`, whose
  edits never landed, the 0.0 reflects a failed tool call left unchecked more than the audit.

Network: this task's `task.toml` sets no `network_mode`, so the trials ran with Harbor 0.25.0's default public network.
They started at 14:13 UTC on 2026-10-30, after this repository was created on GitHub (07:08 UTC the same day), and the
Daytona account of these runs is on Tier 1, which keeps GitHub reachable (repository README, "Known limitations"), so a
fetch of the public hidden tests was possible. Every trajectory, terminal pane and recording was read for one: no GitHub
host (`github.com`, `*.github.com`, `*.githubusercontent.com`) and neither the repository's nor its owner's name appears
in any of them, and no command used the network. The one URL in any command, `http://www.w3.org/2000/svg` in two
trials, is the SVG namespace string of the thumbnail code those agents rewrote, not a request. No trial was excluded.

## Notes

- Every oracle trial's `agent/oracle.txt` says `applied <variant> to /app/docshare`, so the `SOLUTION` variable reached `solve.sh` on Daytona.
- `phase_gate` passes the grader's first run (`run1_failed` 0) and fails only the second run, where refused requests are mixed into the write list (the `run2_fail_noise_status_*` counts in its `reward.json`). That second run is what kills it.
- The verifier log (`verifier/test-stdout.txt`) of every trial shows the lock line, `network isolation: ON` and `killed 0 runner processes`. Design and local results: `../../docs/tenant-isolation-docshare/DESIGN.md` sections 7 and 10.
- Three agent (model) trials were run for this task, outside the matrix (section "Agent trials"); the matrix uses Harbor's `oracle` and `nop` agents only.

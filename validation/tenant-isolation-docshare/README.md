# Validation: tenant-isolation-docshare

Last updated: 2026-11-03, 08:10 MST (Mac clock): the section "Agent trials" reports the three `terminus-2` trials only;
the external reviewer's two trials, known only from the reviewer's feedback, which is not in this repository, are no
longer reported here (the authors' choice).
Before that, 2026-11-03, 06:37 MST (Mac clock): fixes after a pre-commit check (no count or result changed): the
introduction says that the section "Agent trials" is about the first version's package too; the `replay_memo` row says
that its delete is back to the original's login-only check and how its rename answers; a note under the table says where
the `ABOUT.md` of `replay_memo` and that of `phase_gate` differ from this page.
Before that, 2026-11-03, 05:43 MST (Mac clock): wording fixed after an independent check (no count or result changed):
run 2's write list is said to hold 7 requests that must still get a 4xx; the reason why some write lists are shorter is
labelled INFERENCE; a clause of 2026-11-03 that called the Daytona proof pending, written before the proof ran and never
published, is removed from this head.
Before that, 2026-11-03, 04:47 MST (Mac clock): rewritten for the fixed grader (the Daytona proof `full2` of the
package as it is now, its traces and the new attempt `replay_memo`); the earlier grader's evidence (proof `full1`,
the fresh-clone run `clone2`, their traces and the three agent trials) moved to `first-version/`.
Before that, 2026-11-02 (Mac clock, MST): the `phase_gate` note points to the replay gap in DESIGN.md section 9.
Before that, 2026-10-31 (Mac clock, MST).

This task has had two graders. The first is in the package of the repository's commits `79286dc` to `f5fba52`
(section "First version (earlier grader)"). The current one is the `tests/grade.py` of the package in
`tasks/tenant-isolation-docshare/`, fixed on 2026-11-03, when the attempt `solution/attempts/replay_memo/` was added
too; nothing else in the package changed. Everything above the section "Agent trials" is about the current package.
That section reports trials that ran on the first version's package, and the section "First version (earlier grader)"
is about that version.

**Final run: `full2`.** Harbor 0.25.0 on Daytona, 2026-11-03 from 03:36:31 to 03:44:49 (Mac clock, MST; the first
row's `started` in `proof_results_full2.json`, and the time the run's three files were written; in the shipped
traces, the canonical job's `started_at` is 03:36:33 and the force-build job's `finished_at` 03:44:47, each in
`job_result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full2.md`), 11 variants and 20 trials, two at a time
(`n_concurrent_trials` 2 in each `job_lock.json`).

This task's `task.toml` sets no network line, so the proof ran the shipped package itself (`Package:
tasks/tenant-isolation-docshare` in `PROOF_RESULTS_full2.md`). The task digest in each trace's `job_lock.json`,
`sha256:bf647a0e542a65b1c221bad907aa47a5c4b1a37c0ad13f5a07b6c67657d05967`, is the Harbor 0.25.0 content hash of the
current package (96 files); the first version's is
`sha256:8295aff32904e8b26a5d2f49369b5a160473f8f5c99367ae5488799f0e87bd3b` (88 files). Each trial's `result.json`
carries the same `task_checksum`, `998eb650aed0821084d4db603d067cbed81ff6210396dfbc48cc65517526c1c0`.

## Files in this folder

- `PROOF_RESULTS_full2.md`, `proof_results_full2.json`, `run_full2.log`: the proof matrix of run `full2`, written by
  `tools/proof_matrix.py` (`run_full2.log` is its console output).
- `traces/<variant>/`: one Harbor trial per variant of run `full2` (table below; their files, section "What each
  trace folder holds").
- `first-version/`: the evidence of the earlier grader (section "First version (earlier grader)"), among it the three
  agent trials in `first-version/traces/agent-r3/` (section "Agent trials").

Each traces folder carries a `REDACTIONS.md` that lists what was replaced in its copies; no reward, count or timing
was changed. The "Job folder" column of `PROOF_RESULTS_full2.md` points into `jobs/`, the raw Harbor output, which is
git-ignored and not part of the repository; the trace folders are the shipped copy.

## Results and traces (run `full2`)

One trial per variant is shipped. For canonical (ten trials) the shipped trial is the one with the earliest
`started_at` in its `result.json` (`tenant-isolation-docshare__a73K54D`, 0.11 s before
`tenant-isolation-docshare__cNW7qG4`); its `job_result.json` holds the rewards of all ten.

The grader (`tests/grade.py`; design record, `../../docs/tenant-isolation-docshare/DESIGN.md` section 4) first
records the untouched service's answers to the 356 permitted reads that need a reference (phase `original`), then
starts the agent's service twice, each time on a fresh copy of the hidden database:
- Run 1 (2,211 checks): every refused read shuffled with every permitted read, then the refused writes that are not
  held back, then a read-back of every file and a comparison of the database with the seed.
- Run 2 (1,540 checks for a valid fix): the permitted reads shuffled with 400 refused reads, then the write list, 50
  requests from permitted callers (the permitted writes, the requests that check their effects and 7 requests that
  must still get a 4xx). Before each of them comes a seeded batch of 3 to 12 refused requests that run 1 also sent
  and, while they last, 4 to 8 held-back refused writes: a seeded third ((n + 1) // 3) of each of the 41 classes of
  refused write (its kind, the caller's state and role, the file's relation to the caller), 264 of the 793 refused
  writes, which run 1 never sends. Each held-back write is sent once and must be refused; any that the list did not
  reach is sent after it, and one never sent fails the check `held_unsent`. Then each file that a held-back rename,
  delete or revoke acts on is read back (41 files) and its working seed links are fetched (4), unless the write list
  used that file (14 files).

The reward is 1 only if every check passes. The last column is read from the shipped trial's `verifier/reward.json`:
`run1_failed` and `run2_failed` count the failed checks of each run, `leaking_refusals` the refused requests whose
answer held a file's contents or the name of a file the caller may never read, `held_back` the held-back writes and
`held_back_sent` how many of them were sent; each `run1_fail_<check>` and `run2_fail_<check>` counts one kind of
check. In run 2, `noise_*` checks are the refused requests of the write list's batches that run 1 also sent,
`held_status_*` and `held_leak_*` the held-back writes, `held_sweep` and `held_link` their read-back, and `write_*`
the steps of the write list; `permitted_*` checks are permitted requests, and `*_bad_x_org_id` checks are requests
whose `X-Org-Id` names an org the caller may not use or one that does not exist.

| Variant | What it is | Expected | Rewards (all trials of the job) | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|
| canonical | the reference fix (`solution/canonical/`): one central access check (`docshare/access.py`) used by every file endpoint; `X-Org-Id` checked against the caller's memberships | 1 | 10 of 10 = 1.0 | [`traces/canonical/`](traces/canonical/) | `tenant-isolation-docshare__a73K54D` | `run1_failed` 0 of 2211, `run2_failed` 0 of 1540, `leaking_refusals` 0; `held_back` 264, `held_back_sent` 264 |
| alt | a different valid fix (`solution/alt/`): no central helper; every SQL query scoped by the caller's org and role; refusals are 403 instead of 404 | 1 | 1.0 | [`traces/alt/`](traces/alt/) | `tenant-isolation-docshare__rBry9aP` | `run1_failed` 0 of 2211, `run2_failed` 0 of 1540, `leaking_refusals` 0; `held_back` 264, `held_back_sent` 264 |
| nop | Harbor's nop agent: the shipped service, all six planted flaws in place | 0 | 0.0 | [`traces/nop/`](traces/nop/) | `tenant-isolation-docshare__R5XdHAM` | `run1_failed` 1624 of 2211, `run2_failed` 684 of 1412, `leaking_refusals` 768; `held_back` 264, `held_back_sent` 264; held-back writes: `run2_fail_held_status_*` 99 in all, `held_sweep` 40, `held_link` 4; largest: `run1_fail_status_read_bad_x_org_id` and the status and leak checks of downloads and thumbs with a bad `X-Org-Id`, 128 each |
| deny_most | the canonical fix plus: support refused everywhere, link creation refused and `/s/<token>` always 404 | 0 | 0.0 | [`traces/deny_most/`](traces/deny_most/) | `tenant-isolation-docshare__m8bfDuz` | `run1_failed` 142 of 2211, `run2_failed` 152 of 1428, `leaking_refusals` 0; `held_back` 264, `held_back_sent` 264; every failure a permitted request refused: in run 1 the 142 `run1_fail_permitted_*` (largest `permitted_folder_files_support` 24, `permitted_export_support` 20), in run 2 the same plus `write_create_link` 3, `write_link_works` 3 and `held_link` 4 (the read-back's seed links answer 404) |
| drop_org_switching | the canonical fix, but `X-Org-Id` refused unless it names the caller's home org, so support can name none | 0 | 0.0 | [`traces/drop_org_switching/`](traces/drop_org_switching/) | `tenant-isolation-docshare__rEuW5DN` | `run1_failed` 140 of 2211, `run2_failed` 149 of 1436, `leaking_refusals` 0; `held_back` 264, `held_back_sent` 264; every failure a permitted request refused: in run 1 the 140 `run1_fail_permitted_*` (largest `permitted_folder_files_support` 24; support's downloads, reads, thumbs and exports 16 each), in run 2 the same plus 9 `write_*`; no `held_*` failure |
| hardcode_visible_orgs | the canonical fix, but the membership check behind `X-Org-Id` uses a table copied from the visible development data | 0 | 0.0 | [`traces/hardcode_visible_orgs/`](traces/hardcode_visible_orgs/) | `tenant-isolation-docshare__CQ9LLLW` | `run1_failed` 517 of 2211, `run2_failed` 277 of 1540, `leaking_refusals` 249; `held_back` 264, `held_back_sent` 264; held-back writes with a bad `X-Org-Id`: `run2_fail_held_status_rename_bad_x_org_id` 11, `_share_bad_x_org_id` 11, `_revoke_bad_x_org_id` 9, `held_sweep` 8, `held_link` 3; largest: `run1_fail_status_list_files_bad_x_org_id`, `run1_fail_status_list_folders_bad_x_org_id` and `run1_fail_status_me_bad_x_org_id` 46 each |
| membership_plus_get | fixes the header trust and the shared loader only; misses thumbs, export, share and delete | 0 | 0.0 | [`traces/membership_plus_get/`](traces/membership_plus_get/) | `tenant-isolation-docshare__y56Ps4B` | `run1_failed` 230 of 2211, `run2_failed` 125 of 1527, `leaking_refusals` 125; `held_back` 264, `held_back_sent` 264; held-back writes: `run2_fail_held_status_delete` 11, `run2_fail_held_status_share` 9, `held_sweep` 14; largest: `run1_fail_status_export` and `run1_fail_leak_export` 52 each, `run1_fail_status_thumb` and `run1_fail_leak_thumb` 32 each |
| patch_get_only | fixes only the two endpoints the report names (`GET /api/files/<id>` and its `/download`) | 0 | 0.0 | [`traces/patch_get_only/`](traces/patch_get_only/) | `tenant-isolation-docshare__dxymdvz` | `run1_failed` 1182 of 2211, `run2_failed` 520 of 1412, `leaking_refusals` 505; `held_back` 264, `held_back_sent` 264; held-back writes: `run2_fail_held_status_*` 99 in all, `held_sweep` 40, `held_link` 4; largest: `run1_fail_status_thumb_bad_x_org_id` and `run1_fail_leak_thumb_bad_x_org_id` 128 each, `run1_fail_status_rename_bad_x_org_id` and `run1_fail_status_share_bad_x_org_id` 85 each |
| phase_gate | the canonical fix for reads and `X-Org-Id`, writes unchecked: every write refused on the first start of its code copy and allowed on every later start | 0 | 0.0 | [`traces/phase_gate/`](traces/phase_gate/) | `tenant-isolation-docshare__ztBKNYn` | `run1_failed` 0 of 2211, `run2_failed` 139 of 1491, `leaking_refusals` 0; `held_back` 264, `held_back_sent` 264; in run 2 refused writes that run 1 also sent (`run2_fail_noise_status_rename` 6, `_share` 6, `_revoke` 8, `_delete` 6) and held-back ones (`run2_fail_held_status_rename` 15, `_share` 13, `_revoke` 20, `_delete` 19), `held_sweep` 32, `held_link` 4 and 10 `write_*` |
| replay_memo | new on 2026-11-03: the canonical fix for reads, `X-Org-Id` and revokes; rename and link creation back to the original's role-only checks and delete to its login-only check (any file id, in any organisation; a rename still answers through the canonical check, so one outside the active organisation is carried out and then answered 404), behind a guard that refuses and records every such write on the first start of its code copy and on later starts refuses only the recorded ones | 0 | 0.0 | [`traces/replay_memo/`](traces/replay_memo/) | `tenant-isolation-docshare__Ng2ZkEA` | `run1_failed` 0 of 2211, `run2_failed` 60 of 1491, `leaking_refusals` 0; `held_back` 264, `held_back_sent` 264; in run 2 held-back writes only among the refusals: `run2_fail_held_status_delete` 20, `run2_fail_held_status_share` 9, `held_sweep` 26, `held_link` 2, no `run2_fail_noise_*` key; also `write_rename`, `write_create_link` and `write_delete` 1 each |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | [`traces/force-build/`](traces/force-build/) | `tenant-isolation-docshare__qjhkmeV` | `run1_failed` 0 of 2211, `run2_failed` 0 of 1540, `leaking_refusals` 0; `held_back` 264, `held_back_sent` 264 |

The "What it is" column condenses each variant's own description: the comment at the top of `solution/solve.sh` for
canonical and alt, and the `ABOUT.md` of each attempt in `solution/attempts/`. Each failing row also has
`run1_fail_*` and `run2_fail_*` keys not named here; the shipped `reward.json` has them all, and
`verifier/test-stdout.txt` shows up to three examples per failed check.
Two of those `ABOUT.md` files differ from this page on one point each. The one of `replay_memo` says that its rename,
delete and link creation are "back to the original's role-only checks", which fits its rename and link creation but not
its delete: the original's delete checks the login only, one of its six planted flaws. The one of `phase_gate` says that
it "scored 1 on the first version of the grader": that is the grader before the review fix of 2026-10-28, which was
never published, not the earlier grader of the section "First version (earlier grader)", under which `phase_gate` scored
0.0 in run `full1`.

## What each trace folder holds

| File | What it shows |
|---|---|
| `result.json` | Harbor's trial record: the reward and the grader's metrics, the exception if any, phase start and end times (UTC, ending in `Z`), and the trial config |
| `config.json` | the trial config: task path, agent (`oracle` or `nop`) and, for alt and the attempts, the `SOLUTION` variable passed with `--ae` |
| `trial.log` | Harbor's trial log (the builds of the agent and verifier sandboxes and the artifact collection) |
| `agent/oracle.txt` | what `solution/solve.sh` printed in the sandbox (the nop trial has no `agent/` folder) |
| `verifier/reward.txt`, `verifier/reward.json` | the reward Harbor read, and the grader's metrics |
| `verifier/test-stdout.txt` | the verifier's full log (`tests/test.sh` and the grader) |
| `artifacts/manifest.json` | what Harbor downloaded from the agent sandbox for the verifier (the downloaded copy of `/app` itself is not shipped) |
| `job_result.json` | the job-level `result.json`: every trial of that job with its reward (for canonical, all ten), and job start and end times (Mac clock, MST, no zone suffix) |
| `job_lock.json` | the job-level `lock.json`: `harbor.version` (0.25.0), the task digest and the trial settings |

## What the proof shows

Read in all 20 trials of the run (each trial's `verifier/reward.json`, `verifier/test-stdout.txt`, `result.json` and,
for the 19 oracle trials, `agent/oracle.txt`):

- The verifier's privilege steps: each `verifier/test-stdout.txt` starts with the same lock line (below), and its last
  line reports the reward with `killed 0 runner processes`; `verifier_environment_mode` is `separate` in every
  `result.json`.

      [test.sh] lock ok: /logs/verifier 0:0 755, /logs 0:0 755, owner before 0:0; protected_symlinks=1 protected_hardlinks=1 protected_regular=2; setid files left: 0

- The answer key: `tests/grade.py` checks every file listed in `tests/SHA256SUMS` (the hidden database and
  `tests/original/`) before anything else and stops on a mismatch (`check_sums`), printing nothing when all match.
  Every trial logged `2012 refusal cases, 402 permitted reads; 264 refused writes held back for run 2`, which
  `grade()` prints only after that check has passed, and no `reward.json` holds `grader_error`.
- The kit's real-mode steps, which a local run does not take (design record, section 7): in every trial four
  `staged ... for uid 1001 at /work/w<8 hex>` lines, the database checkpoint run as uid 1001 (`ran
  ['/usr/local/bin/python3', '-I', '-c', "import sqlite3, ...`, with `rc=0 timed_out=False` and `net=private
  strays_killed=0`) and no `unreadable (` line. Each trial also has three `service on 127.0.0.1:<port> answered after`
  lines, at 0.20 or 0.21 s.
- Network: `[kit] network isolation: ON (private namespace, loopback only)`, with its probe's `NETNS-OK`, once in
  every trial. That setting covers the commands the kit runs as the runner uid, here the checkpoint; the agent's
  service keeps the host network, a limit of the shared kit (`start_service_as_runner` in `tests/kit.py`; design
  record, section 4, "What a service sees").
- The held-back writes: `held_back` 264 and `held_back_sent` 264 in every `reward.json`, no `held_unsent` key, and in
  every log `held-back writes read back: 41 files and 4 seed links; 14 files they act on were used by the write list
  and not read back`. In 14 trials all 264 went out within the write list (`sent in run 2: 264 (264 in the write
  list, 0 after it)`): the ten canonical trials, alt, force-build, `hardcode_visible_orgs` and `membership_plus_get`.
  In the other six the write list stopped short and the rest were sent after it: `deny_most` 53, `drop_org_switching`
  47, nop and `patch_get_only` 65 each, `phase_gate` and `replay_memo` 11 each.
- The write list: `write list: 50 requests, with 379 refused requests and 264 held-back refused writes mixed in; 0
  steps skipped` in 13 trials (the ten canonical trials, alt, force-build and `hardcode_visible_orgs`); shorter lists,
  each with 0 steps skipped, in `membership_plus_get` (48 requests), `phase_gate` and `replay_memo` (43),
  `drop_org_switching` (36), `deny_most` (35), nop and `patch_get_only` (33). INFERENCE from `tests/grade.py`
  (`share_cycle` returns after a failed link creation, `delete` after a failed delete): the requests that depend on a
  failed step are not sent, so a list is shorter only in a trial that already fails.
- `replay_memo`, as the design record required of this run (section 7): 0.0 with `run1_failed` 0. In run 2,
  `run2_fail_held_status_delete` 20, `run2_fail_held_status_share` 9, `run2_fail_held_sweep` 26 and
  `run2_fail_held_link` 2, and no `run2_fail_noise_*` key: it refused every refused request that run 1 had also sent
  and let held-back writes through. INFERENCE (from those keys and its `ABOUT.md`): its record of run 1's writes
  survived between the two starts on Daytona, so the held-back writes, which run 1 never sent, are what failed it. Its
  three write-list failures (`write_rename`, `write_create_link` and `write_delete`, 1 each) come after held-back
  writes it carried out; its log shows one: a held-back delete of file `aa4f05f5-9234-4dc5-b975-f7f0af77cde4` answered
  204, and the write list's link creation on that file later got 404. On the earlier grader it scored 1 (local runs;
  design record, section 5).
- `phase_gate`, as required (section 7): 0.0 with `run1_failed` 0, and in run 2 both kinds of refused write failing:
  ones that run 1 also sent (`run2_fail_noise_status_rename` 6, `_share` 6, `_revoke` 8, `_delete` 6) and held-back
  ones (`run2_fail_held_status_rename` 15, `_share` 13, `_revoke` 20, `_delete` 19), with `held_sweep` 32 and
  `held_link` 4.
- The local matrix: in each of the 20 trials every count in `reward.json` (the checks and failures of both runs,
  `leaking_refusals` and every `run1_fail_*` and `run2_fail_*` count) equals the row of its variant in the grader's
  local matrix on the same `tests/grade.py` (`../../docs/tenant-isolation-docshare/local_results.txt`, run
  2026-11-03 02:21:36 MST; nop against the local `original`, the shipped service, and force-build against
  `canonical`). Only `grading_seconds` differs; that file does not list `held_back`.
- `agent/oracle.txt`: each of the 19 oracle trials printed `applied <variant> to /app/docshare` (`canonical` for the
  canonical and force-build rows), so the `SOLUTION` variable reached `solve.sh` on Daytona; the nop trial has no
  `agent/` folder.
- Times (the phase lines `phase <name>: <n> checks, <n> failed, <s>s` in `verifier/test-stdout.txt`,
  `grading_seconds` in `verifier/reward.json`, and the Harbor verifier phase from `verifier.started_at` to
  `verifier.finished_at` in `result.json`):

| Rows | `grading_seconds` | phase original / run1 / run2 | Harbor verifier phase |
|---|---|---|---|
| canonical (10 trials) | 4.89-5.78 s | 0.54-0.62 / 2.49-3.21 / 1.73-2.03 s | 12.0-32.2 s |
| alt | 5.56 s | 0.59 / 2.96 / 1.98 s | 21.4 s |
| force-build | 5.51 s | 0.61 / 2.80 / 2.08 s | 39.4 s |
| nop and the seven attempts | 4.84-6.28 s | 0.52-0.68 / 2.69-3.29 / 1.60-2.28 s | 13.2-23.2 s |

The slowest run of a service took 3.29 s (run 1 of `replay_memo`; of a valid fix, 3.21 s, run 1 of a canonical trial)
against the 90 s cap per run that the instruction states (`PHASE_CAP` in `tests/grade.py`); under the earlier grader
the slowest valid run 1 on Daytona took 6.56 s (run `full1`, in the design record). The Harbor verifier phases took
12.0 to 39.4 s against `verifier.timeout_sec` 900 s in `task.toml`.

## How to reproduce

From the repository root, with Harbor 0.25.0 on `PATH`:

    python tools/proof_matrix.py tenant-isolation-docshare --tag <tag> --n 2 --oracle-k 10

Without `--env` (or `HARBOR_ENV`), the script passes `-e docker`, Harbor's default backend. Only Daytona was run for
this task. Run `full2` was the Daytona form (the backend and `-k 10` in `PROOF_RESULTS_full2.md`; two trials at a time
in each `job_lock.json`):

    python tools/proof_matrix.py tenant-isolation-docshare --tag full2 --n 2 --oracle-k 10 --env daytona --env-file <file>

- This task's `task.toml` sets no network line, so the script runs the shipped package itself. Its option
  `--without-agent-network-line` does not apply here: the script stops unless `task.toml` has exactly one `[agent]
  network_mode` line.
- The script runs, per variant, the command below followed by the row's arguments in `PROOF_RESULTS_full2.md`
  (`-a oracle -k 10` for canonical, `-a oracle --ae SOLUTION=<variant>` for alt and the attempts, `-a nop`,
  `-a oracle --force-build`), and writes `PROOF_RESULTS_<tag>.md` and `proof_results_<tag>.json` here. The variants
  come from the package's `solution/` folder.

      harbor run -p tasks/tenant-isolation-docshare -e <env> --env-file <file> -n <n> -o jobs/tenant-isolation-docshare --job-name tenant-isolation-docshare-<variant>-<tag>

- The env file is how Harbor gets the provider's key (`DAYTONA_API_KEY` for Daytona); it is not in the repository.
- `--n 2` runs two trials at a time, as run `full2` did; each agent sandbox has 1 vCPU and 1,024 MB (`[environment]`
  in `task.toml`). The authors' runs also raised Harbor's wait for the environment build three-fold
  (`environment_build_timeout_multiplier` 3.0 in each trial's `config.json`); the script has no option for it.

## Agent trials

No agent (model) trial has run on the current grader. Three trials of Harbor's `terminus-2` agent with the model
`openai/gpt-oss-120b` ran on this task as published in commits `79286dc` to `f5fba52`, on 2026-10-30, so the earlier
grader graded them (section "First version (earlier grader)"): 0 of 3 (below). Their traces are in
`first-version/traces/agent-r3/`.

How an agent fares on the current grader is not known: none of these trials was re-run. INFERENCE (from the three
`terminus-2` trials' `reward.json` and the design record, section 4, where run 1 of the current grader is the earlier
run 1 without the held-back writes, request for request): each of the three failed checks on reads in run 1 (460,
1,280 and 908 of its failed run-1 checks, in the order of the table below), so each would fail the current grader
too. Canonical and alt pass both graders (runs `full1` and `full2`), and four more valid fixes pass the current one
locally (design record, section 7).

The `terminus-2` trials ran outside the proof matrix: Harbor's `terminus-2` agent with the model
`openai/gpt-oss-120b`, served by an OpenAI-compatible model service (its URL is `<model-endpoint>` in the traces), on
Daytona and on the first version's package (the task digest in each agent trace's `job_lock.json` is
`sha256:8295aff32904e8b26a5d2f49369b5a160473f8f5c99367ae5488799f0e87bd3b`, as in run `full1`). They are one job,
`tenant-isolation-docshare-terminus2-gptoss-r3` (`-k 3`, two trials at a time, from 07:13:20 to 07:19:28, Mac clock,
MST; job `result.json`); agent and verifier timeouts were those of `task.toml` (agent 1,800 s), and Harbor waited up
to three times its default image-build time (`--environment-build-timeout-multiplier 3`). Every trial finished without
an exception (`result.json`). None passed: 0 of 3. Flaw numbers are those of the six planted flaws in
`../../docs/tenant-isolation-docshare/DESIGN.md` section 3; the check counts are the earlier grader's (2,475 run-1 and
1,231 run-2 checks for a valid fix).

| Trial | Episodes | Agent phase | Reward | What the trial's files show | Trace |
|---|---|---|---|---|---|
| `tenant-isolation-docshare__U5her8X` | 11 | 162 s | 0.0 | `files.py`, `thumbs.py`, `export.py` and `share.py` edited: flaws 1, 3, 4 and 5 closed unless the request names another org in `X-Org-Id`; flaw 2 (`X-Org-Id` trusted without a membership check) and flaw 6 (delete not limited to org_admin) open. Run 1: 643 of 2,475 checks failed; run 2: 246 of 1,231; 257 leaking refusals | [`first-version/traces/agent-r3/tenant-isolation-docshare__U5her8X/`](first-version/traces/agent-r3/tenant-isolation-docshare__U5her8X/) |
| `tenant-isolation-docshare__9n7yLqH` | 12 | 151 s | 0.0 | no source file changed: both edit commands called `apply_patch`, which is not in the image (`command not found`), and no later command edited a file. `reward.json` equals the first version's nop trace except `grading_seconds` (run 1: 1,742 of 2,475 failed; run 2: 603 of 1,139; 785 leaking refusals) | [`first-version/traces/agent-r3/tenant-isolation-docshare__9n7yLqH/`](first-version/traces/agent-r3/tenant-isolation-docshare__9n7yLqH/) |
| `tenant-isolation-docshare__5JS5qnC` | 15 | 140 s | 0.0 | `thumbs.py`, `export.py` and `share.py` edited: flaws 3, 4 and 5 closed as above; the reported flaw 1, flaw 2 and flaw 6 open; support users' thumbnail and export requests now refused (400 instead of 200). Run 1: 1,246 of 2,475 failed; run 2: 433 of 1,139; 515 leaking refusals | [`first-version/traces/agent-r3/tenant-isolation-docshare__5JS5qnC/`](first-version/traces/agent-r3/tenant-isolation-docshare__5JS5qnC/) |

Episodes are `n_episodes` and the agent phase runs from `agent_execution.started_at` to `finished_at`, both in each
trial's `result.json`; the check counts are from `verifier/reward.json`. The edited files are under
`docshare/routes/`. Each of these trace folders holds the files of a proof trace except `agent/oracle.txt`; its
`agent/` holds `trajectory.json`, `terminus_2.pane` and `recording.cast` instead.

What the trials show:
- In every trial most failed run-1 checks are requests whose `X-Org-Id` names an org the caller may not use (the
  `*_bad_x_org_id` keys of `verifier/reward.json`: 577 of 643, 1,309 of 1,742 and 1,007 of 1,246, in the order of the
  table).
- All three agents read `/app/docs/PERMISSIONS.md`, which states the membership rule (section 2) and that only
  org_admin deletes (section 3), and each marked the task complete after the 9 visible tests passed; those tests pass
  on the unfixed service too (`../../docs/tenant-isolation-docshare/DESIGN.md` section 2).
- Reading (INFERENCE, from these files): capability gaps the task targets (a complete audit of every code path and of
  the identity layer, follow-through on the rules read, checking the result), not a task defect. In `9n7yLqH`, whose
  edits never landed, the 0.0 reflects a failed tool call left unchecked more than the audit.

Network: the first version's `task.toml` sets no `network_mode` (nor does the current one), so the trials ran with
Harbor 0.25.0's default public network. They started at 14:13 UTC on 2026-10-30, after this repository was created on
GitHub (07:08 UTC the same day), and the Daytona account of these runs is on Tier 1, which keeps GitHub reachable
(repository README), so a fetch of the public hidden tests was possible. Every trajectory, terminal pane and recording
was read for one: no GitHub host (`github.com`, `*.github.com`, `*.githubusercontent.com`) and neither the
repository's nor its owner's name appears in any of them, and no command used the network. The one URL in any
command, `http://www.w3.org/2000/svg` in two trials, is the SVG namespace string of the thumbnail code those agents
rewrote, not a request. No trial was excluded.

## First version (earlier grader) (`first-version/`)

The package as published in commits `79286dc` to `f5fba52` (Harbor digest
`sha256:8295aff32904e8b26a5d2f49369b5a160473f8f5c99367ae5488799f0e87bd3b`, 88 files, the digest in each of its
traces' `job_lock.json`) had the earlier grader. On 2026-11-03 only the grader changed, `tests/grade.py` (the
held-back refused writes, their drain, the check `held_unsent`, the logged counts and the read-back), and the attempt
`solution/attempts/replay_memo/` (8 files) was added. The instruction, `task.toml`, `environment/` (the service and
its six planted flaws), the hidden data, `tests/SHA256SUMS`, the shared kit and the canonical and alt solutions are as
published. The earlier grader's run 2 sent only refused requests that run 1 had already sent, and both runs start the
service from the same copy of `/app`, so a service that recorded the refused writes of its first start and later
refused only those scored 1 with write authorization unfixed: `replay_memo` did, in local runs (design record,
section 5). Under that grader a valid fix had 2,475 run-1 and 1,231 run-2 checks, and every refused write was sent in
run 1.

Its evidence, at the top of this folder in commit `f5fba52`, is now in `first-version/`, every file byte for byte as
it was there:

- Proof run `full1` (`PROOF_RESULTS_full1.md`, `proof_results_full1.json`, `run_full1.log`), Harbor 0.25.0 on
  Daytona, 2026-10-28 from 19:45:27 to 19:56:43 MST (job `result.json`): ALL AS EXPECTED, 10 variants and 19 trials
  (canonical 10 of 10 = 1.0, alt and force-build 1.0, nop and the six attempts of that time 0.0; `replay_memo` did not
  exist yet).
- `first-version/traces/<variant>/`: one trial per variant of `full1` (canonical `tenant-isolation-docshare__rCxcLLy`,
  the earliest-started of its ten), and `first-version/traces/agent-r3/<trial>/`, the three `terminus-2` trials
  (section "Agent trials"); `first-version/traces/REDACTIONS.md` lists what was replaced in their copies. The first
  version's design record is `git show f5fba52:docs/tenant-isolation-docshare/DESIGN.md`.
- The fresh-clone run `clone2` (`PROOF_RESULTS_clone2.md`, `proof_results_clone2.json`): on 2026-10-30 this
  repository was cloned from GitHub at commit `495c9f5` (06:18, Mac clock, MST), and `tools/proof_matrix.py` ran this
  task from the clone on Daytona with Harbor 0.25.0, canonical once (`-a oracle -k 1`) and nop once (`-a nop`), one
  trial at a time; the two rows started at 07:01:08 and 07:02:10 MST, and the files were written at 07:02:39 MST.
  Rewards: canonical [1.0], nop [0.0]; ALL AS EXPECTED. The task digest in both jobs' `lock.json` is
  `sha256:8295aff32904e8b26a5d2f49369b5a160473f8f5c99367ae5488799f0e87bd3b`, so the clone graded the same package as
  `full1`. Harbor waited up to three times its default image-build time (`--environment-build-timeout-multiplier 3`)
  because Daytona's status page reported degraded performance for a subset of US runners that morning; task, agent and
  verifier timeouts were those of `task.toml`. Only the two results files are shipped from this run (no traces, no run
  log).

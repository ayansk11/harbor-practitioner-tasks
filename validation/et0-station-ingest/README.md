# Validation: et0-station-ingest

Last updated: 2026-11-04, 00:38 MST (Mac clock): the second smoke attempt is given only the figures of its row in
`../agent_trials_m1.json` (`RateLimitError` after 28 s of agent time), and the review's re-run of `wKcgixc`'s code
without its wind line is marked as recorded outside this repository.
Before that, 2026-11-03, 17:25 MST (Mac clock; late edits to 20:39 MST by the file's time): the section "Agent trials"
adds run m1 of 2026-11-03 (eight `terminus-2` trials with four models, 7 of 8 pass, traces in `traces/agent-m1/`; two
smoke attempts gave no result); the summary line, the file list, the trace notes, the pilot's closing paragraph and the
notes count them.
Before that, 2026-10-31 (Mac clock, MST).

**Final run: `full1`.** Harbor 0.25.0 on Daytona, 2026-10-28 from 19:45:27 to 19:56:20 (Mac clock, MST; job `result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full1.md`).

**Fresh-clone run: `clone2`.** The task as published in commit `495c9f5`, run again from a fresh clone of the GitHub repository on 2026-10-30: canonical 1.0, nop 0.0, ALL AS EXPECTED (section "Fresh-clone run").

**Agent trials:** 11 trials of Harbor's `terminus-2` agent: 7 of 8 pass in run m1 of 2026-11-03 (four models), and 0 of
3 before it (the pilot of 2026-10-29 and two trials of 2026-10-30, one model); two smoke attempts of run m1 gave no
result (sections "Agent pilot" and "Agent trials").

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py` (for the pre-check `smoke` and the fresh-clone run `clone2`, the first two only).
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below); `traces/agent-pilot/`: the agent pilot (section "Agent pilot"); `traces/agent-r3/<trial>/`: the agent trials of 2026-10-30 (section "Agent trials").
- `traces/agent-m1/<trial>/`: the eight agent trials of run m1 of 2026-11-03 (section "Agent trials").
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies, and the model service's URL in the agent traces' copies.
- `traces/agent-m1/REDACTIONS.md`: the same for the copies of run m1.
- `NOTES.md`: what the run showed beyond the rewards.

The "Job folder" column of the `PROOF_RESULTS_*.md` files points into `jobs/`, the raw Harbor output (for `clone2`, the `jobs/` folder of the fresh clone). `jobs/` is git-ignored and not part of the repository; the trace folders below are the shipped copy.

## Results and traces

One trial per variant is shipped. Variants with one trial ship that trial. For canonical (ten trials) the shipped trial is the one with the earliest `started_at` in its `result.json`; its `job_result.json` holds the rewards of all ten. The last column is read from the shipped trial's `verifier/reward.json`.

| Variant | What it is | Expected | Rewards (all trials of the job) | Run | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|---|
| canonical | reference fix: convert at load time (FAO-56 Eq. 47 wind height, W/m2 to MJ) and fix the southern-latitude sign | 1 | 10 of 10 = 1.0 | `full1` | [`traces/canonical/`](traces/canonical/) | `et0-station-ingest__ezrRVNG` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance), hidden run rc 0 |
| alt | a different valid fix: keep raw readings, convert inside the FAO-56 call chain, regex latitude parser | 1 | 1.0 | `full1` | [`traces/alt/`](traces/alt/) | `et0-station-ingest__iveydVi` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance), hidden run rc 0 |
| nop | Harbor's nop agent: the three defects stay | 0 | 0.0 | `full1` | [`traces/nop/`](traces/nop/) | `et0-station-ingest__KVxKDWV` | `app_locked` 1; visible ok 0 (max error 66.684361 mm/day, 0 rows missing, 2184 over tolerance); hidden ok 0 (max error 67.411037 mm/day, 0 rows missing, 3461 over tolerance), hidden run rc 0 |
| abs_app_path | defence probe: conversion constants read from a config file by an absolute `/app` path | 0 | 0.0 | `full1` | [`traces/abs_app_path/`](traces/abs_app_path/) | `et0-station-ingest__5Fm7A6i` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 0 (no rows to compare (`max_abs_err` -1.0), 3651 rows missing, 0 over tolerance), hidden run rc 1 |
| fit_to_metservice | fixes the radiation units, then calibrates to the met-service sample | 0 | 0.0 | `full1` | [`traces/fit_to_metservice/`](traces/fit_to_metservice/) | `et0-station-ingest__MqcH3kN` | `app_locked` 1; visible ok 0 (max error 1.455069 mm/day, 0 rows missing, 1597 over tolerance); hidden ok 0 (max error 1.378314 mm/day, 0 rows missing, 3073 over tolerance), hidden run rc 0 |
| fix_altitude | follows the misleading altitude lead (changes the formula code) plus the units fix | 0 | 0.0 | `full1` | [`traces/fix_altitude/`](traces/fix_altitude/) | `et0-station-ingest__r5BbKJx` | `app_locked` 1; visible ok 0 (max error 1.451069 mm/day, 0 rows missing, 1898 over tolerance); hidden ok 0 (max error 1.445369 mm/day, 0 rows missing, 2901 over tolerance), hidden run rc 0 |
| hardcode_output | a one-off script writes a correct visible `et0.csv`; the pipeline stays broken | 0 | 0.0 | `full1` | [`traces/hardcode_output/`](traces/hardcode_output/) | `et0-station-ingest__K2dYS5L` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 0 (max error 67.411037 mm/day, 0 rows missing, 3461 over tolerance), hidden run rc 0 |
| linear_wind | a single 10 m wind factor (0.75) instead of FAO-56 Eq. 47 | 0 | 0.0 | `full1` | [`traces/linear_wind/`](traces/linear_wind/) | `et0-station-ingest__ETJJkV3` | `app_locked` 1; visible ok 0 (max error 0.751535 mm/day, 0 rows missing, 730 over tolerance); hidden ok 0 (max error 1.139314 mm/day, 0 rows missing, 2693 over tolerance), hidden run rc 0 |
| nearest_height | Eq. 47 factors for the visible mast heights only; other heights use the nearest one | 0 | 0.0 | `full1` | [`traces/nearest_height/`](traces/nearest_height/) | `et0-station-ingest__kCVjMH6` | `app_locked` 1; visible ok 1 (max error 0.001172 mm/day, 0 rows missing, 0 over tolerance); hidden ok 0 (max error 0.434041 mm/day, 0 rows missing, 2174 over tolerance), hidden run rc 0 |
| read_answers | defence probe: the unfixed pipeline copies the grader's expected values if it can read them | 0 | 0.0 | `full1` | [`traces/read_answers/`](traces/read_answers/) | `et0-station-ingest__nqjSQ34` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 0 (max error 67.411037 mm/day, 0 rows missing, 3461 over tolerance), hidden run rc 0 |
| symlink_output | defence probe: canonical fix, then the output is replaced by a symlink into `/tests` | 0 | 0.0 | `full1` | [`traces/symlink_output/`](traces/symlink_output/) | `et0-station-ingest__kgRb5cS` | `app_locked` 1; visible ok 0 (no rows to compare (`max_abs_err` -1.0), 2920 rows missing, 0 over tolerance); hidden ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance), hidden run rc 0 |
| units_not_latitude | fixes wind height and radiation units, not the southern-latitude sign | 0 | 0.0 | `full1` | [`traces/units_not_latitude/`](traces/units_not_latitude/) | `et0-station-ingest__UuEkT2z` | `app_locked` 1; visible ok 0 (max error 1.405081 mm/day, 0 rows missing, 715 over tolerance); hidden ok 0 (max error 1.106565 mm/day, 0 rows missing, 1027 over tolerance), hidden run rc 0 |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | `full1` | [`traces/force-build/`](traces/force-build/) | `et0-station-ingest__p2Z8pSw` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance), hidden run rc 0 |

Command for each row: `harbor run -p tasks/et0-station-ingest -e daytona --env-file <file> -n <n> -o jobs/et0-station-ingest --job-name et0-station-ingest-<variant>-<run>` followed by the row's arguments in `PROOF_RESULTS_<run>.md` (`-a oracle -k 10` for canonical, `-a oracle --ae SOLUTION=<variant>` for the others, `-a nop`, `-a oracle --force-build`). The env file is how Harbor gets the Daytona key (`DAYTONA_API_KEY`); it is not in the repository.

## What each trace folder holds

Each `traces/<variant>/` folder holds the files of one Harbor trial, copied from the job folder of the final run
(`traces/agent-pilot/`, each `traces/agent-r3/<trial>/` and each `traces/agent-m1/<trial>/`, from the job folder of
that agent trial):

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

`traces/REDACTIONS.md` lists the machine-specific paths that were replaced in these copies, and the model service's URL in the agent traces (`traces/agent-pilot/`, `traces/agent-r3/`). Nothing else was changed.
`traces/agent-m1/REDACTIONS.md` lists the same for the copies of run m1.

## Fresh-clone run

Run `clone2` ([`PROOF_RESULTS_clone2.md`](PROOF_RESULTS_clone2.md), `proof_results_clone2.json`) checks the published
package. On 2026-10-30 this repository was cloned from GitHub at commit `495c9f5` (06:18, Mac clock, MST), and
`tools/proof_matrix.py` ran this task from the clone on Daytona with Harbor 0.25.0, from 07:00:24 to 07:01:08 (Mac clock,
MST): canonical once (`-a oracle -k 1`) and nop once (`-a nop`), one trial at a time. Rewards: canonical [1.0], nop
[0.0]; overall ALL AS EXPECTED. The task digest in both jobs' `lock.json` is the one in this folder's `job_lock.json`
files (`sha256:d12ec221a0433f886ecefc347a4c5a59b7507b708fd28cc6057d959481422120`), so the clone graded the same package
as `full1`. Harbor waited up to three times its default image-build time (`--environment-build-timeout-multiplier 3`)
because Daytona's status page reported degraded performance for a subset of US runners that morning; task, agent and
verifier timeouts were those of `task.toml`. Only the two results files are shipped from this run (no traces, no run
log).

## Agent pilot

One trial of a model agent, outside the proof matrix: Harbor's `terminus-2` agent with `openai/gpt-oss-120b`, served by an
OpenAI-compatible model service (its URL is `<model-endpoint>` in the trace), on 2026-10-30 from 00:31:00 to 00:41:03
UTC (2026-10-29, 17:31 to 17:41 on the Mac clock, MST). It ran on the same task package as `full1`: the task digest in
`traces/agent-pilot/job_lock.json` equals the one in the other traces. Reward 0.0. The trace,
[`traces/agent-pilot/`](traces/agent-pilot/), holds the same files as the others except `agent/oracle.txt`, plus the agent's
record (`agent/trajectory.json`: the prompt and 29 agent steps), its terminal pane (`agent/terminus_2.pane`) and a
terminal recording (`agent/recording.cast`). The downloaded `/app` is not shipped; the agent's final code is in
`agent/trajectory.json`: its last `cat > et0/ingest.py` (step 23) and its `cat > et0/pipeline.py` (step 28).

What the trace shows:
- The agent rewrote `et0/ingest.py` with the wind-height conversion (FAO-56 Eq. 47) and the radiation-unit conversion.
  It read `et0/meta.py`, judged its latitude parsing correct (step 9) and left it unchanged, so the southern-latitude
  defect stayed.
- It compared the first five days of one station (PAL) with the met-service sample, whose values are given to 0.1
  mm/day, and never looked at the sample's other station, CDB, which is in the southern hemisphere; then it made the
  pipeline round every value to 0.1 mm/day. Rounding alone can move a value by up to 0.05 mm/day, more than the 0.03
  tolerance.
- It ran the pipeline only with `--out output/et0_fixed.csv` and never regenerated `/app/output/et0.csv`, which the
  instruction asks for; then it marked the task complete.
- The visible check read the untouched `/app/output/et0.csv`: 2,184 of 2,920 rows over the tolerance, max error 66.68
  mm/day, the same as the nop trial. The hidden run of the agent's pipeline: 2,016 of 3,651 rows over the tolerance,
  max error 1.09 mm/day (`verifier/reward.json`, `verifier/test-stdout.txt`).

The trial ended on 2026-10-30 at 00:41 UTC, before this repository was created on GitHub (07:08 UTC the same day), and
none of its commands used the network. Two more trials with the same model followed on 2026-10-30, and eight with four
models in run m1 of 2026-11-03 (section "Agent trials"; what they mean for the `difficulty` label in `task.toml` is in
`../../docs/et0-station-ingest/DESIGN.md` section 11, limitation 2).

## Agent trials

Eleven trials of Harbor's `terminus-2` agent have been graded on this task, outside the proof matrix, all on the same
task package as `full1` (the task digest in each agent trace's `job_lock.json` equals the one in the other traces):
eight in run m1 of 2026-11-03 with four models (7 of 8 passed), and three with `openai/gpt-oss-120b`, the pilot of
2026-10-29 and two trials of 2026-10-30 (0 of 3; section "Agent pilot" and subsection "Earlier trials (2026-10-29 and
2026-10-30)"). Run m1 also made two smoke attempts on this task that gave no result (below).

### Run m1 (2026-11-03)

Eight trials of Harbor 0.25.0's `terminus-2` agent: two attempts with each of four models of an OpenAI-compatible
model service (its URL is `<model-endpoint>` in the traces). The models are named as the service names them (each
`config.json` gives the name with LiteLLM's `openai/` prefix); which weights served them is UNVERIFIED. `terminus-2`
runs its loop on the machine that runs Harbor, which calls the model service, and the model's commands in the task's
Daytona sandbox. Each trial is a job of its own, `et0-station-ingest-terminus2-<tag>-m1-<attempt>` (`<tag>` a short
model tag such as `gemma4-31b`, `glm53flash`, `gptoss120b` or `qwen38-27b`; each `config.json` gives the job's
`trials_dir`; `n_concurrent_trials` 1 in each `job_lock.json`); the eight jobs ran from 09:15:28 to 09:25:29 (Mac
clock, MST; each `job_result.json`), up to four at a time. Agent and verifier timeouts were those of `task.toml`
(agent 1,800 s; `timeout_multiplier` 1.0), and Harbor waited up to three times its default image-build time
(`environment_build_timeout_multiplier` 3.0). Every trial finished without an exception (`result.json`). Seven
passed: 7 of 8. The run's rows for all five tasks are in `../agent_trials_m1.json`;
[`traces/agent-m1/REDACTIONS.md`](traces/agent-m1/REDACTIONS.md) lists what was replaced in these copies.

| Trial | Model | Attempt | Episodes | Agent seconds | Reward | What the trial's files show | Trace |
|---|---|---|---|---|---|---|---|
| `et0-station-ingest__vQFWbAG` | gemma-4-31B-it | 1 | 16 | 100 | 1.0 | pass: the three defects fixed in `et0/meta.py` and `et0/ingest.py`; judged by a plausible station mean and the self-check; its two looks at the met-service sample after the fix (steps 14 and 15) set no day of the sample beside the same day of its output | [`traces/agent-m1/et0-station-ingest__vQFWbAG/`](traces/agent-m1/et0-station-ingest__vQFWbAG/) |
| `et0-station-ingest__A56ZWSZ` | gemma-4-31B-it | 2 | 18 | 106 | 1.0 | pass: the three fixed; PAL and the first ten CDB days checked against the sample | [`traces/agent-m1/et0-station-ingest__A56ZWSZ/`](traces/agent-m1/et0-station-ingest__A56ZWSZ/) |
| `et0-station-ingest__y4XU2MG` | glm-5.3-flash | 1 | 19 | 290 | 1.0 | pass: the three fixed (Eq. 47 as a new helper in `et0/fao56.py`; no ET0 formula changed); PAL and CDB within 0.05 mm/day of the sample; a run as `nobody` from a copy | [`traces/agent-m1/et0-station-ingest__y4XU2MG/`](traces/agent-m1/et0-station-ingest__y4XU2MG/) |
| `et0-station-ingest__qhwGNJ4` | glm-5.3-flash | 2 | 12 | 203 | 1.0 | pass: the three fixed; compared with the sample before and after the fix, and ET0 written again on its own for a row-by-row check | [`traces/agent-m1/et0-station-ingest__qhwGNJ4/`](traces/agent-m1/et0-station-ingest__qhwGNJ4/) |
| `et0-station-ingest__eZGoutP` | gpt-oss-120b | 1 | 6 | 50 | 1.0 | pass: the three named in its analysis after reading the sources (step 4) and fixed; no sample comparison; the shortest trial | [`traces/agent-m1/et0-station-ingest__eZGoutP/`](traces/agent-m1/et0-station-ingest__eZGoutP/) |
| `et0-station-ingest__wKcgixc` | gpt-oss-120b | 2 | 29 | 481 | 0.0 | fail: wind height and radiation units fixed, the hemisphere sign missed (`et0/meta.py` unchanged), then a wind cut (x0.3 above 1,500 m) to fit the sample's January rows. Visible: 1,080 rows over the tolerance (max error 1.842164 mm/day); hidden: 1,392 (max 1.669566 mm/day) | [`traces/agent-m1/et0-station-ingest__wKcgixc/`](traces/agent-m1/et0-station-ingest__wKcgixc/) |
| `et0-station-ingest__Fd3SWyE` | qwen3.8-27b | 1 | 11 | 141 | 1.0 | pass: the three listed before it ran the pipeline or the self-check, then fixed; all 730 PAL and CDB sample rows within 0.05 mm/day (the sample's rounding); a run from a copy of `/app` | [`traces/agent-m1/et0-station-ingest__Fd3SWyE/`](traces/agent-m1/et0-station-ingest__Fd3SWyE/) |
| `et0-station-ingest__FWn3aTq` | qwen3.8-27b | 2 | 9 | 125 | 1.0 | pass: the three fixed; the sample compared (largest difference 0.050 mm/day); a run from a copy; a 2.0 m shortcut skips Eq. 47's factor there (1.000222), hence its max error of 0.001172 (visible) and 0.001187 (hidden) mm/day | [`traces/agent-m1/et0-station-ingest__FWn3aTq/`](traces/agent-m1/et0-station-ingest__FWn3aTq/) |

Episodes are `n_episodes` (`agent_result.metadata`) and agent seconds the agent phase, from
`agent_execution.started_at` to `finished_at`, rounded as in `../agent_trials_m1.json`, both from each trial's
`result.json`; the row counts and errors are from `verifier/reward.json`. The column "What the trial's files show"
condenses the authors' review of the run (by model agents, recorded outside this repository), which read every
trajectory, compared each final `/app` with the package and ran each final pipeline again on the visible and hidden
stations.

The two smoke attempts came first, with the model `openai/gpt-oss-20b` on Groq's free plan (the two rows of this task
with no trace in `../agent_trials_m1.json`; not shipped). Neither gave a result: the first failed on a configuration
error of the authors' run script (`AuthenticationError`, after 2 s of agent time), and the second hit the plan's rate
limit (`RateLimitError`) after 28 s of agent time. Neither ran a command or reached the
verifier, and neither counts in the eight.

What run m1 shows:
- The seven passes: in each `reward.json`, 0 rows over the 0.03 mm/day tolerance on the visible output and on the
  hidden run (max error 0.0005 mm/day; `FWn3aTq` above), hidden run rc 0. Each fixed the three input defects for any
  register: FAO-56 Eq. 47 from each station's `wind_height_m`, the 0.0864 factor for `W/m2`, and the sign of an "S"
  latitude. None changed an ET0 formula, and none followed the misleading altitude lead. Five of the seven also checked
  PAL and CDB against the met-service sample; `vQFWbAG` and `eZGoutP` passed on METHOD.md alone. Reading (INFERENCE,
  from each trial's final code against the task's `environment/app`, its commands, and the review's runs of each final
  pipeline, which reproduced every `reward.json` and gave 0 rows over the tolerance on ten more stations in METHOD.md
  forms the hidden set lacks, such as "45S", "0.50S" and heights from 1.0 to 19.5 m): every pass is a genuine, general
  fix; none hard-codes output, edits a check or reads `/tests`.
- The failure (`wKcgixc`) missed the hemisphere sign, as all three earlier trials did. It then compared its annual PAL
  mean with the January rows at the top of the met-service sample, multiplied the wind by 0.3 for stations above
  1,500 m (`et0/ingest.py`), and closed by claiming that its pipeline follows FAO-56 exactly. Run again by the review
  without that line (a run recorded outside this repository), its code gives 715 visible and 1,027 hidden rows over the
  tolerance (max error 1.405081 and 1.106565 mm/day), the figures of the shipped attempt `units_not_latitude` (its row
  above): the altitude lead was followed in one trial, which already failed on the hemisphere sign, and decided none.
  Its only read of `docs/METHOD.md` (step 3) came back cut, so sections 3.1 to 3.3, with the rule that "34.92S" is
  -34.92, never reached it (the observation carries `terminus-2`'s marker "70 interior bytes omitted"; see the harness
  note below). It still read `return float(text.rstrip("NS"))` in `et0/meta.py`, "south negative" in METHOD.md section 1
  and in the `et0/fao56.py` docstring, and "34.92S" in `config/stations.yaml`, so the failure stays a capability gap the
  task targets, not a task defect (INFERENCE, the review's).
- Reading (INFERENCE, from these counts): the task is easy for `gemma-4-31B-it`, `glm-5.3-flash` and `qwen3.8-27b`
  (6 of 6, in 100 to 290 s of the 1,800 s), and `gpt-oss-120b` passed 1 of 2. Over the 11 graded `terminus-2` trials,
  `gpt-oss-120b` has passed 1 of 5 and the three other models 6 of 6, so the earlier 0 of 3 reflected one model, not
  the task. The code points at the defects: `et0/ingest.py` comments the raw columns as already "m/s at 2 m" and
  "MJ m-2 day-1" (lines 35 and 36), and `et0/meta.py` drops the hemisphere letter in one line (line 29). The same three
  models passed the four tasks other than `feature-leakage-churn` in 23 of 24 attempts (`../agent_trials_m1.json`).
  Two attempts per model are counts, not pass rates, and a low pass rate is not the goal in itself; the `difficulty`
  label (`easy-medium` in `task.toml`) is discussed in `../../docs/et0-station-ingest/DESIGN.md` section 11,
  limitation 2.
- Informational: a lower-case `w/m2`, a form METHOD.md does not list, splits the passes (some leave it unconverted,
  some raise an error as the canonical does, some convert it). No hidden station uses it (passes that leave it
  unconverted scored 1.0) and the instruction does not ask for it, so it is not a gap.
- A harness note: Harbor 0.25.0's `terminus-2` cuts each long observation twice, so the size its marker reports
  understates what was cut (`_limit_output_length` in `harbor/agents/terminus_2/terminus_2.py`). Four passing trials
  of this task got cut observations too, and each saw METHOD.md section 3.2 in another read; in the failing trial the
  cut one is the METHOD.md read of `wKcgixc` above. No verdict depends on it.

Network: this task's `task.toml` sets no network line, so the trials ran with Harbor 0.25.0's default public network,
long after this repository became public, and a fetch of the public hidden tests was possible. The agent's loop ran on
the machine that runs Harbor and called the model service from there; only the model's commands ran in the sandbox.
Every trajectory, terminal pane and recording was read for network use: no URL, no network command (such as `curl`,
`wget`, `pip`, `apt`, `nc`, `ssh` or `ping`) and no network code in any command; no GitHub host (`github.com`,
`*.github.com`, `*.githubusercontent.com`) and neither the repository's nor its owner's name appears in any of them.
The only hits were not network use: `wget` in the first prompt of `terminus-2` itself, a JSON-escaped newline before
`cat`, and the local file `reference/metservice_et0_2025.csv`. No command read `/tests`, `/logs` or the hidden data.
No trial was excluded.

### Earlier trials (2026-10-29 and 2026-10-30)

Three trials ran before run m1: the pilot of 2026-10-29 (section "Agent pilot") and two trials on 2026-10-30. All three
used Harbor's `terminus-2` agent with the model `openai/gpt-oss-120b`, served by an OpenAI-compatible model service
(its URL is `<model-endpoint>` in the traces), on Daytona and on the same task package as `full1` (the task digest in
each agent trace's `job_lock.json` equals the one in the other traces).
The two trials of 2026-10-30 are one job, `et0-station-ingest-terminus2-gptoss-r3` (`-k 2`, both at once, from
07:07:52 to 07:12:12, Mac clock, MST; job `result.json`); agent and verifier timeouts were those of `task.toml` (agent
1,800 s), and Harbor waited up to three times its default image-build time
(`--environment-build-timeout-multiplier 3`). Every trial finished without an exception (`result.json`). None passed:
0 of 3.

| Trial | Date (Mac clock) | Episodes | Agent phase | Reward | What the trial's files show | Trace |
|---|---|---|---|---|---|---|
| `et0-station-ingest__pKWPTuY` (pilot) | 2026-10-29 | 29 | 521 s | 0.0 | wind height and radiation units converted; the latitude parsing read and kept; `/app/output/et0.csv` never regenerated (section "Agent pilot") | [`traces/agent-pilot/`](traces/agent-pilot/) |
| `et0-station-ingest__Ac3eDsn` | 2026-10-30 | 11 | 72 s | 0.0 | wind height (FAO-56 Eq. 47) and radiation units converted in `et0/ingest.py`, output regenerated; `et0/meta.py` unchanged, so the southern-latitude sign stays wrong | [`traces/agent-r3/et0-station-ingest__Ac3eDsn/`](traces/agent-r3/et0-station-ingest__Ac3eDsn/) |
| `et0-station-ingest__TwBGkQK` | 2026-10-30 | 17 | 230 s | 0.0 | the same two conversions in `et0/ingest.py`, output regenerated; `et0/meta.py` unchanged | [`traces/agent-r3/et0-station-ingest__TwBGkQK/`](traces/agent-r3/et0-station-ingest__TwBGkQK/) |

Episodes are `n_episodes` and the agent phase runs from `agent_execution.started_at` to `finished_at`, both in each
trial's `result.json`.

What the two trials of 2026-10-30 show (`verifier/reward.json`, and each trial's final code against the task's
`environment/app`):
- Both changed `et0/ingest.py` and regenerated `output/et0.csv`; `et0/fao56.py` is unchanged, so neither followed the
  misleading altitude lead. Neither changed `et0/meta.py`, which drops the hemisphere letter of a text latitude,
  although `/app/docs/METHOD.md` states that "34.92S" is the same place as -34.92.
- Both end with exactly the figures of the shipped attempt `units_not_latitude` (its row above; its `ingest.py` is the
  canonical one, its `meta.py` the original): visible 715 of 2,920 rows over the tolerance, max error 1.405081 mm/day;
  hidden 1,027 of 3,651 rows over the tolerance, max error 1.106565 mm/day.
- The met-service sample shows the error: against it, both outputs match PAL to the sample's 0.1 mm/day rounding, while
  CDB, its southern station, is off by more than 0.05 mm/day on 351 of 365 days (up to 1.118 mm/day).
- Reading (INFERENCE, from these files): a capability gap the task targets (finding all three input defects and checking
  the output against the sample), not a task defect: the missed rule is in the task's own material.

Network: this task's `task.toml` sets no `network_mode`, so every trial ran with Harbor 0.25.0's default public
network. The trials of 2026-10-30 started at 14:07 UTC, after this repository was created on GitHub, and the Daytona
account of these runs is on Tier 1, which keeps GitHub reachable (repository README, "Known limitations"), so a fetch of
the public hidden tests was possible. Every trajectory, terminal pane and recording was read for one: no GitHub host
(`github.com`, `*.github.com`, `*.githubusercontent.com`) and neither the repository's nor its owner's name appears in
any of them, and no command used the network. No trial was excluded.

## Notes

- A smoke run (`PROOF_RESULTS_smoke.md`: canonical with one trial 1.0, nop 0.0) ran just before `full1` as a pre-check. No traces are shipped from it.
- This task's `solve.sh` prints no `applied <variant>` line; `agent/oracle.txt` holds the pipeline's own output. The evidence that each `SOLUTION` reached `solve.sh` is that each attempt's errors in `verifier/reward.json` match the local results in `../../docs/et0-station-ingest/DESIGN.md` section 9.
- The three defence probes (from NOTES.md): `read_answers` scored 0 because the agent's user could not read `/tests` (an INFERENCE, see NOTES.md); `abs_app_path` scored 0 because the grader made `/app` unavailable before running the agent's code (`app_locked` 1, hidden run rc 1); `symlink_output` scored 0 because Harbor's artifact step did not keep the symlink into `/tests`, so the verifier saw no output file. For `symlink_output`, three files show this: `trial.log` (Harbor's traceback from the artifact download), `artifacts/manifest.json` (`/app` has status `failed`) and `artifacts/app_output_listing.txt` (a listing, made on 2026-10-29 from the local job folder, showing that the downloaded `output/` folder was empty). The grader's own symlink defence was therefore not exercised on Daytona.
- Eleven agent (model) trials were graded for this task, outside the matrix: three in 2026-10 and eight in run m1 of
  2026-11-03, beside two smoke attempts of run m1 that gave no result (sections "Agent pilot" and "Agent trials"); the
  matrix uses Harbor's `oracle` and `nop` agents only.

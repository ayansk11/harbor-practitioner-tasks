# Five Harbor tasks: take-home submission (MTS)

Five Harbor task packages, each a piece of practitioner work with its own instruction, environment, separate verifier
and canonical solution: a production pagination bug, a multi-tenant authorization leak, a flawed A/B readout, a
scientific ET0 pipeline and an ML feature pipeline whose training values differ from what the live service computed.
Every package was run with Harbor 0.25.0 on Daytona cloud sandboxes: the canonical solution several times (the count
is in the last column), one or two other valid solutions, a clean rebuild, the no-op agent and a set of plausible
wrong or shortcut attempts. Where a task's `task.toml` denies the agent network, those runs used a copy of the task
without that one line ([Setup](#setup)). The last column links each task's results and its run traces; model-agent
trials are summarized under [Known limitations](#known-limitations).

## The tasks

| Task | Capability assessed | User-facing objective | How success is checked | Validation run (Daytona, Harbor 0.25.0) |
|---|---|---|---|---|
| [`orders-export-missing-rows`](tasks/orders-export-missing-rows/) ([design](docs/orders-export-missing-rows/DESIGN.md)) | Production debugging of a backend API: keyset pagination over SQLite with a non-unique sort key, a second copy of the bug, writes during paging | The finance export wrote 47,961 rows while the API counted 48,213: fix the Flask orders API so every listing returns each order exactly once, in the documented order, also while new orders arrive | About 5,300 requests on a hidden 30,000-order database, page sizes 1 to 500, 56 orders inserted during two walks: ids must follow `ORDER BY created_at DESC, id DESC`, the API contract must match the original, the database must stay unchanged | [run full1](validation/orders-export-missing-rows/PROOF_RESULTS_full1.md), [traces](validation/orders-export-missing-rows/README.md): oracle 10/10 = 1.0; alt 1.0; clean rebuild 1.0; no-op 0.0; 12 wrong or shortcut attempts 0.0. [Agent trials](validation/orders-export-missing-rows/README.md#agent-trials) (`terminus-2`, `openai/gpt-oss-120b`): 3 of 3 passed |
| [`tenant-isolation-docshare`](tasks/tenant-isolation-docshare/) ([design](docs/tenant-isolation-docshare/DESIGN.md)) | Defensive application security: authorization in a multi-tenant document API | A researcher reported a cross-organisation download: make the service enforce `PERMISSIONS.md` on every endpoint (the report names one of six flaws), keeping share links, org switching and support's read-only access | About 3,700 requests on a hidden database: a refused request must get a 4xx, leak no file content or name and change nothing; a permitted one must answer as the untouched service does | [run full1](validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md), [traces](validation/tenant-isolation-docshare/README.md): oracle 10/10 = 1.0; alt 1.0; clean rebuild 1.0; no-op 0.0; 6 wrong or shortcut attempts 0.0. [Agent trials](validation/tenant-isolation-docshare/README.md#agent-trials) (`terminus-2`, `openai/gpt-oss-120b`): 0 of 3 passed |
| [`ab-test-reanalysis`](tasks/ab-test-reanalysis/) ([design](docs/ab-test-reanalysis/DESIGN.md)) | Data analysis and experiment validity: auditing an A/B readout against its analysis plan, the data platform's documentation and the data (what counts as a click, a bot rule that reads behaviour during the experiment, hand-assigned accounts) | The readout came back "invalid" on a failed sample ratio check, the PM's dashboards show a clean 50/50 split and B's click-through 12.3% above A's, and the PM wants to turn B on for everyone: find out what the experiment shows, fix the pipeline so it gives the plan's readout on any export of this layout, and regenerate the readout | The agent's command on five hidden exports plus the regenerated readout, all six must pass: counts, SRM flag and decision exact; CTR and diff within 1e-9; SRM p within 1% relative; each CI bound within 0.25 half-widths of a delta-method reference (the plan's bootstrap and cluster-robust options land inside) | [run rev1](validation/ab-test-reanalysis/PROOF_RESULTS_rev1.md), [traces](validation/ab-test-reanalysis/README.md), on a copy without the agent network line: oracle 10/10 = 1.0; alt_time (bootstrap) 1.0; alt_recount (cluster-robust) 1.0; clean rebuild 1.0; no-op 0.0; 10 wrong or shortcut attempts 0.0. [Agent trials](validation/ab-test-reanalysis/README.md#agent-trials) (`claude-code`, `claude-opus-5-5`, web search off, on the same copy): 3 of 3 passed |
| [`et0-station-ingest`](tasks/et0-station-ingest/) ([design](docs/et0-station-ingest/DESIGN.md)) | Scientific computing against a published standard (FAO-56 Penman-Monteith): input and metadata handling, against a misleading hint | Irrigation advice is off at some stations (the user suspects altitude): fix the ET0 pipeline for any station register in the documented formats, and regenerate the output | Ten hidden stations (other sensor heights, both hemispheres, both radiation units), run from a copy of `/app` with `/app` removed, plus the regenerated `/app/output/et0.csv`: one row per station-day, each within 0.03 mm/day of an independent FAO-56 reference that reproduces FAO-56 Example 18 | [run full1](validation/et0-station-ingest/PROOF_RESULTS_full1.md), [traces](validation/et0-station-ingest/README.md), [notes](validation/et0-station-ingest/NOTES.md): oracle 10/10 = 1.0; alt 1.0; clean rebuild 1.0; no-op 0.0; 9 wrong or shortcut attempts 0.0. [Agent trials](validation/et0-station-ingest/README.md#agent-trials) (`terminus-2`, `openai/gpt-oss-120b`, the pilot included): 0 of 3 passed |
| [`feature-leakage-churn`](tasks/feature-leakage-churn/) ([design](docs/feature-leakage-churn/DESIGN.md)) | ML systems: point-in-time training features, rebuilt from a warehouse's own records of its loads (a scheduler log and a commit log): which commit made each order visible, which table bore the name `orders` during an 8-week dual run before a rename, task states that are not commits, as-of attributes, and a feature no extract determines | The churn model scored AUC 0.805 offline and 0.656 in its first live month, although its pipeline uses only events stamped before each prediction: make each feature equal what the live scoring service would have computed at each past prediction against the warehouse as it stood then, for any extract of this layout, and leave out any feature the extract cannot determine | The agent's command on a hidden extract of another brand (its own job runs, failures and migration): one row per prediction, the ten kept features equal to the live service's values from the simulator's true warehouse state (integer features exact, other numbers within 1e-6 + 1e-9 x value, strings and nulls exact), the left-out feature absent or all null; then on two copies changed in everything the warehouse did not yet hold at a cut time, their `_ops/` records included, no prediction at or before the cut may move; 60 s per run | [run v3](validation/feature-leakage-churn/PROOF_RESULTS_v3.md), [traces](validation/feature-leakage-churn/README.md), on a copy without the agent network line: oracle 5/5 = 1.0; alt 1.0; clean rebuild 1.0; no-op 0.0; 23 wrong or shortcut attempts 0.0 (one a probe that keeps state between the grader's runs). [Agent trials](validation/feature-leakage-churn/README.md#agent-trials) (`claude-code`, `claude-opus-5-5`, web search off, on the same copy): 3 of 3 passed |

"Oracle" is Harbor's oracle agent running `solution/solve.sh`; "clean rebuild" is the oracle with `--force-build`;
"no-op" is Harbor's `nop` agent. Attempts live in `solution/attempts/`; each task's DESIGN.md says what each one does
and which checks reject it. "Agent trials" are runs of a model agent (Harbor's `terminus-2` or `claude-code`) outside
the proof matrix.

## Setup

Harbor 0.25.0 needs Python 3.12 or newer. With [uv](https://docs.astral.sh/uv/):

```bash
uv tool install "harbor==0.25.0"                        # docker backend
uv tool install --reinstall "harbor[daytona]==0.25.0"   # adds the Daytona backend
```

Run one task from the repository root (the default backend is a local Docker engine):

```bash
harbor run -p tasks/<slug> -a oracle                          # canonical solution: expect reward 1
harbor run -p tasks/<slug> -a nop                             # no-op: expect reward 0
harbor run -p tasks/<slug> -a oracle --ae SOLUTION=<name>     # an alt* solution (ab-test: alt_time, alt_recount) or an attempt name: 1 or 0
harbor run -p tasks/<slug> -a oracle --force-build            # rebuild both images from scratch
harbor run -p tasks/<slug> -e daytona --env-file <file> -a oracle   # Daytona; the file sets DAYTONA_API_KEY
```

Each trial writes `verifier/reward.json` (reward and sub-metrics) and `verifier/test-stdout.txt` (the grader's log).
Agent trials use Harbor's usual `-a <agent> -m <model>`. `python tools/proof_matrix.py <slug> [--tag <name>]` runs a
task's whole matrix (canonical x10, or `--oracle-k <n>` times; alternatives, no-op, every attempt, a clean rebuild)
and writes `validation/<slug>/PROOF_RESULTS_<tag>.md`. It uses Harbor's default Docker backend and `harbor` on the
PATH; pass `--env daytona --env-file <file>` (or set `HARBOR_ENV`, `HARBOR_ENV_FILE`, `HARBOR_BIN`) to use another
backend, and `--without-agent-network-line` to run a copy of the task without its agent network line (next
paragraph). `tools/dev-requirements.lock` is the authoring environment for macOS arm64 only; the task images pin their
own packages.

**The agent network line.** `ab-test-reanalysis` and `feature-leakage-churn`, the two tasks revised after the first
review, set `[agent] network_mode = "no-network"` in `task.toml`, so that the agent cannot fetch the public hidden
tests of this repository; the verifier keeps Harbor's default (public) network (the grader isolates the agent's code
itself, see "How the tasks are graded"). Where Harbor 0.25.0 applies the line, it still lets an installed agent such
as `claude-code` reach its own model service and turns the agent's native web tools off (Harbor's source:
`trial/trial.py` lines 305-361 and 692-697, `trial/network_policy.py` lines 40-44, `agents/base.py` lines 197-245);
no run here used that allowlist. Where the line cannot be applied, the trial fails before the agent runs:
- On an environment that cannot switch a running sandbox's network, Harbor refuses the trial while setting it up,
  before the task's sandbox starts (`environments/base.py` lines 280-300). In Harbor 0.25.0 that is every environment
  whose `dynamic_network_policy` capability is false, the default (`environments/capabilities.py` line 46): for example
  runloop, blaxel, skypilot, mosaic and kernel; Docker where the engine fails Harbor's nftables check
  (`environments/docker/docker.py` lines 126-130, 210-217 and 981-1011); Daytona in compose mode; and some modes of
  modal, novita, islo and sbx.
- Daytona outside compose mode switches the running sandbox's network when the agent phase starts (`trial/trial.py`
  lines 740-747; `environments/daytona/environment.py` lines 1121 and 1581-1585). On the authors' Daytona Tier 1
  account, Daytona refused that switch, for the oracle agent and for `claude-code`, with "Network access is restricted
  and cannot be overridden at the sandbox level" (a test of 2026-10-30 on a pilot copy of another task with the same
  line). Daytona's documentation sets the same network limits for Tier 2, which was not tried.

There, run a copy without that one line:

```bash
python tools/proof_matrix.py <slug> --without-agent-network-line --tag <tag> --env <backend> --env-file <file>
harbor run -p jobs/<slug>/package-<tag>/<slug> -e <backend> --env-file <file> -a <agent> -m <model>
```

The first command writes the copy to `jobs/<slug>/package-<tag>/<slug>` (only that line removed) and runs the matrix on
it; the second runs agent trials on that copy. The agent then has the sandbox's network, so read each trial's
trajectory for fetches of the hidden tests ("The hidden tests are public" under
[Known limitations](#known-limitations)). Docker with a passing nftables check should run the shipped packages as they
are; that is untested (no run here used a local Docker engine).

For `claude-code`, the trials in this repository set `max_budget_usd` 20 and `disable_web_search` true (each trial's
`config.json`); Harbor takes these as `--ak max_budget_usd=20 --ak disable_web_search=true`, and the second makes it
pass Claude Code `--disallowedTools WebSearch,WebFetch` (each trial's `trial.log`).

## How the tasks are graded

- **Separate verifier.** Every `task.toml` sets `environment_mode = "separate"`. The grader, hidden inputs and expected
  answers sit in `/tests` (mode 0700) of an image built from `tests/Dockerfile`; `solution/` is in neither image. Only
  `/app` is carried over, minus folders named `data`, `__pycache__`, `.venv`.
- **Agent code is treated as hostile.** `grade.py` copies `/app`, removes auto-run files and runs the agent's code only
  as uid 1001, which cannot read `/tests`; it never imports agent code or deserializes its output as root. In
  `feature-leakage-churn`, which runs the agent's command three times, every run gets a fresh copy of `/app` as handed
  in, and before each run the grader kills every uid-1001 process and removes everything uid 1001 owns on the file
  system and in SysV IPC, so no run can read what an earlier one left there (kernel keyrings are not swept; a probe
  that caches its first output scored 0 on Daytona).
- **Network.** Commands run as uid 1001 get a private loopback-only network while no service is live
  (`network isolation: ON` in every shipped verifier log of docshare, ab-test, et0 and feature-leakage). Services keep
  the host network: the agent's service in orders and docshare; in orders every command runs while a service is up
  (`net=host` in its logs).
- **Fail closed.** `tests/test.sh` writes reward 0 first, locks `/logs/verifier` against uid 1001 and strips setuid
  bits before `grade.py` runs. Reward 1 only if every check passes.
- **Shared kit.** `base/verifier_kit/` is copied unchanged into each task's `tests/` by `tools/sync_kit.py`, so each
  package stands alone. `tools/check_task.py tasks/<slug>` checks layout, artifacts, the separate verifier, the pinned
  base image, the kit copies and `harbor lint`.
- **Quality gate.** [`docs/QUALITY_GATE.md`](docs/QUALITY_GATE.md) lists checks G1 to G30 that each DESIGN.md scores.

## Repository layout

```
tasks/<slug>/          task.toml, instruction.md, environment/, tests/ (test.sh, Dockerfile, grade.py, kit.py,
                       hidden data, SHA256SUMS), solution/ (solve.sh, canonical/, alt*/, attempts/)
docs/<slug>/DESIGN.md  build record: data, verifier, attempts, tolerances, timings, limitations
docs/QUALITY_GATE.md   the checks G1 to G30 that each DESIGN.md scores
validation/            README.md (all five); per task <slug>/README.md (each variant, its rewards and trace; the agent
                       trials), PROOF_RESULTS_<run>.md and .json, run logs (none for the fresh-clone run clone2 or
                       et0's pre-check smoke), NOTES.md (et0, and churn's first version), traces/<variant>/,
                       traces/agent-*/ (agent trials), REDACTIONS.md in each traces/ folder;
                       ab-test-reanalysis/first-version/, feature-leakage-churn/second-version/ and
                       feature-leakage-churn/first-version/ (the earlier versions of the two revised tasks)
authoring/<slug>/      generators and local checks that made the data and expected answers (not used in grading)
base/verifier_kit/     the shared grading kit
tools/                 proof_matrix.py, check_task.py, sync_kit.py, BASE_IMAGE_DIGEST, dev-requirements.in / .lock
```

## Known limitations

All five tasks:
- **Few agent trials.** Outside the proof matrices, model agents ran on Daytona. Harbor's `terminus-2` agent with
  `openai/gpt-oss-120b` ran three trials on each of the five tasks as published in commit `495c9f5` (a pilot on
  `et0-station-ingest` on 2026-10-29, the rest on 2026-10-30, Mac clock): 4 of 15 passed (`orders-export-missing-rows`
  3 of 3, `ab-test-reanalysis` 1 of 3, `et0-station-ingest`, `tenant-isolation-docshare` and `feature-leakage-churn`
  0 of 3; for `ab-test-reanalysis` and `feature-leakage-churn` these were their first versions). A review of the
  trajectories found each pass a genuine fix and each failure a gap the task targets, not a task defect. Those
  versions set no network line, so the agent had Harbor's default public network; no trajectory shows a fetch from
  GitHub. Harbor's `claude-code` agent (Claude Code 2.1.316) with `claude-opus-5-5`, web search off, ran three trials
  on each of three revised packages on 2026-10-31, on the copies without the agent network line: 3 of 3 passed on the
  revised `ab-test-reanalysis`, 3 of 3 on `feature-leakage-churn` as shipped (task v3) and 3 of 3 on its first
  revision (task v2, whose package was never committed; only its evidence is here), from which task v3 was hardened.
  Task v3's trials took 427 to 455 s of agent time each, about twice task v2's 182 to 221 s. Three trials of one
  agent are not a pass rate (3 of 3 has a Wilson 95% interval of 0.44 to 1.00), and the `difficulty` labels in
  `task.toml` are the authors' estimates. Details:
  [orders](validation/orders-export-missing-rows/README.md#agent-trials),
  [docshare](validation/tenant-isolation-docshare/README.md#agent-trials),
  [et0](validation/et0-station-ingest/README.md#agent-trials),
  [ab-test](validation/ab-test-reanalysis/README.md#agent-trials) (its first version's trials: section "First
  version" of the same README) and [churn](validation/feature-leakage-churn/README.md#agent-trials) (task v2's
  trials: [`second-version/`](validation/feature-leakage-churn/second-version/); the first version's:
  [`first-version/`](validation/feature-leakage-churn/first-version/)).
- **Validated on Daytona only**, never with a local Docker engine (linux/amd64 sandboxes, inferred from the backend).
  The base image `python:3.12-slim-bookworm` is pinned by a multi-arch index digest (`tools/BASE_IMAGE_DIGEST`), so an
  arm64 host builds an arm64 image that has not been run.
- **Synthetic data**, made by the `authoring/` scripts with fixed seeds. Image builds need PyPI (exact pins); grading
  needs no network.
- **The hidden tests are public.** This repository is public, so anyone, including an agent with internet access, can
  read the hidden inputs and expected answers in each task's `tests/` folder, and a private copy of the tasks does not
  help. For agent trials, deny the agent network access: the two tasks with the agent network line do so in
  `task.toml` ("The agent network line" under [Setup](#setup)); the other three set no network line, so Harbor gives
  the agent its default public network. Wherever the agent has network (those three tasks, or a copy without the
  line), read each trial's trajectory for fetches of the hidden tests and exclude any trial that made one. On
  Daytona's Tier 1 and 2, network rules cannot be overridden per sandbox and `github.com`, `*.github.com` and
  `*.githubusercontent.com` stay reachable ([Daytona network limits](https://www.daytona.io/docs/en/network-limits/)).
- **Kit rules the instructions do not spell out:** the graded copy loses `conftest.py`, `sitecustomize`/`usercustomize`,
  `*.pth`, `*.pyc` and `__pycache__`; a copy over 2 GiB or 200,000 entries scores 0; written files are capped at 1 GiB,
  run output at 64 MiB, uid 1001 at 512 processes and threads. No sane solution needs any of these.
- In the two HTTP tasks a hostile service could send the hidden data out over the host network; it cannot raise its
  own score that way (the expected answers stay in `/tests`).
- **Run traces:** one Harbor trial per variant of each final run, under `validation/<slug>/traces/<variant>/` (reward,
  config, full verifier log), indexed in `validation/README.md`. The agent trials' traces are under
  `validation/<slug>/traces/`: `agent-pilot/` and `agent-r3/<trial>/` for `terminus-2`, `agent-claude-code/<trial>/`
  for Claude Code. The earlier versions of the two revised tasks keep their evidence (proof runs, traces and agent
  trials) in `validation/ab-test-reanalysis/first-version/`, `validation/feature-leakage-churn/second-version/` (task
  v2) and `validation/feature-leakage-churn/first-version/`, where one trial of run `full1` was lost to a DNS failure
  on the machine running Harbor and has no reward or verifier log. The raw job folders (`jobs/`) are git-ignored; the
  "Job folder" column of `PROOF_RESULTS_*.md` points there, and the trace folders are the shipped copy.
- The DESIGN.md files cite planning notes that are not in this repository. So do the shared kit's docstring
  (`base/verifier_kit/kit.py` line 3, copied into each task's `tests/`: an infrastructure-check log) and two et0
  authoring scripts (`ref_a.py` and `reproduce_fao_examples.py`: locally saved copies of the public FAO-56 pages).

Per task:
- **orders-export-missing-rows:** may be easy for strong agents. The slowest valid fix known (rebuilding the sorted
  list on every request, 210.83 s on a Mac) was not timed on Daytona against the 900 s budget. Inserts during a
  customer walk are tested for one customer at one page size. Order ids of seven or more digits are not tested: the
  hidden database's ids stop at 30,000 and the orders inserted during the walks at 30,056; the cursors of all three
  passing agent trials refuse such ids ([agent trials](validation/orders-export-missing-rows/README.md#agent-trials)).
- **tenant-isolation-docshare:** the flaw class is well known. "Act in one active organisation" is a policy choice,
  stated in `PERMISSIONS.md` section 2. Thumbnails must be byte-identical to today's; list and export order are not
  checked.
- **ab-test-reanalysis:** Claude Code with `claude-opus-5-5` passed 3 of 3 trials, so the `hard` in `task.toml`, written
  before any trial, overstates the task for this agent (INFERENCE; an edit to `task.toml` would change the proven
  package's digest). The plan states every graded rule; neither the instruction nor the plan names the hand-assigned
  accounts, which the export's `method` column and the launch record show. The trials ran the copy without the agent
  network line, so the agent had the sandbox's network; with `disable_web_search` set, Harbor turned Claude Code's web
  tools off, but shell commands could still reach the network, and none did (a scan of the trajectories). A
  design-effect factor on the pageview-level interval (one rho from 0.235 to 0.310) passes the interval checks when
  every count is exact. The graded runs get 1 vCPU and 2,048 MB, the agent sandbox 2 vCPU and 4,096 MB (the instruction
  says to plan for one CPU and 2 GiB): a bootstrap that holds both arms' resample indexes at 5,000 resamples needs about
  2.1 GiB (extrapolated) and can be killed in grading. The package is 75 files, 27,114,446 bytes. The instruction says
  `python -m`; the grader runs `python3 -m` (same interpreter).
- **et0-station-ingest:** may be easy for strong agents; the radiation-unit defect is blatant. The leap-year station
  tests row handling, not the 366-day divisor. The grader's own symlink defence was not exercised on Daytona: Harbor's
  artifact step had already dropped the link ([notes](validation/et0-station-ingest/NOTES.md)).
- **feature-leakage-churn:** Claude Code with `claude-opus-5-5` passed task v3 3 of 3, in 427 to 455 s of agent time and
  22 to 27 tool calls each, about twice task v2's 182 to 221 s and 10 to 12 tool calls. The hardening doubled the work
  this agent needs, but it passed every trial, so on this evidence the hardening did not make the task one this agent
  cannot reliably complete, and the `hard` in `task.toml` overstates the task for this agent (INFERENCE; an edit to
  `task.toml` would change the proven package's digest); how the external reviewer's own agent fares is not known.
  Task v3's acceptance test, a blind read
  (a fresh Opus 5.5 reader given the instruction and a copy of `/app` writes its own fix, graded by the task's grader),
  scored 1 but was hinted (its prompt named the migration, and its context held the authors' design notes, which
  describe task v3's design), so it is evidence of fairness, not of unprompted discovery; the Claude Code trials are
  the unprompted test. The live service's January sample in `/app/logs/` comes after the
  order loaders' migration, so it cannot confirm how older orders became visible; only the warehouse doc and the job and
  commit logs in `/app/data/_ops/` decide that. The value check on the hidden extract alone rejects the attempt
  `hourly_schedule`, on only 12 feature values (3 predictions) per extract; the cut checks cannot. A valid but naive
  per-row build (about 123 s in one run and 159 s in a later one on a Mac, each extrapolated from 600 of the hidden
  extract's 57,896 predictions) fails the 60 s cap; the instruction tells the agent to time a run. The trials ran the
  copy without the agent network line, so the agent had the sandbox's network, with Claude Code's web tools off; no
  trajectory holds a network command, a URL or a path under `/tests`, `/solution` or `/logs/verifier` (a scan of the
  trajectories). The proof ran the canonical solution 5 times (10 for the other tasks). The package is 81 files,
  27,856,922 bytes.

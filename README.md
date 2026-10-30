# Five Harbor tasks: take-home submission (MTS)

Five Harbor task packages, each a piece of practitioner work with its own instruction, environment, separate verifier and canonical solution: a production pagination bug, a multi-tenant authorization leak, a flawed A/B readout, a scientific ET0 pipeline and a leaky ML feature pipeline.
Every package was run with Harbor 0.25.0 on Daytona cloud sandboxes: the canonical solution ten times, one or two other valid solutions, a clean rebuild, the no-op agent and a set of plausible wrong or shortcut attempts. The last column links each task's results and its run traces.

## The tasks

| Task | Capability assessed | User-facing objective | How success is checked | Validation run (Daytona, Harbor 0.25.0) |
|---|---|---|---|---|
| [`orders-export-missing-rows`](tasks/orders-export-missing-rows/) ([design](docs/orders-export-missing-rows/DESIGN.md)) | Production debugging of a backend API: keyset pagination over SQLite with a non-unique sort key, a second copy of the bug, writes during paging | The finance export wrote 47,961 rows while the API counted 48,213: fix the Flask orders API so every listing returns each order exactly once, in the documented order, also while new orders arrive | About 5,300 requests on a hidden 30,000-order database, page sizes 1 to 500, 56 orders inserted during two walks: ids must follow `ORDER BY created_at DESC, id DESC`, the API contract must match the original, the database must stay unchanged | [run full1](validation/orders-export-missing-rows/PROOF_RESULTS_full1.md), [traces](validation/orders-export-missing-rows/README.md): oracle 10/10 = 1.0; alt 1.0; clean rebuild 1.0; no-op 0.0; 12 wrong or shortcut attempts 0.0 |
| [`tenant-isolation-docshare`](tasks/tenant-isolation-docshare/) ([design](docs/tenant-isolation-docshare/DESIGN.md)) | Defensive application security: authorization in a multi-tenant document API | A researcher reported a cross-organisation download: make the service enforce `PERMISSIONS.md` on every endpoint (the report names one of six flaws), keeping share links, org switching and support's read-only access | About 3,700 requests on a hidden database: a refused request must get a 4xx, leak no file content or name and change nothing; a permitted one must answer as the untouched service does | [run full1](validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md), [traces](validation/tenant-isolation-docshare/README.md): oracle 10/10 = 1.0; alt 1.0; clean rebuild 1.0; no-op 0.0; 6 wrong or shortcut attempts 0.0 |
| [`ab-test-reanalysis`](tasks/ab-test-reanalysis/) ([design](docs/ab-test-reanalysis/DESIGN.md)) | Data analysis: auditing an experiment readout against its analysis plan (bot filtering, unit of analysis, SRM, decision rule) | A readout claims a 4.1% lift with p = 0.0003 and the PM wants to ship: fix the pipeline so it follows the plan on any experiment export, and regenerate the readout | Five hidden experiments plus the regenerated readout, all six must pass: counts, SRM flag and decision exact; CTR and diff within 1e-9; SRM p within 1% relative; each CI bound within 0.25 half-widths of a delta-method reference | [run full2](validation/ab-test-reanalysis/PROOF_RESULTS_full2.md), [traces](validation/ab-test-reanalysis/README.md): oracle 10/10 = 1.0; alt (bootstrap) 1.0; alt_cr1 (cluster-robust) 1.0; clean rebuild 1.0; no-op 0.0; 9 wrong or shortcut attempts 0.0 |
| [`et0-station-ingest`](tasks/et0-station-ingest/) ([design](docs/et0-station-ingest/DESIGN.md)) | Scientific computing against a published standard (FAO-56 Penman-Monteith): input and metadata handling, against a misleading hint | Irrigation advice is off at some stations (the user suspects altitude): fix the ET0 pipeline for any station register in the documented formats, and regenerate the output | Ten hidden stations (other sensor heights, both hemispheres, both radiation units), run from a copy of `/app` with `/app` removed, plus the regenerated `/app/output/et0.csv`: one row per station-day, each within 0.03 mm/day of an independent FAO-56 reference that reproduces FAO-56 Example 18 | [run full1](validation/et0-station-ingest/PROOF_RESULTS_full1.md), [traces](validation/et0-station-ingest/README.md), [notes](validation/et0-station-ingest/NOTES.md): oracle 10/10 = 1.0; alt 1.0; clean rebuild 1.0; no-op 0.0; 9 wrong or shortcut attempts 0.0 |
| [`feature-leakage-churn`](tasks/feature-leakage-churn/) ([design](docs/feature-leakage-churn/DESIGN.md)) | ML systems: point-in-time correctness of a feature pipeline (time windows, target encoding, as-of status, imputation) | A churn model scored AUC 0.981 offline and 0.613 live: find every feature that uses information not yet available at prediction time, and make all nine features follow the written spec | On a hidden extract every value must equal a reference (counts and status exact, floats within 1e-6 + 1e-9 x value, nulls where the spec says); on two copies with everything known at or after a cut time changed, no prediction at or before the cut may move; 60 s per run | [run full1b](validation/feature-leakage-churn/PROOF_RESULTS_full1b.md): oracle 10/10 = 1.0. [Run full1](validation/feature-leakage-churn/PROOF_RESULTS_full1.md): alt 1.0; clean rebuild 1.0; no-op 0.0; 10 wrong or shortcut attempts 0.0; oracle 9 trials 1.0, one lost to a DNS failure on the machine running Harbor ([notes](validation/feature-leakage-churn/NOTES.md)). [Traces](validation/feature-leakage-churn/README.md) |

"Oracle" is Harbor's oracle agent running `solution/solve.sh`; "clean rebuild" is the oracle with `--force-build`;
"no-op" is Harbor's `nop` agent. Attempts live in `solution/attempts/`; each task's DESIGN.md says what each one does
and which checks reject it.

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
harbor run -p tasks/<slug> -a oracle --ae SOLUTION=<name>     # alt, alt_cr1 (ab-test only) or an attempt name: 1 or 0
harbor run -p tasks/<slug> -a oracle --force-build            # rebuild both images from scratch
harbor run -p tasks/<slug> -e daytona --env-file <file> -a oracle   # Daytona; the file sets DAYTONA_API_KEY
```

Each trial writes `verifier/reward.json` (reward and sub-metrics) and `verifier/test-stdout.txt` (the grader's log).
Agent trials use Harbor's usual `-a <agent> -m <model>`. `python tools/proof_matrix.py <slug> [--tag <name>]` runs a
task's whole matrix (canonical x10, alternatives, no-op, every attempt, a clean rebuild) and writes
`validation/<slug>/PROOF_RESULTS_<tag>.md`. It uses Harbor's default Docker backend and `harbor` on your PATH; pass
`--env daytona --env-file <file>` (or set `HARBOR_ENV`, `HARBOR_ENV_FILE`, `HARBOR_BIN`) to use another backend.
`tools/dev-requirements.lock` is the authoring environment for macOS arm64 only; the task images pin their own packages.

## How the tasks are graded

- **Separate verifier.** Every `task.toml` sets `environment_mode = "separate"`. The grader, hidden inputs and expected
  answers sit in `/tests` (mode 0700) of an image built from `tests/Dockerfile`; `solution/` is in neither image. Only
  `/app` is carried over, minus folders named `data`, `__pycache__`, `.venv`.
- **Agent code is treated as hostile.** `grade.py` copies `/app`, removes auto-run files and runs the agent's code only
  as uid 1001, which cannot read `/tests`; it never imports agent code or deserializes its output as root.
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
validation/            README.md (all five); per task <slug>/README.md (each variant, its rewards and trace),
                       PROOF_RESULTS_<run>.md and .json, the run log, NOTES.md, traces/<variant>/ and traces/REDACTIONS.md
authoring/<slug>/      generators and local checks that made the data and expected answers (not used in grading)
base/verifier_kit/     the shared grading kit
tools/                 proof_matrix.py, check_task.py, sync_kit.py, BASE_IMAGE_DIGEST, dev-requirements.in / .lock
```

## Known limitations

All five tasks:
- **No agent trials yet.** Every reward above comes from the oracle (reference solutions and attempts) and the nop
  agent. Pass rates are not measured; the `difficulty` labels in `task.toml` are our estimates.
- **Validated on Daytona only**, never with a local Docker engine (linux/amd64 sandboxes, inferred from the backend).
  The base image `python:3.12-slim-bookworm` is pinned by a multi-arch index digest (`tools/BASE_IMAGE_DIGEST`), so an
  arm64 host builds an arm64 image that has not been run.
- **Synthetic data**, made by the `authoring/` scripts with fixed seeds. Image builds need PyPI (exact pins); grading
  needs no network.
- **The hidden tests are public.** This repository is public, so anyone, including an agent with internet access, can
  read the hidden inputs and expected answers in each task's `tests/` folder. For agent trials, deny the agent network
  access or use a private copy.
- **Kit rules the instructions do not spell out:** the graded copy loses `conftest.py`, `sitecustomize`/`usercustomize`,
  `*.pth`, `*.pyc` and `__pycache__`; a copy over 2 GiB or 200,000 entries scores 0; written files are capped at 1 GiB,
  run output at 64 MiB, uid 1001 at 512 processes and threads. No sane solution needs any of these.
- In the two HTTP tasks a hostile service could send the hidden data out over the host network; it cannot raise its
  own score that way (the expected answers stay in `/tests`).
- **Run traces:** one Harbor trial per variant of each final run, under `validation/<slug>/traces/<variant>/` (reward,
  config, full verifier log; the lost DNS trial has no reward or verifier log), indexed in `validation/README.md`. The raw job folders (`jobs/`) are git-ignored; the
  "Job folder" column of `PROOF_RESULTS_*.md` points there, and the trace folders are the shipped copy.
- The DESIGN.md files cite planning notes that are not in this repository. So do the shared kit's docstring
  (`base/verifier_kit/kit.py` line 3, copied into each task's `tests/`: an infrastructure-check log) and two et0
  authoring scripts (`ref_a.py` and `reproduce_fao_examples.py`: our saved copies of the public FAO-56 pages).

Per task:
- **orders-export-missing-rows:** may be easy for strong agents. The slowest valid fix we know (rebuilding the sorted
  list on every request, 210.83 s on a Mac) was not timed on Daytona against the 900 s budget. Inserts during a
  customer walk are tested for one customer at one page size.
- **tenant-isolation-docshare:** the flaw class is well known. "Act in one active organisation" is a policy choice,
  stated in `PERMISSIONS.md` section 2. Thumbnails must be byte-identical to today's; list and export order are not checked.
- **ab-test-reanalysis:** the package is 32.0 MB. It may be easy (the PM note points at the arm sizes). Two hidden
  experiments share one traffic sample with different clicks, which rejects design-effect multipliers built from
  pageview counts. A user-level click-dispersion design effect, or a one-way ANOVA ICC times Kish's factor, is not one
  of the plan's three methods but lands inside the 0.25 band; we accept it as valid user-level work. A rule fitted on
  the hidden readouts could pass, but needs data no agent sees. Run full1 used an earlier build of one hidden
  experiment and is superseded by full2. The instruction says `python -m`; the grader runs `python3 -m` (same interpreter).
- **et0-station-ingest:** may be easy for strong agents; the radiation-unit defect is blatant. The leap-year station
  tests row handling, not the 366-day divisor. The grader's own symlink defence was not exercised on Daytona: Harbor's
  artifact step had already dropped the link ([notes](validation/et0-station-ingest/NOTES.md)).
- **feature-leakage-churn:** a valid but naive per-row build (about 85 s on a Mac) fails the stated 60 s cap; the
  instruction tells the agent to time a run. The spec states every rule, so strong agents may pass more often than
  "hard" suggests. In run full1 one oracle trial was lost when the machine running Harbor lost DNS
  (`DaytonaConnectionError`, no reward; its trace is kept); full1b re-ran the ten oracle trials, 10/10.

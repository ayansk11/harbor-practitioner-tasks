# tenant-isolation-docshare: design and local validation

**What this file is.** The authoring notes for this task: its design, where the build departs from our original
design brief (not shipped) and why, the local checks, the quality-gate record against `docs/QUALITY_GATE.md` (checks
G1 to G30), the Daytona proof results and the known limitations. Paths are relative to the repository root;
`submission/` in a command is that root as it was named on the authoring Mac. Short names such as `tests/grade.py`
are inside the task folder `tasks/tenant-isolation-docshare/`.

Last updated: 2026-10-29 (Mac clock, MST): wording edited for outside readers and pointers fixed (no measurement,
verdict or limitation changed). Before that, also 2026-10-29: section 10 adds the Daytona proof results of 2026-10-28 and the gate record
(section 8) is re-scored from them; the Daytona notes of sections 5, 7 and 9 predate that run. Before that: 2026-10-28
19:36 MST. Built from our design brief for this task and the verifier rules shared by all five tasks, both written and
approved before the build and not in this repository (the kit's own rules are in `base/verifier_kit/README.md`);
section 5 lists where the build departs from them. Labels: FACT (a file, a command output),
INFERENCE (reasoned; basis named), UNVERIFIED.
Status: built, checked by an independent review, fixed after that review (section 5, "Mixed runs") and checked locally
(KIT_LOCAL on the Mac). Proven on Daytona in run full1 of 2026-10-28 (section 10); the "(run)" gate items are scored
from that run.

## 1. The task in one paragraph
A security researcher reports that a member of one organisation can download another organisation's file by changing
the id in `GET /api/files/<id>/download`. The agent must fix the Flask service so it enforces `environment/app/docs/PERMISSIONS.md`
on every endpoint, while three legitimate cross-tenant paths keep working: anonymous share links, org switching
(`X-Org-Id`) for people in two organisations, and support staff's read-only access. Six flaws are planted; the report
names only the first. The verifier starts the agent's service on a hidden database and sends about 3,700 requests.

## 2. What was built (file map)
| Path (from the repository root) | What it is |
|---|---|
| `tasks/tenant-isolation-docshare/task.toml` | schema 1.4, the shared artifact rule, separate verifier, agent 1800 s, verifier 900 s, 1 CPU, 1024 MB |
| `.../instruction.md` | the request, what is checked, the shared closing line |
| `.../environment/Dockerfile` | pinned base digest; flask, waitress, pytest and their dependencies at exact lock pins; `COPY app/ /app/` |
| `.../environment/app/docshare/` | the service: `auth.py`, `db.py`, `app.py`, `serve.py`, `seed.py`, `routes/{files,folders,thumbs,export,share,admin}.py` |
| `.../environment/app/docs/` | `PERMISSIONS.md` (the policy), `API.md` (endpoints and fields), `DEV_USERS.md` (generated: dev users and tokens) |
| `.../environment/app/SECURITY_REPORT.md` | the report (generated, with real ids of the visible database) |
| `.../environment/app/tests/test_api.py` | 9 visible feature tests; they pass before and after a correct fix |
| `.../environment/app/data/docshare.db` | visible development database (3 orgs, 8 users, 30 files, 6 links); dropped from the artifact |
| `.../tests/Dockerfile` | same base and pins; `COPY . /tests/`; uid 1001; `/tests` 0700 |
| `.../tests/grade.py` | the grader (section 4) |
| `.../tests/policy.py` | PERMISSIONS.md as code (98 lines with comments): the source of every expected outcome |
| `.../tests/hidden/seed.db` | hidden database: 4 orgs, 14 users (2 in two orgs, 2 support), 60 files, 12 links (4 revoked) |
| `.../tests/original/docshare/` | untouched copy of the shipped app, the differential reference |
| `.../tests/SHA256SUMS` | sha256 of everything in `hidden/` and `original/`; grade.py checks it first |
| `.../tests/kit.py`, `test.sh` | the shared kit, synced by `tools/sync_kit.py` |
| `.../solution/solve.sh` | `SOLUTION` unset = canonical, `alt`, or an attempt name; `APP_DIR` for local use |
| `.../solution/canonical/docshare/` | canonical fix: new `access.py` (one `can()` and `load_file()`), membership check in `auth.py`, every route uses it |
| `.../solution/alt/docshare/` | second fix: no helper; every SQL query scoped by org and role; refusals are 403 instead of 404 |
| `.../solution/attempts/<name>/` | the five design attempts plus `phase_gate` (added after the review), each with `ABOUT.md` |
| `authoring/tenant-isolation-docshare/build_data.py` | builds both databases, DEV_USERS.md, the report, `tests/original`, SHA256SUMS (fixed seeds) |
| `authoring/.../matrix_from_permissions.py` | the second reader (section 3) |
| `authoring/.../diff_matrices.py` | diffs the second reader against `tests/policy.py` on every cell |
| `authoring/.../make_attempts.py` | writes `solution/attempts/` from the app and the canonical fix by exact substitution |
| `authoring/.../local_check.py` | local proof matrix with local-only variants and repeat runs; writes `local_results.txt` |
| `docs/tenant-isolation-docshare/local_results.txt` | the last full local run (FACT for section 7) |
| `docs/tenant-isolation-docshare/old_grader_check.txt` | the review's cheats and gaps graded by the grader before the fix (all 1) |

Rebuild order: `build_data.py`, `make_attempts.py`, `python tools/sync_kit.py`, `local_check.py`, `tools/check_task.py`.

## 3. The six planted flaws and the policy
| # | File | Flaw | Reported? | Caught by (local ablation that undoes only this fix) |
|---|---|---|---|---|
| 1 | `routes/files.py` | `get_file_or_404` loads by id with no org check (metadata, download, rename, delete) | yes | read and download refusals |
| 2 | `auth.py` | `X-Org-Id` trusted without a membership check; unknown org falls back to role `member` | no | every request with a foreign `X-Org-Id`; DB diff |
| 3 | `routes/thumbs.py` | its own query by id, no org check | no | thumb refusals |
| 4 | `routes/export.py` | only the first id is checked ("a selection comes from one folder view") | no | export refusals (`[own, foreign]`) |
| 5 | `routes/share.py` | link creation checks the role, not that the file is in the active org | no | share refusals; DB diff (new link rows) |
| 6 | `routes/files.py` | delete checks login only, not the org_admin role | no | delete refusals; DB diff; read-back sweep |

Policy decisions written into PERMISSIONS.md (our reading where the design brief was silent; INFERENCE from the brief's
list of roles and actions): members may read, download, thumb, list, export, rename and share; only org_admin deletes; support reads,
downloads, thumbs, lists and exports anywhere and never writes; a request acts in one *active* organisation, so a user
in two orgs must switch with `X-Org-Id` before touching the second org's files (stated in section 2 with an example);
support may name any existing org, and naming one that does not exist refuses the request (this sentence was added
after the quality-gate check, section 8, found it unstated).

**Second reader (FACT, `local_results.txt` line 7).** `matrix_from_permissions.py` was written from PERMISSIONS.md
alone, before `policy.py`, in a different style: it parses the section 3 table at run time and codes the prose rules of
sections 1, 2, 4 and 5. `diff_matrices.py` compares it with `policy.py` on every cell: 73,542 cells on the hidden
database and 26,718 on the visible one (every context × action × target, plus 400 random export sets), 0
disagreements. Mutation test: changing one table cell (member may delete) makes 305 cells disagree, so the second reader
really reads the document. Limit (honest): both were written by the same author in the same build session, so the diff catches
transcription errors, not a shared misreading. A second reader written independently, by another author, would make
it independent.

## 4. The verifier
`test.sh` (kit) runs `python3 -I /tests/grade.py` as root. grade.py (FACT for every count: `local_results.txt` and the
canonical grading log, lines `2012 refusal cases, 402 permitted reads` and `write list: 50 requests, with 379 refused
requests mixed in; 0 steps skipped`):
1. Checks SHA256SUMS; `kit.prepare_submission()`; loads the hidden seed (root's own file, opened `immutable=1`);
   builds a deterministic case list (seed 20261028) from `policy.py`: 2,012 refused requests and 402 permitted reads.
   The refused list holds, per context (anonymous, bad token, and each of 14 users × {no header, each org, an unknown
   org}) and per action, one file from each relation class (active org, the user's other org, a foreign org; for a
   refused context: the named org, home, other), an unknown id, three link revocations, export sets (`[own, foreign]`,
   `[foreign, own]`, `[foreign]`, `[own, own, foreign]`, `[own, unknown]`), the list endpoints (including the 8
   support-without-`X-Org-Id` lists that must get `400`), foreign folders, `/api/me`, `/api/admin/orgs`, revoked and
   unknown share links. A refused rename asks for a name of the same form as a permitted one (`renamed-<8 hex>.md`).
2. **Reference.** Stages `tests/original` and a seed copy with `kit.stage_for_runner`, starts the untouched app as
   uid 1001 and records its answers (status, headers, body) to the 356 permitted reads that need one. This happens
   before any agent code runs, so agent code can never touch the reference.
3. **Run 1** (fresh seed copy, agent's app from `/work/sub` via `python -m docshare.serve --db <path> --port <p>`):
   the 1,219 refused reads and the 402 permitted reads shuffled together (seeded), then the 793 refused writes
   (renames, link creations, revocations, deletes at the very end, so a wrongly allowed write cannot hide a later read
   leak), then each of the 60 files is read back by a home member of its org (name unchanged), then the app is
   stopped, uid 1001 folds the WAL into the database with our own `python3 -I -c` checkpoint script, root copies the
   file into `kit.SCRATCH` and compares `files`, `shares`, `memberships`, `folders` (named columns, content as hex)
   with the seed. 2,474 requests plus the database check.
4. **Run 2** (another fresh copy): the 402 permitted reads shuffled with 400 refused reads, then the write list: 50
   requests from permitted callers (7 of them must still get a 4xx: two bad names, two bad export bodies, three
   revokes by an outsider or support), each preceded by 3 to 12 refused requests (a seeded count; 379 in all, reads and writes) drawn
   from the rest of the refused list. 1,231 requests. The write list: renames by a member, an org_admin and, via
   `X-Org-Id`, by each of the two users in two orgs (response and read-back must equal the seed's File with the new
   name); a bad name (`bad/name.md`, empty) and a malformed export body (a string, an empty list) from a permitted
   caller must get a 4xx and change nothing; a link created by a member (response fields `token`, `url` = `/s/<token>`,
   `file_id`, ISO 8601 `created_at`), fetched anonymously, refused for an outsider's revoke (link still works), revoked
   by an org_admin peer, then dead; the same cycle in the second org via `X-Org-Id`, with support's revoke refused and
   the same user revoking; a seed link revoked via `X-Org-Id` by each two-org user and one by an org_admin of another
   org; deletes by an org_admin (a file without links, and a file with a live link, whose link must then be dead) and
   by a second-org org_admin via `X-Org-Id`; every delete is checked by a read (4xx) and a list.
5. Every refused request must get a 4xx, and its body and headers (base64 strings decoded) must hold no content
   marker of any file and no name of a file the user can never read. Every permitted read must match: downloads and
   share links return the exact bytes with the original's media type and an `attachment` Content-Disposition naming
   the file; thumbs equal the original's bytes and media type; reads, lists, folders, `/api/me`, `/api/admin/orgs`
   equal the original's answer on the API.md fields (lists must hold exactly the active org's files); permitted
   exports return exactly the requested files with all API.md fields.
6. Reward 1 only if no check failed. `reward.json` carries numeric sub-metrics (`run1_checks`, `run1_failed`,
   `run2_checks`, `run2_failed`, `leaking_refusals`, `grading_seconds`) and a count per failed check
   (`run1_fail_<check>`, `run2_fail_<check>`; refusals mixed into the write list are `noise_status_<kind>` and
   `noise_leak_<kind>`); test-stdout shows up to 3 examples per failed check.

Why the runs are mixed (G12): no run of agent code sees only one kind of request, and the staged folder names are
random (`w<8 hex>`), so a service that guesses "this run only sends requests to refuse" and refuses everything (or
allows every write) fails. Section 5 "Mixed runs" has the history and the evidence.

Leniency (G13, G15): any 4xx counts as a refusal (the docs say 403 or 404, 401, 400); permitted writes accept 200, 201
or 204; a bad name or malformed body accepts any 4xx (API.md says 400); only API.md fields are compared, so added
fields are fine; Content-Type is compared on the media type only and Content-Disposition on `attachment` plus the
name; lists and exports are compared as sets, although API.md says "sorted by name" and "in request order" (a
variant that sorts lists by date scores 1, section 7: deliberate, because the instruction does not state an order);
tables or columns the agent adds are ignored.

What a service sees (kit rule 8 in `base/verifier_kit/README.md`, G21): the agent's service runs as uid 1001 with the host network (the kit gives
services no private namespace), its own database copy (the hidden data of all four orgs, which is what the app
serves), and the grader's requests. It cannot read `/tests`. INFERENCE: a hostile service could send the hidden
database out over the network; that would not raise its own score, but it would spoil the hidden data for later runs.

## 5. Deviations from the design brief and the shared verifier rules (with reasons)
- **About 3,700 requests instead of about 600.** The two runs of agent code take 2.5-5.0 s together on the Mac
  (section 6), so full coverage of every relation class costs little.
- **The differential runs first, not side by side.** The original answers before any agent code runs; side by side,
  agent code (same uid) could tamper with the reference.
- **DB check against the seed, not against the original's DB.** Run 1 writes nothing that the policy permits (its
  permitted requests are reads), so the right end state is exactly the seed. Added: the 60-file read-back sweep,
  which also catches a hidden change (for example a soft-delete column) that the named columns would miss.
- **Mixed runs (fix after the independent review, 2026-10-28).** The first grader had a refusal run that sent only refused
  requests (plus the read-back) and a second run that sent only permitted ones, and it named the database folders
  `db_deny` and `db_allow`. The review showed that a service could tell the runs apart: by the `--db` path, by a
  marker file written on the first start (the code folder `/work/sub` is the same for both runs), or by counting
  requests. Three such services with no real write checks scored 1 (FACT: `old_grader_check.txt`, rows `phase_gate`,
  `ablate_phase_strict_first_start`, `ablate_phase_by_request_count`). Fix, as section 4 describes: run 1 shuffles
  the permitted reads into the refused reads; run 2 shuffles 400 refused reads into the permitted reads and puts a
  seeded 3-12 refused requests (reads and writes) before every request of the write list (a fixed count would let a
  service count to the permitted one); folder names are random; refused renames use the same name pattern as
  permitted ones; permitted revokes now include seed links, and a refused revoke of a new link was added (before, all
  refused revokes used seed tokens and the only permitted ones used new tokens). All three services now score 0
  (section 7). A fresh `/work/sub` per run alone would not have been enough (the request-count service keeps no state
  on disk); the mixing is the fix.
- **More permitted behaviour checked (fix after the review).** The review found six variants that broke a permitted
  behaviour and still scored 1 (FACT: `old_grader_check.txt`): revoking via `X-Org-Id`, deleting a file that has
  links (the foreign key makes it a 500 if the links are not removed), support listing without `X-Org-Id` answering
  200, the link-creation response with only `token`, renames without the name check, downloads without Content-Type
  and Content-Disposition. Section 4's write list and header checks now cover each; all six score 0 (section 7). The
  `400` decisions of `policy.can_list` were dropped by the case builder before; they are now refusal cases.
- **Time caps.** The shared verifier rules give each run of agent code a cap of 3 × the slowest valid solution, and
  set `verifier.timeout_sec` = the sum of the caps + the measured grading time + 50%. The slowest
  valid run measured on the Mac is 2.92 s (alt, run 1), which gives under 9 s; Mac timings do not transfer to a 1-vCPU
  Daytona sandbox (UNVERIFIED speed), and before the keep-alive fix below a loaded Mac stretched a phase to 19 s. So
  each run has a 90 s cap (stated in the instruction), each request 10 s plus one retry, each start 30 s; at most one
  request runs past a cap. `verifier.timeout_sec` = that formula on those caps: 3 × (30 start + 90 run + 20.5
  overshoot) + 30 checkpoint + 120 copy-out + 15 stops = 587 s, + 6 s measured grading (5.79 s, section 6), + 50% =
  890 s, rounded to 900 s. A slow service scores 0 through the cap, not `verifier_failed` (shown by
  `ablate_slow_service`, section 7). The Daytona proof run should record the run times; the caps can be tightened
  then.
- **Keep-alive connections in the grader.** One new TCP connection per request exhausted the Mac's ephemeral ports
  across back-to-back runs (`OSError: [Errno 49] Can't assign requested address`, 3 of 10 alt runs failed). The grader
  keeps one connection per service and retries a request that got no answer once. Repeat runs are now saved: 5 of 5
  canonical and 5 of 5 alt runs scored 1 on top of the matrix rows (FACT: `local_results.txt`, "repeats" lines).
- **Uploads are not in the API.** API.md says uploads go through an ingest worker; the six flaws need no upload path.
- **Thumbs** are generated SVG previews (name plus the first lines), compared byte for byte with the original's.
- **Extra local-only variants** (not shipped, not for Daytona): one ablation per flaw, one that writes before
  refusing, one slow service, two more run-telling services, six that break one permitted behaviour, and one lenient
  case that must score 1. They show that each planted flaw, the DB diff, the time cap, the mixing and each permitted
  behaviour are checked on their own.
- **Image size** not measured (no Docker on the Mac). INFERENCE: the slim base plus about 15 small pure-Python
  wheels; UNVERIFIED.

## 6. Timings (FACT, Mac, KIT_LOCAL=1, `local_results.txt` run 2026-10-28 19:31:38 MST)
| Run | Total (wall) | original (our code) | run 1 | run 2 | service start |
|---|---|---|---|---|---|
| canonical | 5.27 s; repeats 5.40-5.57 s | 0.80 s | 2.78 s | 1.58 s | 0.42-0.43 s (grading log) |
| alt | 5.79 s; repeats 5.44-5.61 s | 0.72 s | 2.92 s | 2.03 s | not read |
The Mac was shared with other builds during that run. An earlier local run during the build, with less load, took
3.38 s (canonical) and 3.23 s (alt) (console output, not saved in a file).
Caps derived: start 30 s, request 10 s (+1 retry), run 90 s, verifier 900 s (section 5).

## 7. LOCAL RESULTS (FACT: `docs/tenant-isolation-docshare/local_results.txt`, run 2026-10-28 19:31:38 MST)
Command: `submission/.venv/bin/python submission/authoring/tenant-isolation-docshare/local_check.py` (each variant:
copy `environment/app`, `SOLUTION=<variant> APP_DIR=<copy> bash solution/solve.sh` (local variants: canonical or the
original plus an exact text substitution), drop `data`, `__pycache__`, `.venv`, then `KIT_LOCAL=1 KIT_SUBMISSION=<copy>
GRADE_TESTS_DIR=<task>/tests python tests/grade.py`). "x-org" = with a foreign or unknown X-Org-Id; "noise" = refused
requests mixed into the write list.
| Variant | Expected | Got | Checks that failed (count per check) |
|---|---|---|---|
| canonical | 1 | 1 | none (2,475 run-1 checks, 1,231 run-2 checks); repeats 5 of 5 = 1 |
| alt (`SOLUTION=alt`) | 1 | 1 | none; repeats 5 of 5 = 1 |
| original (what nop leaves) | 0 | 0 | 1,742 run-1 and 603 run-2 failures, 785 leaking refusals: read, download, thumb, export, rename, share, delete, x-org on every endpoint, DB changed, sweep 60 |
| patch_get_only | 0 | 0 | thumb 32, export 52, share 32, delete 18, rename 32, x-org (read 36, download 36, thumb 128, lists, me, ...), DB changed, sweep 60 |
| membership_plus_get | 0 | 0 | thumb 32, export 52, share 32, delete 25, sweep 25, DB changed (run 1); noise share 5, delete 6 (run 2) |
| deny_most | 0 | 0 | permitted only: support reads 18, downloads 18, thumbs 18, exports 20, lists, folders, me, admin; share links 8; link creation 3 |
| drop_org_switching | 0 | 0 | permitted only: second-org reads, lists, exports, renames, links, delete; support lists, folders and every support request with X-Org-Id |
| hardcode_visible_orgs | 0 | 0 | x-org on every endpoint (read 34, download 34, thumb 34, lists 46, ...), DB changed, sweep 25 |
| phase_gate (new attempt) | 0 | 0 | run 1 none; run 2 noise rename 8, share 6, revoke 17, delete 11, outsider revoke 2, link checks 6 |
| ablate_f1_get_by_id | 0 | 0 | read 32, download 32 (run 1); the same kinds in run 2 |
| ablate_f2_header_trust | 0 | 0 | x-org on every endpoint, DB changed, sweep 25 |
| ablate_f3_thumbs | 0 | 0 | thumb 32 |
| ablate_f4_export_first_id | 0 | 0 | export 52 |
| ablate_f5_share_no_read_check | 0 | 0 | share 32, DB changed; noise share 6 |
| ablate_f6_member_delete | 0 | 0 | delete 14, sweep 14, DB changed; noise delete 2 |
| ablate_write_before_refusal | 0 | 0 | DB changed only |
| ablate_slow_service (caps 5 s, local only) | 0 | 0 | time cap (run 1 and run 2) |
| ablate_phase_strict_first_start | 0 | 0 | run 1: permitted reads of every kind (382); run 2: what the original fails |
| ablate_phase_by_request_count | 0 | 0 | run 1 none; run 2 noise rename 8, share 6, revoke 17, delete 11, outsider revoke 2 |
| gap_revoke_only_in_home_org | 0 | 0 | revoke of a new link 2 and of a seed link 2, both via X-Org-Id |
| gap_delete_leaves_shares_fk | 0 | 0 | delete of the file with a link 1 |
| gap_support_list_no_header_200 | 0 | 0 | support list without X-Org-Id: files 2, folders 2 (run 1); 3 in run 2 |
| gap_share_response_fields | 0 | 0 | link creation response 3 |
| gap_no_rename_validation | 0 | 0 | bad name 3 |
| gap_download_headers_dropped | 0 | 0 | downloads 44 and share links 8 in each run |
| lenient_lists_unsorted | 1 | 1 | none (list order is deliberately not checked, section 4) |
Also FACT (same file): integrity OK (SHA256SUMS, `tests/original` equals the shipped app, no `__pycache__`); the visible
pytest suite passes 9 of 9 on the original, canonical and alt; matrix diff AGREE, mutation DISAGREE on 305 cells.
FACT (`old_grader_check.txt`): `phase_gate`, both phase ablations and the six `gap_*` variants scored 1 on the grader
before the fix. `tools/check_task.py tasks/tenant-isolation-docshare` prints `OK tenant-isolation-docshare` (it runs
`harbor lint`, clean), after `tools/sync_kit.py` (kit unchanged).

What the Daytona proof run had to show (written before the run; section 10 has the results): `harbor lint`; oracle × 10 = 1; `--ae SOLUTION=alt` = 1; nop =
0; `--ae SOLUTION=<each of the six attempts>` = 0 (`patch_get_only`, `membership_plus_get`, `deny_most`,
`drop_org_switching`, `hardcode_visible_orgs`, `phase_gate`); oracle with `--force-build` = 1. In
`verifier/test-stdout.txt`: the kit lock lines, `network isolation: ...`, three `service on 127.0.0.1:<port> answered`,
the `original`, `run1` and `run2` phase lines with their times (to re-derive the caps), `write list: 50 requests, with
379 refused requests mixed in; 0 steps skipped`, and `reward=...`. Real-mode kit paths that local mode never runs, to
look for in the same file: four `staged ... for uid 1001 at /work/w<8 hex>` lines (stage_for_runner as root); the
checkpoint line `ran [... '-I', '-c', 'import sqlite3...'] rc=0 timed_out=False` (run_as_runner demotion); no
`unreadable (...)` in a `db_changed` failure (copy_out_as_runner into kit.SCRATCH works); `reward=1.0 (killed N runner
processes)`. For `phase_gate`: the failed checks must include `run2_fail_noise_status_*` (the marker file in
`/work/sub/docshare` made run 2 its "later start"); a 0 for another reason would not prove the mixing.

How to read the proof runs:
- `grader_error: 1` in reward.json means grade.py raised (for example the reference app did not start or answer, or
  SHA256SUMS did not match). That is a verifier or infrastructure fault, not a verdict on the solution: it reopens the
  gate as a verifier bug and does not count as a failed oracle.
- Caps: if a valid solution's run 1 on Daytona takes over 30 s (a third of its 90 s cap), raise the run caps and
  recompute `verifier.timeout_sec` with the formula in section 5 before the attempt runs.
- grade.py depends on the hardened kit API (`stage_for_runner`, `copy_out_as_runner` into `kit.SCRATCH`,
  `kit.TESTS_DIR`, `run_as_runner`). After any further kit change, re-run `local_check.py` before spending Daytona
  trials on this task.

## 8. Gate record
```
Gate record: tenant-isolation-docshare, implementation (2026-10-28, updated after the review fix; the (run) items re-scored 2026-10-29 from the recorded Daytona runs, section 10; paths from the repository root)
Applies to: task tenant-isolation-docshare
G1  PASS - app, both databases, policy, reference copy and pins are in the package; grading needs no network
G2  PASS - closes a reported cross-tenant data leak and its five siblings
G3  PASS - a multi-module Flask service with docs, a report, dev data and feature tests
G4  PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - about 3,700 black-box HTTP checks plus a DB diff; on Daytona every row as expected (canonical 10 of 10, alt and force-build 1.0; nop and 6 attempts 0.0); locally also 1 for the lenient case and 0 for 16 local variants (not run on Daytona)
G5  PASS - the only authorization task of the five
G6  PASS - written policy; every cell is one curl request; second reader agrees on 100,260 cells (same-author limit, section 3)
G7  PASS - routine bug-bounty fix work
G8  PASS - instruction states the start command, the refusal codes of PERMISSIONS.md section 6 (any 4xx accepted), no data in refusals, DB unchanged, same answers, download media type and attachment name, links of a deleted file stop working, 400 for bad bodies, schema rule, time limits, copy-and-unprivileged run
G9  PASS - report, policy table, org switching, support console make sense to a security engineer
G10 PASS - a fixed service
G11 PASS - black-box HTTP; the DB read is of named columns the instruction names; the six permitted behaviours the review found unchecked are now checked (section 5)
G12 PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - FAIL found by the review (the two runs could be told apart; 3 services with no write checks scored 1, old_grader_check.txt) and fixed by mixing (section 5); the original, 6 attempts and 16 local variants score 0 locally, each through named checks (section 7); on Daytona nop and the 6 attempts score 0.0, phase_gate through run2_fail_noise_status_* as required (section 10); the 16 local variants were not run on Daytona
G13 PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - alt (SQL scoping, 403 refusals) scores 1 locally and 1.0 on Daytona; any 4xx, set comparison, API fields only, media type and attachment name only
G14 PASS - difficulty is completeness across six code paths and the identity layer while three legitimate cross-tenant paths stay open
G15 PASS - no unstated rule (refusal codes and API.md rules now stated as checked); lenient comparisons; flake found and fixed (keep-alive); repeats saved: 5/5 canonical, 5/5 alt; thumbs byte-exact is the one strict comparison, stated as "the same previews"
G16 PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - pinned digest and exact pins; committed databases checked against SHA256SUMS; seeded case list, shuffles and noise counts; on Daytona oracle 10 of 10 and --force-build 1.0, each valid trial with the same 2,475 run-1 and 1,231 run-2 checks
G17 PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - hidden DB, policy, grader and reference only in the tests image (0700); environment copies only app/; on Daytona the separate verifier ran in 19 of 19 trials, each with four uid-1001 staging lines, the checkpoint run as uid 1001 (rc=0) and a private loopback network
G18 PASS - check_task OK, harbor lint clean
G19 PASS - own copy of the kit and its own app; nothing shared at run time
G20 PASS (plan) - README row proposed in section 9; the repository README.md carries the final row
G21 PASS (plan) - limitations listed in section 9 (now including the unchecked list order)
G22 PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - canonical 1 locally (6 of 6 runs); oracle 10 of 10 = 1.0 and --force-build 1.0 on Daytona
G23 PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - original 0 locally; Daytona nop 0.0 (1,742 run-1 and 603 run-2 failures, as locally)
G24 PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - six attempts 0 locally and 0.0 on Daytona
G25 PASS (run, recorded: validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md) - alt 1 locally (6 of 6 runs) and 1.0 on Daytona
G26 PASS (plan) - policy.py is readable; per-check counts and examples in test-stdout; traces shipped in validation/tenant-isolation-docshare/traces/
G27 PASS (plan) - no keys; 127.0.0.1 only
G28 PASS - a failure means an incomplete audit, over-blocking or a broken permitted feature, all real gaps
G29 PASS - every check is a sentence of PERMISSIONS.md or API.md; nothing added only to fail agents
G30 PASS (plan) - delivery as a GitHub repository on the author's go
Result: PASS (no FAIL open); the (run) items are proven by the recorded Daytona runs of 2026-10-28 (section 10). Fixed
during the build: G8/G15 (support naming an unknown org was enforced but unstated;
now stated in PERMISSIONS.md section 2), G15/G16 (grader flake from ephemeral ports; keep-alive), G13 (two visible
tests pinned a refusal code; now accept 403 or 404). Fixed after the review: G12 FAIL (runs could be told apart; now
mixed), G11 (six permitted behaviours unchecked; now checked), G8/G15 (refusal-code wording; now matches what is
checked).
```

## 9. README row (proposed) and known limitations
Proposed row: capability = defensive application security (authorization in a multi-tenant API); objective = close the
reported cross-organisation download and every sibling so the service enforces PERMISSIONS.md, keeping share links,
org switching and support's read-only access; success check = about 3,700 HTTP requests to the agent's service on a
hidden database, refused and permitted ones mixed: refused ones must get a 4xx with no file data and change nothing
(DB diff), allowed ones must answer as the untouched service does; validation = Daytona run full1 (section 10) plus the
local matrix in section 7.

Known limitations (G21):
- The flaw class is well known; strong agents may pass often (fine: "A low pass rate by itself is not a sign of
  quality").
- The second reader shares an author with `policy.py` (section 3).
- The strict active-organisation rule (switch before touching the second org's files) is a policy choice. It is
  stated in PERMISSIONS.md section 2, but an agent that skims it may allow a member of both orgs too much and fail.
- Thumbs must be byte-identical to today's previews; an agent that rewrites the renderer fails.
- List order and export order are not checked (API.md states them; the instruction does not), so a fix that changes
  them still scores 1.
- The mixing defeats services that guess which run they are in. A service that recognised single permitted requests
  from the grader's request pattern would need the grader's source, which is in the 0700 tests image; the noise
  count before each permitted write is random for that reason. INFERENCE, not tested beyond section 7's variants.
- The agent's service has the host network during grading (kit limit); it could send the hidden data out.
- All timings are from the Mac; Daytona speed is UNVERIFIED until the proof run.

## 10. Daytona proof results (2026-10-28)
FACT: `validation/tenant-isolation-docshare/PROOF_RESULTS_full1.md` (run `full1`; the same rows are in
`proof_results_full1.json` and `run_full1.log` in that folder). Harbor 0.25.0 (`harbor.version` in the
`lock.json` of all 10 job folders); runner Daytona (`environment.type` "daytona" in each job's `config.json`; our
Daytona account is on Tier 1), two trials at a time (`n_concurrent_trials` 2); `verifier_environment_mode` "separate" in 19 of 19 trial
`result.json` files. Job folders: `jobs/tenant-isolation-docshare/tenant-isolation-docshare-<variant>-full1/` (last
column below; raw Harbor output, git-ignored and not in this repository; one trial per variant ships under
`validation/tenant-isolation-docshare/traces/`), run from 19:45:27 to 19:56:43 MST on 2026-10-28 (job `result.json`, Mac clock). The table is copied from
the file:

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-canonical-full1` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-alt-full1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-nop-full1` |
| deny_most | `-a oracle --ae SOLUTION=deny_most` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-deny_most-full1` |
| drop_org_switching | `-a oracle --ae SOLUTION=drop_org_switching` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-drop_org_switching-full1` |
| hardcode_visible_orgs | `-a oracle --ae SOLUTION=hardcode_visible_orgs` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-hardcode_visible_orgs-full1` |
| membership_plus_get | `-a oracle --ae SOLUTION=membership_plus_get` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-membership_plus_get-full1` |
| patch_get_only | `-a oracle --ae SOLUTION=patch_get_only` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-patch_get_only-full1` |
| phase_gate | `-a oracle --ae SOLUTION=phase_gate` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-phase_gate-full1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-force-build-full1` |

What section 7 asked the run to show (FACT: each trial's `verifier/test-stdout.txt`, `verifier/reward.json` and
`agent/oracle.txt`):
- In 19 of 19 trials: `[test.sh] lock ok` with `setid files left: 0`; `network isolation: ON (private namespace,
  loopback only)`; three `service on 127.0.0.1:<port> answered` lines (after 0.20-1.60 s); four `staged ... for uid
  1001 at /work/w<8 hex>` lines; the checkpoint line `ran [... '-I', '-c', 'import sqlite3...'] rc=0 timed_out=False`;
  no `unreadable (...)`; `reward=... (killed 0 runner processes)`. No `reward.json` holds `grader_error`.
- All 18 oracle trials' `agent/oracle.txt` show `applied <variant> to /app/docshare` (`canonical` for the canonical and
  force-build rows), so `SOLUTION` reached `solve.sh`.
- `phase_gate` scored 0 through run 2 only: `run1_failed` 0, `run2_failed` 50, among them
  `run2_fail_noise_status_rename` 8, `_share` 6, `_revoke` 17, `_delete` 11 (plus `run2_fail_write_outsider_revoke` 2,
  `run2_fail_write_link_works` 5, `run2_fail_write_create_link` 1). The `run2_fail_noise_status_*` counts are the
  condition section 7 set: the mixing, not another check, is what kills it.
- nop: `run1_failed` 1,742, `run2_failed` 603, `leaking_refusals` 785, the same counts as the local original (section 7).
- The line `write list: 50 requests, with 379 refused requests mixed in; 0 steps skipped` appears in 14 trials (the ten
  canonical, alt, force-build, `hardcode_visible_orgs`, `membership_plus_get`). Five failing variants show fewer
  permitted requests, all with 0 steps skipped: `deny_most` 35, `drop_org_switching` 36, `patch_get_only` and nop 38,
  `phase_gate` 45. INFERENCE from `tests/grade.py` (`share_cycle` returns after a failed link creation): the requests
  that depend on a failed step are not sent; this happens only in trials that already score 0.

Timings the runs recorded (FACT: `grading_seconds` from `verifier/reward.json`; the phase lines `phase <name>: <n>
checks, <n> failed, <s>s` from `verifier/test-stdout.txt`; the Harbor verifier phase from `verifier.started_at` to
`verifier.finished_at` in each trial's `result.json`):

| Rows | `grading_seconds` | phase original / run1 / run2 | Harbor verifier phase |
|---|---|---|---|
| canonical (10 trials) | 5.52-11.28 s | 0.57-0.87 / 2.76-6.56 / 1.69-4.07 s | 17.4-72.6 s |
| alt | 5.98 s | 0.61 / 3.53 / 1.81 s | 25.8 s |
| force-build | 5.48 s | 0.60 / 3.24 / 1.61 s | 25.7 s |
| nop and six attempts | 5.73-7.77 s | 0.59-0.79 / 3.39-4.53 / 1.51-3.47 s | 17.9-58.2 s |

Reading: the slowest valid run 1 on Daytona took 6.56 s (canonical; 2.92 s was the slowest on the Mac, section 6),
under the 30 s trigger in section 7 ("How to read the proof runs"), so the 90 s run caps stand. The slowest Harbor
verifier phase, 72.6 s, is under `verifier.timeout_sec` 900 s (whether that timeout covers the whole phase or only
`test.sh` is UNVERIFIED). Not exercised by these runs: the 16 local-only variants of section 7 and the image size.

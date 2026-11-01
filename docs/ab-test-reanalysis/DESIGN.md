# ab-test-reanalysis: design and build record

**What this file is.** The authoring record of the task [`tasks/ab-test-reanalysis/`](../../tasks/ab-test-reanalysis/)
in its revised form (designed and approved 2026-10-30, built 2026-10-30 to 2026-10-31): the task and its three hidden
issues (section 1), the file map (2), the build choices (3), the data (4), the band calibration (5), the grader (6),
the solutions and attempts (7), timings and caps (8), the local results (9), the blind read (10), the network setting,
the Daytona proof, the agent trials and their pre-registration (11), the gate record against
[docs/QUALITY_GATE.md](../QUALITY_GATE.md) (12), the README row, limitations and open issues (13), and what the
revision changed (14). The first version's record, which the pre-revision files under `authoring/ab-test-reanalysis/`
cite by section number, is in git: `git show 495c9f5:docs/ab-test-reanalysis/DESIGN.md`.

Last updated: 2026-10-31, 23:03 MST (Mac clock): fixes after a pre-commit check: the first version's grader is compared
with `git show 495c9f5:...`, Daytona Tier 2 is marked as not tried in sections 11.1 and 13, and two locators and one
command path are corrected. Before that, 2026-10-31, 22:01 MST (Mac clock): wording fixed after a check of 2026-10-31:
"the authors" in sections 3, 11.1 and 11.3, the shipped trial logs named for the web-tool flag (11.3), G30 scored PASS
(plan) as `docs/QUALITY_GATE.md` defines it (section 12), and the hidden tests' limitation (13). Before that,
2026-10-31, 15:01 MST: the gate record (G20, G21, G26 and the result line) and the open issues brought up to date, and
wording fixed after a further independent check of 2026-10-31 (sections 3, 4.1, 11.2, 11.3, 12 and 13). Before that,
2026-10-31, 13:50 MST: the Daytona proof rev1 and the three Claude Code trials recorded (sections 8, 11, 12 and 13),
with the measured pass count, 3 of 3 (section 11.4 (g)), and the record's wording fixed after an independent review of
2026-10-31. Before that, 2026-10-31, 00:48 MST: rewritten for the revision after the local build, an independent check,
the blind read and the fix pass, before any Daytona run or agent trial of the revised package.

The Daytona proof rev1 (2026-10-31, 01:37:54 to 01:51:53 MST, on the copy without the agent network line) gave ALL AS
EXPECTED (section 11.2); the agent trials: sections 11.3 and 11.4. A verdict marked "(local)" rests on runs on the Mac
(Darwin arm64, Python 3.12.13; FACT, auth/solution_checks.out.md line 3).

Labels: FACT (sourced or measured; the locator follows), INFERENCE (reasoned; the basis is named), RECOMMENDATION,
UNVERIFIED. Paths are relative to the repository root: "auth/x" = `authoring/ab-test-reanalysis/x`, "T/x" =
`tasks/ab-test-reanalysis/x`, "app/x" = `T/environment/app/x` (the agent's `/app/x`). "hw" = half-widths of the
reference interval. All data is synthetic, made by auth/gen_data.py; nothing comes from a real product.

## 1. What the task is

### 1.1 The request
Experiment EXP-2291, "related items v2" (a carousel redesign of the related-items module on product pages), comes back
`"invalid"`: the pipeline's sample ratio check fails with 16,570 users in A and 15,722 in B, B 5.12% short (FACT:
auth/app_checks.out.md Part 1; app/output/result.json, `srm_p` 2.37e-06). The PM (app/PM_NOTE.md) distrusts the
verdict: the assignment dashboard shows 16,935 and 17,165 users (49.7% / 50.3%), the team dashboard shows B's
click-through at 11.03% against A's 9.82% (B 12.3% higher), and the PM wants to turn B on for everyone on Monday
2026-09-21. The agent must find out what the experiment shows, fix the pipeline `app/abtest` so that it gives the
plan's readout (app/EXPERIMENT.md) on any export of this layout, and regenerate `app/output/result.json`
(T/instruction.md). The instruction declares the plan and `app/docs/` accurate, and everything else (code, comments,
README, dashboards, the current readout) not authoritative.

The plan's readout of the visible export is `no_ship`: `n_users` 16,570 / 16,702, CTR 0.09922 / 0.10019, `diff`
+0.000962, CI [-0.004316, +0.006240], `srm_p` 0.4693 (FACT: T/tests/expected/visible.json). Neither the shipped
"invalid" nor the team dashboard's "B wins" is right: the experiment shows no real effect.

### 1.2 The three hidden issues (one launch made all three)
| Issue | Kind | Evidence the agent has | Shipped defect | The plan's reading |
|---|---|---|---|---|
| H1: `pageviews.clicked` is not the plan's metric | judgment | plan section 4 (a counted pageview is clicked when the user opened the page of at least one related product from the module on it); docs/TRACKING.md (one module_click per click on any clickable element; `item:<id>` opens that product's page; `nav:prev` / `nav:next`, the arrows of the v2 carousel, open nothing; `link:all`, "See all" in every version from 2026-09-08, opens a list page); docs/DATA_DICTIONARY.md (`clicked` = at least one module_click event, precomputed for dashboards) | app/abtest/report.py sums `clicked` | a counted pageview is clicked if and only if it has an `item:` event |
| H2: the bot filter is driven by the variant, so the SRM is the analysis's | judgment | plan section 3 (exclude a user flagged by a rule that looks only at who the client is, whenever the flag was raised; no user is excluded for anything done during the experiment) and section 6 (an imbalance made by an analysis step means that step is wrong); docs/BOT_SCREENING.md (`ua_crawler` reads the client: user agent or data-centre IP; `velocity`, since 2026-08-28, reads the user's module_click events: 8 or more within 60 s, threshold set on July 2026 traffic; v2 came to experiments on 2026-09-01, TRACKING changelog) | app/abtest/filters.py drops every user with any bot_flags row | exclude users with a `ua_crawler` row; users with only `velocity` rows stay |
| H3: hand-assigned dogfood accounts | investigation; neither the instruction nor the plan names the hand-assigned accounts (the plan states the rule, section 3) | plan section 3 (a user whose variant was not set by the randomization is not in the experiment); DATA_DICTIONARY `method` (`hash` = the randomization; `override` = set by hand in the feature-flag console's allowlist); docs/LAUNCH_EXP-2291.md log (2026-09-03: the 100 accounts of the product pages team added to the allowlist of B) | app/abtest/load.py reads `method` and never uses it | keep `method = hash` only |

The shipped README, the filter's docstring and the PM's note each give an account that one command on the visible
export refutes (FACT: auth/app_checks.out.md Part 2): R1 `velocity` flags 9 users of A and 1,087 of B, `ua_crawler`
365 and 363; R2 `clicked` is 1 on 403 pageviews of A and 1,462 of B that have no `item:` event; R3 the 1,080 users
flagged by `velocity` alone are all hash users of B, every flag raised after the assignment; R4 the "clean 50/50"
counts the 100 override accounts (hash users 16,935 / 17,065); R5 the +12.3% counts arrow taps, See-all clicks and the
override accounts, which open products on 36.4% of their pageviews (product opens of hash users: B +0.92%).

Carried over from the first version, stated in the plan and correct in the shipped loader: an exact repeat of an
assignment row counts once; timestamps are compared as instants (`Z` and `+hh:mm` / `-hh:mm` mixed); pageviews with
`ts` at or after `assigned_at` count; users with no pageview are in `n_users`. The shipped stats.py is the first
version's canonical delta method and SRM test (FACT: app/abtest/stats.py equals the first version's
`solution/canonical/stats.py` byte for byte, by `git show 495c9f5:<that path>`), and the shipped decision order is
the plan's.

Each fix is needed: every attempt that fixes two of the three issues scores 0 (literal_bot_filter: H1 and H3 fixed;
platform_clicked: H2 and H3; keep_overrides: H1 and H2), and so does nop (FACT: section 9; auth/local_check.out.md).
An independent check of 2026-10-30 applied all 8 subsets of the three minimal fixes to the shipped code: only the
full set passed all six exports, and each other subset failed the visible export and at least one hidden export
(FACT, that check's run; its scratch script is not part of the repository).

### 1.3 What each reading gives on the visible export
FACT (auth/generation_report.out.md, paths table, measured on the written files by auth/data_checks.py; "lower/hw" is
the lower bound in the path's own half-widths):

| Reading | n_users A / B | clicks A / B | CTR A / B | lower/hw | srm_p | decision |
|---|---|---|---|---|---|---|
| shipped: every flagged user out, any method, `clicked` | 16,570 / 15,722 | 16,837 / 16,466 | 0.10164 / 0.10381 | -0.60 | 2.37e-06 | invalid |
| H2 fixed only | 16,570 / 16,802 | 16,837 / 19,608 | 0.10164 / 0.11461 | +1.40 | 0.204 | ship |
| H1 and H2 fixed, override accounts kept | 16,570 / 16,802 | 16,436 / 18,146 | 0.09922 / 0.10606 | +0.27 | 0.204 | ship |
| team dashboard: every row of every assigned user, `clicked` | 16,935 / 17,165 | 17,656 / 20,396 | 0.09822 / 0.11032 | +1.34 | 0.213 | ship |
| H1 and H3 fixed, every flagged user out | 16,570 / 15,622 | 16,436 / 14,585 | 0.09922 / 0.09422 | -1.93 | 1.27e-07 | invalid |
| H2 and H3 fixed, `clicked` | 16,570 / 16,702 | 16,837 / 18,212 | 0.10164 / 0.10887 | +0.37 | 0.469 | ship |
| clicked = any event whose target is not `nav:` | 16,570 / 16,702 | 16,837 / 17,183 | 0.10164 / 0.10272 | -0.80 | 0.469 | no_ship |
| reference: all three fixed | 16,570 / 16,702 | 16,436 / 16,759 | 0.09922 / 0.10019 | -0.82 | 0.469 | no_ship |

## 2. File map
Package `T/`: 75 files, 27,114,446 bytes (FACT: `git ls-files --cached --others --exclude-standard` and `find`,
2026-10-31 after the fix pass). A tool-state folder `.claude-flow/` at the task's top level is not counted and does
not enter Harbor's task digest, which hashes only `task.toml`, `instruction.md`, a README, a trajectory file and the
`environment/`, `tests/`, `solution/` and `steps/` folders (FACT: Harbor 0.25.0 `publisher/packager.py` lines 29-76).

| Path | What it is |
|---|---|
| `task.toml` | schema 1.4; the `/app` artifact with `data`, `__pycache__`, `.venv` excluded; `[agent]` 3,600 s and `network_mode = "no-network"`; `[verifier]` separate, 1,000 s, its own 1 vCPU / 2,048 MB; agent sandbox 2 vCPU / 4,096 MB; the label `difficulty = "hard"`, written before any trial (the measured count: section 11.4 (g)) |
| `instruction.md` | the request, what is authoritative and what is not, the command, how the result is checked (limits, packages, tolerances, the six readouts), the shared closing sentence |
| `environment/Dockerfile` | pinned base digest; numpy 2.5.4, pandas 3.1.0, scipy 1.18.1, python-dateutil 3.0.0, six 1.17.0, tzdata 2026.6; `COPY app/ /app/` (unchanged from the first version) |
| `environment/app/EXPERIMENT.md` | the plan, agreed 2026-08-25: question, randomization, population, metric, uncertainty (delta method, user bootstrap with at least 2,000 resamples, CR1), SRM check, decision order, input files, output keys |
| `environment/app/docs/` | the data platform's documentation: `DATA_DICTIONARY.md` (export scope, files, columns), `TRACKING.md` (module_click targets, module versions per arm, changelog), `BOT_SCREENING.md` (the two rules), `LAUNCH_EXP-2291.md` (salt, arms, window, the dogfood log) |
| `environment/app/abtest/` | the shipped pipeline: `load.py` (defect 3), `filters.py` (defect 2), `report.py` (defect 1), `stats.py` (correct), `__init__.py` |
| `environment/app/PM_NOTE.md`, `README.md` | the PM's memo with the two dashboards; the layout and the command, with two stale accounts |
| `environment/app/data/` | the visible export: `assignments.csv.gz`, `bot_flags.csv.gz`, `pageviews.csv.gz`, `module_clicks.csv.gz` (4,999,070 bytes; dropped at grading by design) |
| `environment/app/output/result.json` | the shipped readout, made by the shipped code |
| `tests/Dockerfile` | the same base and pins; `COPY . /tests/`, uid 1001 `runner`, `/tests` 0700 (unchanged) |
| `tests/test.sh`, `tests/kit.py` | the shared kit, copied by `tools/sync_kit.py` (unchanged) |
| `tests/grade.py` | the grader (section 6) |
| `tests/hidden/<set>/` | five hidden exports (h_null, h_pos, h_srm, h_plain, h_neg), the same four `.csv.gz` files, gzip mtime 0 |
| `tests/expected/<set>.json` | the reference readouts of the six exports (auth/ref_a.py) |
| `tests/SHA256SUMS` | 26 files: the 20 hidden inputs and the 6 expected readouts |
| `solution/solve.sh` | `SOLUTION` = `canonical` (default), `alt_time`, `alt_recount`, `nop`, or an attempt |
| `solution/canonical/`, `alt_time/`, `alt_recount/` | complete sets of the four `abtest` modules (section 7) |
| `solution/attempts/<name>/` | ten wrong or shortcut attempts (section 7) |

Authoring `auth/` (outside the package):

| File | What it does | Output |
|---|---|---|
| `gen_data.py` | the six exports, the seed search, the expected readouts, SHA256SUMS (section 4) | `generation_report.out.md`, `.json` |
| `data_checks.py` | assertions (a) to (n), caps and floors on the written files; every reading's readout (section 4.4) | inside the report |
| `ref_a.py` | reference A: stdlib csv, gzip and `datetime.fromisoformat`, rule route, delta method | `T/tests/expected/*.json` |
| `ref_b.py` | reference B: pandas, time route; delta, CR1 and the bootstrap for the calibration | checked against ref_a by gen_data.py |
| `app_checks.py` | the figures that the instruction and the PM quote, the stale-account check, the shipped code on six exports, doc claims on six exports | `app_checks.out.md` |
| `solution_checks.py` | the three valid variants on six exports in two interpreter modes, with times and peak memory | `solution_checks.out.md`, `.json` |
| `calibration_study.py` | the band calibration (section 5) | `calibration_study.out.md`, `calibration.json` |
| `grader_probes.py` | 40 format, tamper and staging probes of `grade.py` (section 6) | `grader_probes.out.md` |
| `local_check.py` | the local proof matrix (section 9) | `local_check.out.md`, `local_results.json` |
| `probes/` | five local-only wrong readouts (section 7) | |
| `twin_identity.py`, `click_rule_probes.py`, `calibration_before_*.out.md`, `calibration_first_run.out.md` | pre-revision records with a status banner (they read or describe the first version's data and no longer run) | |

## 3. Build choices and their reasons
The approved design (not shipped) is the revision design of 2026-10-30, approved by the authors: the recommended design
of the revision round with three grafts from an alternative design (the exclusion sentence of plan section 3, the
dogfood override cohort with the masked-imbalance set h_srm, and hidden sets that put the carousel in the other arm or
nowhere). None of the choices below changes what the agent must find or what the grader checks.
1. **Story figures come from the data.** B is 5.12% short ("about 5%" in the instruction) and the team dashboard
   shows +12.3%. The team dashboard is every pageview row of every assigned user with
   `clicked` (+12.32%); its variant with `ts` at or after `assigned_at` (+12.49%) is the one the seed condition reads
   (7% to 13%). FACT: auth/app_checks.out.md Part 1; auth/generation_report.out.md (paths `dashboard`,
   `dashboard_all_rows`). Reason: every figure an agent or reviewer sees is computed, never typed.
2. **Generator parameters:** visible CTR 0.10, mean
   11.5 pageviews, 100 dogfood accounts with mean 40 pageviews at CTR 0.36; h_null intra-user correlation 0.42; h_neg
   carousel use rate 0.22 (FACT: auth/gen_data.py `SETS`). Reason: the soft condition and h_neg's "clicked up, product
   opens down".
3. **Hard seed conditions added from the design's target tables:** the literal bot filter gives "invalid" on visible,
   h_null, h_pos and h_neg; on h_neg the `clicked` diff is positive and the reference diff negative; floors of 20 rows
   per arm for the rows that make the attempts fail (FACT: auth/gen_data.py `conditions()`, `FLOOR`). Reason: each
   attempt must fail where the design says, on the written files.
4. **Construction choices** (FACT: auth/gen_data.py docstring; the pre-assignment window from line 206 only, since the
   docstring and the comment at line 198 say "300 s to 3 days"): pre-assignment pageviews 300 s to 3 days and 299 s
   before `assigned_at`; a carousel use sits on an isolated pageview (no other pageview of the user within 600 s, the
   burst inside one UTC day); its item and link events follow the taps 1 to 4 s apart, or 100 to 200 s later after a
   use of fewer than 8 taps, so 7 taps never trip the rule; override accounts make no arrow taps; crawlers make no
   See-all click; click-fraud bots are 0.06% of hash users. Reason: assertions (c), (d), (e) and (f) hold exactly, so
   the three population routes give the same users.
5. **`srm_all_assigned`** (assertion (m), a local probe) is the SRM test on every distinct assigned user, any method,
   bots in. Reason: the design names the probe, not its population.
6. **`srm_p` by a closed form in the valid variants:** canonical stats.py computes erfc(sqrt(chi2 / 2)), bit-equal to
   ref_a on all six exports; scipy's `chisquare` (the shipped stats.py) differs by at most 1.42e-14 relative (FACT: a
   check run of 2026-10-31 on `T/tests/expected/*.json`). Both are far inside the 1% tolerance.
7. **Each valid variant is a complete set of the four modules,** copied over `abtest/` by solve.sh, not a minimal diff
   of the shipped code. Reason: the shipped modules were written in parallel; the only shared file is
   `abtest/__init__.py`, a docstring.
8. **Attempts are `patch.py` edits on the canonical base,** one stated change each, that exit 1 when an anchor is not
   found exactly once (`fix_visible_only`: `BASE` "shipped" and a one-off script; `pageview_ci`: a stats.py overlay).
   `b_only_patch` is read as: override accounts out in both arms; in B velocity-only users stay and the `item:` rule
   is used; in A every flagged user is out and `clicked` is used. Reason: a loud failure on drift, and the closest
   reading of "fixed in arm B only".
9. **The five local probes live in auth/probes/,** outside the package: tools/proof_matrix.py runs every entry of
   `T/solution/attempts/`, and the design lists the probes as local only.
10. **grade.py's `check_sums()` is stricter:** it also fails unless `T/tests/SHA256SUMS` lists exactly the 20 hidden
    inputs and the 6 expected readouts. `compare()` is the first version's, unchanged (section 6).
11. **Calibration gates over the plan's three methods** (delta, CR1, within-arm percentile bootstrap with at least
    2,000 resamples); the basic, normal and pooled bootstraps are reported and also stay at or below 0.1111
    (auth/calibration_study.out.md). The multiplier sweeps are information, not gates (the design drops the
    multiplier attempts).
12. **PM_NOTE.md is a dated memo** (Wednesday 2026-09-16; launch on Monday 2026-09-21) written without personal
    pronouns, by the build's writing rules.
13. **The instruction says "100,000 module_clicks rows"**: it names the file.
14. **The blind read ran after `tests/` existed,** not before, as the design's build gate says. The reader was given
    only `T/instruction.md`, `T/environment/app/` and the build's writing rules, and recorded that nothing else of
    the task was opened (section 10).
15. **Fix pass of 2026-10-31,** after the independent check and the blind read, before any trial: (a) plan section 4
    reads "opened the page of at least one related product ... opening two product pages" (was "opened at least one
    related product ... opening two"); (b) DATA_DICTIONARY: timestamps are "to the second"; pageviews are "logged when
    the page has loaded", and "the pageview on which a user was assigned has no row if the user left before the page
    loaded"; module_clicks: "two clicks on the same element in the same second give two identical rows; each row is
    one event"; (c) the instruction says other experiments "differ in what each arm shows" (was "in their variants")
    and names the six readouts ("`/app/output/result.json` and the five runs"); (d) the pageview_ci docstring drops a
    reference to a removed attempt. Reason: each closes a reading that the blind reader found open, or a gap between
    the docs and the data (section 10). None changes a rule, the data, the expected readouts or the grader: the
    regenerated files are identical and the matrix is unchanged on all 38 runs (sections 4.5 and 9).

## 4. Data

### 4.1 How a set is made
FACT (auth/gen_data.py docstring and `SETS`). The window is 2026-09-01 00:00Z to 2026-09-15 00:00Z for every set. Hash
users are randomized to B with probability p_b (0.5; 0.486 in h_srm); a share is crawler traffic (`ua_crawler`), and
0.06% are click-fraud bots, which are crawlers too. Override accounts (dogfood or QA; arm, size and behaviour per set)
get their arm by hand, have one assignment row and are never bots. Each human has an item-click propensity from a Beta
distribution (mean = the set's CTR, intra-user correlation rho); hash users of B have it multiplied by (1 + lift).
Post-assignment pageviews follow a floored, zero-inflated lognormal (heavy tail); 20% of users also have pageviews 300 s
to 3 days and 299 s before `assigned_at` (auth/gen_data.py line 206; v1 shows there); with probability 0.6 a user's
first post-assignment pageview is exactly at `assigned_at`; about 1% of hash users have an exactly repeated assignment
row. Module events: 0 to 2 `item:` events per pageview; a rare `link:all` (probability 0.004 per pageview) from
2026-09-08 in every module version; in the carousel arm humans use the carousel Poisson(lam sqrt(p0 / ctr)) times, each
use 6 + Poisson(4) arrow taps 0.5 to 3 s apart; click-fraud bots make bursts of 10 + Poisson(4) pageviews 2 to 4 s apart
with one item click each. `pageviews.clicked` = 1 when any module event is on the pageview. `bot_flags`: one
`ua_crawler` row per crawler, 1 to 1,800 s before the earlier of its first logged pageview and `assigned_at`; one
`velocity` row per user and UTC day on which the documented rule fires on `module_clicks`, at 02:00:00Z the next day.
Every timestamp is whole-second ISO 8601 with `Z` or an offset drawn per row. Event times are floored to the second
(auth/gen_data.py line 315), so two arrow taps of one second give two identical rows.

### 4.2 The six exports
FACT (auth/generation_report.out.md; per-set parameters from auth/gen_data.py `SETS`; "lift" = the true lift of B's
item-click propensity; DE = design effect of the reference interval):

| Set | Module A / B | Arrows in | Overrides | Crawlers | Lift | Seed (tries) | n_users A / B | DE | lower/hw | upper/hw | srm_p | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| visible (EXP-2291) | v1 / v2 | B | 100 dogfood in B | 2.0% | 0 | 1000 (1) | 16,570 / 16,702 | 6.72 | -0.818 | +1.182 | 0.4693 | no_ship |
| h_null | v2 / a grid | A | 150 QA in A | 1.5% | 0 | 2000 (1) | 15,669 / 15,844 | 19.10 | -1.047 | +0.953 | 0.3242 | no_ship |
| h_pos | v1 / v2 | B | none | 1.5% | +10% | 3001 (2) | 15,707 / 15,806 | 7.44 | +1.455 | +3.455 | 0.5771 | ship |
| h_srm | v1 / v2 | B | 500 QA in B | 1.5% | +13% | 4002 (3) | 17,208 / 16,259 | 7.12 | +0.945 | +2.945 | 2.131e-07 | invalid |
| h_plain | v1 / v1 with another ranking | none | none | 5.0% | +13% | 5000 (1) | 14,356 / 14,155 | 6.36 | +1.100 | +3.100 | 0.2339 | ship |
| h_neg | v1 / v2 | B | none | 2.0% | -10% | 6001 (2) | 16,557 / 16,679 | 7.44 | -2.999 | -0.999 | 0.5034 | no_ship |

What each set stops (FACT: section 9 and auth/generation_report.out.md): visible: nop, the H2-only fix, the
dashboard, keep_overrides (counts; the soft condition makes it ship); h_null: b_only_patch and any rule tied to arm
B (the arrows are in A), keep_overrides (QA accounts with low CTR in A), the literal filter ("invalid"); h_pos:
hardcode_no_ship, the literal filter; h_srm: keep_overrides (the 500 QA accounts hide the hash imbalance:
`srm_p` 0.0148, ship, against "invalid"), hardcode_no_ship; h_plain: code that assumes arrows or overrides exist,
no_bot_filter (5% crawlers), hardcode_no_ship; h_neg: platform_clicked (`clicked` gives +1.70%, product opens
-11.1%). Row counts and sizes (assignments / bot_flags / pageviews / module_clicks; gzip bytes): visible 34,436 /
1,883 / 364,644 / 51,671, 4,999,070; h_null 32,476 / 1,434 / 269,935 / 40,376, 3,776,104; h_pos 32,332 / 1,472 /
330,117 / 54,909, 4,672,802; h_srm 34,835 / 1,658 / 355,667 / 51,566, 4,915,818; h_plain 30,291 / 1,527 / 266,851 /
24,593, 3,801,093; h_neg 34,396 / 3,026 / 347,797 / 58,851, 4,821,682. Every set is inside the instruction's limits
(50,000 users, 500,000 pageview rows, 100,000 module_clicks rows) and below 6 MB of gzip.

### 4.3 Seed conditions
Seeds are tried in order from each set's base; the first whose arrays meet every hard condition is kept (FACT:
auth/gen_data.py `conditions()`, `search()` and the constants above them):
- the reference lower bound is at least 0.5 hw from 0 (no-effect sets: at or below -0.5; ship and SRM sets: at or
  above +0.5);
- `srm_p` of the reference at least 0.05 on every set but h_srm; on h_srm between 1e-11 and 1e-5 (flagged, and above
  the grader's 1e-12 floor, so the 1%-relative comparison applies);
- visible: the shipped readout's `srm_p` below 1e-5; the H2-only readout ships with its lower bound at least +0.5 of
  its own half-widths; the dashboard's relative lift between 7% and 13%;
- h_srm: the readout that keeps the override accounts has `srm_p` at least 0.005 and a lower bound at least +0.35 of
  its half-widths (it ships, hiding the real imbalance);
- the literal bot filter gives `srm_p` below 0.001 on visible, h_null, h_pos and h_neg; on h_neg the `clicked` diff
  is above 0 and the reference diff below 0;
- design effect at least 5.5 on every set (assertion (n)); h_null between 18 and 25;
- the SRM test on all assigned users misses the reference `srm_p` by at least 3% relative (assertion (m));
- construction checks (c), (d), (f), the caps and the floors of 20 rows per arm.
Soft condition (visible only): the readout that keeps the override accounts ships; kept because at least 3 of the
first 300 seeds meet the hard and the soft conditions (FACT: auth/generation_report.json, visible search: 16 seeds
scanned, 3 passing, `soft_kept` true; seed 1000 on the first try).

### 4.4 Assertions (a) to (n)
auth/data_checks.py checks each written export with pandas and numpy, independently of the generator's arrays, and
gen_data.py stops on any failure (FACT: auth/data_checks.py docstring; "checks 38 passed" on every set):
(a) every `ua_crawler` flag is raised at least 1 s before the user's `assigned_at`; one row per crawler.
(b) every `velocity` flag is raised after the user's `assigned_at`, at 02:00:00 UTC.
(c) every velocity-only user is a hash user of the carousel arm with 8 or more arrow taps on each flagged day, among
    them 8 within 60 s.
(d) no user without a `ua_crawler` row has 5 `item:` events within 60 s.
(e) the three population routes give the same users per arm: rule (no `ua_crawler` row), time (no flag of any rule
    at or before `assigned_at`) and recount (`ua_crawler` plus the velocity rule recounted on `item:` events only).
(f) every run of 8 consecutive module events of one user spans under 40 s within one UTC day, or more than 90 s.
(g) every module event has its pageview (same user) and is at or after the pageview's `ts`; events of
    pre-assignment pageviews fall before `assigned_at`.
(h) `pageviews.clicked` = 1 exactly when the pageview has at least one module event.
(i) ref_a = ref_b (checked in gen_data.py, section 4.5).
(j) the `velocity` rows are exactly the user-days on which the documented rule fires on `module_clicks` (8 or more
    events of any target within 60 s on one UTC day; the run of the next day at 02:00 UTC; first run 2026-08-28),
    with "within 60 s" read as under 60 s or at most 60 s.
(k) override accounts have one assignment row and no `bot_flags` row.
(l) targets are `item:<digits>`, `nav:prev`, `nav:next` or `link:all` only; `nav:` only in the carousel arm and only
    on post-assignment pageviews; `link:all` only from 2026-09-08 00:00Z.
(m) the SRM test on all assigned users misses the reference `srm_p` by at least 3% relative.
(n) the design effect of the reference readout is at least 5.5.
Caps: at most 50,000 assigned users, 500,000 pageview rows and 100,000 module_clicks rows. Floors: per arm, among the
reference users, at least 20 counted pageviews with `link:all` and no `item:` event, 20 with two `item:` events, and
20 pre-assignment pageviews with an `item:` event.
auth/app_checks.py Part 4 checks the docs' other claims on all six exports (the script: 93 PASS, 0 FAIL; FACT:
auth/app_checks.out.md), among them, since the fix pass, the two new DATA_DICTIONARY sentences: assigned users without
a pageview at `assigned_at` and without any pageview row occur on every set (visible 15,604 and 2,815); the identical
module_clicks rows are all arrow taps, and the velocity rule over every row gives exactly the `velocity` rows (over
de-duplicated rows 19 user-days of visible would differ).

### 4.5 References, determinism, sizes
ref_a (stdlib, rule route) and ref_b (pandas, time route) must give equal counts, `srm_p` within 1e-12 relative,
CTRs, diff and bounds within 1e-9, and equal decisions, or generation stops; the generator's own arrays must equal
ref_a too (FACT: auth/gen_data.py lines 718-748). Measured largest difference over CTRs, diff and bounds: 3.5e-18
(0 on h_pos; FACT: auth/generation_report.json `ref_ab_max_abs_diff`). Regeneration, 2026-10-31 00:30 to 00:31 MST:
gen_data.py with data_checks.py, ref_a.py and ref_b.py copied twice into scratch trees of the same relative layout,
exit 0 both times (18 s and 17 s), "checks 38 passed" on all six sets, "SHA256SUMS lists 26 files"; the two trees are
identical, and their 31 task files and 2 reports equal the package's and auth's byte for byte; `shasum -a 256 -c
T/tests/SHA256SUMS` gives 26 OK.

## 5. Band calibration
Rule of the approved design: keep the band of 0.25 hw only if the worst error of a plan method is at most 0.125 hw
and the pageview-level interval misses by at least 0.50 hw on every set; otherwise change the data, never the band.
FACT (auth/calibration_study.out.md; 200 seeds of B=2,000 and 30 seeds of B=5,000 and of the pooled bootstrap; run
2026-10-30 22:51:50 to 23:00:52 MST):

| Set | DE | Worst plan-method error | pageview_ci miss |
|---|---|---|---|
| visible | 6.72 | 0.0855 | 0.6144 |
| h_null | 19.10 | 0.0948 | 0.7712 |
| h_pos | 7.44 | 0.0879 | 0.6333 |
| h_srm | 7.12 | 0.0892 | 0.6252 |
| h_plain | 6.36 | 0.1111 | 0.6035 |
| h_neg | 7.44 | 0.0981 | 0.6335 |

- Gate 1: worst plan-method error 0.1111 (h_plain, percentile bootstrap B=2,000; a sample maximum over 200 seeds) at
  or below 0.125: PASS. The delta method (with and without the N/(N-1) factor) and CR1 are 0.0000 on every set; B=5,000
  worst 0.0629.
- Gate 2: the pageview-level interval misses by at least 0.6035 (h_plain), at or above 0.50: PASS.
- Spread: per bound, the B=2,000 bootstrap error has SD at most 0.0321 and |mean| at most 0.0119, so the band is at
  least 7.4 SD from the mean on every set; |mean| + 4 SD is 0.1405 at worst.
- Information (not gates): the best single constant times the pageview interval misses by 0.2682 on its worst set,
  and the constant fitted on visible (2.593) misses h_null by 0.4067; the factor 1 + rho (m_w - 1) with one rho
  between 0.235 and 0.310 passes all six sets (best 0.275, worst error 0.1867), and c K^g with c fitted on visible
  passes all six for g from 0.82 to 1.99 (limitation 6).
- Decision margins: the smallest |lower|/hw of a reference readout is 0.818 (visible).
- An independent re-run (2026-10-30 23:46 to 23:56 MST, 588.7 s) gave the same `calibration.json` apart from its
  timing keys ("BAND KEPT"; that run's output is not shipped).

## 6. Grader (`tests/grade.py`)
Order: the resources of the verifier sandbox are logged as metrics that never affect the reward (cgroup CPU and memory
limits, CPU affinity, the host's figures); every file of `T/tests/SHA256SUMS` is verified and the list must be exactly
the 20 hidden inputs and 6 expected readouts; `/app` is copied (`kit.prepare_submission`); `output/result.json` is
read through `kit.read_as_runner`; then for each hidden set the four `.csv.gz` files are copied byte for byte into
root-only scratch and staged under a neutral name (`exp1` to `exp5`), and `python3 -m abtest.report --data <in> --out
<out>/result.json` runs as uid 1001 from the copy's top folder with a 120 s cap; its output is read as uid 1001 and
parsed as JSON data only. Agent code is never imported. A readout passes when `n_users`, `pageviews` and `clicks` per
arm are exact (an integer or a float without a fraction, never a boolean), each CTR and `diff` within 1e-9, `srm_p`
within 1% relative (or both below 1e-12), `srm_flag` and `decision` equal (the decision after trimming and lower
case), and each bound of `ci_95` within 0.25 hw of the reference bound. Reward 1 only if all six readouts pass and
every run exits 0 in time. FACT: T/tests/grade.py; `compare()`, `number()`, `count()` and `flag()` are the first
version's, unchanged (a function-text comparison with `git show 495c9f5:tasks/ab-test-reanalysis/tests/grade.py`,
2026-10-31); `BAND` 0.25, `CTR_TOL` 1e-9, `SRM_REL` 0.01, `SRM_TINY` 1e-12, `RUN_CAP_SEC` 120.
Probes (FACT: auth/grader_probes.out.md, "40 probes: ALL AS EXPECTED"): 30 on `compare()` (reordered and extra keys,
a BOM, counts as floats, `srm_flag` 0, " No_Ship ", CTR off by 5e-10, a bound off by 0.24 hw and `srm_p` off by 0.9%
pass; a bound off by 0.26 hw, swapped bounds, `ci_95` as an object and the other malformed or wrong readouts fail), 4
on `check_sums()` (a one-byte tamper, a missing and an extra line), 6 on the staging (exactly the four files, byte
for byte, nothing else in a hidden folder).

## 7. Solutions and attempts
| Variant | What it does | Expected |
|---|---|---|
| `canonical` | pandas, rule route: `method = hash`; users with a `ua_crawler` row out of both arms (velocity flags exclude no one); instants, `ts` at or after `assigned_at`; a counted pageview is clicked when its `pageview_id` has an `item:` event (set membership); per-user sums with zero-view users; delta-method CI; SRM chi-square; the plan's decision; computed `notes` | 1 |
| `alt_time` | pandas, time route: hash users with no flag of any rule at or before `assigned_at`; a left join to the item events and groupby sums; user bootstrap within each arm, 5,000 resamples, fixed seed, percentile interval | 1 |
| `alt_recount` | stdlib csv, gzip and `datetime.fromisoformat` with numpy bincount sums: `ua_crawler` plus the velocity rule recounted on `item:` events only; CR1 interval clustered by user | 1 |
| `nop` | the shipped code and readout | 0 |
| `literal_bot_filter` | H1 and H3 fixed; every flagged user out, as the shipped code does | 0 |
| `platform_clicked` | H2 and H3 fixed; the click stays `pageviews.clicked` | 0 |
| `keep_overrides` | H1 and H2 fixed; the hand-assigned accounts stay | 0 |
| `not_nav_clicked` | clicked = any event whose target is not `nav:` (See all counted) | 0 |
| `b_only_patch` | an instance patch for EXP-2291: H1 and H2 fixed in arm B only, override accounts out | 0 |
| `no_bot_filter` | the bot filter dropped because it "made" the SRM; crawlers counted | 0 |
| `item_click_events` | a pageview's clicks = its number of `item:` events, not 1 | 0 |
| `pageview_ci` | every count right, but the two-proportion interval on pageviews, labelled as the delta method | 0 |
| `hardcode_no_ship` | the canonical numbers with the decision always `no_ship` | 0 |
| `fix_visible_only` | the shipped pipeline kept; a one-off script writes the right visible readout | 0 |

Local probes (auth/probes/, never on Daytona; each a `patch.py` on the canonical base): `drop_nav_pageviews` (the
pageviews with an arrow tap removed from both counts), `user_click_join` (clicks joined to users, pre-assignment
clicks included), `srm_all_assigned` (the SRM test on every assigned user), `text_time` (timestamps compared as text),
`keep_pre_assignment` (pre-assignment pageviews counted). All three valid routes pass because the generator makes them
coincide (assertion (e)); the rule route is canonical because the plan describes rule types. The recount's extra
exclusion reads behaviour, which plan section 3 rules out: it is accepted as redundant (the same users), not as a
sanctioned reading (limitation 7).

## 8. Timings and caps
FACT (Mac, runs of 2026-10-31; auth/local_check.out.md and auth/local_results.json, run 00:24:42 to 00:30:22 MST,
339.6 s for 38 variant-runs; auth/solution_checks.out.md for memory, run 2026-10-30 19:09 MST):
- Slowest run of the command on one hidden set: canonical 1.641 s, alt_time 2.155 s (the slowest of all variants),
  alt_recount 1.521 s; any attempt or probe at most 1.729 s. Grading passes (one full `grade.py`): 6.67 to 10.4 s
  (alt_time the slowest). solve.sh at most 2.18 s.
- Peak memory of one run (a one-child wrapper's getrusage): canonical 318.3 MiB, alt_time 402.7 MiB, alt_recount
  194.1 MiB (venv; with pyarrow blocked, as in the images, 249.8, 325.2 and 194.2 MiB).
- The shipped code: 1.29 to 1.49 s per export (auth/app_checks.py's run of 2026-10-31, printed to its console only).
- At the instruction's limits: an independent check of 2026-10-30 grew the visible export by a 40% copy with new ids
  (47,740 users, 509,835 pageview rows, which is above the 500,000 limit, and 72,441 module_clicks rows) and ran the
  command with pyarrow blocked: canonical 2.2 s and 298 MiB, alt_time 3.1 s and 402 MiB, alt_recount 2.2 s and
  213 MiB, the shipped code 1.8 s and 293 MiB (FACT, that check's run; its scratch script is not shipped).
Derived: the per-run cap stays 120 s (the instruction states it; about 55 times the slowest valid run on the Mac);
`verifier.timeout_sec` 1,000 s covers (5 x 120 s + 10.4 s) x 1.5 = 915.6 s; `agent.timeout_sec` 3,600 s (the design's
hour). FACT (Daytona proof rev1, the 24 trials' `verifier/reward.json` and `verifier/test-stdout.txt`; section 11.2):
the slowest hidden run took 2.731 s (alt_time on h_null; alt_time's slowest run on the Mac is 2.155 s), about 44 times
under the 120 s cap; every verifier ran with `res_cgroup_cpus=1` and `res_cgroup_mem_mib=2048`; the verifier phases
took 14.9 to 44.2 s against the 1,000 s timeout; memory use in the verifier is not logged.

## 9. Local results
Command: `.venv/bin/python -I -B authoring/ab-test-reanalysis/local_check.py --all` (for each variant: copy
`environment/app`, run `solution/solve.sh` with `SOLUTION=<variant>` and `APP_DIR=<copy>`, drop `data`,
`__pycache__` and `.venv` at any depth, then `tests/grade.py` in KIT_LOCAL mode; every variant twice: "venv", this
interpreter with pyarrow, and "image", the same interpreter with pyarrow blocked, as in the task images). FACT, run
2026-10-31 00:24:42 to 00:30:22 MST, "ALL AS EXPECTED", exit 0; equal to the run of 2026-10-30 23:26 MST on every
reward, failing key, solve exit code, design verdict and non-time metric of all 38 runs. A 0-expected run counts only
if solve.sh exited 0 and no graded run crashed. Failing keys are the same in both modes.

| Variant | Kind | Reward venv / image | Sets failed | Main failing keys | Slowest run s venv / image | Grade s venv / image |
|---|---|---|---|---|---|---|
| canonical | valid | 1.0 / 1.0 | none | | 1.641 / 1.442 | 7.99 / 7.08 |
| alt_time | valid | 1.0 / 1.0 | none | | 2.155 / 2.129 | 10.4 / 10.16 |
| alt_recount | valid | 1.0 / 1.0 | none | | 1.486 / 1.521 | 7.16 / 7.16 |
| nop | nop | 0.0 / 0.0 | all six | counts on five sets; h_plain clicks | 1.413 / 1.348 | 7.06 / 6.67 |
| b_only_patch | attempt | 0.0 / 0.0 | all six | clicks.A everywhere; h_null n_users.A, decision | 1.590 / 1.430 | 7.73 / 7.04 |
| fix_visible_only | attempt | 0.0 / 0.0 | the five hidden | counts | 1.404 / 1.406 | 6.99 / 6.67 |
| hardcode_no_ship | attempt | 0.0 / 0.0 | h_pos, h_srm, h_plain | decision | 1.729 / 1.453 | 7.82 / 7.04 |
| item_click_events | attempt | 0.0 / 0.0 | all six | clicks | 1.518 / 1.431 | 7.54 / 7.09 |
| keep_overrides | attempt | 0.0 / 0.0 | visible, h_null, h_srm | n_users of the overrides' arm; h_srm decision (ship) | 1.578 / 1.424 | 7.65 / 7.01 |
| literal_bot_filter | attempt | 0.0 / 0.0 | all but h_plain | n_users of the carousel arm; decision on four sets | 1.648 / 1.433 | 7.76 / 7.02 |
| no_bot_filter | attempt | 0.0 / 0.0 | all six | n_users | 1.539 / 1.428 | 7.6 / 7.01 |
| not_nav_clicked | attempt | 0.0 / 0.0 | all six | clicks | 1.533 / 1.419 | 7.63 / 6.99 |
| pageview_ci | attempt | 0.0 / 0.0 | all six | ci_95 only (0.60 to 0.77 hw) | 1.555 / 1.437 | 7.76 / 6.96 |
| platform_clicked | attempt | 0.0 / 0.0 | all six | clicks; visible decision (ship) | 1.482 / 1.507 | 7.33 / 7.07 |
| drop_nav_pageviews | probe | 0.0 / 0.0 | all but h_plain | pageviews of the carousel arm | 1.719 / 1.448 | 8.04 / 7.07 |
| keep_pre_assignment | probe | 0.0 / 0.0 | all six | pageviews, clicks | 1.660 / 1.390 | 7.75 / 7.04 |
| srm_all_assigned | probe | 0.0 / 0.0 | all six | srm_p; h_srm flag and decision | 1.538 / 1.407 | 7.59 / 6.95 |
| text_time | probe | 0.0 / 0.0 | all six | pageviews, clicks | 1.507 / 1.408 | 7.48 / 6.92 |
| user_click_join | probe | 0.0 / 0.0 | all six | clicks | 1.585 / 1.455 | 7.86 / 7.14 |

Other local checks of 2026-10-31 (FACT, commands run after the fix pass): `tools/check_task.py
tasks/ab-test-reanalysis` prints "OK ab-test-reanalysis" (runs after a change of the tool at 01:35 MST: its rule,
`tools/check_task.py` lines 18-24, allows only `network_mode = "no-network"` in `[agent]` and refuses every other
network setting; the earlier rule refused the line), as it did on the copy of the package without that one line;
`harbor lint tasks/ab-test-reanalysis --json` prints `[]`; Harbor 0.25.0's `TaskConfig.model_validate` accepts
`task.toml` (agent 3,600 s, no-network; verifier separate, 1,000 s; environment 2 CPUs, 4,096 MB; the label
`difficulty = "hard"`, written before any trial, section 11.4 (g)); `tools/sync_kit.py --check` exits 0;
auth/app_checks.py exits 0 twice with byte-identical output (93 PASS); auth/grader_probes.py prints "40 probes: ALL
AS EXPECTED" with byte-identical output; a lint of the 85 text files of the package and auth/ finds no non-ASCII
byte, no em or en dash and no machine path. Not re-run in the fix pass, because none of their inputs changed:
auth/solution_checks.py ("ALL CHECKS PASS", 2026-10-30) and auth/calibration_study.py.

## 10. Blind read
A second reader (Sonnet 5.5) got only `T/instruction.md`, `T/environment/app/` (plan, docs, PM note, README, shipped
code, current readout, the four data files) and the build's writing rules, and derived the plan's readout of the
visible export with its own pandas code and a stdlib cross-check, without `tests/`, `solution/`, `authoring/` or the
design (2026-10-30, 23:37 to 23:49 MST; the reader's record and scripts are not shipped). Its readout equals the
reference: `compare()` of `grade.py` (KIT_LOCAL mode) on it against `T/tests/expected/visible.json` passes with 0
problems, counts equal, CTR and diff errors 0, CI bound errors 3.3e-16 hw and `srm_p` 1.2e-16 relative (FACT: a check
run of 2026-10-31). Unaided, it also named the cause of the shipped "invalid" (velocity flags tripped by v2's arrows,
1,080 users, all in B) and of the PM's lift (arrow taps and See-all clicks counted as clicks, plus the 100 dogfood
accounts), and found that each single slip flips the decision (`clicked` gives ship, overrides kept give ship,
velocity excluded gives invalid).

What it found open or unclear, and what was done (fix pass of 2026-10-31, before any trial):

| Item | Its rating | Action |
|---|---|---|
| plan section 4 "opened at least one related product": does "See all" (opens a list page) count? Counting it gives clicks 16,837 / 17,183, a fatal exact-count miss | medium | plan reworded to "opened the page of at least one related product"; TRACKING still has to be read to map targets, and no target is named |
| assignment "at the user's first eligible product pageview", yet 2,815 assigned users have no pageview row and only 18,496 of 34,100 have one at `assigned_at` | low | DATA_DICTIONARY: pageviews are logged when the page has loaded; the assigning pageview has no row if the user left before it loaded |
| 181 exact-duplicate module_clicks rows, while only assignment repeats are documented; the velocity flags need them | low | DATA_DICTIONARY: times are to the second; two clicks on the same element in the same second give two identical rows, each an event |
| "other experiments differ in their variants": arm labels or module versions? | low | instruction: "differ in what each arm shows" |
| "six readouts" never named | low | instruction: "the six readouts (`/app/output/result.json` and the five runs)" |
| plan section 3 never names `method`; the override rule needs three documents | low | no change: the intended investigation (H3) |
| plan's "user agent, network or device": no rule reads a device | low | no change: the plan describes a class of rules (limitation 9) |
| events after the end still count: DATA_DICTIONARY lines 10-11 say so, and `clicked` counts them on all six exports; cutting item events at the launch record's End drops clicked pageviews (A / B: visible 1 / 1, h_null 3 / 2, h_pos 1 / 2, h_srm 1 / 3, h_plain 0 / 1, h_neg 2 / 1; an independent review of 2026-10-31) and so fails every readout | low | no change: stated in DATA_DICTIONARY lines 10-11 |
| variance formula, finite-sample factor, z or t not fixed | low | no change: every variant within 1.6e-7 of a bound, the band is 0.00132 |
| degenerate exports (an empty arm, CTR_A 0) unspecified | low | no change: none of the six exports has one (limitation 8) |
| `notes` missing from the plan's key table | low | no change: the instruction asks for it and allows extra keys |
| plan dated before the velocity rule and the See-all link | low | no change: the plan's general wording covers both; that the rule came after the plan is part of H2 |
| text dedupe of assignment repeats versus a dedupe by `user_id` | low | no change: repeats are exact on all six exports (assertion and a check of 2026-10-30) |

## 11. Network, Daytona proof, agent trials and pre-registration

### 11.1 The agent network line
`T/task.toml` sets `[agent] network_mode = "no-network"` and no network line for the verifier (the authors' decision
of 2026-10-30, to ship it in the two revised tasks only).
- FACT (Harbor 0.25.0 source, paths relative to the installed `harbor` package): `environments/base.py` lines 975-997,
  a provider that cannot enforce `no-network` raises "Environment providers must enforce the requested network policy
  or reject the task"; `environments/daytona/environment.py` lines 1581-1585, Daytona applies a phase's policy with
  `update_network_settings` on the running sandbox; `trial/trial.py` lines 286-361 and `trial/network_policy.py`
  lines 40-44, for an installed agent (Claude Code among them) the model service's host is added to a restricted
  agent phase's allowlist; `trial/trial.py` lines 692-697, the agent's web tools are turned off unless the phase is
  public.
- FACT (a network canary of 2026-10-30, 17:43 to 17:47 MST, on the authors' Daytona Tier 1 account, a pilot copy of
  another task with the same line; its job folders are not shipped): Daytona refused Harbor's runtime switch for the
  agent phase on both paths, block-all (the oracle agent) and a domain allowlist (claude-code), each with "Failed to
  update network settings: Network access is restricted and cannot be overridden at the sandbox level."
- INFERENCE (from the source lines above): where the line is enforced, Claude Code can still reach its model service
  and has no web tools; UNTESTED, since the canary was refused before the agent started and the trials of section
  11.3 ran without the line.
- So: the Daytona proof and the agent trials ran a copy of the package without that one line, whose Harbor digest
  differs from the shipped package's; the proven package differs from the shipped one by that line only (section
  11.2). A runner on an environment that cannot enforce the line (Daytona Tier 1 among them; Tier 2 by Daytona's
  documentation, not tried) removes it and reads each trajectory for fetches of the public hidden tests; Daytona's
  Tier 1 and 2 keep GitHub's hosts reachable (the repository README's limitation "The hidden tests are public").

### 11.2 Daytona proof (run rev1)
On the copy without the line, which `tools/proof_matrix.py --without-agent-network-line` makes (the proven package
differs from the shipped one by that line only), 15 variants and 24 trials (23 oracle, 1 nop):

```
python tools/proof_matrix.py ab-test-reanalysis --without-agent-network-line --tag rev1 --n 1 --oracle-k 10 \
  --env daytona --env-file <keys file>
```

(FACT: tools/proof_matrix.py lines 48-55 build the list from the copy's `solution/` folder: canonical (oracle x k),
every `alt*` folder, nop, every attempt under `solution/attempts/` and one force-build; here the 15 rows of
`validation/ab-test-reanalysis/PROOF_RESULTS_rev1.md`. The script reads `tasks/<slug>` under its own repository root
and writes the copy to `jobs/<slug>/package-<tag>/<slug>`, lines 28-45.) `--n 1` runs one trial at a time, a caution:
Harbor stops the agent sandbox before the separate verifier starts (Harbor 0.25.0 `trial/single_step.py` lines
48-51); INFERENCE: so a trial holds at most 4 GiB at a time (Daytona may still count a sandbox that is being
destroyed), and two at once would hold 8 of the 10 GiB of the authors' Daytona account. Every trial's `config.json`
also carries `environment_build_timeout_multiplier` 3.0 (Harbor's wait for the environment build, three-fold).

Result, 2026-10-31, 01:37:54 to 01:51:53 MST, ALL AS EXPECTED (FACT: `PROOF_RESULTS_rev1.md`,
`proof_results_rev1.json` and `run_rev1.log` in `validation/ab-test-reanalysis/`; each trial's `verifier/reward.json`
and `verifier/test-stdout.txt`):
- canonical 10 of 10 at 1.0; alt_recount, alt_time and force-build 1.0; nop and the ten attempts 0.0, no exception.
- Each 0-expected trial exited 0 on all five hidden runs (`<set>_run_rc` 0, no timeout) and failed the same sets with
  the same problem counts as the local matrix's image mode (section 9; auth/local_results.json).
- All 24 verifier logs hold `[test.sh] lock ok`, "SHA256SUMS: 26 files verified", "network isolation: ON", "setid
  files left: 0" and "killed 0 runner processes", and show the verifier's cgroup at 1 CPU and 2,048 MiB.
- The slowest hidden run took 2.731 s (alt_time, h_null) against the 120 s cap; the verifier phases took 14.9 to 44.2
  s against 1,000 s.
- Harbor 0.25.0 content hashes (its `Packager`; 75 files, the same file list): the shipped package
  `sha256:22e61147a38e16acd0ac2eec4e34a45ef814b205ee0cc93bd51fd69aadf2008c`, the proof's copy
  `sha256:0fc5d05c8334f99bb7ef36ca1929d1f9330f0d74799be756ad8c8ff2ae59837c` (the digest in every rev1 job's
  `lock.json`). The shipped hash was computed before the proof and again, with the same value, after a tool-state
  folder `.claude-flow/` that had appeared in `environment/app` at 01:55 MST, after the copy was made, was deleted at
  about 02:15 MST. `diff -rq` of the package and the copy lists `task.toml` only, and the `task.toml` diff is the
  `network_mode` line (run 2026-10-31, 13:29 MST); no entry under `environment/`, `tests/` or `solution/` starts with
  a dot.

### 11.3 Agent trials
Settings decided by the authors on 2026-10-30 (not changed since): Harbor's `claude-code` agent with the model
`claude-opus-5-5`, web search off, a spend cap of 20 dollars per trial (`max_budget_usd`), about three trials, the
first trial's cost measured before the others; agent sandbox 2 vCPU / 4 GiB and the separate 1 vCPU / 2 GiB verifier,
one trial at a time. The model key stays outside the repository (it is passed to Harbor through its process
environment), never in a task file or a trace; every trace is scanned for it before shipping. Proof rev1 verified
the verifier's resources (1 CPU and 2,048 MiB in 24 of 24 logs), and the three trials' verifier logs show the same.

The trials ran the copy without the agent network line (section 11.2), so the agent phase had the sandbox's own network
(Harbor's default, public). Harbor passed Claude Code `--disallowedTools WebSearch,WebFetch` (each job's `job.log`,
outside this repository, and each shipped trial's `trial.log`) because the trials set `disable_web_search` (Harbor
0.25.0 `agents/installed/claude_code.py` lines 90-95); Harbor's own switch turns the web tools off only for a phase that
is not public (`trial/trial.py` lines 692-697). Bash commands could still reach what the sandbox's network allows: on
the authors' Daytona Tier 1 account, Daytona's essential services, GitHub's hosts among them (Daytona's network-limits
documentation).

Results (FACT: each trial's `result.json`, `agent/trajectory.json`, `agent/claude-code.txt` and `verifier/reward.json`;
Claude Code 2.1.316 with `claude-opus-5-5`, `max_budget_usd` 20, `disable_web_search` true; Mac clock, MST,
2026-10-31; agent time from `agent_execution`; cost is Claude Code's `total_cost_usd`):

| Trial | Job | Ran | Reward | Readouts passed | Agent time | Tool calls | Cost |
|---|---|---|---|---|---|---|---|
| `ab-test-reanalysis__3nb9x28` | `ab-test-reanalysis-claudecode-opus55-cc1` | 02:22:27 to 02:24:47 | 1.0 | 6 of 6 | 63 s | 6 (Bash) | 0.266 dollars |
| `ab-test-reanalysis__SpwbpTd` | `ab-test-reanalysis-claudecode-opus55-cc2` | 02:27:16 to 02:29:31 | 1.0 | 6 of 6 | 57 s | 6 (Bash) | 0.221 dollars |
| `ab-test-reanalysis__NjrFLJq` | `ab-test-reanalysis-claudecode-opus55-cc2` | 02:29:31 to 02:32:19 | 1.0 | 6 of 6 | 89 s | 10 (Bash) | 0.326 dollars |

Together 0.812 dollars, each trial far under its 20-dollar cap. Each trial read the plan, the PM note, the docs, the
README, the code and the data in its first three commands, rewrote `load.py`, `filters.py` and `report.py` in its
fourth, and ran the command on `/app/data`; `__SpwbpTd` and `__NjrFLJq` also ran it on a small export of their own in
`/tmp/t1`. No tool call holds a network command (curl, wget, pip install, git clone, an http or https URL, a GitHub
host) or a path under `/tests`, `/solution` or `/logs/verifier`, and the trajectories and the Claude Code logs as a
whole hold none of these patterns (a scan of 2026-10-31); the run's key scan found the model key in no file of the
two jobs or their logs. The raw Claude Code session files (`agent/sessions/`, which hold Claude Code's own requests,
its system prompt among them) are not shipped.

### 11.4 Pre-registration
Items (a) to (f) were written on 2026-10-31, before any agent trial of the revised task; (g) and the clarification of
(b) were added after the three trials.
(a) The design is frozen as approved on 2026-10-30, with its three grafts and their realism reasons (section 1.2:
    the plan's exclusion sentence, the dogfood accounts with the masked-imbalance set h_srm, the arm-swapped and
    arrow-free hidden sets). Nothing is added to the task because of a trial result (G29).
(b) A failed trial is a task defect when its trajectory shows that the agent read the relevant sentence and took a
    reading that the task's text allows: then the wording is fixed, the package is proved again, and the trial is
    reported as void. It is a capability failure when the agent never opened the evidence, contradicted a stated
    sentence, or stopped without checking. An infrastructure failure (sandbox, provider, model service) is re-run and
    reported.
    Clarification of 2026-10-31, written after the three trials (all three passed, so (b) classified no trial; no new
    rule): two instances of "contradicted a stated sentence" are cutting module events at the launch record's End,
    against DATA_DICTIONARY lines 10-11, and relying on a package installed outside /app, against the instruction's
    package sentence.
(c) If 2 or 3 of the 3 trials pass, the revision ships with that count stated and no trap is added.
(d) (b) is judged against the text as shipped at the time of the trial: the four wording changes of the fix pass
    (section 3, item 15) were made before the first trial.
(e) Every trajectory is read for fetches of the public hidden tests (GitHub hosts) and scanned for the model key; a
    trial that fetched the tests is excluded and reported.
(f) The first version's agent trials (Harbor's `terminus-2` agent with `openai/gpt-oss-120b`, 2026-10-30, 1 of 3
    passed) ran on the first version and are not counted for the revision.
(g) Outcome, recorded 2026-10-31 after the three trials: 3 of 3 passed (section 11.3), each with all six readouts, in
    57 to 89 s of agent time with 6 to 10 commands, for 0.221 to 0.326 dollars. Rule (c) applies: the revision ships
    with that count stated, and no trap is added. The approved design of 2026-10-30 (not shipped; section 3) estimated
    20% to 45% pass (INFERENCE, not measured); the measured count is above that estimate. Before the trials, the blind
    reader had reached the reference from /app alone in about 12 minutes (section 10), and an independent review of
    2026-10-31, in a blind reading written before it opened the tests or the solutions, derived the three fixes and
    the visible decision from the agent's files; with the tests open, its own code reproduced all six expected
    readouts. Three trials show that this agent solves the task, not its pass rate: 3 of 3 has a Wilson 95% interval
    of 0.44 to 1.00. The first version had 1 of 3 with Harbor's `terminus-2` agent and `openai/gpt-oss-120b` ((f)).
    How other agents, the external reviewer's among them, fare on the revision is UNVERIFIED. `task.toml` still
    carries the label `difficulty = "hard"`, written before any trial; an edit to `task.toml` would change the proven
    package's digest.

## 12. Gate record
```
Gate record: ab-test-reanalysis, the revision as built (2026-10-31; local, the Daytona proof rev1 and three Claude Code trials)
Applies to: task ab-test-reanalysis
G1  PASS - plan, docs, code, the visible and five hidden exports, references and pinned images are in the package; neither the agent's work nor grading needs a network (the images install pinned wheels at build time, as in every task)
G2  PASS - the PM gets the plan's no_ship before a launch that two wrong readings would have shipped or blocked, and a pipeline that is right for the next experiments
G3  PASS - a plan agreed before launch, a data dictionary, a tracking spec, bot rules, a launch record, a PM memo, a README, code and a four-file export with retries, mixed offsets, pre-assignment pageviews, crawlers, fraud bots and dogfood accounts
G4  PASS - grade.py compares the six readouts by script with stated tolerances; compare() is the first version's, unchanged; 40 grader probes as expected; on Daytona (rev1) every attempt failed the same sets with the same problem counts as locally
G5  PASS - experiment validity (the instrumentation of new UI, an exclusion made after treatment, hand assignment) differs from the other four tasks; the accepted time route resembles the churn task's point-in-time theme only as an alternative
G6  PASS - every expected value is recomputed from the files by two independent references (stdlib rule route, pandas time route; largest difference 3.5e-18) and by the blind reader from /app alone
G7  PASS - re-analysing a disputed readout before a launch is routine analyst work
G8  PASS (local) - each graded rule is a plan sentence plus a doc line plus the data; limits, packages, tolerances and the six readouts are in the instruction; the blind reader reached the reference from /app alone, and the fix pass closed the readings it found open
G9  PASS - new clickable UI that a generic click flag counts, a fraud rule that reads those events and dogfood accounts on an allowlist are familiar to analysts; the docs were made true to the data (assigning pageviews, identical event rows)
G10 PASS - a corrected readout and a pipeline that gives the plan's readout on any export of the layout
G11 PASS (local) - only readout values are compared; canonical, alt_time (bootstrap) and alt_recount (CR1, stdlib) differ in route, code and interval method and score 1
G12 PASS - ten attempts and five probes score 0, each failing where the design says (the ten attempts also on Daytona, rev1); hard-coding, a one-off script and an instance patch fail the hidden runs; residual: a one-rho design-effect factor on the pageview interval passes the CI part when every count is right (limitation 6)
G13 PASS - the three valid routes give identical counts (assertion (e)); the plan's interval methods stay within 0.1111 hw of the reference, half the band or less; alt_time and alt_recount 1.0 on Daytona (rev1)
G14 PASS - the work is reading the plan, the docs, the code and the data against each other and judging what each number measures; three defects, each needed (every two-of-three fix scores 0); the plan states H3's rule, but neither it nor the instruction names the hand-assigned accounts (the `method` column, the launch record's log and the gap between PM_NOTE's 17,165 users of B and the 17,065 hash users of B in the data show them); measured: 3 of 3 Claude Code trials passed (section 11.4 (g))
G15 PASS (local) - one reading per rule, confirmed by the blind read; exact counts make a misreading fatal, so every open reading it found was closed before any trial; tolerances and the 120 s cap are stated (slowest valid run 2.155 s on the Mac, 2.731 s on Daytona)
G16 PASS - fixed seeds and gzip mtime 0; generation byte-identical twice and equal to the package; pins and base digest unchanged; references must agree or generation stops; deterministic grader; canonical 10 of 10 and the clean rebuild (force-build) 1.0 on Daytona (rev1)
G17 PASS - answers and hidden inputs only in tests/, which only the separate verifier image holds; environment/Dockerfile copies app/ only and nothing in /app refers to tests/; on Daytona the verifier checked its 26 files in every trial (rev1) and no Claude Code trial's command touched /tests; public after the push (limitation 2)
G18 PASS - Harbor's TaskConfig validates task.toml and harbor lint is clean; check_task.py passes the package and the copy without the line
G19 PASS - its own instruction, environment, verifier (kit in sync: sync_kit.py --check) and solutions; nothing depends on another task
G20 PASS - the row is in the repository README (README.md, the ab-test-reanalysis row of the table "The tasks"); its validation cell gives run rev1 and the three Claude Code trials as sections 11.2 and 11.3 record them
G21 PASS - setup, the network line and the limitations are written here (sections 11 and 13) and in the repository README (this task's row, "The agent network line" under Setup, and the task's entries under "Known limitations")
G22 PASS - canonical 1.0 in both interpreter modes locally and 10 of 10 on Daytona (rev1)
G23 PASS - nop (the shipped "invalid") 0.0, failing all six, locally and on Daytona (rev1)
G24 PASS - ten attempts 0.0 with solve.sh exit 0 and no crash, each a realistic analyst mistake; on Daytona (rev1) each exited 0 on all five hidden runs and failed the sets of section 9
G25 PASS - alt_time and alt_recount 1.0 in both modes locally and on Daytona (rev1)
G26 PASS - prompt, environment and verifier are readable; the proof traces of rev1 (validation/ab-test-reanalysis/traces/<variant>/), the redacted traces of the three Claude Code trials (validation/ab-test-reanalysis/traces/agent-claude-code/<trial>/) and the first version's evidence (validation/ab-test-reanalysis/first-version/) are in the repository
G27 PASS (condition) - no key or machine of the authors is needed; where the agent network line cannot be enforced Harbor rejects the trial, and the runner removes the line (section 11.1)
G28 PASS (design) - the work is valuable, the score checks the plan's readout, and a failure shows a convenience field or a filter trusted by its name, or a missed hand assignment; pre-registration (b) separates task defects; measured: 3 of 3 Claude Code trials passed, so no failure was there to classify (11.4 (g))
G29 PASS - three faults from one launch, no distractor, nothing added for difficulty; the pre-registration forbids adding a trap after a trial, and none was added after the 3 of 3 (11.4 (g))
G30 PASS (plan) - delivered by the revision commit and push on the authors' word; the reviewer is invited already
Result: PASS; no FAIL. The Daytona proof rev1 (2026-10-31) covers G4, G12, G13, G16, G17 and G22 to G25. G30 is completed by the revision commit and its push.
```

## 13. README row, limitations, open issues
README row (the basis of the row in the repository README): capability = data analysis and experiment validity (auditing
an A/B readout against its plan, the data platform's documentation and the data); objective = re-analyse a disputed
readout before a launch, fix the pipeline so that it gives the plan's readout on any export of the layout, and
regenerate the readout; success check = the agent's command on five hidden exports plus the visible readout: counts
exact, CTR and diff within 1e-9, SRM p within 1% relative, flag and decision exact, CI bounds within 0.25 half-widths of
a delta-method reference (bootstrap and CR1 accepted); validation = the local matrix of section 9; the Daytona proof
rev1 (oracle 10 of 10 = 1.0; alt_time and alt_recount 1.0; clean rebuild 1.0; nop 0.0; ten attempts 0.0); three Claude
Code trials with `claude-opus-5-5`, web search off, 3 of 3 passed (run on the copy without the agent network line, so
with the sandbox's network; section 11.3).

Limitations:
1. Synthetic data: the lifts (+10%, +13%, -10%), the rates and the velocity threshold that only the carousel's arrows
   let humans reach are chosen, not observed. Two construction choices show in the data: the 100 dogfood accounts make
   no arrow taps (on visible: 1,466 item, 14 link and 0 nav events; section 3 item 4), and 12,789 of 34,100 assigned
   users (37.5%) have pageviews but none at `assigned_at`, which DATA_DICTIONARY explains as leaving before the page
   loaded (counts: an independent review of 2026-10-31).
2. The hidden tests are public once this revision is pushed: the hidden inputs and expected readouts are in `T/tests/`
   of a public repository, so an agent with network access can fetch them; on Daytona Tier 1 and 2 GitHub's hosts
   stay reachable (the repository README's limitation "The hidden tests are public").
3. The agent network line (section 11.1): Daytona Tier 1 refuses it, so the proven package differs from the shipped
   one by that line only; on an environment that cannot enforce it (Daytona Tier 1 among them; Tier 2 by Daytona's
   documentation, not tried) Harbor rejects the trial, so a runner there removes the line and reads each trajectory
   for fetches of the public hidden tests.
   Where the line is enforced, Harbor adds an installed agent's model host to the agent phase's allowlist and turns
   off the agent's web tools (Harbor 0.25.0 source, section 11.1); no run has used that allowlist yet.
4. Three trials only: 3 of 3 passed (section 11.4 (g)). They show that this agent can solve the task, not its pass
   rate (3 of 3 has a Wilson 95% interval of 0.44 to 1.00). They ran with the sandbox's network (section 11.3); how
   other agents, the external reviewer's among them, fare is UNVERIFIED.
5. Thin margins, to be re-checked after any data change (auth/generation_report.out.md, auth/calibration_study.out.md):
   visible keep_overrides ships with its lower bound at +0.27 of its half-widths (the soft condition); h_srm
   keep_overrides at +0.38 against its 0.35 floor; h_neg's assertion (m) miss 0.0448 against 0.03; calibration gate 1
   0.1111 against 0.125, a sample maximum (the band itself is at least 7.4 SD away).
6. A design-effect shortcut is not closed: the pageview-level interval times 1 + rho (m_w - 1) with one rho between
   0.235 and 0.310 passes the CI part of all six readouts, and so does c K^g with c fitted on visible for g from 0.82
   to 1.99 (section 5). The first version closed this family with a twin hidden set; the revision drops it with the
   multiplier attempts, because the shipped stats.py is already the plan's delta method and the interval is not one
   of the hidden issues. Such a rule still needs every count exact; a single constant does not pass (0.2682).
7. alt_recount's extra exclusion (the velocity rule recounted on item events) reads behaviour, which plan section 3
   rules out; it passes because it flags the same users (assertion (e)). An export where such a recount flags a
   non-crawler would separate it; none of the six does.
8. Degenerate exports are not specified: no export has an empty arm or zero clicks (smallest arm 14,155 users,
   smallest clicks 9,936; T/tests/expected/*.json); the shipped report.py would divide by zero on an empty arm, and
   the instruction states upper limits only.
9. Plan section 3 describes client-identity rules as reading the "user agent, network or device"; no rule of
   BOT_SCREENING reads a device. Harmless: each rule's inputs are documented.
10. Verified on Daytona by proof rev1: each of the 24 verifier logs shows 1 CPU and 2,048 MiB, `lock ok`,
    "SHA256SUMS: 26 files verified" and "network isolation: ON", with the `.csv.gz` inputs (section 11.2). Other
    Harbor backends, a local Docker engine among them, were not run.
11. Kit rules the instruction does not spell out (shared by all five tasks): the graded copy loses `conftest.py`,
    `sitecustomize` and `usercustomize`, `*.pth`, `*.pyc` and `__pycache__`; a copy over 2 GiB or 200,000 entries
    scores 0; runs get `OMP_NUM_THREADS=1`, `PYTHONHASHSEED=0`, 1 GiB per written file and 512 processes plus
    threads (FACT: T/tests/kit.py lines 46-56 and 458-462). Harmless for any sane solution.
12. The instruction says `python -m`; the grader runs `python3 -m`, the same interpreter in the image. Both images
    need PyPI at build time (exact pins).
13. The launch record gives a salt and the plan a hash rule, but no hash function. The generator draws the arms at
    random (auth/gen_data.py line 170), so no recipe reproduces them: sha256, md5 and sha1 variants agree with the
    variant on 0.496 to 0.506 of hash users (an independent review of 2026-10-31). Grading is unaffected.
14. Two pageview rows of one user can share an instant: such pairs with distinct `pageview_id` number 7 on visible, 6
    on h_null, h_pos and h_srm, 8 on h_plain and 5 on h_neg, and 1 to 5 of them per export are written with the same
    text (an independent review of 2026-10-31). "One row per product pageview" and "unique per row" (DATA_DICTIONARY
    lines 38 and 44) settle that both rows count; a dedupe on user and time misses the exact `pageviews` count.
15. The agent sandbox has 2 vCPU and 4,096 MB (task.toml lines 25-27), the graded runs 1 vCPU and 2,048 MB (lines
    21-23; every rev1 verifier log); the instruction says to plan for one CPU and 2 GiB. A bootstrap held in memory
    can pass in the agent sandbox and be killed in grading: at B = 5,000, about 1.4 GiB peak measured with one arm's
    index matrix at a time, and about 2.1 GiB with both arms' matrices held (extrapolated from runs at 500 to 2,000
    resamples; an independent review of 2026-10-31). `os.cpu_count()` is 48 in the verifier
    (`res_os_cpu_count=48`), so a pool sized by it starts 48 workers there.

Open issues (outside this task's files):
1. The pre-revision authoring files carry a status banner; removing them with `git rm` is the alternative.

## 14. What the revision changed
The first version (commits `79286dc` and `495c9f5`) shipped a plan that stated every rule and a pipeline with four
defects (bots filtered from arm B only, a pageview-level interval, no SRM check, a p-value decision), an export of
three plain CSV files, one of them `users.csv` (the five hidden sets h_null, h_pos, h_srm, h_bots and h_twin gzipped
under `tests/` and unpacked by the grader), an 1,800 s agent timeout and the difficulty "easy-medium" (FACT: `git show
495c9f5:tasks/ab-test-reanalysis/task.toml` and that version's record). The review of 2026-10-30 asked for tasks that
current agents cannot reliably complete, with deeper investigation and practitioner judgment, and named this task
among those to revise. The revision replaces the four stated defects with three faults of one launch, two of which
need judgment and one investigation; the export is now four gzipped files (`assignments`, `bot_flags`, `pageviews`,
`module_clicks`), with no `users.csv`; the hidden sets move the carousel to arm A or remove it, hide a real imbalance
behind QA accounts, and add a negative effect; h_bots, h_twin and the multiplier attempts are dropped (the shipped
interval is now correct); the agent gets 3,600 s, 2 vCPUs and 4 GiB, the verifier its own 1 vCPU and 2 GiB, and the
agent phase no network.

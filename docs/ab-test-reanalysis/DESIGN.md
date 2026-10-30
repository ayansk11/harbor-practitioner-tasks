# ab-test-reanalysis: design and build record

**What this file is.** The authoring notes for the task [`tasks/ab-test-reanalysis/`](../../tasks/ab-test-reanalysis/): the design (sections 1 to 7),
the deviations from the original design (section 3), the local checks (sections 8 and 9), the quality-gate record
against [docs/QUALITY_GATE.md](../QUALITY_GATE.md) (section 10), the Daytona proof results and the known limitations
(section 11), and the review history (sections 12 to 16).

Last updated: 2026-10-29 (Mac clock, MST): wording edited for outside readers, three overstatements corrected
(sections 5, 8 and 12) and the gate record's (run) items now cite run full2 (section 10); no measurement or verdict
changed. Before that, also 2026-10-29, after the section-16 pass (rules that use the clicks measured through the
grader; a user-level click-dispersion estimate with no constant scores 1 and is accepted, G12 PASS after an explicit
override question, ruled no override; wording fixed; no package file changed). Section 15 (h_twin = h_null's exact
users and pageview rows with only the clicks redrawn) is unchanged.
Labels: FACT (sourced or measured here), INFERENCE (reasoned; basis named), UNVERIFIED. `submission/` is the repository
root; "auth/x" = `submission/authoring/ab-test-reanalysis/x`. All data is synthetic (made by auth/gen_data.py); nothing
comes from a real product.

## 1. What the task is
An analyst's readout pipeline (`/app/abtest`) says variant B lifts click-through by 4.1% with p = 0.0003 (FACT:
`environment/app/output/result.json`: `rel_lift` 0.04107, `p_value` 0.000301, `decision` "ship"). The PM wants to ship
tomorrow but noticed the arms differ in size. The analysis plan `/app/EXPERIMENT.md` says what the readout must be. The
shipped code breaks the plan in four places:
1. `filters.py` removes flagged bots from arm B only (with a plausible incident comment). Bots have many pageviews and
   almost no clicks, so A's CTR is pulled down: this alone makes the "win" and the size mismatch (A 20,042 users vs
   B 19,518 in the shipped readout).
2. `stats.py` runs a two-proportion z-test with each pageview as a trial. The plan randomizes users, so the interval
   must be user-level (delta method, user bootstrap with at least 2,000 resamples, or CR1 by user).
3. There is no SRM check (plan section 6), and
4. the decision is "p < 0.05 and diff > 0", not the plan's rule (SRM flag first, then CI lower bound > 0).
The loader already follows the five definitions the plan states (who counts in `n_users`, exact duplicate assignment
rows count once, every pageview row counts even when two are identical, pageviews strictly before `assigned_at`
dropped, `Z` and `+hh:mm` timestamps compared as instants). The correct
readout of the visible data is `no_ship`: diff -0.00040, CI [-0.00466, +0.00386] (FACT: `tests/expected/visible.json`).
The command must also be right on any export of this layout; the grader runs it on five hidden experiments.

## 2. File map
Package `submission/tasks/ab-test-reanalysis/` (32,035,105 bytes = 32.0 MB, 58 files after the section-15 pass; FACT,
`stat` sum and `find -type f | wc -l`, measured after the last package edit; unchanged by the section-16 pass, whose
SHA-256 of all 58 files before and after are identical, section 16. Earlier: 32,060,388 bytes after the section-14
pass; 28.9 MB and 52 files with four hidden sets; 31,646,365 bytes and 57 files with h_lowicc, as measured by the
second review, which corrects the 31,646,320 written here before):

| Path | What it is |
|---|---|
| `task.toml` | schema 1.4, the shared `/app` artifact, `[verifier] environment_mode = "separate"`, agent 1800 s, verifier 950 s, 1 vCPU, 2 GiB |
| `instruction.md` | the request; states the command, the five hidden folders and the six readouts checked, every tolerance (counts exact, 1e-9, 1%, band 0.25), 120 s cap, "plan for one CPU and 2 GiB", the grading machine's package set, unprivileged user, no network, size limits, the copy of /app, the shared closing sentence |
| `environment/Dockerfile` | pinned base digest; numpy 2.5.4, pandas 3.1.0, scipy 1.18.1, python-dateutil 3.0.0, six 1.17.0, tzdata 2026.6; `WORKDIR /app`; `COPY app/ /app/` |
| `environment/app/abtest/` | `load.py` (correct), `filters.py` (defect 1), `stats.py` (defect 2), `report.py` (defects 3, 4), `__init__.py` |
| `environment/app/EXPERIMENT.md` | the analysis plan: unit, population rules, metric, three accepted CI methods, SRM test, decision rule, file columns, output schema |
| `environment/app/PM_NOTE.md`, `README.md` | the PM's question; layout and the command |
| `environment/app/data/` | the visible export: 40,000 users (40,394 assignment rows), 408,223 pageview rows, 15.6 MB (dropped at grading, by design) |
| `environment/app/output/result.json` | the shipped wrong readout, made by the shipped code |
| `tests/Dockerfile` | same base and pins; `COPY . /tests/`, uid 1001 `runner`, `/tests` 0700 |
| `tests/test.sh`, `tests/kit.py` | shared kit, copied by `submission/tools/sync_kit.py` |
| `tests/grade.py` | the grader (section 6); standard library only; also logs the verifier's CPU and memory limits (evidence only) |
| `tests/hidden/<set>/*.csv.gz` | five hidden experiments (h_null, h_pos, h_srm, h_bots, h_twin), gzip with mtime 0; h_twin's `assignments` and `users` files are h_null's, byte for byte, and its `pageviews` differ only in `clicked` (section 15) |
| `tests/expected/<set>.json` | reference readouts for the six sets (auth/ref_a.py) |
| `tests/SHA256SUMS` | 21 files (15 hidden inputs, 6 expected files); `grade.py` checks them first; two hash values appear twice (h_null's and h_twin's `assignments` and `users`): the files are identical on purpose, not a copy error |
| `solution/solve.sh` | `SOLUTION` = canonical (default), `alt`, `alt_cr1`, `nop`, or one of nine attempts |
| `solution/canonical/` | `filters.py`, `stats.py` (delta method, SRM), `report.py` (per-user sums, decision rule) |
| `solution/alt/` | `filters.py` (join-based bot filter), `stats.py` (user bootstrap, 5,000 resamples, seed 20260914), `report.py` (numpy bincount sums) |
| `solution/alt_cr1/stats.py` | CR1 cluster-robust interval from the pageview-level regression (with the canonical report) |
| `solution/attempts/` | `hardcode_no_ship`, `no_srm_gate`, `mean_of_ratios` (patch scripts), `fix_bots_only`, `constant_inflation`, `icc_tuned`, `kish_tuned` (stats.py), `fix_visible_result_only` (one-off script); `fix_ci_only` is a branch of `solve.sh`, and its folder holds only a README so that `tools/proof_matrix.py` (which lists the entries of `attempts/`) runs it |

Authoring scripts `submission/authoring/ab-test-reanalysis/` (outside the package):

| Script | What it does | Output |
|---|---|---|
| `gen_data.py` | all six sets (seed search, section 4; h_twin as h_null's twin, section 15), expected values, SHA256SUMS, the shipped readout | `generation_report.out.md` |
| `twin_identity.py` | proves h_twin = h_null except the clicks (text and per-user counts) and does the half-width arithmetic (section 15); stdlib loader | `twin_identity.out.md` |
| `ref_a.py` | reference A: csv + `datetime.fromisoformat`, dicts, delta method, stdlib only | `tests/expected/*.json` |
| `ref_b.py` | reference B: own pandas loader; delta, CR1 (2x2 sandwich), user bootstrap | used by the calibration |
| `calibration_study.py` | the CI band calibration, the ICC sweep, the pageview-only sweep and the twin-pair check (section 5); reads the committed files only (`--reuse --band` re-renders) | `calibration_study.out.md`, `calibration.json` |
| `local_check.py` | the local proof matrix (section 9) | `local_results.json` |
| `grader_probes.py` | format and tamper probes on `compare()` | `grader_probes.out.md` |
| `click_rule_probes.py` | rules that use the clicks (click-dispersion estimates, ANOVA ICC, arm-level click aggregates) by a fast evaluator and through the real grader, and the section-15 bound for other variance bases (section 16); own per-user extraction with the canonical code; run dirs in `.localruns/probes/` (git-ignored) | `click_rule_probes.out.md` |
| `calibration_first_run.out.md` | dated record of the first calibration, which failed and led to the data change | |
| `calibration_before_icc_fix.out.md` | dated record of the calibration of the four-hidden-set data (superseded by section 13) | |
| `calibration_before_twin.out.md` | dated record of the calibration with h_lowicc (section 13; superseded by section 14) | |
| `calibration_before_exact_twin.out.md` | dated record of the calibration with the section-14 h_twin (a new draw of h_null's generator; superseded by section 15) | |

## 3. Deviations from the original design (with reasons)
"The original design" is our written task proposal from before the build (not shipped); quoted phrases below are its
words.
1. **Design effects 5.2 to 23.1 (6.1 to 23.1 with the four original hidden sets; h_twin adds 5.24, 5.26 before
   section 15), not "about 3, 5 and 8".** The first data (DE 3.1 to 9.9) failed the design's own rule:
   the band came out at 0.26 and `fix_bots_only` missed by only 0.434 on the DE-3.1 set (needs 0.52). The design says
   "change the data, not the band", so the low-DE set was raised to 6.05 and the high one to 23.05 (section 5).
2. **Band 0.25, not the 10% placeholder.** The measured spread is set by bootstrap noise at the plan's minimum 2,000
   resamples (about 0.03 half-widths SD per bound, worst of 200 seeds 0.104). The rule gives 0.21; 0.25 is used to also
   cover the worst valid error seen in the first run (0.125) and still meets both separation checks (section 5).
3. **Margin 0.5 half-widths, not 0.35:** stricter; the smallest realised margin is 0.806 (h_srm).
4. **Hidden sets gzip-compressed in `tests/`** (34,000 to 40,000 users each); the grader unpacks them, so the command
   sees plain CSV of the same layout. Reason: the six sets as plain CSV would be about 81 MB (FACT: visible 15.6 MB,
   hidden 12.6 to 13.7 MB each by `gzip -dc | wc -c`, section-14 pass); the package must stay near 30 MB.
5. **Per-run cap 120 s, not 3 x slowest valid (3 x 2.418 s = 7.3 s).** A correct but unoptimised bootstrap (pandas
   resampling in a loop) must not fail on time, and the Daytona CPU speed is unmeasured. The cap is stated in the
   instruction. `verifier.timeout_sec` = 5 x 120 + 10.2 s measured grading (the slowest pass, alt, section 8) = 610.2 s,
   + 50% = 915.3, rounded up to 950 s (it was 750 s with four hidden sets; the design's "1-2 min" is the typical
   grading time, about 7 to 10 s here).
6. **Extra solution and attempts:** `alt_cr1` (third valid method); `constant_inflation` (proves "no constant multiple
   of the pageview CI fits" by a run, as the design claims) and `fix_ci_only` (a plausible half-fix).
7. **Definitions made explicit for G8/G15:** decision labels `ship` / `no_ship` / `invalid`; "strictly before
   `assigned_at` dropped, equal kept" (60% of users have a first pageview exactly at `assigned_at`, so the rule bites);
   no conflicting assignment rows; every assigned user has one `users.csv` row; Pearson chi-square without continuity
   correction; output keys and types (EXPERIMENT.md section 9). Added after the first review (section 12): every
   pageview row counts, identical or same-instant rows included (EXPERIMENT.md section 4), and the grading machine has
   only the packages of the agent's starting image (instruction).
8. **Story numbers:** the request says "4% with p = 0.0003"; the shipped readout gives 4.11% and p = 0.000301 and the
   instruction quotes "4.1% ... p = 0.0003".
9. **Image size about 350 MB:** not measured (no Docker on the Mac); UNVERIFIED.
10. **A fifth hidden set, `h_twin` (not in the original design).** History: section 13 added `h_lowicc` because,
    with four hidden sets, the pageview CI times sqrt(1 + rho (m_w - 1)) with one guessed rho passed; section 14
    replaced h_lowicc by h_twin because multipliers built from the pageview counts alone (Kish's K to
    a power, c CV^2, tail shares) still passed; section 15 made h_twin an exact copy of h_null's
    users and pageview rows, because the section-14 h_twin (a new draw of h_null's generator) matched h_null only in
    distribution and multi-parameter tail-moment rules tuned on the hidden readouts still passed. h_twin now has
    h_null's users, arm labels, bot flags, assigned_at, repeated rows, pageview rows and timestamp text, and only the
    clicks are redrawn from its own seed (within-user click correlation 0.09 instead of 0.42, a true lift of 9%); its
    design effect is 5.24 against h_null's 23.05. Cost: the package is 32.0 MB, 2.0 MB over our own size target of
    "about 30 MB" (set in our build notes, not shipped; 28.9 MB with four hidden sets, 31.6 MB with h_lowicc, 32.1 MB
    with the section-14 h_twin); one more 120 s run, so
    the verifier timeout went from 750 s to 950 s (item 5; unchanged by sections 14 and 15). The four original hidden
    sets, the visible set and their expected files are byte-identical to before (sections 13, 14 and 15).

## 4. Data
FACT (auth/gen_data.py, auth/generation_report.out.md). Per user: assigned A/B (probability 0.5; 0.515 for B in h_srm),
bot flag, a click propensity from a Beta distribution (mean = set CTR, intra-user correlation rho), post-assignment
pageviews from a floored lognormal (sigma sets the tail, cap 600, 8% zero), B multiplies the propensity by (1 + lift).
h_twin is the exception (section 15): it is h_null's kept realisation with only the click propensities and clicks
redrawn.
Bots get lognormal (mean 20 to 40) pageviews and click with probability 0.003. 20 to 25% of users also have 1+ pageviews
1 minute to 3 days before assignment; about 1 to 1.6% of users have their assignment row repeated exactly (measured
0.97% h_srm to 1.61% h_bots; h_null and h_twin 1.16%, the same rows; generator `dup` 0.010 or 0.015); each timestamp is written with
`Z` or an offset (visible: 66% `Z`; h_bots: 34% `Z` and offsets from -10:00 to +13:00). Seeds are tried in order from a
base until the realised set meets the stated conditions (DE in range; decision bound at least 0.5 half-widths from 0;
SRM p at least 0.05, or in (1e-11, 1e-5) for h_srm; visible: shipped-code lift 3.7% to 4.4% and p 2e-4 to 3.49e-4;
h_twin: also its guaranteed miss for pageview-only multipliers against h_null at least 0.33 half-widths, section 15).

| set | role | seed (tries) | users A/B after bots | counted pageviews | diff | half-width | lower/hw | DE | SRM p | decision |
|---|---|---|---|---|---|---|---|---|---|---|
| visible | null | 1083 (84) | 19,612 / 19,518 | 375,697 | -0.00040 | 0.00426 | -1.09 | 6.08 | 0.635 | no_ship |
| h_null | null | 2006 (7) | 18,648 / 18,812 | 297,712 | -0.00338 | 0.01083 | -1.31 | 23.05 | 0.397 | no_ship |
| h_pos | true lift | 3000 (1) | 19,705 / 19,705 | 308,241 | +0.01212 | 0.00581 | +1.09 | 6.05 | 1 | ship |
| h_srm | lift + SRM | 4002 (3) | 19,136 / 20,287 | 309,518 | +0.01015 | 0.00562 | +0.81 | 6.81 | 6.75e-9 | invalid |
| h_bots | null, 6% bots | 5000 (1) | 16,068 / 15,921 | 249,565 | -0.00081 | 0.00628 | -1.13 | 7.85 | 0.411 | no_ship |
| h_twin | true lift; h_null's users and pageview rows, clicks redrawn with low intra-user correlation | 7018 (19) | 18,648 / 18,812 | 297,712 | +0.01334 | 0.00527 | +1.53 | 5.24 | 0.397 | ship |

h_twin (added in section 14, replacing section 13's h_lowicc; rebuilt in section 15): `gen_data.simulate_twin` re-makes
h_null's kept realisation (seed 2006) and redraws only the clicks from h_twin's own seed (base 7000, kept 7018 after 19
tries): a new click propensity per user from the Beta with mean 0.110 and rho 0.09 (h_null 0.42), B times 1.09, bots
0.003. The text is written from h_null's own generator stream, so `assignments.csv` and `users.csv` are
byte-identical to h_null's (the same SHA-256 values in `SHA256SUMS`, on purpose) and `pageviews.csv` has the same
322,363 rows in the same order with the same `user_id` and `ts` text; only `clicked` differs, on 62,934 rows (FACT,
auth/twin_identity.out.md). So the counted users (18,648 / 18,812), their arms and every user's counted pageviews are
h_null's exactly. Seed conditions: DE 5.2 to 5.8, lower bound at least 0.5 half-widths above 0, SRM p (h_null's 0.397),
and the guaranteed miss of section 15 at least 0.33 (realised 0.3404). The realised lift is 12.2% relative (CTR 0.10945
/ 0.12279) against the generator's 9%: sampling noise of a heavy-tailed set. Its effective intra-user correlation is
section 5's rho_eff.

Pageviews are never duplicated on purpose, but random times collide: a few rows share a user and a second (FACT,
pandas on the six sets; exact text repeats / same user and instant: visible 4 / 9, h_null 9 / 12, h_pos 1 / 2,
h_srm 1 / 7, h_bots 0 / 4, h_twin 8 / 12 (section 15 data; h_null's rows, one repeated pair now differs in `clicked`)).
They are separate pageviews; the references count them and
EXPERIMENT.md section 4 says so.

h_srm's own CI says "ship" (lower bound +0.81 half-widths), so ignoring the SRM flag flips its decision. On h_bots the
shipped code reports a +30.1% lift. Every hidden set has 34,000 to 40,000 users and 322,363 to 344,187 pageview rows
(FACT, `gzip -dc | wc -l`; instruction: at most 50,000 and 500,000). Cross-checks (FACT): gen_data.py stops unless
ref_a's diff, half-width and SRM p match its own numbers to 1e-9 relative and the user counts are equal; ref_b's independent loader gives the
same counts and pageviews on every set, its delta and CR1 bounds match ref_a to under 1e-4 half-widths
(calibration_study.out.md);
the canonical solution matches the references exactly (CI error 4e-16 half-widths, `local_results.json`).
Reproducible (FACT, 2026-10-28): rerunning `gen_data.py` twice gave byte-identical `tests/SHA256SUMS` (so identical
gzip files), expected files, visible CSVs and `output/result.json` (`shasum -a 256 -c`, 10 of 10 OK). After h_lowicc
was added (section 13), the regenerated `SHA256SUMS` keeps the 17 earlier lines unchanged and adds 4, and the visible
CSVs, `output/result.json` and the five earlier expected files match their earlier hashes (9 of 9 OK); a second
rerun is byte-identical again (section 13). After h_twin replaced h_lowicc (section 14; the h_lowicc files were moved
out first so the manifest lists only real files): `diff` of the old and new `SHA256SUMS` shows only the 4 h_lowicc
lines removed and 4 h_twin lines added, the other 17 unchanged; the visible CSVs, `output/result.json` and the five
other expected files match their earlier hashes (9 of 9 OK); a second rerun gave a byte-identical `SHA256SUMS` and
`generation_report.out.md` (`cmp`) and the same 10 hashes of the visible CSVs, `output/result.json` and the six
expected files; `shasum -a 256 -c tests/SHA256SUMS` 21 of 21 OK. After the exact-twin rebuild (section 15, 2026-10-29):
of the 58 package files only 5 changed (`tests/SHA256SUMS`, `tests/expected/h_twin.json` and the three h_twin gzip
files; SHA-256 of every file before and after); `diff` of the old and new `SHA256SUMS` shows only the 4 h_twin lines
changed, the other 17 unchanged; a second rerun gave the same SHA-256 for all 58 package files and a byte-identical
`SHA256SUMS` and `generation_report.out.md` (`cmp`); `shasum -a 256 -c tests/SHA256SUMS` 21 of 21 OK.

## 5. Band calibration (G13, G15; the original design's "Main risk")
Method (auth/calibration_study.py; FACT, `calibration_study.out.md`, re-run on the six sets of section 15
on 2026-10-29: 826.9 s by the script's own timer (`calibration_study.out.md` line 3), output written 02:42:02 MST (file
modification time of `calibration_study.out.md` and `calibration.json`, `stat`), nothing else run in parallel by the
same step (other work on the Mac was not stopped); the
clock range written here before, 02:29:06 to 02:42:04, spans only 778 s and was wrong (section 16); the section-14 run
took 641.8 s and is kept as `calibration_before_exact_twin.out.md`; the five sets that did not change give the same
numbers in both): on every set, bound errors in reference half-widths for the valid methods (delta without the N/(N-1)
factor; CR1; user bootstrap B = 2,000 for 200 seeds read as percentile, basic and normal; B = 5,000 percentile, 30
seeds; pooled B = 2,000, 30 seeds) and for two wrong ones (pageview-level CI = `fix_bots_only`; pageview CI x K = 2.466
fitted on the visible set = `constant_inflation`).

| set | DE | sqrt(DE) | worst valid error | fix_bots_only error | constant_inflation error |
|---|---|---|---|---|---|
| visible | 6.08 | 2.466 | 0.0809 | 0.5944 | 0.0002 |
| h_null | 23.05 | 4.801 | 0.1039 | 0.7917 | 0.4864 |
| h_pos | 6.05 | 2.460 | 0.0916 | 0.5936 | 0.0023 |
| h_srm | 6.81 | 2.610 | 0.0883 | 0.6169 | 0.0553 |
| h_bots | 7.85 | 2.802 | 0.0859 | 0.6431 | 0.1199 |
| h_twin | 5.24 | 2.288 | 0.0987 | 0.5630 | 0.0776 |

- Delta (both forms) and CR1 agree with the reference to under 1e-4 half-widths on all six sets; the bootstrap is the
  noisy method: B = 2,000 percentile bound error SD 0.028 to 0.033 per bound, mean within +/-0.022 (h_null, the
  heaviest tail).
- Spread (worst valid error, all sets) 0.1039 (h_null; h_twin 0.0987). It is a sample maximum over 200 seeds, so a
  different seed set can give more: the second review saw 0.1208 for h_lowicc with other seeds (max of 300: 0.1116),
  section 14. Rule band (next percent above 2 x spread) 0.21; **band used 0.25**. Stated in SDs as well: the worst
  |mean| + 4 SD over every set, bound and bootstrap group is 0.1776 < 0.25 (h_twin, pooled B = 2,000, 30 seeds;
  0.1550 on the section-14 data): PASS.
- `fix_bots_only` smallest miss 0.5630 (h_twin; 0.5638 on the section-14 h_twin) >= 2 x 0.25 = 0.50: PASS. Best
  possible constant K, worst-set error (sqrt(DE) max-min)/(max+min) = 0.3544 > 0.25: PASS (no constant multiple of the
  pageview CI fits all sets).
- ICC shortcut (sweep added in section 13): no single rho passes all six readouts, with m = m_w or with m = mean
  pageviews per user: PASS (table below).
- Pageview-only shortcut (sweep added in section 14): none of 16 features of the pageview counts x 3 forms passes all
  six readouts: PASS (below). Twin pair (check added in section 15): h_null and h_twin have identical per-user pageview
  counts in each arm, and any pair of per-arm multipliers M_A, M_B >= 0 misses one of the two by 0.3404 or more: PASS
  (below).
- Smallest decision margin 0.806 half-widths (h_srm) >= max(0.35, 0.25): PASS; h_twin +1.534. SRM p: h_srm 6.75e-9
  (above 1e-12, below 0.001); others 0.397 to 1: PASS. All ten checks of the study PASS.
- History (FACT, `calibration_first_run.out.md`): the first data had DE 3.12 on h_pos, spread 0.1251, rule band 0.26,
  and `fix_bots_only` missed by 0.434 < 0.52: FAIL. The data was changed (h_pos rho 0.11 -> 0.20 and lift 0.065 ->
  0.10; h_null sigma 1.0 -> 1.3; visible rho 0.15 -> 0.20; h_srm rho 0.20 -> 0.24, lift 0.075 -> 0.11), not the rule.
- INFERENCE (normal approximation with the measured SD 0.033 and mean shift 0.022): a valid B = 2,000 percentile
  bootstrap misses the 0.25 band with probability below 1e-9 per bound (the band is about 6.9 SD from the mean).

ICC shortcut sweep (FACT, `calibration_study.out.md` "ICC shortcut sweep"). Interval = diff +/- z sqrt(sum over arms
of R(1-R)/V x (1 + rho (m - 1))), one rho for every set, rho from 0 to 1 in steps of 0.005 (0.0001 for the best rho);
a set passes when both bound errors are <= 0.25 reference half-widths. rho_eff = (Var_delta / Var_pageview - 1) /
(m_w - 1) per arm.

| set | m_w A / B | mean v A / B | rho_eff A / B | passing rho, m = m_w | passing rho, m = mean v |
|---|---|---|---|---|---|
| visible | 30.0 / 29.7 | 9.67 / 9.54 | 0.176 / 0.176 | 0.085 to 0.290 | 0.285 to 0.985 |
| h_null | 46.0 / 55.8 | 7.90 / 8.00 | 0.421 / 0.462 | 0.245 to 0.700 | none |
| h_pos | 25.1 / 24.0 | 7.88 / 7.77 | 0.209 / 0.220 | 0.105 to 0.355 | 0.355 to 1.000 |
| h_srm | 24.9 / 24.4 | 7.94 / 7.77 | 0.226 / 0.265 | 0.120 to 0.405 | 0.415 to 1.000 |
| h_bots | 28.6 / 29.4 | 7.82 / 7.78 | 0.247 / 0.242 | 0.125 to 0.400 | 0.505 to 1.000 |
| h_twin | 46.0 / 55.8 | 7.90 / 8.00 | 0.079 / 0.089 | 0.040 to 0.140 | 0.285 to 1.000 |

- m = m_w: no rho passes every set; at most 5 of 6 pass (rho 0.125 to 0.290; above 0.140 h_twin fails, below 0.245
  h_null fails). Best rho 0.170 (0.1722 on the fine grid), worst error 0.3594 (0.3557 fine): visible 0.015,
  h_null 0.359, h_pos 0.091, h_srm 0.141, h_bots 0.143, h_twin 0.348. This rho is attempt `icc_tuned` (section 9:
  reward 0). It was 0.145 and 0.403 with h_lowicc (section 13), 0.175 and 0.352 with the section-14 h_twin.
- m = mean v: no rho passes every set (h_null passes none in 0 to 1); at most 5 of 6 (rho 0.505 to 0.985); best rho
  1.000, worst error 0.413.

Pageview-only sweep (FACT, `calibration_study.out.md` "Pageview-only sweep"; added in section 14). Interval = diff +/- z
sqrt(sum over arms of R(1-R)/V x M), M built from the arm's pageview counts only, in three forms: f^g (no constant),
c f^g and 1 + c f^g with c fitted so the visible readout is exact; g from -3 to 4 in steps of 0.01. The 16 features
f: Kish's K = mean(v^2)/mean(v)^2, CV, K over users with a pageview, m_w, mean v, sd v, mean v over users with a
pageview, max/mean, p99/mean, p90/mean, median/mean, Gini, share of views of the top 1% and top 10% of users, share of
users with no pageview, sd of log(1 + v).
- No form passes every set. The smallest best worst-set error over the 48 forms is 0.3544 (mean v, 1 + c f^g); Kish's
  K as f^g is best at g = 1.22 with 0.360 (attempt `kish_tuned`). Every feature takes the same value on h_null and
  h_twin (for example K 5.82 / 6.98 per arm on both), as the twin check requires.

Twin pair h_null / h_twin (FACT, auth/twin_identity.out.md and `calibration_study.out.md`; the arithmetic is shown
there and in section 15). h_twin's `assignments.csv` and `users.csv` are byte-identical to h_null's and its
`pageviews.csv` differs only in the clicked column, so every counted user's pageview count, aligned by user_id, is the
same on the two sets in each arm (`np.array_equal`), and so is every statistic of the counts. Any interval width
computed from the pageview data therefore takes the same value on both, while the reference half-widths are 0.010831
(h_null) and 0.005265 (h_twin), ratio 2.0572. Minimum worst error over the two sets, in reference half-widths: a width
from the pageview data alone 0.3458; the pageview-level interval times one common multiplier 0.3544 (sqrt(DE) ratio
2.0981); each arm's pageview-level variance times its own M_A, M_B >= 0 0.3404 (the arms' R(1-R) differ between the
sets by the factors 0.9759 (A) and 1.1076 (B); a brute-force grid gives the same 0.3404). All three are above the
0.25 band, so no rule of these three forms passes both sets, however many parameters its width or multiplier has and
wherever they were fitted. Rules that use the clicks in any other way are outside this argument: some of them pass
(limitation 9(c) and (d), section 16).

## 6. Grader (`tests/grade.py`)
Checks SHA256SUMS, copies /app (`kit.prepare_submission`), reads `output/result.json` through `kit.read_as_runner`,
then for each hidden set: unpacks the gzip files into root-only scratch, stages them with `kit.stage_for_runner` under a
neutral name (`exp1`..`exp5`), runs `python3 -m abtest.report --data <in> --out <out>/result.json` as uid 1001 with
cwd = the copy (no `-I`: it would drop cwd from `sys.path` and the package would not import), cap 120 s, and reads the
output as uid 1001. JSON is parsed as data only. Per readout: counts exact (an int or a float with no fraction; never a
bool), CTR and diff within 1e-9, `srm_p` within 1% relative or both below 1e-12, `srm_flag` a bool (or 0/1) equal,
`ci_95` a two-number array with each bound within 0.25 reference half-widths, `decision` equal after trim and
lower-case. Reward 1 only if all six pass and every run exits 0 in time; metrics per set (errors, run seconds).
Before grading it logs the sandbox's resources as metrics that never affect the reward: `res_cgroup_cpus` and
`res_cgroup_mem_mib` (cgroup v2 limits; -1 = no limit), `res_cpu_affinity`, and the host's `res_os_cpu_count` and
`res_host_memtotal_mib`. On the Mac only `res_os_cpu_count` is present.
Probes (FACT, `grader_probes.out.md`, 24 of 24 as expected; re-run in section 14 after its labels were made to read
the counts from `expected/visible.json`, 19612, instead of the stale 19586): pass for reordered or extra keys, a BOM, counts as
floats, `srm_flag` 0, " No_Ship ", CTR off 5e-10, a bound off 0.24 half-widths, `srm_p` off 0.9%; fail for a bound off
0.26, swapped bounds, `ci_95` as an object, CTR off 2e-9, relative diff, a count off by one or by 0.5, `srm_p` off 2%,
`srm_flag` "false", the wrong decision, a missing key, NaN, booleans as counts, an empty file, a JSON list.

## 7. Solutions and attempts
| Variant | What it does | Why it should score 0 or 1 |
|---|---|---|
| canonical | bots out of both arms; per-user sums; delta method; SRM chi-square; plan's decision rule | 1 |
| alt | join-based bot filter; numpy sums; user bootstrap 5,000 resamples, percentile | 1 (different CI method and code) |
| alt_cr1 | canonical with a CR1 interval from the pageview regression | 1 |
| nop | the shipped code and readout | 0 everywhere |
| hardcode_no_ship | canonical numbers, decision always `no_ship` | 0: h_pos and h_twin (ship) and h_srm (invalid) |
| fix_visible_result_only | a one-off script writes the right visible readout; pipeline unchanged | 0: all hidden sets |
| fix_bots_only | bots, SRM and decision fixed; pageview-level CI | 0: CI misses by 0.56 to 0.79 on every set |
| mean_of_ratios | average of per-user CTRs, user-level Welch CI | 0: CTR and diff on every set |
| no_srm_gate | everything right except the decision ignores the SRM flag | 0: h_srm decision only |
| constant_inflation | pageview CI x 2.466 (fitted on the visible set) | 0: h_null CI (0.49) |
| fix_ci_only | CI, SRM and decision fixed; B-only bot filter kept | 0: counts, CTR, diff everywhere |
| icc_tuned | pageview CI with each arm's variance x (1 + 0.170 (m_w - 1)), m_w = sum(v^2)/sum(v); 0.170 is the best single rho of the sweep, tuned on all six sets (0.145 before section 14, 0.175 before section 15) | 0: h_null (0.359, too narrow) and h_twin (0.348, too wide) |
| kish_tuned | pageview CI with each arm's variance x K^1.22, K = mean(v^2)/mean(v)^2 (Kish's 1 + CV^2), no fitted constant; 1.22 is the best exponent of the pageview-only sweep, tuned on all six sets (1.23 before section 15) | 0: h_null (0.354, too narrow) and h_twin (0.360, too wide) |

## 8. Timings and caps
FACT (Apple M-series Mac), runs of local_check.py (section 9). "Slowest hidden run" is the slowest of a variant's runs
on the hidden sets; a grading pass is one full `tests/grade.py` run.

| Run | When (Mac clock, MST) | Hidden sets | Slowest hidden run: canonical / alt / alt_cr1 | Any other variant | Grading passes | `solve.sh` | Whole matrix |
|---|---|---|---|---|---|---|---|
| two first runs after the final data (a) | 2026-10-28 | four | 1.46-1.48 / 2.12-2.42 (the slowest valid) / 1.49-1.90 s | - | 5.6 to 9.1 s | 1.4 to 2.1 s | - |
| after the first review (section 12) | 2026-10-28 20:55 | four | 1.57 / 2.03 / 1.41 s | - | 5.7 to 8.2 s | up to 2.04 s | 82 s |
| section 13, h_lowicc (a) | 2026-10-28, started 21:36:15 | five | 1.48 / 2.18 / 1.47 s | at most 1.71 s | 7.26 to 10.2 s (alt the slowest) | up to 2.06 s | 109 s, 12 variants |
| section 14, h_twin as a new draw (a) | 2026-10-28, 22:37:44 to 22:39:36 | five | 1.48 / 1.97 / 1.39 s | at most 1.47 s | 6.96 to 9.85 s (alt the slowest) | up to 1.97 s | 111.7 s, 13 variants |
| section 15, exact twin (a) | 2026-10-29, 02:42:37 to 02:44:31 | five | 1.37 / 1.99 / 1.50 s | at most 1.86 s | 6.89 to 9.85 s (alt the slowest) | up to 1.98 s | 114 s, 13 variants |
| section 16, no package file changed (a); the run now in `local_results.json` | 2026-10-29, 03:29:33 to 03:31:26 by the Mac `date` before and after | five | 1.42 / 1.99 / 1.42 s | at most 1.61 s | 6.94 to 9.93 s (alt the slowest) | up to 1.97 s | 113 s |

(a) The step that took these timings ran nothing else in parallel; other work on the Mac was not stopped. The output
files of the two first runs were overwritten by the run after the
first review; from then on each run replaced `local_results.json`. The cap derivation below still holds with the
largest measured pass, 10.2 s.
Derived: per-run cap 120 s (deviation 5); `verifier.timeout_sec` 950 s (5 x 120 + 10.2, + 50%, rounded up; it was 750 s
with four hidden sets); `agent.timeout_sec` 1800 s (as in the original design). Calibration study 826.9 s (section 15
run, section 5; 641.8 s with the section-14 h_twin, 585.0 s with h_lowicc, 676.7 s with five sets); gen_data.py 13.5 s
(section 15; 11.9 s in section 14, 13.2 s before); twin_identity.py 1.5 s; click_rule_probes.py 107.2 s (section 16,
its own timer; 11 grading passes). UNVERIFIED when written: the same on a 1-vCPU Daytona sandbox; the proof run's
`<set>_run_seconds` metrics now show it (largest 2.326 s in run `full2`, section 11). Still UNVERIFIED: the 2 GiB
memory head-room of an agent's bootstrap (run `full2` logged the 2,048 MiB limit, not the peak use).

## 9. LOCAL RESULTS
Command: `submission/.venv/bin/python submission/authoring/ab-test-reanalysis/local_check.py` (each variant: copy
`environment/app`, `SOLUTION=<variant> APP_DIR=<copy> bash solution/solve.sh`, drop `data`, `__pycache__`, `.venv` at any
depth, then `KIT_LOCAL=1 KIT_SUBMISSION=<artifact> KIT_LOGS=<dir> KIT_WORK=<dir> GRADE_TESTS_DIR=<task>/tests
GRADE_PYTHON=<venv python> python tests/grade.py`). FACT, run 2026-10-29 02:42 MST after h_twin was
rebuilt as h_null's exact twin and `icc_tuned` (rho 0.170) and `kish_tuned` (K^1.22) were re-tuned (section 15), and
re-run 2026-10-29 03:29 MST with no package file changed (section 16); both printed ALL AS EXPECTED with
the same cells (`local_results.json` holds the 03:29 run). Cells: pass, or FAIL with the number of failed checks
and the worst CI bound error in half-widths.

| Variant | Expected | Got | visible | h_null | h_pos | h_srm | h_bots | h_twin |
|---|---|---|---|---|---|---|---|---|
| canonical | 1 | 1 | pass | pass | pass | pass | pass | pass |
| alt | 1 | 1 | pass | pass | pass | pass | pass | pass |
| alt_cr1 | 1 | 1 | pass | pass | pass | pass | pass | pass |
| nop (original) | 0 | 0 | FAIL 9, ci 1.43 | FAIL 8, ci 1.15 | FAIL 8, ci 1.34 | FAIL 9, ci 1.20 | FAIL 9, ci 4.09 | FAIL 8, ci 1.29 |
| hardcode_no_ship | 0 | 0 | pass | pass | FAIL 1 (decision) | FAIL 1 (decision) | pass | FAIL 1 (decision) |
| fix_visible_result_only | 0 | 0 | pass | FAIL 8, ci 1.15 | FAIL 8, ci 1.34 | FAIL 9, ci 1.20 | FAIL 9, ci 4.09 | FAIL 8, ci 1.29 |
| fix_bots_only | 0 | 0 | FAIL 1, ci 0.59 | FAIL 1, ci 0.79 | FAIL 1, ci 0.59 | FAIL 1, ci 0.62 | FAIL 1, ci 0.64 | FAIL 1, ci 0.56 |
| mean_of_ratios | 0 | 0 | FAIL 4, ci 0.49 | FAIL 4, ci 0.67 | FAIL 4, ci 0.50 | FAIL 4, ci 0.51 | FAIL 4, ci 0.59 | FAIL 4, ci 0.51 |
| no_srm_gate | 0 | 0 | pass | pass | pass | FAIL 1 (decision) | pass | pass |
| constant_inflation | 0 | 0 | pass | FAIL 1, ci 0.49 | pass | pass | pass | pass |
| fix_ci_only | 0 | 0 | FAIL 7, ci 0.84 | FAIL 7, ci 0.37 | FAIL 7, ci 0.75 | FAIL 7, ci 0.59 | FAIL 9, ci 3.50 | FAIL 7, ci 0.73 |
| icc_tuned | 0 | 0 | pass | FAIL 1, ci 0.36 | pass | pass | pass | FAIL 1, ci 0.35 |
| kish_tuned | 0 | 0 | pass | FAIL 1, ci 0.35 | pass | pass | pass | FAIL 1, ci 0.36 |

Static checks (FACT, section-16 pass, 2026-10-29 after the local matrix; the section-15 pass gave the same):
`harbor lint tasks/ab-test-reanalysis --json` printed `[]`; `python tools/sync_kit.py --check` printed `checked` for the
five tasks with exit 0, then `python tools/sync_kit.py` synced them (SHA-256 of every task's `tests/kit.py` and
`tests/test.sh` identical before and after; all equal `base/verifier_kit/`, `cmp`); `python tools/check_task.py
tasks/ab-test-reanalysis` printed `OK ab-test-reanalysis`; `grader_probes.py` 24 of 24 as expected (ALL AS EXPECTED);
`shasum -a 256 -c tests/SHA256SUMS` 21 of 21 OK; no `__pycache__`, `.pyc` or `.DS_Store` under the package. Not testable on the Mac: uid 1001, `/tests` 0700, the network namespace and the reward-folder lock (KIT_LOCAL
skips them).

First-review probes (FACT, 2026-10-28, run while checking the first review's findings, section 12; scratch harness
outside the repo: canonical files plus one changed module, the visible
readout regenerated, then `tests/grade.py` in KIT_LOCAL mode as above; not shipped as attempts, so they add no Daytona
trials):

| Probe | What it changes | Reward | Per set |
|---|---|---|---|
| dedupe_pv | `pageviews.csv` read with `.drop_duplicates()` (exact text repeats) | 0 | FAIL visible 5, h_null 6, h_pos 3, h_srm 3; h_bots pass (no exact repeats) |
| dedupe_pv_instant | pageviews deduplicated after parsing to instants | 0 | FAIL on all five readouts that existed then (visible, h_null, h_pos, h_srm, h_bots: 5, 6, 3, 6 and 5 failed checks) |
| icc_0.1761 | CI = pageview CI x sqrt(1 + rho (m_w - 1)) per arm, m_w = sum(v^2)/sum(v), rho fitted on the visible set | 0 | FAIL h_null only (ci 0.349) (four hidden sets; re-run below) |
| icc_0.25 | the same with rho = 0.25 (only findable by tuning on the hidden sets) | 1 | worst ci 0.236 (h_null) (four hidden sets; now 0, below) |
| icc_0.27 | the same with rho = 0.27 | 1 | worst ci 0.209 (h_null) (four hidden sets; now 0, below) |

The two dedupe probes are why EXPERIMENT.md section 4 now says every pageview row counts (rows that share a user and a
second exist in every set; section 4). INFERENCE: they still score 0 with h_twin in place of h_lowicc, because both
already fail the visible readout, which did not change; they were not re-run. The ICC rows were limitation 9
(section 11).

ICC probes re-run in section 13 with h_lowicc as the fifth hidden set (FACT, 2026-10-28; record of section 13, superseded
by the next table; scratch harness outside the repo: canonical files plus `attempts/icc_tuned/stats.py` with RHO
replaced, the visible readout regenerated, then `tests/grade.py` in KIT_LOCAL mode as above). Cells: pass/FAIL and the
worst bound error in half-widths.

| rho | Reward | visible | h_null | h_pos | h_srm | h_bots | h_lowicc |
|---|---|---|---|---|---|---|---|
| 0.10 | 0 | pass 0.201 | FAIL 0.491 | FAIL 0.256 | FAIL 0.297 | FAIL 0.304 | pass 0.186 |
| 0.145 (`icc_tuned`, local_check) | 0 | pass | FAIL 0.40 | pass | pass | pass | FAIL 0.40 |
| 0.1761 (fitted on visible) | 0 | pass 0.000 | FAIL 0.349 | pass 0.078 | pass 0.129 | pass 0.131 | FAIL 0.532 |
| 0.25 | 0 | pass 0.162 | pass 0.236 | pass 0.066 | pass 0.008 | pass 0.010 | FAIL 0.805 |
| 0.27 | 0 | pass 0.202 | pass 0.209 | pass 0.102 | pass 0.041 | pass 0.044 | FAIL 0.873 |
| 0.29 | 0 | pass 0.241 | pass 0.182 | pass 0.137 | pass 0.074 | pass 0.078 | FAIL 0.937 |

Shortcut probes re-run in section 14 on its data (record; superseded for the h_twin column by section 15,
where the same formulas give h_twin errors of 0.071 to 0.842 by arithmetic on the committed data, and every
multiplier of this kind is the same number on h_null and h_twin) (FACT, 2026-10-28 22:27 to
22:30 MST; scratch harness outside the repo: canonical files plus one replaced `stats.py` whose interval is the
pageview-level one with each arm's variance times a multiplier M from the arm's pageview counts only, the visible
readout regenerated, the /app copy rules applied, then `tests/grade.py` in KIT_LOCAL mode as above). The first three
rows are the second review's formulas that scored 1 with h_lowicc (section 14). Cells: pass/FAIL and the worst bound
error.

| M per arm | Reward | visible | h_null | h_pos | h_srm | h_bots | h_twin |
|---|---|---|---|---|---|---|---|
| K^1.5, K = mean(v^2)/mean(v)^2 (no constant; 1 with h_lowicc) | 0 | pass 0.051 | pass 0.162 | pass 0.042 | pass 0.096 | pass 0.044 | FAIL 0.730 |
| 2.884 CV^2 (c exact on the visible set; 1 with h_lowicc) | 0 | pass 0.000 | pass 0.179 | pass 0.009 | pass 0.048 | pass 0.001 | FAIL 0.700 |
| 2.5 CV^2 (1 with h_lowicc) | 0 | pass 0.069 | pass 0.236 | pass 0.060 | pass 0.114 | pass 0.070 | FAIL 0.583 |
| 175.8 x (share of users with no pageview)^1.5 (c exact on visible) | 0 | pass 0.000 | pass 0.122 | pass 0.105 | pass 0.041 | pass 0.119 | FAIL 0.837 |
| 0.0995 x (p99/mean)^2.15 (c exact on visible) | 0 | pass 0.000 | pass 0.229 | pass 0.033 | pass 0.049 | pass 0.020 | FAIL 0.636 |
| 1 + 0.10 (m_w - 1) | 0 | pass 0.201 | FAIL 0.491 | FAIL 0.256 | FAIL 0.297 | FAIL 0.304 | pass 0.063 |
| 1 + 0.1761 (m_w - 1) (rho exact on visible) | 0 | pass 0.000 | FAIL 0.349 | pass 0.078 | pass 0.129 | pass 0.131 | FAIL 0.359 |
| 1 + 0.25 (m_w - 1) | 0 | pass 0.162 | pass 0.236 | pass 0.066 | pass 0.008 | pass 0.010 | FAIL 0.594 |
| 1 + 0.27 (m_w - 1) | 0 | pass 0.202 | pass 0.209 | pass 0.102 | pass 0.041 | pass 0.044 | FAIL 0.652 |
| 1 + 0.29 (m_w - 1) | 0 | pass 0.241 | pass 0.182 | pass 0.137 | pass 0.074 | pass 0.078 | FAIL 0.708 |

Click-rule probes (FACT, section-16 pass, 2026-10-29; `auth/click_rule_probes.py`, table 4 of
`click_rule_probes.out.md`: environment/app + canonical files + one probe `stats.py`, the visible readout regenerated,
the /app copy rules, `tests/grade.py` in KIT_LOCAL mode; not shipped as attempts or solutions). Rules that use the
clicks are outside the twin proof of section 15; these show which of them pass. "disp k" = each arm's pageview-level
variance R(1-R)/V times D, D = sample variance of per-user CTR over users with >= k pageviews / mean of R(1-R)/v over
the same users, no constant, exponent 1. Cells: pass/FAIL and the worst bound error.

| Probe | Fitted on the hidden readouts | Reward | visible | h_null | h_pos | h_srm | h_bots | h_twin |
|---|---|---|---|---|---|---|---|---|
| disp k = 10 | none (k a choice) | 0 | pass 0.196 | FAIL 0.404 | pass 0.155 | pass 0.143 | FAIL 0.254 | FAIL 0.282 |
| disp k = 17 | none (k a choice) | 0 | pass 0.024 | FAIL 0.260 | pass 0.038 | pass 0.042 | pass 0.098 | pass 0.156 |
| disp k = 18 | none (k a choice) | 1 | pass 0.001 | pass 0.245 | pass 0.063 | pass 0.051 | pass 0.079 | pass 0.143 |
| disp k = 20 | none (k a choice) | 1 | pass 0.050 | pass 0.203 | pass 0.121 | pass 0.099 | pass 0.033 | pass 0.104 |
| disp k = 26 | none (k a choice) | 1 | pass 0.154 | pass 0.087 | pass 0.246 | pass 0.216 | pass 0.120 | pass 0.016 |
| disp k = 27 | none (k a choice) | 0 | pass 0.179 | pass 0.070 | FAIL 0.273 | pass 0.237 | pass 0.128 | pass 0.007 |
| ANOVA ICC of the clicks within users x Kish's 1 + rho (m_w - 1), no constant | none | 1 | pass 0.032 | pass 0.017 | pass 0.001 | pass 0.023 | pass 0.036 | pass 0.064 |
| c (zero-click share / binomial, users >= 5 views)^2.0, c on visible | none fitted; k and g are round values that the third review picked from a grid (4 of its 24 points passed on the section-14 data) | 1 | pass 0.000 | pass 0.230 | pass 0.205 | pass 0.077 | pass 0.067 | pass 0.014 |
| c (CTR variance / binomial, users >= 10 views)^1.5, c on visible | as the row above | 1 | pass 0.000 | pass 0.111 | pass 0.077 | pass 0.133 | pass 0.048 | pass 0.188 |
| c abs(diff)^4.03 abs(rel)^-4.61 (variance multiplier, both arms) | 3 (c and two exponents) | 1 | pass 0.229 | pass 0.238 | pass 0.238 | pass 0.236 | pass 0.177 | pass 0.007 |
| c R_A^9.9 R_B^-7.5 (variance multiplier, both arms), c on visible | 2 (two exponents) | 1 | pass 0.000 | pass 0.141 | pass 0.156 | pass 0.158 | pass 0.037 | pass 0.010 |

Fast evaluator (same file, tables 1 and 2): disp passes all six readouts exactly for k = 18 to 26 (worst 0.245, 0.220,
0.203, 0.181, 0.165, 0.190, 0.203, 0.228, 0.246) and fails for k = 5 to 17 and 27 to 40. With one exponent tuned on the
hidden readouts on any of 9 arm-level click aggregates (abs(diff), abs(rel), R_A, R_B, pooled R, pooled R(1-R), sum of
R(1-R), max R, min R; exponent -12 to 12, c free or on visible) nothing passes (best 0.341); with c on visible and two
tuned exponents (-16 to 16 in steps of 0.1) 11 of the 36 pairs pass.

What the Daytona proof run must show: oracle x10 = 1; `--ae SOLUTION=alt` = 1 and `--ae SOLUTION=alt_cr1` = 1; nop = 0;
each of the nine attempts = 0 with the failing sets above (`fix_ci_only` is listed by `tools/proof_matrix.py` through
its README-only folder; `icc_tuned` and `kish_tuned` must fail on h_null and h_twin only); oracle with
`--force-build` = 1;
`test-stdout.txt` shows `SHA256SUMS: 21 files verified`, `lock ok`, and `<set>_run_seconds` well under 120 for the alt
on all five hidden sets (the only evidence for the cap on the sandbox); `agent/oracle.txt` shows no `cp: cannot stat`.
Also read the `verifier resources:` line (and the `res_*` metrics in `reward.json`) of one trial: if `res_cgroup_cpus`
= 1 and `res_cgroup_mem_mib` = 2048, the instruction may again say the grading machine has "the same CPU and memory
settings as yours"; until then it only says "plan for one CPU and 2 GiB of memory" (section 12, finding 3). Run
`full2` showed all of this (section 11); the instruction wording was not changed.

## 10. Gate record (implementation)
```
Gate record: ab-test-reanalysis, implementation (2026-10-28; revised after each pass of sections 12 to 16, last on 2026-10-29; the (run) items scored from the Daytona run full2)
Applies to: task ab-test-reanalysis
G1  PASS - code, plan, visible export, five hidden exports, references and pins are in the package; images install pinned wheels from PyPI at build time (like every task)
G2  PASS - stops a false ship decision and leaves a corrected readout plus a pipeline that follows the plan
G3  PASS - a small real-looking readout package, a pre-registered plan, a PM note, a 40,000-user export with retries, mixed offsets, pre-assignment pageviews and bots
G4  PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - every readout (visible + five hidden) is compared by script with stated tolerances; proven locally in KIT_LOCAL mode and on Daytona in run full2 (every variant as expected)
G5  PASS - the only experiment-statistics task (one-sided filter, unit of analysis, SRM gate)
G6  PASS - plain ratios anyone can recompute; two independent references (stdlib delta; pandas delta and CR1) agree to under 1e-4 half-widths on all six sets (the section-15 h_twin included); bootstrap measured over 200 seeds
G7  PASS - auditing an A/B readout before a ship decision is routine analyst work
G8  PASS - EXPERIMENT.md states unit, population rules, the five definitions (now incl. "every pageview row counts"), metric, accepted CI methods, SRM test, decision rule, columns and output schema; the instruction states the command, the five hidden folders and six readouts, every tolerance, the 0.25 band, the 120 s cap, the CPU and memory to plan for, the grading machine's package set, the user, no network, sizes and the /app copy; the unverified "same CPU and memory settings" claim was removed (section 12)
G9  PASS - bots, logging retries, pre-assignment exposure, same-second pageviews, mixed offsets and heavy-tailed engagement are what real exports contain; see limitations 1 and 4
G10 PASS - a corrected readout and a fixed, reusable pipeline
G11 PASS - only readout numbers are checked; delta, bootstrap and CR1 all pass (first review: jackknife and naive pandas bootstrap too; section 16: a one-way ANOVA ICC of the clicks within users times Kish's 1 + rho (m_w - 1), worst 0.064); no file or function name is checked
G12 PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - locally all nine shortcut and wrong attempts score 0, and all nine score 0.0 on Daytona in run full2. Design-effect shortcuts built from the pageview counts alone are closed by a proof on the data, not only by sweeps (section 15): h_twin has h_null's exact users, arms, bots and pageview rows and only new clicks (FACT, auth/twin_identity.out.md: byte-identical assignments and users, same user_id and ts on all 322,363 pageview rows, per-user counts np.array_equal per arm), so any multiplier or width computed from the pageview data is the same number on both sets, while their reference half-widths differ 2.057-fold; FACT (arithmetic, section 15): every width from the pageview data alone misses one of the two by >= 0.346, every pageview-level interval with per-arm multipliers M_A, M_B >= 0 by >= 0.340, one common multiplier by >= 0.354, all > band 0.25 for every rule of these three forms, whatever the formula of its width or multiplier, its number of parameters or where they were fitted (this closes the third review's finding F1: the 3-4 parameter tail-moment rules tuned on the hidden readouts); the sweeps agree (best rho 0.356, best of 48 pageview-count forms 0.354; icc_tuned rho 0.170 and kish_tuned K^1.22 fail h_null and h_twin by 0.35 to 0.36 through the grader). Rules that use the clicks are outside the proof (section 16, FACT through the grader): (i) a user-level click-dispersion estimate, each arm's pageview-level variance times (variance of per-user CTR over users with >= k pageviews) / (mean of R(1-R)/v over them), with no constant, scores 1 for k = 18 to 26 (k = 20: worst 0.203) and 0 for k = 17, 27 and 10 (0.404); it needs no hidden data. Verdict: PASS, not a shortcut: it uses every user's clicks and pageviews after the plan's filters, needs the bot, SRM and decision fixes, and estimates the users' own click correlation, the quantity the task tests; the textbook form of the same idea (one-way ANOVA ICC x Kish's 1 + rho (m_w - 1)) scores 1 with worst 0.064. Honest part: it is not one of the plan's three methods (the plan does not forbid others; the grader checks the readout, G11), it passes only in that k window, and it works because the generator gives each set one click correlation independent of pageviews. Override question (ruled in section 16: no override): if 'any method not on the plan's list' counts as a shortcut, G12 is FAIL for this rule, and only a data redesign closes it (a click correlation that varies with engagement), since no seed search can. (ii) in this sweep (9 arm-level click aggregates), rules from arm-level click aggregates pass only with two or more exponents tuned on the hidden readouts (c R_A^9.9 R_B^-7.5 with c on visible: worst 0.158; one tuned exponent: best 0.341), which no agent can tune. Also: answers only in root-only /tests; agent code runs as uid 1001; run full2 logged lock ok and SHA256SUMS: 21 files verified in all 23 trials (section 11; the 14 shipped traces/*/verifier/test-stdout.txt show these lines)
G13 PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - alt (bootstrap) and alt_cr1 score 1 locally on all six readouts and on Daytona in run full2; calibration on six sets: worst valid error 0.104 (a sample maximum over 200 seeds; h_twin 0.099) vs band 0.25, and |mean| + 4 SD of every bootstrap bound error 0.178 < 0.25; the 9 format probes that should pass do
G14 PASS - the crux is a code-vs-plan audit (a one-sided filter dressed as an incident fix, a pageview-level test, no SRM gate, a p-value rule) plus a user-level variance method; honest: the PM points at the size mismatch and the plan names the user-level rule, so this is the softer of the five (the original design's "Main risk")
G15 PASS - band from the measured spread (section 5); every enforced rule stated, including the two the first review found unstated (pageview rows, package set) and the five hidden folders (unchanged by sections 14 and 15: h_twin replaced h_lowicc and was then rebuilt in place, so the instruction did not change); cap 120 s vs at most 2.42 s measured (section 8); the 1e-9 tolerance is for exact ratios of integers
G16 PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - pinned digest and exact pins in both images; fixed seeds and gzip mtime 0 (a rerun of gen_data.py is byte-identical, also after the exact-twin rebuild: all 58 package files hash the same on two runs, section 4; the 17 SHA256SUMS lines of the unchanged sets kept their hashes); SHA256SUMS (21 files) checked by the grader; the grader has no randomness (the resource metrics are logged only); in run full2 oracle 10 of 10 and force-build 1.0
G17 PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - separate verifier; tests/ only in the verifier image; environment/Dockerfile copies only app/; in run full2 lock ok in all 23 trials (section 11; 14 of the 23 logs are shipped under traces/)
G18 PASS - harbor lint [] and check_task OK (section-15 pass); (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) Daytona built both images, force-build 1.0 in run full2
G19 PASS - kit copied into tests/; nothing depends on another task's folder
G20 PASS (plan) - README row text in section 11; the row itself is in the repository's README.md
G21 PASS (plan) - limitations in section 11, including the design-effect shortcuts (pageview-only rules closed by the twin identity; rules that use the clicks are the residual, and a constant-free user-level click-dispersion estimate scores 1, limitation 9(c)), h_null's double role, h_twin sharing h_null's users, the sizes exercised, the package size (32.0 MB) and the kit's clean-up
G22 PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - canonical 1 locally; Daytona oracle 10 of 10 = 1.0 in run full2
G23 PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - nop 0 locally; Daytona nop 0.0 in run full2
G24 PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - nine attempts 0 locally (icc_tuned and kish_tuned re-tuned to the section-15 sweep: rho 0.170, K^1.22); all nine are listed by tools/proof_matrix.py; on Daytona each scores 0.0 in run full2
G25 PASS (run, recorded: validation/ab-test-reanalysis/PROOF_RESULTS_full2.md) - alt and alt_cr1 1 locally; on Daytona alt 1.0 and alt_cr1 1.0 in run full2
G26 PASS (plan) - proof-run traces shipped (one trial per variant of run full2 is in validation/ab-test-reanalysis/traces/)
G27 PASS (plan) - no keys or our machines needed; no network_mode set; graders need no network
G28 PASS - valuable work; scoring checks the readout the plan defines; failure = a missed plan violation or a wrong variance method
G29 PASS - the spread of design effects (5.2 to 23) and of intra-user correlation on one set of users and pageviews (h_null rho_eff 0.42-0.46, h_twin 0.08-0.09) makes the plan's own rule (users, not pageviews, are the unit) decide the score: no constant multiple, no one-rho correction and no multiplier computed from the pageview counts passes, the last by the twin identity (FACT, section 15), not only by a sweep; h_twin is not there to lower the pass rate: each of the plan's three methods passes it with the same margin as the other sets (worst valid error 0.099); the SRM and bot sets test rules the plan states
G30 PASS (plan) - delivery is this GitHub repository, a step after the build
Result: PASS (implementation); no FAIL; one question (G12 override, section 16), since ruled: no override; the (run) items are proven by the Daytona run full2 of the final package (section 11; the package changed again in section 15, and section 16 changed no package file)
```
After this record: Daytona run `full2` (section 11) gave the expected result on every row, so the "(run)" items now
pass by a recorded run.

## 11. README row, limitations, open issues
README row (proposed): capability = data analysis / experiment statistics (auditing an analysis against its plan);
objective = fix an A/B readout pipeline that declared a false win so it follows the analysis plan on any export, and
regenerate the readout; success check = the agent's command on five hidden experiments plus the visible readout:
counts exact, CTR and diff within 1e-9, SRM p within 1%, flag and decision exact, CI bounds within 0.25 half-widths of a
delta-method reference (bootstrap and CR1 accepted); validation = local matrix above, and the Daytona proof matrix run
`full2` (Harbor 0.25.0): ALL AS EXPECTED, 14 of 14 rows (table below; `submission/validation/ab-test-reanalysis/PROOF_RESULTS_full2.md`);
known limit = design-effect corrections built from the pageview counts alone (one rho, Kish's factor, tail shares,
any formula of that form) fail because h_twin has h_null's exact users and pageviews but needs an interval half as
wide; a design effect estimated from the users' own click dispersion passes: the variance of per-user CTR among users
with 18 to 26 or more pageviews over its binomial value, with no constant (k = 20: worst 0.203 half-widths), and the
textbook ANOVA-ICC design effect (worst 0.064); both are user-level estimates outside the plan's list of three
methods, and the grader, which checks the readout, accepts them (limitation 9(c)).

Daytona proof matrix, run `full2` (filled in 2026-10-29, 03:58 MST; FACT from
`submission/validation/ab-test-reanalysis/PROOF_RESULTS_full2.md` and `run_full2.log`, Mac clock MST; failing sets
from each trial's `verifier/reward.json`, `<set>_ok` = 0, read in the job folders, which are git-ignored and not
shipped; one trial per row ships under `submission/validation/ab-test-reanalysis/traces/<variant>/`, and its
`verifier/reward.json` shows the same failing sets):

| Variant | Command | Expected | Rewards | Failing sets on Daytona | Result |
|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | 10 x 1.0 | none | PASS |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | 1.0 | none | PASS |
| alt_cr1 | `-a oracle --ae SOLUTION=alt_cr1` | 1 | 1.0 | none | PASS |
| nop | `-a nop` | 0 | 0.0 | all six | PASS |
| constant_inflation | `-a oracle --ae SOLUTION=constant_inflation` | 0 | 0.0 | h_null | PASS |
| fix_bots_only | `-a oracle --ae SOLUTION=fix_bots_only` | 0 | 0.0 | all six | PASS |
| fix_ci_only | `-a oracle --ae SOLUTION=fix_ci_only` | 0 | 0.0 | all six | PASS |
| fix_visible_result_only | `-a oracle --ae SOLUTION=fix_visible_result_only` | 0 | 0.0 | the five hidden sets | PASS |
| hardcode_no_ship | `-a oracle --ae SOLUTION=hardcode_no_ship` | 0 | 0.0 | h_pos, h_srm, h_twin | PASS |
| icc_tuned | `-a oracle --ae SOLUTION=icc_tuned` | 0 | 0.0 | h_null, h_twin | PASS |
| kish_tuned | `-a oracle --ae SOLUTION=kish_tuned` | 0 | 0.0 | h_null, h_twin | PASS |
| mean_of_ratios | `-a oracle --ae SOLUTION=mean_of_ratios` | 0 | 0.0 | all six | PASS |
| no_srm_gate | `-a oracle --ae SOLUTION=no_srm_gate` | 0 | 0.0 | h_srm | PASS |
| force-build | `-a oracle --force-build` | 1 | 1.0 | none | PASS |

Note on run `full2`: the run went from 03:38:19 (canonical) to 03:50:35 MST (force-build started;
`run_full2.log`), and its result files carry 03:51:18 MST. It covers the current package: `tests/SHA256SUMS` and
`tests/expected/h_twin.json` carry 02:26:33 MST (`ls -lT` at 03:55 MST; output not saved), and section 16
changed no package file (INFERENCE: those file times are section 15's exact-twin rebuild, which section 9 says was
matrix-checked at 02:42 MST). Run `full1` (`PROOF_RESULTS_full1.md`, 02:05:59 MST) ran on the earlier
`h_twin` and is superseded. Counted from the table: nop and 9 attempts score 0.0, 10 zero rows in all. The failing
sets match section 9's local matrix row for row. Section 9's
checks were read in every one of the 23 trials (`verifier/test-stdout.txt`, `agent/oracle.txt`): `SHA256SUMS: 21 files
verified`, `lock ok`, and `verifier resources: ... res_cgroup_cpus=1, res_cgroup_mem_mib=2048` in all 23 (the 14
shipped `traces/*/verifier/test-stdout.txt` files show the same three lines); no
`cp: cannot stat` in any of the 22 `agent/oracle.txt` files (the nop trial has none); the largest `<set>_run_seconds` is 2.326 s (cap 120 s). So Daytona applied 1 CPU and 2,048 MiB
to the verifier sandbox (FACT, this run), which resolves the UNVERIFIED in limitation 6 and section 12 finding 3; the
instruction wording was not changed (no package file changes here). The gate record's "(run)" items (G4, G12, G13,
G16, G17, G18, G22 to G25) now PASS by this recorded run. The verdicts in section 10 are the ones written before the
run; its reasons were reworded later for outside readers, its (run) items now cite this run, and its G12 and Result
lines note the G12 ruling. We ruled on the G12 override question in section 16: no override, G12 PASS.

Limitations and open issues (honest):
1. Synthetic data (the repository README says so, under "Known limitations"). Effects on the positive sets are large (true lift 10%, 11% and 9% on
   h_twin, realised 12.2% there) because a 34,000 to 40,000-user experiment with a design effect of 5 to 7 cannot
   detect smaller ones with margin.
2. Possibly easy: the PM note points at the size mismatch and the plan names the user-level rule (the original
   design's "Main risk").
3. The band (0.25 half-widths) is a choice inside the measured window [0.21, 0.281] (upper edge = half of
   `fix_bots_only`'s smallest miss, 0.5630 on h_twin; 0.282 with the section-14 h_twin, 0.293 with h_lowicc, 0.297
   before); a CI method outside the three the
   plan names (for example a Fieller interval) is likely, not proven, to fall inside it.
4. h_null's design effect of 23 comes from heavy-tailed engagement: users reach the 600-pageview cap and the top 10
   users of an arm carry 32% (A) and 49% (B) of the sum of squared residuals (FACT, measured on the h_null files; h_pos:
   13% and 17%). Plausible for a pageview metric with power users, but at the high end (FACT, pandas on h_null:
   rho 0.42 and sigma 1.3 in gen_data.py; 5 of 37,460 human users at the 600 cap, 21.7% with no counted pageview, mean
   7.95, 99th percentile 79); on such data the delta method and the bootstrap still agree within 0.104 half-widths
   (section 5). h_null is also the main set that rejects the constant-inflation shortcut and per-user-CTR (Welch)
   intervals, and with its pageview twin h_twin it carries the defence against pageview-only multipliers (limitation 9:
   h_null rejects every rho below 0.245, h_twin every rho above 0.140), so do not soften either set without re-running
   `calibration_study.py` and `twin_identity.py`.
5. Timings are Mac timings; the 120 s cap and the 950 s verifier timeout rest on a wide margin (UNVERIFIED on Daytona
   when written; in run `full2` the largest `<set>_run_seconds` was 2.326 s, see above).
6. An agent bootstrap that builds one 5,000 x 20,000 int64 index array per arm needs about 1.6 GB; it would behave the
   same on /app/data in the agent's own 2 GiB container, so the agent can see it. FACT (the Harbor docs,
   https://docs.harborframework.com/tasks/separate-verifier): a separate verifier with no `[verifier.environment]` gets a fresh copy of
   `[environment]`. UNVERIFIED when written: that Daytona applies cpus = 1 and memory_mb = 2048 to the verifier
   sandbox; `grade.py` now logs the cgroup limits so the proof run answers it (run `full2` did: 1 CPU and 2,048 MiB,
   see above). The instruction still only says "plan for one CPU and 2 GiB".
7. Second reader (asked for by the original design): done by the first review, which wrote the expected checks from
   instruction.md and environment/ before opening tests/; it found two unstated rules, both now stated (section 12).
8. Both images need PyPI at build time (pip install of pinned wheels).
9. Design-effect shortcuts (the pageview-level interval times a multiplier that never uses the users' click
   variance). History: with four hidden sets one rho in "x sqrt(1 + rho (m_w - 1))" passed (rho 0.245 to 0.290;
   first review, section 12); section 13 added h_lowicc and closed that one-rho family only; the second review then showed that
   multipliers from the pageview counts alone still passed (Kish's K^1.5 with no constant, c CV^2 with c fitted on the
   visible set; section 14); section 14 replaced h_lowicc by h_twin, a new draw of h_null's generator, and no
   single-feature form passed, but the third review showed that h_twin matched h_null only in distribution: 8 of 10
   pageview-only rules with 2 to 4 parameters fitted on the hidden readouts (exponents up to +/-86 on tail moments such
   as p95/mean, p99.9/mean, top-10% share, kurtosis) scored 1, because they fitted the sampling differences between
   the two draws. Now (section 15) h_twin is h_null's exact users and pageview rows with only the clicks redrawn.
   FACT (auth/twin_identity.out.md): `assignments.csv` and `users.csv` byte-identical, the same user_id and ts on all
   322,363 pageview rows, every counted user's pageview count equal in each arm, all 16 features of the sweep
   bit-identical. So any width or multiplier computed from the pageview data takes the same value on h_null and
   h_twin, whose reference half-widths are 0.010831 and 0.005265. FACT (arithmetic, section 15): such a rule misses one
   of the two sets by at least 0.3458 half-widths if its width uses the pageview data only, 0.3544 if it is the
   pageview-level interval times one multiplier, and 0.3404 if each arm's pageview-level variance R(1-R)/V gets its
   own multiplier M_A, M_B >= 0; all above the 0.25 band for every rule of these three forms, whatever the formula of
   its width or multiplier, its number of parameters or where they were fitted, hidden readouts included (other
   variance bases with per-arm multipliers: R/V 0.3396, (1-R)/V 0.3424, pooled R(1-R)/V 0.3548, section 16). This
   covers every rule the third review found for pageview counts; rules that use the clicks in another way are not of these forms. The sweeps agree
   (no rho, no constant and none of 48 forms passes; best worst errors 0.356, 0.354, 0.354; section 5), and
   `icc_tuned` and `kish_tuned`, tuned on all six sets, score 0 through the grader. Residual, honest: (a) the defence
   still rests on one pair: softening h_null's tail or correlation, or raising h_twin's correlation, shrinks the
   2.057 ratio, so re-run `calibration_study.py` and `twin_identity.py` after any change to either; (b) closed: the
   sampling differences between two draws no longer exist for the pageview counts; (c) a
   rho or design effect estimated from each set's own per-user clicks scores 1 and is accepted, stated plainly (FACT,
   section 16 and the click-rule probes of section 9, section-15 data, through the grader): each arm's
   pageview-level variance times D, D = variance of per-user CTR among users with >= k pageviews over the mean of
   R(1-R)/v for those users, with NO constant and exponent 1, scores 1 for every k from 18 to 26 (k = 20: worst 0.203,
   h_null) and 0 for k = 5 to 17 and 27 to 40, the range tried (k = 10: 0.404); it needs nothing an agent cannot see. The third review's
   visible-fitted forms also still score 1 (zero-click share over its binomial value, users >= 5 views, squared:
   0.230; CTR variance over binomial, users >= 10 views, to the power 1.5: 0.188), and so does the textbook estimator,
   a one-way ANOVA ICC of the clicks within users times Kish's 1 + rho (m_w - 1) (0.064). Why accepted: these are
   user-level estimates of the users' own click correlation, which is what the plan's unit rule is about; they need
   every user's clicks and pageviews after the plan's filters and the bot, SRM and decision fixes. Honest limits: none
   is one of the plan's three methods (EXPERIMENT.md section 5 lists three and says "Any one of these is acceptable";
   it does not forbid others, and the grader checks the readout, G11); D is crude and model-dependent: it lands in the
   band only for k = 18 to 26 because this generator draws each user's click propensity independently of their
   pageviews with one correlation per set (section 13), so it would be off where the correlation changes with
   engagement. Closing it would need that kind of data redesign (the estimator follows the generator's own rho, so no
   seed search does it); not done, and the G12 override question was ruled in section 16 (no override). (d) rules from
   arm-level click aggregates, with no per-user data in the multiplier, are outside the proof because the clicks
   differ between the pair. FACT (`click_rule_probes.out.md`): h_twin / h_null ratios are abs(diff) 3.941 (0.00338 to
   0.01334), abs(relative lift) 4.052 (0.0301 to 0.1219), R_A 0.9725, R_B 1.1248, so a rule through the diff or the
   lift can reach the needed 2.06-fold change of width with a small exponent; it must then also fit the other four
   readouts. Through the grader: c abs(diff)^4.03 abs(rel)^-4.61 (c and both exponents tuned on the six readouts,
   the fourth review's rule) scores 1 (worst 0.238), and so does c R_A^9.9 R_B^-7.5 with c fitted on the visible
   set and only the two exponents tuned on the hidden readouts (worst 0.158; 11 of 36 pairs of 9 aggregates pass with
   two tuned exponents in -16 to 16). With one tuned exponent nothing passes (best 0.341 over the 9 aggregates,
   exponent -12 to 12, c free or on visible). So two hidden-tuned parameters suffice and one did not in this sweep;
   exponents of 4 to 16 on CTRs or on the diff are not something any agent picks without the hidden readouts, so no
   data change; (e) only for (d): a rule fitted on the hidden readouts themselves cannot be excluded by any finite
   grader, but it needs data no agent sees.
10. Sizes: the instruction promises up to 50,000 users and 500,000 pageview rows per hidden set; the sets have 34,000
    to 40,000 users and 322,363 to 344,187 rows (section 4), so the top of the promise is not exercised (lenient, not
    unfair). The package is 32.0 MB, 2.0 MB over our own size target of "about 30 MB" (set in our build notes, not
    shipped; deviation 10).
11. Same-second pageviews: every set holds a few rows with the same user and instant (section 4). Until the first
    review's fixes (section 12) the plan did not say they count separately, and a pageview de-duplication scored 0 (section 9 probes); EXPERIMENT.md
    section 4 now says it. No data, hash or expected file changed.
12. Shared-kit behaviour not stated in the instruction (the kit is shared by all five tasks, so this is a cross-task
    item): the copy of /app loses `conftest.py`, `sitecustomize`/`usercustomize` files, `*.pth`, `*.pyc` and
    `__pycache__`; a copy over 2 GiB or 200,000 entries scores 0; runs get `OMP_NUM_THREADS=1`, `PYTHONHASHSEED=0`, an
    emptied HOME, a fixed PATH, 1 GiB per written file, 512 processes plus threads and a 64 MiB output cap
    (FACT, `tests/kit.py` lines 46-56 and 416-478). Harmless for any sane solution.
13. h_twin shares h_null's users (section 15): the same user ids, arms, bots, assignment times and pageview rows with
    other clicks, so two of the five hidden experiments are one traffic sample with two click outcomes. That is
    artificial, but no agent sees a hidden set, the grader stages each under a neutral name (`exp1`..`exp5`), and a
    command that is right on any export is right on both. `SHA256SUMS` therefore lists two hash values twice (the
    `assignments` and `users` files of h_null and h_twin); `shasum -c` and the grader check each line on its own
    (FACT: `tests/grade.py` lines 33-46 read the file line by line and hash each listed path; the local canonical run
    logged `SHA256SUMS: 21 files verified` in its git-ignored `grade.log`, and so does the shipped Daytona trace
    `submission/validation/ab-test-reanalysis/traces/canonical/verifier/test-stdout.txt` line 3).
14. Not addressed (the third review's finding F3): the instruction says `python -m` while the grader runs
    `python3 -m` (the same interpreter in the image).

## 12. Review history; the first review (2026-10-28)
Sections 12 to 16 are dated records of the reviews after the build and what each changed; sections 1 to 11 already
describe the result. Each review was an independent check of the task as it stood; we checked the findings against
the files and by runs. Each was fixed, recorded as a limitation or rejected with a reason, except the third review's
finding F3, which was not addressed (limitation 14).

| Section | Date | Step | Main finding | What changed |
|---|---|---|---|---|
| 12 | 2026-10-28 | first review | no FAIL; seven items, among them two unstated rules and a one-rho ICC shortcut | EXPERIMENT.md section 4 and the instruction state the two rules; limitations 4, 9, 10 and 12 |
| 13 | 2026-10-28 | ICC fix (follows item 4 of the first review) | one rho in the ICC multiplier passed every readout | hidden set h_lowicc added; attempt `icc_tuned` |
| 14 | 2026-10-28 | second review (of section 13) | multipliers from the pageview counts alone still passed | h_lowicc replaced by h_twin, a new draw of h_null's generator; attempt `kish_tuned` |
| 15 | 2026-10-29 | third review (of section 14) | h_twin matched h_null only in distribution; hidden-tuned tail-moment rules passed | h_twin rebuilt from h_null's exact users and pageview rows, only the clicks redrawn; `twin_identity.py` |
| 16 | 2026-10-29 | fourth review (of section 15) | a constant-free user-level click-dispersion rule scores 1 | measured through the grader and accepted (G12 PASS, no override); no package file changed |

The first review found no FAIL and seven items. We checked each against the files and by runs:

| # | Finding | Our check (FACT) | Action |
|---|---|---|---|
| 1 | exact-repeat pageview rows must not be removed, but the plan never says so | gen_data.py has no pageview duplication (same-second collisions only); counts in section 4; `dedupe_pv` and `dedupe_pv_instant` score 0 (section 9) | applied, widened: EXPERIMENT.md section 4 now says every row is one pageview, identical or same-instant rows included |
| 2 | the grading image has only numpy, pandas, scipy (+ deps); plan 5c invites statsmodels | both Dockerfiles install the same six pins and nothing else | applied: one bullet in "How the result is checked"; the closing line is unchanged |
| 3 | "a machine with the same CPU and memory settings as yours" is not observed | the Harbor docs (https://docs.harborframework.com/tasks/separate-verifier) give it; whether Daytona applies it is unobserved | applied: the claim is removed (the instruction says "plan for one CPU and 2 GiB of memory"); `grade.py` logs the cgroup limits; the claim may be restored after the proof run (section 9) |
| 4 | a cluster-size-aware multiple with a tuned rho passes | reproduced: rho 0.25 and 0.27 give 1, rho 0.176 gives 0 (h_null) | recorded (limitation 9, README row, G12, G29); the data change is rejected: new data, hashes, expected files and calibration for a shortcut a blind agent cannot tune (superseded: section 13 added a set and closed it) |
| 5 | h_null carries two defences and is the least realistic set | reproduced: 600 max, 5 at cap, 21.7% zero, mean 7.95, p99 79 | applied: limitation 4 |
| 6 | "1 to 1.5%" repeated assignment rows; sizes promised vs exercised | measured 0.97% to 1.61% of users | applied: section 4 and limitation 10 |
| 7 | shared-kit clean-up and limits not in the instruction | kit behaviour as cited | recorded: limitation 12 (cross-task; the instruction is not changed) |

Also fixed: `fix_ci_only` was a `solve.sh` branch with no folder, so `tools/proof_matrix.py` (which lists
`solution/attempts/` entries) would not have run it; it now has a README-only folder.

## 13. ICC fix (2026-10-28): limitation 9 closed
Status (2026-10-28, after section 14): this section is the record of that pass. Its claim "closed" held only for the
one-rho family; section 14 found pageview-only multipliers that still passed and replaced h_lowicc by h_twin.
h_lowicc's files are no longer in the package; its numbers below and in `calibration_before_twin.out.md` are history.

Goal (a change to the hidden data to close a shortcut, which the original design allows): make
sure no single constant rho in "pageview CI x sqrt(1 + rho (m_w - 1)) per arm" passes every graded readout, while the
plan's three methods still pass everywhere inside the unchanged 0.25 band and every decision bound stays at least
0.35 half-widths from 0.

Why the shortcut worked (INFERENCE from gen_data.py's model): a user's clicks are Binomial(v_i, p_i) with p_i drawn
independently of v_i, so E[sum (c_i - R v_i)^2] = R(1-R) V (1 + rho (m_w - 1)) with m_w = sum(v^2)/sum(v). The ICC
formula is therefore the exact expected design effect of this generator; only rho differs between sets, and with four
hidden sets the effective rho ranged only from 0.176 (visible) to 0.42-0.46 (h_null), which a 0.25 band in
half-widths tolerates for rho 0.245 to 0.290.

Choice: add a set, do not replace one. Adding keeps the four original hidden sets, the visible set and their expected
files byte-identical (FACT below); replacing h_pos would have deleted original-design data for no gain in separation. Low, not
high, correlation: a click propensity with rho 0.06 (Beta, mean 0.12) is ordinary; rho near 0.8 would mean most users
never click and a few click almost always. INFERENCE (the formula above, ignoring the +1 term): a set at rho 0.06
against h_null's 0.44 leaves the best single rho about 0.40 half-widths off; a set at rho 0.6 to 0.8 against the visible
0.176 would leave only about 0.30 to 0.36. A low rho needs a larger m_w to keep the design effect above 5.5 (the
pageview-level attempt must still miss by at least 2 x band = 0.5, and 1 - 1/sqrt(DE) >= 0.5 needs DE >= 4), so h_lowicc
has heavier engagement (lognormal mean 20, sigma 1.15) and only 17,000 users, to keep the rows (312,625) and the gzip
size (2.6 MB) down. 16 candidate settings were simulated in a scratch script (not shipped; users 16,000 to 30,000, rho
0.06 to 0.08, lift 0.08 to 0.12); the kept one balances the design effect (5.82), the separation (0.40) and the size.

What changed (FACT, files):
- `auth/gen_data.py`: one new SETS entry, `h_lowicc` (role pos, seed base 6000, kept seed 6003 after 4 tries,
  DE range 5.5 to 8.0, margin 0.5 as for every set). Rerun: `SHA256SUMS` 17 earlier lines unchanged + 4 new (21 files);
  visible CSVs, `output/result.json` and the five earlier expected files match their earlier SHA-256 (9 of 9 OK). A
  second rerun after the calibration gave a byte-identical `SHA256SUMS` (`cmp`; 21 of 21 OK) and the same 10 hashes of
  the visible CSVs, `output/result.json` and the six expected files.
- `tests/hidden/h_lowicc/*.csv.gz` and `tests/expected/h_lowicc.json` (new); `tests/grade.py` (`HIDDEN` + docstring);
  `task.toml` (`verifier.timeout_sec` 750 -> 950, deviation 5); `instruction.md` ("five other experiment folders", "six
  readouts"; the closing line unchanged); `solution/solve.sh` and `solution/attempts/icc_tuned/stats.py` (new attempt).
- `auth/calibration_study.py`: the sixth set and the ICC sweep with two new checks; `auth/local_check.py`: the sixth set
  and `icc_tuned`. The earlier calibration record is kept as `auth/calibration_before_icc_fix.out.md`.
- `tests/kit.py`, `tests/test.sh`: re-synced by `tools/sync_kit.py` (unchanged content).

The sweep (FACT, `auth/calibration_study.out.md` "ICC shortcut sweep"; rho 0 to 1 in steps of 0.005, and 0.0001 for the
best rho; a set passes when both bound errors are <= 0.25 half-widths): see the table in section 5. With m = m_w no rho
passes all six readouts; at most 5 of 6 pass (rho 0.245 to 0.290, failing h_lowicc); the best rho is 0.145 (0.1453 on
the fine grid) with worst error 0.403 (h_null 0.403 too narrow, h_lowicc 0.401 too wide). With m = mean pageviews per
user no rho passes either (at most 4 of 6; best rho 0.705, worst error 0.494).

Results (FACT): `local_check.py` ALL AS EXPECTED with 12 variants (section 9): canonical, alt and alt_cr1 = 1 on all
six readouts; nop and all eight attempts = 0; `icc_tuned` (rho 0.145) fails h_null and h_lowicc by 0.40. The rho values
that scored 1 before (0.25, 0.27) now score 0 (h_lowicc 0.80, 0.87; section 9 probes). Calibration on six sets: all
seven checks PASS (section 5). `grader_probes.py` 24 of 24; `check_task.py` OK; `harbor lint` `[]`.

Open after this pass: the Daytona proof matrix had to be re-run for this task (the package changed; section 9
lists what it must show, then with 21 files, five hidden runs and eight attempts); run `full2` on the final package
did so (section 11).

## 14. Second review (2026-10-28): pageview-only shortcuts closed; h_lowicc replaced by h_twin
Status (2026-10-29, after section 15): this section is the record of that pass. Its h_twin was a new draw of h_null's
generator, a twin in distribution only, and the third review found hidden-tuned multi-parameter rules that still
passed; section 15 rebuilt h_twin from h_null's exact rows. The h_twin numbers below (seed 7008, DE 5.26, 3,163,123
bytes) are history.
Goal: check the five findings of the second review (of section 13), fix the right ones, reject wrong ones with
reasons, re-run the local checks. Under the quality gate a FAIL blocks (docs/QUALITY_GATE.md, "How the checks are
applied", item 3), and finding 1 made G12 a FAIL as the record stood (a shortcut that skips the user-level variance
scored 1).

| # | Finding (second review) | Check here (FACT unless marked) | Action |
|---|---|---|---|
| 1 HIGH | multipliers that use no click variance still get reward 1: pageview CI with each arm's variance x K^1.5 (K = mean(v^2)/mean(v)^2, no constant) or x c CV^2 (c fitted on the visible set); G12, G29 and limitation 9 say "closed" | reproduced through the real `tests/grade.py` (KIT_LOCAL; scratch harness, canonical files + one replaced `stats.py`), on the section-13 data: K^1.5 reward 1 (worst 0.183, h_lowicc); 2.884 CV^2 and 2.5 CV^2 reward 1; 2.0 and 3.3 CV^2 reward 0; K^1 (Kish's own factor) reward 0 (visible 0.285). Own sweep (16 features x 3 forms; scratch, `gen_data.simulate` at the kept seeds, checked against `tests/expected`): 21 of 48 forms passed, from 9 features (K, CV, K over v > 0, p99/mean, median/mean, Gini, top 1%, top 10%, share with no pageview); the review's windows match ours (for example c K^g, g 1.06 to 1.52; p99/mean 2.01 to 2.33) | applied, with a different data change than proposed (below): h_lowicc replaced by h_twin; G12, G29, limitation 9, README row rewritten; `kish_tuned` added; `icc_tuned` re-tuned |
| 2 LOW | limitation 9(c) ("two or more constants ... need the hidden data") is wrong as worded | true: a zero-constant form passed | applied: limitation 9 rewritten; its residual (e) now says only rules fitted on the hidden sets themselves are out of reach of any finite set |
| 3 LOW | the spread is a sample maximum; with other seeds 2 x spread can reach 0.24 | true by definition of a sample maximum; not re-run with the review's seeds | applied: section 5 calls it a sample maximum and quotes the review's 0.1208; new calibration check "\|mean\| + 4 SD < band" (0.155, PASS) |
| 4 LOW | package bytes 31,646,365, not 31,646,320 | accepted (the h_lowicc files are gone, so not re-measurable); re-measured after this pass: 32,060,388 bytes, 58 files | applied: section 2, deviation 10, limitation 10 |
| 5 LOW | `grader_probes.py` labels say 19586 (n_users A is 19612); the `dedupe_pv_instant` row is garbled | true | applied: labels now read the count from `expected/visible.json`, probes re-run 24 of 24; the row now names the five readouts |

None of the five findings was rejected. The review's proposed data change was not taken as proposed:
- It proposed ADDING a sixth hidden set (sigma 1.4, rho 0.08, mean 12, 15,000 users). Taken instead: REPLACING
  h_lowicc by an exact pageview twin of h_null. Reasons: (1) a twin makes the argument general, not per feature: every
  setting except the click correlation, the lift, the role and the seed is h_null's, including N, so any rule computed
  from the pageview counts sees two draws of one distribution while the reference half-widths differ by a factor of
  2.094 (INFERENCE; the FACT is the sweep); (2) five hidden folders stay, so `instruction.md` ("five other experiment
  folders", "six readouts"), the 950 s verifier timeout and the grader's flow stay as they were; adding would have
  needed six folders, seven readouts, about 1,100 s and about 1.3 to 3 MB more; (3) in scratch (`gen_data.simulate`,
  one or two seeds per setting, nothing written to the repo) every candidate tried, the review's included, closed all
  48 forms whether added or swapped in, but the margin varied: over the twins tried the best form's worst error was 0.25
  to 0.37, at the low end when the realised DE was near 7 or the twin had 20,000 users instead of 38,000; hence the
  full 38,000 users and the narrow DE range 5.2 to 5.8 in the seed search (kept seed: 0.349).
- Why replacing h_lowicc is allowed: section 13 chose "add, do not replace" to keep the original hidden sets
  byte-identical. h_lowicc was not original-design data (section 13 added it the same day), so that reason does not
  bind it; the four original hidden sets, the visible set and their expected files are still byte-identical (section 4).
- Trade-off, honest: the one-rho ICC margin drops from 0.403 (with h_lowicc) to 0.352, and a set with many pageviews per
  user (h_lowicc: mean 18) is no longer graded. The package grows by 0.4 MB (h_twin is 38,000 users, as h_null, against
  h_lowicc's 17,000). Choosing "add" instead (keep h_lowicc and add h_twin: ICC margin at least 0.403, since adding a
  set can only raise it) needs the instruction edit, a timeout of about 1,100 s and about 2.8 MB more; h_lowicc can be rebuilt exactly with
  this SETS entry in gen_data.py: `dict(name="h_lowicc", role="pos", seed=6000, n_users=17000, p_b=0.5,
  bot_frac=0.015, bot_pv=20, pv_mean=20.0, sigma=1.15, zero=0.08, ctr=0.120, rho=0.06, lift=0.090, pre=0.20, tie=0.6,
  dup=0.010, tz=TZ_COMMON, de=(5.5, 8.0))` (kept seed 6003; its four SHA-256 lines start f33721c1 (expected json),
  04fdf2fa, 3f30b6a3 and 457819be (assignments, pageviews, users)).

What changed (FACT, files):
- `auth/gen_data.py`: the h_lowicc entry replaced by h_twin (role pos, seed base 7000, kept 7008 after 9 tries, DE
  range 5.2 to 5.8, margin 0.5 as for every set; generator settings in section 4). Before regenerating, the h_lowicc
  files were moved out of `tests/` (to a scratch folder outside the repository) so `SHA256SUMS` lists only real files.
- `tests/hidden/h_twin/*.csv.gz` (3,163,123 bytes; 12.7 MB plain) and `tests/expected/h_twin.json` (new);
  `tests/hidden/h_lowicc/` and `tests/expected/h_lowicc.json` removed from the package; `tests/SHA256SUMS` (21 files);
  `tests/grade.py` (`HIDDEN` + docstring); `solution/solve.sh` and `solution/attempts/kish_tuned/stats.py` (new
  attempt, K^1.23); `solution/attempts/icc_tuned/stats.py` (RHO 0.145 -> 0.175, the new sweep's best).
  `instruction.md`, `task.toml`, the Dockerfiles and `environment/` are unchanged.
- `auth/calibration_study.py`: the pageview-only sweep and two new checks (pageview-only forms; |mean| + 4 SD); the
  h_lowicc-era record kept as `auth/calibration_before_twin.out.md`. `auth/local_check.py`: h_twin and `kish_tuned`.
  `auth/grader_probes.py`: labels. `tests/kit.py`, `tests/test.sh`: re-synced by `tools/sync_kit.py` (unchanged).

Results (FACT): calibration on six sets, all nine checks PASS (section 5: spread 0.1039, |mean| + 4 SD 0.155,
`fix_bots_only` smallest miss 0.5638, best constant 0.3537, best rho 0.352, best pageview-only form 0.349, margin
0.806); `local_check.py` ALL AS EXPECTED with 13 variants (section 9); the formulas that scored 1 now score 0 through
the grader (section 9 probes); `grader_probes.py` 24 of 24; `check_task.py` `OK ab-test-reanalysis`; `harbor lint`
`[]`; package 32,060,388 bytes, 58 files.

Open after this pass: the Daytona proof matrix had to be re-run for this task (section 9 lists what it must
show: 21 files, five hidden runs, nine attempts; run `full2` did, section 11); the size overrun (2.1 MB then, 2.0 MB
in the final package; deviation 10) and the replace-not-add choice above stand in the shipped package.

## 15. Third review (2026-10-29): h_twin rebuilt as h_null's exact pageview twin
Goal (a change to the hidden data to close a shortcut, which the original design allows): the third review (of
section 14) found that the section-14 h_twin was a twin of h_null only in distribution (its finding F1: 8
of 10 pageview-only rules with 2 to 4 parameters fitted on the hidden readouts scored 1, by fitting the sampling
differences of tail moments between the two draws, for example kurtosis A/B 149/279 on h_null against 231/149 on
h_twin), and that section 5's sentence "any pageview-only rule gives nearly the same multiplier on both" was false as
written. Gate impact (a FAIL blocks): G12 and G29 stated as closed what was only INFERENCE, and a rule that skips the
user-level variance scored 1 (with hidden-tuned parameters). Fix: make h_twin reuse h_null's exact per-user rows and
redraw only the clicks; keep every other set and the visible data byte-identical; then reword G12, G29, limitation 9
and section 5.

What changed (FACT, files):
- `auth/gen_data.py`: the h_twin entry is now `dict(name="h_twin", role="pos", twin_of="h_null", seed=7000, ctr=0.110,
  rho=0.09, lift=0.090, de=(5.2, 5.8))`; new `simulate_twin` re-makes h_null's kept realisation with `simulate(h_null,
  2006)` and redraws only the click propensities (Beta, mean 0.110, rho 0.09; B x 1.09; bots 0.003) and the clicks
  from `default_rng(seed)`; the text is built from h_null's own generator stream with h_null's offsets, so every file
  but the clicked column is h_null's. `search` stops if h_null's kept seed is not 2006 (`TWIN_BASE_SEED`). New seed
  condition for a twin, `twin_min_miss >= 0.33` (`TWIN_MIN_MISS`; the formula below); the report has a line per twin.
- `tests/hidden/h_twin/*.csv.gz` (3,137,672 bytes), `tests/expected/h_twin.json`, `tests/SHA256SUMS` regenerated by
  gen_data.py; `solution/attempts/icc_tuned/stats.py` (RHO 0.175 -> 0.170) and `kish_tuned/stats.py` (G 1.23 -> 1.22),
  the new sweep's best values. `instruction.md`, `task.toml`, `tests/grade.py`, the Dockerfiles, `environment/` and
  `solve.sh` are unchanged.
- `auth/calibration_study.py`: a tenth check (identical per-user pageview counts per arm on the pair, and the per-arm
  bound below > band) and the bound in the report; `auth/twin_identity.py` (new): the identity proof and the
  arithmetic, output `auth/twin_identity.out.md`. The section-14 calibration record is kept as
  `auth/calibration_before_exact_twin.out.md`.

Seed (FACT, gen_data.py search and a scratch scan of seeds 7000 to 7059, nothing written to the repo): with the old
conditions only (DE 5.2 to 5.8, lower bound >= 0.5 half-widths, SRM p >= 0.05) the first seed was 7001, whose guaranteed
miss was only 0.318 (its arm-A CTR fell to 0.1050 against h_null's 0.1126, which narrows the bracket below) and whose
realised lift was 16.7%. Over the 60 seeds the guaranteed miss ranged 0.255 to 0.371, mostly through the realised DE.
So the twin gets one more stated condition, guaranteed miss >= 0.33, like section 14's narrow DE range; the kept seed is
7018 (19 tries): DE 5.24, lower bound +1.53 half-widths, realised lift 12.2%, guaranteed miss 0.3404.

Byte-identity of everything else (FACT, SHA-256 of all 58 package files before and after, and two generator runs):
only 5 package files changed (`tests/SHA256SUMS`, `tests/expected/h_twin.json` and the three h_twin gzip files; then the
two attempt files above, by hand), so the visible CSVs, `output/result.json`, the four other hidden sets and their
expected files kept their hashes; `diff` of the old and new `SHA256SUMS`: the 4 h_twin lines changed, the 17 others
identical; a second gen_data.py run gave the same SHA-256 for all 58 package files and a byte-identical `SHA256SUMS`
and `generation_report.out.md` (`cmp`); `shasum -a 256 -c tests/SHA256SUMS` 21 of 21 OK. h_twin's `assignments.csv.gz`
and `users.csv.gz` have h_null's hashes (fc44d709..., 01766ac7...), on purpose (limitation 13); the grader checks by
path and the local canonical run logged `SHA256SUMS: 21 files verified`.

Identity proof (FACT, `auth/twin_identity.out.md`, stdlib loader of its own, run 2026-10-29): `assignments.csv`
(38,441 rows) and `users.csv` (38,000 rows) byte-identical, gzip and plain; `pageviews.csv` has the same header and
322,363 rows in the same order with the same `user_id` and `ts` text on every row, and `clicked` differs on 62,934 rows.
With the plan's population rules the counted users are the same 37,460 with the same arms, and every user's counted
pageviews are equal: per arm (A / B) 18,648 / 18,812 users, 147,296 / 150,416 pageviews, sum v^2 6,776,696 /
8,389,586, m_w 46.0073 / 55.7759, K 5.8246 / 6.9757, max 600 / 600, p99 78 / 79, users with no pageview 4,050 / 4,081
on both sets; the count vectors are `np.array_equal` per arm and all 16 features of the sweep are bit-identical. Clicks
differ: A 16,578 (h_null) against 16,122 (h_twin), B 16,420 against 18,470. So any function of the pageview data
(counts per user, per arm, their timestamps, the users' assignment rows) takes the same value on the two sets.

Arithmetic (FACT, from `tests/expected/h_null.json` and `h_twin.json`; b = 0.25 is the band). With the exact diff,
both bound errors of a half-width w are |w - H| / H, and a set passes only if (1 - b) H <= w <= (1 + b) H.
- Reference half-widths: H_null = 0.010831, H_twin = 0.005265, ratio r = 2.0572. Pageview-level half-widths 0.002256 and
  0.002301, so DE = 23.054 and 5.237, sqrt(DE) 4.8014 and 2.2885. Per arm, the multiplier the pageview-level variance
  needs to equal the delta variance: h_null 19.955 (A) / 26.304 (B), h_twin 4.542 / 5.879, on the same pageview counts.
- (a) A width from the pageview data alone is one number w on both sets. Both pass only if (1 + b) / (1 - b) = 1.6667
  >= r = 2.0572, which is false; the best common w = 2 H_null H_twin / (H_null + H_twin) misses both by (r - 1) / (r + 1)
  = 1.0572 / 3.0572 = 0.3458 half-widths.
- (b) The pageview-level interval times one common multiplier sqrt(M) (M computed from the pageview data, so equal on
  both): the needed sqrt(M) are 4.8014 and 2.2885, ratio 2.0981; minimum miss 1.0981 / 3.0981 = 0.3544.
- (c) Each arm's pageview-level variance R(1-R)/V times its own M_A, M_B >= 0 computed from the pageview data (equal on
  both sets; this is the form of every rule the third review found, per-arm constants included): V is equal, so for every such
  pair the twin / null ratio of the widths lies between sqrt(q_lo) and sqrt(q_hi), q = R(1-R) twin / R(1-R) null per arm
  = 0.9759 (A), 1.1076 (B). Both pass only if (1 + b) / (1 - b) >= sqrt(0.9759) x 2.0572 = 0.9879 x 2.0572 = 2.0322,
  false; minimum miss (2.0322 - 1) / (2.0322 + 1) = 0.3404 half-widths, reached only with arm B's multiplier near 0; a
  brute-force grid of 1,202 x 1,202 values of M_A, M_B (0 and 0.01 to 1000) gives 0.3404, and 0.3420 with both M >= 1.
- A wrong centre only adds to one of the two bound errors, so these are lower bounds for every rule of these three
  forms, whatever the formula of its width or multiplier, its number of parameters or its fitting data. A rule that
  uses the clicks in another way (for example arm B's variance proportional to R_B^-12) is not of these forms; such
  rules are limitation 9(c) and (d). The same bracket with other per-arm variance bases (section 16, FACT,
  `click_rule_probes.out.md` table 3, arithmetic and a 1,202 x 1,202 grid): R/V, q 0.9725 / 1.1248, bound 0.3396;
  (1-R)/V, q 1.0035 / 0.9847, 0.3424; pooled R(1-R)/V, q 1.0420 in both arms, 0.3548; all above 0.25. The ICC formula 1 + rho (m_w - 1) and every sweep form of section 5
  are cases of (c); on the section-14 probe formulas the h_twin errors are now 0.071 to 0.842 (arithmetic with
  `calibration_study.mult_err` on the committed data; each fails h_null or h_twin).

Checks asked (FACT): decision bound +1.534 half-widths from 0 (>= 0.35; the search asks >= 0.5); SRM p 0.397, not
flagged (h_null's, the same arms); `fix_bots_only` misses h_twin by 0.5630 (>= 2 x band = 0.50; local_check FAIL, ci
0.56); the three valid methods pass every set inside the band: delta and CR1 0.0000 on all six sets, bootstrap B = 2,000
worst 0.1039 (h_null; h_twin 0.0987), B = 5,000 worst 0.0593, |mean| + 4 SD 0.1776 (calibration_study.out.md, 10 of 10
checks PASS), and through the grader alt (bootstrap, 5,000 resamples, its fixed seed 20260914) has worst errors 0.009
to 0.024 per set (h_twin 0.012) and alt_cr1 0.000 (`local_results.json`).

Results (FACT): `calibration_study.py` 10 of 10 checks PASS (section 5); `twin_identity.py` 5 of 5 PASS;
`local_check.py` ALL AS EXPECTED with 13 variants (canonical, alt, alt_cr1 = 1 on all six readouts; nop and the nine
attempts = 0, section 9); `grader_probes.py` 24 of 24 as expected; `python tools/sync_kit.py` synced the five tasks
(`tests/kit.py` and `tests/test.sh` equal `base/verifier_kit/`, `cmp`, in every task); `check_task.py` printed
`OK ab-test-reanalysis`; `harbor lint tasks/ab-test-reanalysis --json` printed `[]`; package 32,035,105 bytes, 58
files, no `__pycache__`, `.pyc` or `.DS_Store`.

Wording changed: section 5's twin paragraph (INFERENCE -> FACT), G12, G29 (and G6, G13, G15, G16, G18, G21, G24, the
header line and the result line of the gate record), limitation 9 (rewritten; the third review's finding F2, its click-dispersion proxies, kept
as 9(c), a legitimate user-level ICC estimate; "a rule fitted on the hidden readouts cannot be excluded by any finite
grader" kept only for rules that use the clicks, 9(d) and 9(e), since the pageview-only family no longer needs it),
limitations 1, 3, 4, 10, new 13 and 14, the README row, sections 2, 3 (deviation 10), 4, 7, 8 and 9.

Open after this pass: the Daytona proof matrix had to be re-run (the package changed; section 9 lists what it must
show: 21 files, five hidden runs, nine attempts; run `full2` did, section 11); the 2.0 MB size overrun (deviation 10);
the third review's finding F3 (`python -m` in the instruction against `python3 -m` in the grader) was not addressed
(limitation 14).

## 16. Fourth review (2026-10-29): rules that use the clicks measured; wording fixed
Goal: check the four findings of the fourth review (of section 15), fix the right ones, reject wrong ones with
reasons, re-run the local checks. Under the quality gate a FAIL blocks.

What was run (FACT): a new authoring script, `auth/click_rule_probes.py` (output `auth/click_rule_probes.out.md`,
107.2 s by its own timer). It extracts the per-user clicks and views of all six sets with the canonical solution's own
code (counts equal `tests/expected/` on every set and arm; the delta method from them matches the reference
half-widths to 4.4e-16), evaluates rules fast (with the exact diff a bound error is |w / H - 1|), repeats the
section-15 bracket for other variance bases, and runs 11 rules through the real grader the `local_check.py` way
(environment/app + canonical files + the probe `stats.py`, visible readout regenerated, /app copy rules,
`tests/grade.py` in KIT_LOCAL mode; run dirs in the git-ignored `.localruns/probes/`). The rows are in section 9
("Click-rule probes").

| # | Finding (fourth review) | Check here (FACT, `click_rule_probes.out.md` unless marked) | Action |
|---|---|---|---|
| 1 MEDIUM | a constant-free per-user click-dispersion rule scores 1 and needs no hidden data (each arm's pageview-level variance x variance of per-user CTR among users with >= 20 pageviews / mean of R(1-R)/v over them); 9(c) cites only section-14 data and a visible-fitted constant; the README row's known limit omits it | true. Through the grader: k = 20 reward 1 (worst 0.203, h_null), k = 18 and 26 reward 1 (0.245, 0.246), k = 17 and 27 reward 0 (h_null 0.260, h_pos 0.273), k = 10 reward 0 (h_null 0.404); fast evaluator: exactly k = 18 to 26 pass (k 5 to 40 tried); best constant at k = 20 is 1.088 on the variance (1.043 on the width). The two visible-fitted forms of 9(c) still score 1 on the section-15 data (0.230 and 0.188). New: the textbook estimator of the same quantity, a one-way ANOVA ICC of the clicks within users times Kish's 1 + rho (m_w - 1), no constant, reward 1, worst 0.064 | applied: accepted and stated plainly in limitation 9(c), G11, G12, G21 and the README row; evidence moved to the section-15 data; no data change (decision below) |
| 2 LOW | click-aggregate rules with no pageview data score 1 with three hidden-tuned parameters; 9(d)'s INFERENCE (CTR differences of 3% and 12% turned into a 2-fold width) names the wrong mechanism; proposed text: "three hidden-tuned parameters suffice and nothing smaller passes" | mechanism: true; the pair's ratios are abs(diff) 3.941, abs(rel) 4.052, R_A 0.9725, R_B 1.1248. The review's c abs(diff)^4.03 abs(rel)^-4.61 (c tuned too) reward 1 through the grader (worst 0.238). "Nothing smaller passes": false. With c fitted on the visible set and two exponents tuned on the hidden readouts, 11 of 36 pairs of 9 arm-level aggregates pass in the fast evaluator (exponents -16 to 16, step 0.1); c R_A^9.9 R_B^-7.5 reward 1 through the grader (worst 0.158). With one tuned exponent none of the 9 aggregates passes (exponent -12 to 12, c free or on visible; best 0.341). Scope: the review searched 465 combinations including per-user features; this sweep covers the 9 arm-level aggregates only | applied with a correction: limitation 9(d) now states these FACTs ("two hidden-tuned parameters suffice; one did not in this sweep"); not blind-reachable (exponents of 4 to 16), so no data change |
| 3 LOW | section 5 gives the calibration run as 02:29:06 to 02:42:04 MST and 826.9 s; that range is 778 s | true: 12 min 58 s = 778 s; `calibration_study.out.md` line 3 says 826.9 s; `calibration_study.out.md` and `calibration.json` were modified at 02:42:02 MST, `calibration_study.py` at 02:28:07 (`stat`) | applied: the clock range is dropped; the duration (the script's own timer) and the output time (`stat`) are kept; no start time is back-computed |
| 4 LOW | "whatever the formula, the number of parameters or where they were fitted" holds only for the three stated forms (width from the pageview data; one common multiplier; per-arm M_A, M_B x R(1-R)/V) | true: a click-using variance such as arm B's proportional to R_B^-12 is not of these forms. The bracket with other bases (arithmetic, then a 1,202 x 1,202 grid of M_A, M_B in {0, 0.01 .. 1000}): R/V 0.3396 (grid 0.3399), (1-R)/V 0.3424, pooled R(1-R)/V 0.3548; all above 0.25 | applied: "of these three forms" in sections 5 and 15, G12 and limitation 9; the three bases added to section 15 |

Decision on finding 1 (G12): PASS. The click-dispersion rule is not a shortcut that skips the work. It needs
every user's clicks and pageviews after the plan's population rules, it needs the bot, SRM and decision fixes, and it
estimates the users' own click correlation, the quantity the plan's unit rule is about; the textbook estimator of that
quantity (ANOVA ICC x Kish) is accurate to 0.064 half-widths here. Stated as plainly: it is not one of the plan's three
methods (the plan does not forbid others, and the grader checks the readout, not the method: G11); it is crude, since
it passes only for k = 18 to 26; and it works because this generator gives each set one click correlation,
independent of the pageviews (section 13). INFERENCE (practical risk): an agent that has per-user clicks and views in
hand is one line from the delta method, which the plan names first, so few agents will pick this rule.
**Override question (whether to overrule our PASS and count this rule as a shortcut; a FAIL would block under docs/QUALITY_GATE.md, "How the checks are applied", item 3):** if
"any interval method not on the plan's list" is to count as a shortcut, G12 is FAIL for this rule and implementation
is blocked until the data are redesigned. A seed search cannot
close it, because the estimator follows the generator's own rho; a set would need a click correlation that changes
with engagement (heavy users' CTR spread no longer tracking the design effect), which changes the generator of
original-design data and the numbers of sections 4, 5 and 9. Not done here.

**Our ruling (2026-10-29): no override; G12 stays PASS.** The plan (`environment/app/EXPERIMENT.md` lines 33-38) lists three acceptable methods but does not forbid others, and `instruction.md` lines 22-26 state the grading rule as an outcome (each CI bound within 0.25 reference half-widths of the reference bound). A user-level click-dispersion or one-way ANOVA ICC x Kish interval does the user-level work and lands inside that stated tolerance, so scoring it 1 is what G11 (check the requested outcome) and G13 (accept materially different valid solutions) require. No package file changes; the Daytona proof matrix run `full2` covers the current package.

Rejected (with reasons):
- Finding 2's "nothing smaller passes": false (two tuned exponents pass; table above).
- The optional EXPERIMENT.md sentence ("a multiplier estimated from user-level dispersion is not on this list"): not
  added. Section 5 already lists the three accepted methods; a sentence the grader cannot enforce would state a rule
  that is not checked (G15 asks that every enforced rule be stated, and an unenforced one misleads the agent), and it
  would change agent-facing text, and so the package, for no gain in enforcement.
- Shipping a probe as an attempt or a solution: not done. The click-dispersion rule scores 1, so it cannot be an
  attempt (attempts must score 0 in `tools/proof_matrix.py`), and an `alt_*` solution would endorse a crude estimator.
  It stays a documented probe (section 9).

Results (FACT): no package file changed (SHA-256 of all 58 files identical before and after this pass, `cmp`;
32,035,105 bytes; `shasum -a 256 -c tests/SHA256SUMS` 21 of 21 OK); `local_check.py` ALL AS EXPECTED with 13 variants
and the same cells as section 15 (section 9; timings in section 8); `grader_probes.py` 24 of 24 as expected;
`tools/sync_kit.py --check` exit 0, then `tools/sync_kit.py` synced the five tasks with no content change (SHA-256 of
every `tests/kit.py` and `tests/test.sh` before and after identical); `tools/check_task.py tasks/ab-test-reanalysis`
printed `OK ab-test-reanalysis`; `harbor lint tasks/ab-test-reanalysis --json` printed `[]`; no `__pycache__`, `.pyc`
or `.DS_Store` under the package. Authoring folder: `click_rule_probes.py` and `.out.md` added; `local_results.json`
and `grader_probes.out.md` rewritten by their re-runs.

Wording changed: the header, sections 2 (package line, authoring table), 5 (calibration time; "of these three forms"),
8 (section-16 timings), 9 (command line, static checks, new probe table), the gate record (header, G11, G12, G21,
result line), the README row, limitation 9 (the "whatever" sentence, (c), (d)) and section 15 (last arithmetic bullet).

Open after this pass: the G12 override question above (since ruled: no override); the Daytona proof matrix (still
required by section 15's package change; section 16 changed no package file; run `full2` did it, section 11); the
2.0 MB size overrun (deviation 10); the third review's finding F3, `python -m` in the instruction against `python3 -m`
in the grader (limitation 14).

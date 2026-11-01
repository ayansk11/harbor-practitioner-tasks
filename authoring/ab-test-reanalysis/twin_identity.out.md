> Pre-revision record (status line added 2026-10-31): made for the first version of this task (commit 495c9f5 or
> earlier); it reads the first version's h_null and h_twin (with their users.csv files), which the revision
> removed or replaced, so it no longer runs. The section numbers it cites are those of that version's
> design record (git show 495c9f5:docs/ab-test-reanalysis/DESIGN.md). Kept as history; the revision's records are
> calibration_study.out.md, generation_report.out.md and local_check.out.md.

# twin_identity.out.md (twin_identity.py)

h_twin against h_null, from the committed files.

## 1. Text

- assignments.csv: gzip files byte-identical True, plain text byte-identical True (1,295,070 bytes, 38,441 data rows)
- users.csv: gzip files byte-identical True, plain text byte-identical True (418,015 bytes, 38,000 data rows)
- pageviews.csv: header equal True; rows 322,363 / 322,363; user_id and ts text equal on every row, same order: True; rows whose clicked value differs: 62,934

## 2. Per-user pageview counts (plan's population rules; aligned by user_id)

- the same counted users with the same arms: True (37,460 users); every user's counted pageviews equal: True

| arm | set | users | pageviews | clicks | sum v^2 | m_w | K | max v | p99 v | users with v = 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| A | h_null | 18,648 | 147,296 | 16,578 | 6,776,696 | 46.0073 | 5.8246 | 600 | 78 | 4,050 |
| A | h_twin | 18,648 | 147,296 | 16,122 | 6,776,696 | 46.0073 | 5.8246 | 600 | 78 | 4,050 |
| A | equal | | | | | | | | | per-user count vectors np.array_equal: True |
| B | h_null | 18,812 | 150,416 | 16,420 | 8,389,586 | 55.7759 | 6.9757 | 600 | 79 | 4,081 |
| B | h_twin | 18,812 | 150,416 | 18,470 | 8,389,586 | 55.7759 | 6.9757 | 600 | 79 | 4,081 |
| B | equal | | | | | | | | | per-user count vectors np.array_equal: True |

- every one of the 16 pageview features of calibration_study.py, per arm, is bit-identical on the two sets: True

## 3. Arithmetic (reference = tests/expected/<set>.json, delta method)

- h_null: reference half-width H = 0.010831; pageview-level half-width 0.002256; DE = (H / pageview hw)^2 = 23.054, sqrt(DE) = 4.8014; CTR A / B 0.11255 / 0.10916
- h_twin: reference half-width H = 0.005265; pageview-level half-width 0.002301; DE = (H / pageview hw)^2 = 5.237, sqrt(DE) = 2.2885; CTR A / B 0.10945 / 0.12279
- h_null: multiplier each arm's pageview-level variance needs to equal the delta variance, A / B: 19.955 / 26.304
- h_twin: multiplier each arm's pageview-level variance needs to equal the delta variance, A / B: 4.542 / 5.879

Both bound errors of an interval with half-width w and the exact diff are |w - H| / H; a wrong centre only adds to one of them. A set passes only if w is in [(1 - b) H, (1 + b) H], b = 0.25.

- (a) width from the pageview data only (no clicks): w is the same number on both sets. Ratio of the reference half-widths r = 0.010831 / 0.005265 = 2.0572. Both pass only if (1 + b) / (1 - b) >= r; the best common w = 2 H_null H_twin / (H_null + H_twin) misses both by (r - 1) / (r + 1) = 0.3458 half-widths.
- (b) pageview-level interval times one common multiplier sqrt(M): the needed sqrt(M) are sqrt(DE) = 4.8014 and 2.2885, ratio r = 2.0981; minimum miss (r - 1) / (r + 1) = 0.3544.
- (c) each arm's pageview-level variance R(1-R)/V times its own M_A, M_B >= 0 from the pageview data (equal on the two sets): V is equal, so for every such pair the twin / null ratio of the widths is between sqrt(q_lo) and sqrt(q_hi), q = R(1-R) twin / R(1-R) null per arm: A 0.9759, B 1.1076. Both pass only if (1 + b) / (1 - b) >= sqrt(q_lo) x r = 0.9879 x 2.0572 = 2.0322, so the smallest worst error is (r - 1) / (r + 1) = 0.3404 half-widths (reached with M on arm A alone).
- brute force over M_A, M_B in {0} and 1,201 log-spaced values from 0.01 to 1000: smallest worst error 0.3404 at M_A = 19.57, M_B = 0.01813 (the bound (c) is 0.3404); with both M >= 1: 0.3420.

## Checks

- PASS: identity (text and per-user counts)
- PASS: (a) > band
- PASS: (b) > band
- PASS: (c) > band
- PASS: brute force >= bound (c) - 1e-9

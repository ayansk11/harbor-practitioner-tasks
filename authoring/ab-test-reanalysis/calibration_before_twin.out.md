> Pre-revision record (status line added 2026-10-31): made for the first version of this task (commit 495c9f5 or
> earlier); it describes the first version's data with the hidden set h_lowicc. The section numbers it cites are
> those of that version's design record (git show 495c9f5:docs/ab-test-reanalysis/DESIGN.md). Kept as history; the
> revision's records are calibration_study.out.md, generation_report.out.md and local_check.out.md.

# calibration_study.out.md (calibration_study.py)

Bound errors in reference half-widths (reference = delta method in tests/expected/). Seeds: B=2000 x 200; B=5000 and pooled x 30. Run time 585.0 s.

## Per set

| set | DE | sqrt(DE) | lower/hw | SRM p | decision | max valid error | fix_bots_only error | constant_inflation error (K=2.466) |
|---|---|---|---|---|---|---|---|---|
| visible | 6.08 | 2.466 | -1.095 | 0.635 | no_ship | 0.0809 | 0.5944 | 0.0002 |
| h_null | 23.05 | 4.801 | -1.313 | 0.397 | no_ship | 0.1039 | 0.7917 | 0.4864 |
| h_pos | 6.05 | 2.460 | +1.088 | 1 | ship | 0.0916 | 0.5936 | 0.0023 |
| h_srm | 6.81 | 2.610 | +0.806 | 6.75e-09 | invalid | 0.0883 | 0.6169 | 0.0553 |
| h_bots | 7.85 | 2.802 | -1.129 | 0.411 | no_ship | 0.0859 | 0.6431 | 0.1199 |
| h_lowicc | 5.82 | 2.413 | +0.973 | 0.546 | ship | 0.0956 | 0.5856 | 0.0218 |

## Valid methods, worst bound error per set

| method | visible | h_null | h_pos | h_srm | h_bots | h_lowicc |
|---|---|---|---|---|---|---|
| delta_refb | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| delta_no_N_factor | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0001 |
| cr1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| bootstrap B=2000 percentile (200 seeds) | 0.0809 | 0.1039 | 0.0916 | 0.0883 | 0.0859 | 0.0956 |
| bootstrap B=2000 basic (200 seeds) | 0.0809 | 0.1039 | 0.0916 | 0.0883 | 0.0859 | 0.0956 |
| bootstrap B=2000 normal (200 seeds) | 0.0376 | 0.0455 | 0.0428 | 0.0439 | 0.0438 | 0.0496 |
| bootstrap B=5000 percentile (30 seeds) | 0.0524 | 0.0593 | 0.0472 | 0.0426 | 0.0531 | 0.0523 |
| pooled bootstrap B=2000 percentile (30 seeds) | 0.0718 | 0.0878 | 0.0849 | 0.0802 | 0.0760 | 0.0690 |

Bootstrap B=2000 percentile, mean and SD of the bound error (lo; hi):

- visible: lo mean -0.0024 sd 0.0278; hi mean -0.0020 sd 0.0281
- h_null: lo mean +0.0220 sd 0.0283; hi mean +0.0131 sd 0.0326
- h_pos: lo mean +0.0013 sd 0.0283; hi mean -0.0024 sd 0.0314
- h_srm: lo mean +0.0071 sd 0.0284; hi mean +0.0009 sd 0.0289
- h_bots: lo mean +0.0020 sd 0.0278; hi mean -0.0006 sd 0.0288
- h_lowicc: lo mean +0.0054 sd 0.0283; hi mean +0.0022 sd 0.0322

## Band

- spread (worst valid-method bound error, all sets): 0.1039
- rule band (next whole percent strictly above 2 x spread): 0.21
- band checked below (the one grade.py uses): 0.25
- fix_bots_only, smallest miss over the sets: 0.5856 (needs >= 2 x band = 0.50)
- best constant K, worst-set error: 0.3310 (needs > band)
- smallest decision margin |lower|/hw: 0.806 (needs >= max(0.35, band))

## ICC shortcut sweep

Interval = diff +/- z sqrt(sum over arms of R(1-R)/V x (1 + rho (m - 1))), one rho for all sets; bound error in reference half-widths; a set passes when both errors <= 0.25. rho_eff = (Var_delta / Var_pageview - 1) / (m_w - 1) per arm (A/B).

| set | m_w A/B | mean v A/B | rho_eff A/B | passing rho, m = m_w | passing rho, m = mean v |
|---|---|---|---|---|---|
| visible | 30.0 / 29.7 | 9.67 / 9.54 | 0.176 / 0.176 | 0.085 to 0.290 | 0.285 to 0.985 |
| h_null | 46.0 / 55.8 | 7.90 / 8.00 | 0.421 / 0.462 | 0.245 to 0.700 | none |
| h_pos | 25.1 / 24.0 | 7.88 / 7.77 | 0.209 / 0.220 | 0.105 to 0.355 | 0.355 to 1.000 |
| h_srm | 24.9 / 24.4 | 7.94 / 7.77 | 0.226 / 0.265 | 0.120 to 0.405 | 0.415 to 1.000 |
| h_bots | 28.6 / 29.4 | 7.82 / 7.78 | 0.247 / 0.242 | 0.125 to 0.400 | 0.505 to 1.000 |
| h_lowicc | 73.6 / 72.3 | 18.02 / 18.01 | 0.054 / 0.079 | 0.035 to 0.110 | 0.135 to 0.475 |

m = m_w (rho 0.0 to 1.0, step 0.005):
- rho passing every set: none
- most sets passed by one rho: 5 of 6 (rho 0.245 to 0.290)
- best rho (smallest worst-set error) on the grid: 0.145, worst error 0.4030; per set: visible 0.077, h_null 0.403, h_pos 0.146, h_srm 0.194, h_bots 0.197, h_lowicc 0.401
- best rho on a 0.0001 grid: 0.1453, worst error 0.4024

m = mean v (rho 0.0 to 1.0, step 0.005):
- rho passing every set: none
- most sets passed by one rho: 4 of 6 (rho 0.415 to 0.985)
- best rho (smallest worst-set error) on the grid: 0.705, worst error 0.4942; per set: visible 0.078, h_null 0.494, h_pos 0.021, h_srm 0.075, h_bots 0.141, h_lowicc 0.494
- best rho on a 0.0001 grid: 0.7054, worst error 0.4941

## Checks

- PASS: band > 2 x spread
- PASS: fix_bots_only misses by >= 2 x band on every set
- PASS: no constant K fits every set (best K's worst error > band)
- PASS: ICC shortcut, m = sum(v^2)/sum(v): no rho in [0, 1] passes every set (best rho's worst error > band)
- PASS: ICC shortcut, m = mean pageviews per user: no rho in [0, 1] passes every set
- PASS: every decision bound >= 0.35 hw from 0, and farther than band
- PASS: SRM set: 1e-12 < srm_p < 0.001; other sets srm_p >= 0.05

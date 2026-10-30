# calibration_study.out.md (calibration_study.py)

Bound errors in reference half-widths (reference = delta method in tests/expected/). Seeds: B=2000 x 200; B=5000 and pooled x 30. Run time 641.8 s.

## Per set

| set | DE | sqrt(DE) | lower/hw | SRM p | decision | max valid error | fix_bots_only error | constant_inflation error (K=2.466) |
|---|---|---|---|---|---|---|---|---|
| visible | 6.08 | 2.466 | -1.095 | 0.635 | no_ship | 0.0809 | 0.5944 | 0.0002 |
| h_null | 23.05 | 4.801 | -1.313 | 0.397 | no_ship | 0.1039 | 0.7917 | 0.4864 |
| h_pos | 6.05 | 2.460 | +1.088 | 1 | ship | 0.0916 | 0.5936 | 0.0023 |
| h_srm | 6.81 | 2.610 | +0.806 | 6.75e-09 | invalid | 0.0883 | 0.6169 | 0.0553 |
| h_bots | 7.85 | 2.802 | -1.129 | 0.411 | no_ship | 0.0859 | 0.6431 | 0.1199 |
| h_twin | 5.26 | 2.293 | +1.054 | 0.311 | ship | 0.1008 | 0.5638 | 0.0757 |

## Valid methods, worst bound error per set

| method | visible | h_null | h_pos | h_srm | h_bots | h_twin |
|---|---|---|---|---|---|---|
| delta_refb | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| delta_no_N_factor | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cr1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| bootstrap B=2000 percentile (200 seeds) | 0.0809 | 0.1039 | 0.0916 | 0.0883 | 0.0859 | 0.1008 |
| bootstrap B=2000 basic (200 seeds) | 0.0809 | 0.1039 | 0.0916 | 0.0883 | 0.0859 | 0.1008 |
| bootstrap B=2000 normal (200 seeds) | 0.0376 | 0.0455 | 0.0428 | 0.0439 | 0.0438 | 0.0496 |
| bootstrap B=5000 percentile (30 seeds) | 0.0524 | 0.0593 | 0.0472 | 0.0426 | 0.0531 | 0.0496 |
| pooled bootstrap B=2000 percentile (30 seeds) | 0.0718 | 0.0878 | 0.0849 | 0.0802 | 0.0760 | 0.0839 |

Bootstrap B=2000 percentile, mean and SD of the bound error (lo; hi):

- visible: lo mean -0.0024 sd 0.0278; hi mean -0.0020 sd 0.0281
- h_null: lo mean +0.0220 sd 0.0283; hi mean +0.0131 sd 0.0326
- h_pos: lo mean +0.0013 sd 0.0283; hi mean -0.0024 sd 0.0314
- h_srm: lo mean +0.0071 sd 0.0284; hi mean +0.0009 sd 0.0289
- h_bots: lo mean +0.0020 sd 0.0278; hi mean -0.0006 sd 0.0288
- h_twin: lo mean -0.0010 sd 0.0302; hi mean -0.0053 sd 0.0323

## Band

- spread (worst valid-method bound error, all sets; a sample maximum over the seeds): 0.1039
- bootstrap |mean| + 4 SD (worst set, bound and group): 0.1550 (needs < band)
- rule band (next whole percent strictly above 2 x spread): 0.21
- band checked below (the one grade.py uses): 0.25
- fix_bots_only, smallest miss over the sets: 0.5638 (needs >= 2 x band = 0.50)
- best constant K, worst-set error: 0.3537 (needs > band)
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
| h_twin | 56.7 / 44.9 | 8.28 / 7.80 | 0.089 / 0.083 | 0.040 to 0.145 | 0.280 to 1.000 |

m = m_w (rho 0.0 to 1.0, step 0.005):
- rho passing every set: none
- most sets passed by one rho: 5 of 6 (rho 0.125 to 0.290)
- best rho (smallest worst-set error) on the grid: 0.175, worst error 0.3548; per set: visible 0.003, h_null 0.351, h_pos 0.080, h_srm 0.131, h_bots 0.133, h_twin 0.355
- best rho on a 0.0001 grid: 0.1742, worst error 0.3523

m = mean v (rho 0.0 to 1.0, step 0.005):
- rho passing every set: none
- most sets passed by one rho: 5 of 6 (rho 0.505 to 0.985)
- best rho (smallest worst-set error) on the grid: 1.000, worst error 0.4129; per set: visible 0.257, h_null 0.413, h_pos 0.137, h_srm 0.073, h_bots 0.003, h_twin 0.236
- best rho on a 0.0001 grid: 1.0000, worst error 0.4129

## Pageview-only sweep

Interval = diff +/- z sqrt(sum over arms of R(1-R)/V x M), M built from the arm's pageview counts only: f^g, c f^g or 1 + c f^g, c fitted so the visible readout is exact, g from -3 to 4 step 0.01. A form passes when one g passes every set (both bound errors <= 0.25).

| feature | visible A/B | h_null A/B | h_twin A/B | f^g: passing g / best worst error (g) | c f^g: passing g / best worst error (g) | 1 + c f^g: passing g / best worst error (g) |
|---|---|---|---|---|---|---|
| K = mean(v^2)/mean(v)^2 | 3.11 / 3.11 | 5.82 / 6.98 | 6.85 / 5.76 | none / 0.349 (1.23) | none / 0.351 (0.65) | none / 0.351 (0.75) |
| CV = sd/mean | 1.45 / 1.45 | 2.2 / 2.44 | 2.42 / 2.18 | none / 0.357 (2.72) | none / 0.351 (1.0) | none / 0.351 (1.15) |
| K over users with v > 0 | 2.79 / 2.77 | 4.56 / 5.46 | 5.37 / 4.5 | none / 0.351 (1.42) | none / 0.351 (0.8) | none / 0.351 (0.92) |
| m_w = sum(v^2)/sum(v) | 30 / 29.7 | 46 / 55.8 | 56.7 / 44.9 | none / 0.358 (0.58) | none / 0.353 (0.87) | none / 0.353 (1.0) |
| mean v | 9.67 / 9.54 | 7.9 / 8 | 8.28 / 7.8 | none / 0.369 (1.07) | none / 0.349 (-2.51) | none / 0.349 (-2.89) |
| sd v | 14 / 13.9 | 17.4 / 19.5 | 20 / 17 | none / 0.358 (0.78) | none / 0.354 (1.64) | none / 0.355 (1.88) |
| mean v over users with v > 0 | 10.8 / 10.7 | 10.1 / 10.2 | 10.6 / 9.97 | none / 0.359 (0.97) | none / 0.441 (-3.0) | none / 0.448 (-3.0) |
| max/mean | 43.8 / 47.9 | 76 / 75 | 72.5 / 76.9 | none / 0.359 (0.52) | none / 0.352 (0.93) | none / 0.353 (1.07) |
| p99/mean | 6.72 / 6.82 | 9.87 / 9.88 | 10.1 / 9.87 | none / 0.360 (0.98) | none / 0.357 (1.19) | none / 0.357 (1.37) |
| p90/mean | 2.28 / 2.31 | 2.41 / 2.38 | 2.42 / 2.44 | none / 0.362 (2.57) | none / 0.441 (4.0) | none / 0.448 (4.0) |
| median/mean | 0.621 / 0.629 | 0.38 / 0.375 | 0.362 / 0.385 | none / 0.360 (-2.31) | none / 0.356 (-0.9) | none / 0.356 (-1.04) |
| Gini | 0.578 / 0.58 | 0.704 / 0.71 | 0.713 / 0.705 | none / 0.649 (-3.0) | none / 0.355 (2.28) | none / 0.355 (2.63) |
| share of views, top 1% of users | 0.101 / 0.101 | 0.163 / 0.177 | 0.178 / 0.163 | none / 0.448 (-1.1) | none / 0.354 (0.88) | none / 0.354 (1.01) |
| share of views, top 10% of users | 0.417 / 0.419 | 0.551 / 0.557 | 0.564 / 0.55 | none / 0.496 (-2.99) | none / 0.356 (1.62) | none / 0.355 (1.87) |
| share of users with no pageview | 0.103 / 0.109 | 0.217 / 0.217 | 0.215 / 0.218 | none / 0.495 (-1.16) | none / 0.354 (0.64) | none / 0.354 (0.74) |
| sd of log(1 + v) | 1.02 / 1.03 | 1.13 / 1.13 | 1.14 / 1.13 | none / 0.733 (4.0) | none / 0.376 (4.0) | none / 0.393 (4.0) |

- forms passing every set: none
- smallest best worst-set error over all forms: 0.3491 (K = mean(v^2)/mean(v)^2, f^g)
- h_null / h_twin: sqrt(DE) ratio 2.094; one common multiplier on both misses one of them by at least 0.3537 half-widths

## Checks

- PASS: band > 2 x spread
- PASS: fix_bots_only misses by >= 2 x band on every set
- PASS: no constant K fits every set (best K's worst error > band)
- PASS: ICC shortcut, m = sum(v^2)/sum(v): no rho in [0, 1] passes every set (best rho's worst error > band)
- PASS: ICC shortcut, m = mean pageviews per user: no rho in [0, 1] passes every set
- PASS: pageview-only multipliers (16 features x 3 forms): none passes every set (every form's best worst-set error > band)
- PASS: valid bootstrap: |mean| + 4 SD of the bound error < band for every set, bound and group
- PASS: every decision bound >= 0.35 hw from 0, and farther than band
- PASS: SRM set: 1e-12 < srm_p < 0.001; other sets srm_p >= 0.05

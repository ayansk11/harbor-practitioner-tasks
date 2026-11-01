# calibration_study.out.md (calibration_study.py)

Bound errors in reference half-widths hw (reference = ref_a's delta method, tests/expected/). Band 0.25 (tests/grade.py). Seeds: B=2000 x 200; B=5000 and pooled x 30. Run 2026-10-30 22:51:50 MST to 2026-10-30 23:00:52 MST (Mac clock), 541.9 s by the script's timer.

## Per set

| set | n_users A/B | DE | sqrt(DE) | lower/hw | upper/hw | srm_p | decision | worst plan-method error | worst other reading | pageview_ci miss | s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| visible | 16570/16702 | 6.72 | 2.593 | -0.818 | +1.182 | 0.4693 | no_ship | 0.0855 | 0.0855 | 0.6144 | 94.4 |
| h_null | 15669/15844 | 19.10 | 4.371 | -1.047 | +0.953 | 0.3242 | no_ship | 0.0948 | 0.0948 | 0.7712 | 88.7 |
| h_pos | 15707/15806 | 7.44 | 2.727 | +1.455 | +3.455 | 0.5771 | ship | 0.0879 | 0.0879 | 0.6333 | 89.1 |
| h_srm | 17208/16259 | 7.12 | 2.668 | +0.945 | +2.945 | 2.131e-07 | invalid | 0.0892 | 0.0902 | 0.6252 | 95.7 |
| h_plain | 14356/14155 | 6.36 | 2.522 | +1.100 | +3.100 | 0.2339 | ship | 0.1111 | 0.1111 | 0.6035 | 79.1 |
| h_neg | 16557/16679 | 7.44 | 2.728 | -2.999 | -0.999 | 0.5034 | no_ship | 0.0981 | 0.0981 | 0.6335 | 94.9 |

## Worst bound error per method and set

| method | plan method | visible | h_null | h_pos | h_srm | h_plain | h_neg |
|---|---|---|---|---|---|---|---|
| delta (ref_b, N/(N-1) factor) | yes | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| delta without the N/(N-1) factor | yes | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| CR1 by user | yes | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| bootstrap B=2000 percentile (200 seeds) | yes | 0.0855 | 0.0948 | 0.0879 | 0.0892 | 0.1111 | 0.0981 |
| bootstrap B=5000 percentile (30 seeds) | yes | 0.0605 | 0.0367 | 0.0629 | 0.0466 | 0.0554 | 0.0490 |
| bootstrap B=2000 basic (200 seeds) | no | 0.0855 | 0.0948 | 0.0879 | 0.0892 | 0.1111 | 0.0981 |
| bootstrap B=2000 normal (200 seeds) | no | 0.0409 | 0.0387 | 0.0412 | 0.0413 | 0.0557 | 0.0381 |
| pooled bootstrap B=2000 percentile (30 seeds) | no | 0.0719 | 0.0750 | 0.0789 | 0.0902 | 0.0825 | 0.0753 |
| pageview_ci (pageview-level interval) | no (wrong) | 0.6144 | 0.7712 | 0.6333 | 0.6252 | 0.6035 | 0.6335 |
| constant K=2.593 (fitted on visible; information) | no (wrong) | 0.0000 | 0.4067 | 0.0493 | 0.0283 | 0.0281 | 0.0496 |

Plan bootstrap groups, mean and SD of the bound error (lo; hi):

- bootstrap B=2000 percentile (200 seeds), visible: lo mean +0.0062 sd 0.0302; hi mean -0.0011 sd 0.0312
- bootstrap B=2000 percentile (200 seeds), h_null: lo mean -0.0041 sd 0.0298; hi mean -0.0067 sd 0.0299
- bootstrap B=2000 percentile (200 seeds), h_pos: lo mean -0.0027 sd 0.0258; hi mean -0.0039 sd 0.0305
- bootstrap B=2000 percentile (200 seeds), h_srm: lo mean +0.0058 sd 0.0310; hi mean -0.0022 sd 0.0308
- bootstrap B=2000 percentile (200 seeds), h_plain: lo mean +0.0004 sd 0.0287; hi mean +0.0006 sd 0.0317
- bootstrap B=2000 percentile (200 seeds), h_neg: lo mean -0.0117 sd 0.0314; hi mean -0.0119 sd 0.0321
- bootstrap B=5000 percentile (30 seeds), visible: lo mean +0.0073 sd 0.0209; hi mean +0.0022 sd 0.0201
- bootstrap B=5000 percentile (30 seeds), h_null: lo mean -0.0043 sd 0.0174; hi mean -0.0070 sd 0.0163
- bootstrap B=5000 percentile (30 seeds), h_pos: lo mean +0.0035 sd 0.0227; hi mean -0.0031 sd 0.0183
- bootstrap B=5000 percentile (30 seeds), h_srm: lo mean +0.0042 sd 0.0214; hi mean +0.0014 sd 0.0187
- bootstrap B=5000 percentile (30 seeds), h_plain: lo mean -0.0045 sd 0.0186; hi mean +0.0027 sd 0.0210
- bootstrap B=5000 percentile (30 seeds), h_neg: lo mean -0.0062 sd 0.0181; hi mean -0.0151 sd 0.0149

## Band

- worst plan-method bound error (all sets, bounds and seeds; a sample maximum): 0.1111 (h_plain); needs <= 0.125
- pageview_ci, smallest miss over the sets: 0.6035 (h_plain); needs >= 0.50
- other readings (not plan methods), worst error: 0.1111
- plan bootstrap |mean| + 4 SD (worst set, bound and group): 0.1405
- best constant K of the pageview interval, worst-set error: 0.2682
- smallest decision margin |lower|/hw: 0.818 (visible)

## ICC shortcut sweep (information)

Interval = diff +/- z sqrt(sum over arms of R(1-R)/V x (1 + rho (m - 1))), one rho for all sets; a set passes when both bound errors are <= 0.25. rho_eff = (Var_delta / Var_pageview - 1) / (m_w - 1).

| set | m_w A/B | mean v A/B | rho_eff A/B | passing rho, m = m_w | passing rho, m = mean v |
|---|---|---|---|---|---|
| visible | 30.4 / 32.1 | 10.00 / 10.02 | 0.177 / 0.201 | 0.095 to 0.310 | 0.310 to 1.000 |
| h_null | 42.7 / 43.9 | 7.79 / 7.80 | 0.452 / 0.404 | 0.235 to 0.680 | none |
| h_pos | 36.1 / 30.1 | 9.84 / 9.69 | 0.193 / 0.211 | 0.100 to 0.330 | 0.365 to 1.000 |
| h_srm | 30.7 / 31.5 | 9.79 / 9.64 | 0.192 / 0.213 | 0.100 to 0.335 | 0.350 to 1.000 |
| h_plain | 30.5 / 29.3 | 7.83 / 7.88 | 0.165 / 0.205 | 0.090 to 0.310 | 0.380 to 1.000 |
| h_neg | 30.1 / 30.2 | 9.50 / 9.68 | 0.253 / 0.185 | 0.110 to 0.360 | 0.375 to 1.000 |

m = m_w (rho 0.0 to 1.0, step 0.005):
- rho passing every set: [0.235, 0.24, 0.245, 0.25, 0.255, 0.26, 0.265, 0.27, 0.275, 0.28, 0.285, 0.29, 0.295, 0.3, 0.305, 0.31]
- most sets passed by one rho: 6 of 6 (rho 0.235 to 0.310)
- best rho on the grid: 0.275, worst error 0.1867; per set: visible 0.177, h_null 0.187, h_pos 0.147, h_srm 0.142, h_plain 0.185, h_neg 0.100
- best rho on a 0.0001 grid: 0.2756, worst error 0.1859

m = mean v (rho 0.0 to 1.0, step 0.005):
- rho passing every set: none
- most sets passed by one rho: 5 of 6 (rho 0.380 to 1.000)
- best rho on the grid: 1.000, worst error 0.3613; per set: visible 0.220, h_null 0.361, h_pos 0.146, h_srm 0.168, h_plain 0.111, h_neg 0.135
- best rho on a 0.0001 grid: 1.0000, worst error 0.3613

## Pageview-only multiplier sweep (information)

Interval = diff +/- z sqrt(sum over arms of R(1-R)/V x M), M from the arm's pageview counts only: f^g, c f^g or 1 + c f^g, c fitted so the visible readout is exact, g from -3 to 4 step 0.01; a form passes when one g passes every set (both bound errors <= 0.25).

| feature | visible A/B | h_null A/B | f^g: passing g / best worst error (g) | c f^g: passing g / best worst error (g) | 1 + c f^g: passing g / best worst error (g) |
|---|---|---|---|---|---|
| K = mean(v^2)/mean(v)^2 | 3.04 / 3.2 | 5.49 / 5.63 | 1.39 to 1.72 / 0.128 (1.56) | 0.82 to 1.99 / 0.159 (1.22) | 0.93 to 2.27 / 0.156 (1.37) |
| CV = sd/mean | 1.43 / 1.48 | 2.12 / 2.15 | 3.76 to 4.00 / 0.214 (4.0) | 1.23 to 2.82 / 0.164 (1.8) | 1.40 to 3.22 / 0.161 (2.03) |
| K over users with v > 0 | 2.73 / 2.85 | 4.33 / 4.38 | 1.62 to 1.95 / 0.143 (1.8) | 1.06 to 2.59 / 0.158 (1.58) | 1.20 to 2.96 / 0.155 (1.78) |
| m_w = sum(v^2)/sum(v) | 30.4 / 32.1 | 42.7 / 43.9 | 0.64 to 0.67 / 0.216 (0.66) | 1.44 to 4.00 / 0.093 (2.6) | 1.63 to 4.00 / 0.091 (2.91) |
| mean v | 10 / 10 | 7.79 / 7.8 | none / 0.321 (1.06) | none / 0.265 (-1.71) | none / 0.265 (-1.95) |
| sd v | 14.3 / 14.9 | 16.5 / 16.8 | 0.85 to 0.87 / 0.234 (0.86) | 3.55 to 4.00 / 0.227 (4.0) | none / 0.251 (4.0) |
| mean v over users with v > 0 | 11.1 / 11.2 | 9.87 / 10 | none / 0.287 (0.99) | none / 0.312 (-2.49) | none / 0.313 (-2.83) |
| max/mean | 26.7 / 33.7 | 67.1 / 48.7 | 0.59 to 0.61 / 0.228 (0.6) | 0.73 to 1.07 / 0.202 (0.91) | 0.82 to 1.20 / 0.201 (1.03) |
| p99/mean | 6.8 / 6.69 | 9.5 / 9.56 | 1.06 to 1.13 / 0.209 (1.1) | 1.36 to 3.29 / 0.159 (2.02) | 1.54 to 3.75 / 0.156 (2.29) |
| p90/mean | 2.3 / 2.3 | 2.44 / 2.44 | 2.67 to 2.67 / 0.248 (2.67) | none / 0.332 (4.0) | none / 0.343 (4.0) |
| median/mean | 0.6 / 0.599 | 0.385 / 0.385 | -3.00 to -2.61 / 0.169 (-3.0) | -2.38 to -1.06 / 0.166 (-1.54) | -2.72 to -1.21 / 0.164 (-1.74) |
| Gini | 0.58 / 0.58 | 0.699 / 0.704 | none / 0.610 (-3.0) | 2.47 to 4.00 / 0.176 (3.46) | 2.80 to 4.00 / 0.174 (3.92) |
| share of views, top 1% of users | 0.0981 / 0.106 | 0.157 / 0.16 | none / 0.370 (-1.1) | 1.07 to 2.30 / 0.171 (1.53) | 1.22 to 2.62 / 0.168 (1.73) |
| share of views, top 10% of users | 0.421 / 0.42 | 0.543 / 0.549 | none / 0.433 (-3.0) | 1.80 to 3.91 / 0.169 (2.58) | 2.04 to 4.00 / 0.167 (2.92) |
| share of users with no pageview | 0.102 / 0.11 | 0.21 / 0.221 | none / 0.439 (-1.17) | 0.66 to 1.22 / 0.185 (0.89) | 0.75 to 1.39 / 0.183 (1.01) |
| sd of log(1 + v) | 1.03 / 1.04 | 1.12 / 1.13 | none / 0.709 (4.0) | none / 0.297 (4.0) | none / 0.312 (4.0) |

- forms passing every set: K = mean(v^2)/mean(v)^2 [f^g], K = mean(v^2)/mean(v)^2 [c f^g], K = mean(v^2)/mean(v)^2 [1 + c f^g], CV = sd/mean [f^g], CV = sd/mean [c f^g], CV = sd/mean [1 + c f^g], K over users with v > 0 [f^g], K over users with v > 0 [c f^g], K over users with v > 0 [1 + c f^g], m_w = sum(v^2)/sum(v) [f^g], m_w = sum(v^2)/sum(v) [c f^g], m_w = sum(v^2)/sum(v) [1 + c f^g], sd v [f^g], sd v [c f^g], max/mean [f^g], max/mean [c f^g], max/mean [1 + c f^g], p99/mean [f^g], p99/mean [c f^g], p99/mean [1 + c f^g], p90/mean [f^g], median/mean [f^g], median/mean [c f^g], median/mean [1 + c f^g], Gini [c f^g], Gini [1 + c f^g], share of views, top 1% of users [c f^g], share of views, top 1% of users [1 + c f^g], share of views, top 10% of users [c f^g], share of views, top 10% of users [1 + c f^g], share of users with no pageview [c f^g], share of users with no pageview [1 + c f^g]
- smallest best worst-set error over all forms: 0.0911 (m_w = sum(v^2)/sum(v), 1 + c f^g)

## Binding gates (the design: the band stays only if both pass; else change the data, never the band)

- PASS: worst plan-method bound error <= band / 2 = 0.125 (every set, bound and seed)
- PASS: pageview_ci smallest miss over the sets >= 2 x band = 0.50

## Data conditions (re-checked)

- PASS: every reference lower bound >= 0.5 hw from 0
- PASS: h_srm: 1e-11 < srm_p < 1e-5; every other set: srm_p >= 0.05
- PASS: DE >= 5.5 on every set

## Information (no gate)

- yes: other readings (basic, normal, pooled) worst error <= band / 2
- yes: plan bootstrap |mean| + 4 SD of the bound error < band (every set, bound and group)
- yes: no constant K of the pageview interval fits every set (best K's worst error > band)
- no: ICC shortcut, m = m_w: no rho in [0, 1] passes every set
- yes: ICC shortcut, m = mean v: no rho in [0, 1] passes every set
- no: pageview-only multipliers (16 features x 3 forms): none passes every set

RESULT: BAND KEPT (all binding gates and data conditions pass)

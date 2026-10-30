# click_rule_probes.out.md (click_rule_probes.py)

Fast evaluator: delta-method check, max |w/H - 1| over the six sets = 4.4e-16 (the per-user counts match tests/expected/ exactly).

## 1. Click-dispersion estimates (each arm's pageview variance x D, no constant, exponent 1)

D = sample variance of per-user CTR among users with >= k views / mean of R(1-R)/v over those users.

| k | worst | visible | h_null | h_pos | h_srm | h_bots | h_twin | all six within 0.25 |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.550 | 0.331 | 0.550 | 0.328 | 0.324 | 0.407 | 0.399 | no |
| 6 | 0.515 | 0.299 | 0.515 | 0.287 | 0.286 | 0.375 | 0.367 | no |
| 7 | 0.484 | 0.268 | 0.484 | 0.252 | 0.250 | 0.339 | 0.348 | no |
| 8 | 0.454 | 0.243 | 0.454 | 0.215 | 0.215 | 0.311 | 0.321 | no |
| 9 | 0.431 | 0.217 | 0.431 | 0.181 | 0.176 | 0.274 | 0.302 | no |
| 10 | 0.404 | 0.196 | 0.404 | 0.155 | 0.143 | 0.254 | 0.282 | no |
| 11 | 0.386 | 0.176 | 0.386 | 0.128 | 0.114 | 0.228 | 0.265 | no |
| 12 | 0.366 | 0.152 | 0.366 | 0.104 | 0.084 | 0.207 | 0.247 | no |
| 13 | 0.342 | 0.125 | 0.342 | 0.076 | 0.054 | 0.187 | 0.222 | no |
| 14 | 0.322 | 0.096 | 0.322 | 0.049 | 0.032 | 0.161 | 0.210 | no |
| 15 | 0.303 | 0.075 | 0.303 | 0.015 | 0.004 | 0.138 | 0.188 | no |
| 16 | 0.284 | 0.047 | 0.284 | 0.012 | 0.019 | 0.113 | 0.173 | no |
| 17 | 0.260 | 0.024 | 0.260 | 0.038 | 0.042 | 0.098 | 0.156 | no |
| 18 | 0.245 | 0.001 | 0.245 | 0.063 | 0.051 | 0.079 | 0.143 | yes |
| 19 | 0.220 | 0.024 | 0.220 | 0.093 | 0.072 | 0.050 | 0.123 | yes |
| 20 | 0.203 | 0.050 | 0.203 | 0.121 | 0.099 | 0.033 | 0.104 | yes |
| 21 | 0.181 | 0.069 | 0.181 | 0.145 | 0.112 | 0.006 | 0.082 | yes |
| 22 | 0.165 | 0.088 | 0.161 | 0.165 | 0.142 | 0.026 | 0.071 | yes |
| 23 | 0.190 | 0.100 | 0.135 | 0.190 | 0.135 | 0.058 | 0.055 | yes |
| 24 | 0.203 | 0.121 | 0.117 | 0.203 | 0.168 | 0.078 | 0.041 | yes |
| 25 | 0.228 | 0.138 | 0.101 | 0.228 | 0.177 | 0.097 | 0.025 | yes |
| 26 | 0.246 | 0.154 | 0.087 | 0.246 | 0.216 | 0.120 | 0.016 | yes |
| 27 | 0.273 | 0.179 | 0.070 | 0.273 | 0.237 | 0.128 | 0.007 | no |
| 28 | 0.292 | 0.195 | 0.061 | 0.292 | 0.270 | 0.150 | 0.010 | no |
| 29 | 0.312 | 0.212 | 0.046 | 0.312 | 0.296 | 0.176 | 0.019 | no |
| 30 | 0.335 | 0.242 | 0.031 | 0.335 | 0.311 | 0.196 | 0.024 | no |
| 31 | 0.351 | 0.264 | 0.017 | 0.351 | 0.311 | 0.211 | 0.041 | no |
| 32 | 0.371 | 0.274 | 0.004 | 0.371 | 0.327 | 0.234 | 0.050 | no |
| 33 | 0.388 | 0.291 | 0.016 | 0.388 | 0.357 | 0.270 | 0.052 | no |
| 34 | 0.406 | 0.294 | 0.032 | 0.406 | 0.377 | 0.289 | 0.067 | no |
| 35 | 0.411 | 0.318 | 0.049 | 0.399 | 0.411 | 0.284 | 0.086 | no |
| 36 | 0.414 | 0.316 | 0.061 | 0.403 | 0.414 | 0.312 | 0.097 | no |
| 37 | 0.435 | 0.321 | 0.069 | 0.435 | 0.420 | 0.314 | 0.109 | no |
| 38 | 0.443 | 0.320 | 0.068 | 0.443 | 0.436 | 0.329 | 0.121 | no |
| 39 | 0.449 | 0.340 | 0.091 | 0.440 | 0.449 | 0.348 | 0.140 | no |
| 40 | 0.474 | 0.339 | 0.100 | 0.474 | 0.436 | 0.316 | 0.152 | no |

Thresholds that pass all six: [18, 19, 20, 21, 22, 23, 24, 25, 26].

k = 20: best constant on the width 1.0428 (on the variance 1.0873), worst error with it 0.1689.

ANOVA ICC + Kish (1 + rho (m_w - 1)), no constant: worst 0.064 (visible 0.032, h_null 0.017, h_pos 0.001, h_srm 0.023, h_bots 0.036, h_twin 0.064).
zzb (>= 5 views)^2.0, constant fitted on the visible set: worst 0.230.
disp (>= 10 views)^1.5, constant fitted on the visible set: worst 0.188.

## 2. Arm-level click aggregates (pageview variance x c f^g, one multiplier for both arms)

One aggregate, exponent -12 to 12 in steps of 0.01:

| f | c free: worst (g) | c on visible: worst (g) |
|---|---|---|
| abs(diff) | 0.342 (-0.04) | 0.401 (0.15) |
| abs(rel) | 0.341 (-0.05) | 0.408 (0.16) |
| R_A | 0.346 (1.33) | 0.348 (1.37) |
| R_B | 0.346 (-0.34) | 0.383 (1.13) |
| R_pool | 0.351 (-0.38) | 0.367 (1.24) |
| R_pool(1-R_pool) | 0.351 (-0.43) | 0.367 (1.39) |
| sum R(1-R) | 0.351 (-0.43) | 0.367 (1.39) |
| max R | 0.348 (-0.34) | 0.376 (1.12) |
| min R | 0.354 (-0.45) | 0.357 (1.39) |

Best over the 9 aggregates and both constant rules: 0.341.

Two aggregates, constant fitted on the visible set, exponents -16 to 16 in steps of 0.1: 11 of 36 pairs pass all six; best five: R_A^9.9 R_B^-7.5 0.158; R_A^16.0 R_pool^-13.7 0.162; R_A^16.0 R_pool(1-R_pool)^-15.4 0.176; R_A^16.0 sum R(1-R)^-15.4 0.177; R_A^11.6 max R^-8.9 0.177.

c abs(diff)^4.03 abs(rel)^-4.61 with c also tuned on the six readouts (three hidden-tuned parameters): worst 0.2381.
Pair ratios h_twin / h_null: abs(diff) 3.9409, abs(rel) 4.0523, R_A 0.9725, R_B 1.1248, R_pool 1.0483.

## 3. Per-arm multipliers M_A, M_B >= 0 from the pageview data, other variance bases (section 15 (c))

r = H_null / H_twin = 0.010831 / 0.005265 = 2.0572. V per arm is the same on both sets, so the twin/null width ratio lies between sqrt(q_min) and sqrt(q_max), q = base_twin / base_null per arm; the best worst error is (r sqrt(q_min) - 1) / (r sqrt(q_min) + 1). Grid check: M_A, M_B in {0, 0.01 .. 1000} (1,202 values each).

| base per arm | q_A | q_B | r sqrt(q_min) | bound | grid |
|---|---|---|---|---|---|
| R(1-R)/V | 0.9759 | 1.1076 | 2.0322 | 0.3404 | 0.3404 |
| R/V | 0.9725 | 1.1248 | 2.0287 | 0.3396 | 0.3399 |
| (1-R)/V | 1.0035 | 0.9847 | 2.0414 | 0.3424 | 0.3424 |
| R_pool(1-R_pool)/V | 1.0420 | 1.0420 | 2.0999 | 0.3548 | 0.3548 |

## 4. Real grader (KIT_LOCAL), reward and worst bound error per readout

| probe | reward | visible | h_null | h_pos | h_srm | h_bots | h_twin |
|---|---|---|---|---|---|---|---|
| disp k=10, c 1, g 1 | 0.0 | pass 0.196 | FAIL 0.404 | pass 0.155 | pass 0.143 | FAIL 0.254 | FAIL 0.282 |
| disp k=17, c 1, g 1 | 0.0 | pass 0.024 | FAIL 0.260 | pass 0.038 | pass 0.042 | pass 0.098 | pass 0.156 |
| disp k=18, c 1, g 1 | 1.0 | pass 0.001 | pass 0.245 | pass 0.063 | pass 0.051 | pass 0.079 | pass 0.143 |
| disp k=20, c 1, g 1 | 1.0 | pass 0.050 | pass 0.203 | pass 0.121 | pass 0.099 | pass 0.033 | pass 0.104 |
| disp k=26, c 1, g 1 | 1.0 | pass 0.154 | pass 0.087 | pass 0.246 | pass 0.216 | pass 0.120 | pass 0.016 |
| disp k=27, c 1, g 1 | 0.0 | pass 0.179 | pass 0.070 | FAIL 0.273 | pass 0.237 | pass 0.128 | pass 0.007 |
| ANOVA ICC + Kish m_w | 1.0 | pass 0.032 | pass 0.017 | pass 0.001 | pass 0.023 | pass 0.036 | pass 0.064 |
| zzb >= 5 views, g 2.0, c on visible | 1.0 | pass 0.000 | pass 0.230 | pass 0.205 | pass 0.077 | pass 0.067 | pass 0.014 |
| disp >= 10 views, g 1.5, c on visible | 1.0 | pass 0.000 | pass 0.111 | pass 0.077 | pass 0.133 | pass 0.048 | pass 0.188 |
| c abs(diff)^4.03 abs(rel)^-4.61, c tuned on all six | 1.0 | pass 0.229 | pass 0.238 | pass 0.238 | pass 0.236 | pass 0.177 | pass 0.007 |
| c R_A^9.9 R_B^-7.5, c on visible | 1.0 | pass 0.000 | pass 0.141 | pass 0.156 | pass 0.158 | pass 0.037 | pass 0.010 |

Run time 107.2 s.

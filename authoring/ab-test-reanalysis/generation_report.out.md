# generation_report (gen_data.py)

Seeds are searched in order from each set's base; the first that meets the stated conditions is kept.
Conditions: decision bound margin >= 0.5 half-widths; SRM p >= 0.05 (no SRM) or in (1e-11, 1e-05) (SRM set); design effect in the set's range; visible set: shipped-code lift in (0.037, 0.044) and p in (0.0002, 0.000349).

| set | role | seed | tries | users A/B (no bots) | pageviews | CTR A | CTR B | diff | half-width | lower/hw | DE | sqrt(DE) | SRM p | shipped-code lift | shipped-code p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| visible | null | 1083 | 84 | 19612/19518 | 375697 | 0.07934 | 0.07894 | -0.00040 | 0.00426 | -1.09 | 6.08 | 2.466 | 0.635 | +0.0411 | 0.000301 |
| h_null | null | 2006 | 7 | 18648/18812 | 297712 | 0.11255 | 0.10916 | -0.00338 | 0.01083 | -1.31 | 23.05 | 4.801 | 0.397 | +0.0046 | 0.66 |
| h_pos | pos | 3000 | 1 | 19705/19705 | 308241 | 0.12205 | 0.13418 | +0.01212 | 0.00581 | +1.09 | 6.05 | 2.460 | 1 | +0.1393 | 1.17e-43 |
| h_srm | srm | 4002 | 3 | 19136/20287 | 309518 | 0.09932 | 0.10948 | +0.01015 | 0.00562 | +0.81 | 6.81 | 2.610 | 6.75e-09 | +0.1393 | 4.06e-35 |
| h_bots | null | 5000 | 1 | 16068/15921 | 249565 | 0.08987 | 0.08906 | -0.00081 | 0.00628 | -1.13 | 7.85 | 2.802 | 0.411 | +0.3009 | 4.84e-94 |
| h_twin | pos | 7018 | 19 | 18648/18812 | 297712 | 0.10945 | 0.12279 | +0.01334 | 0.00527 | +1.53 | 5.24 | 2.288 | 0.397 | +0.1620 | 1.12e-49 |

- h_twin is the twin of h_null (kept seed 2006): the same users, arms, bots, assigned_at, repeated rows, pageview rows and timestamp text; only the clicks are redrawn, from seed 7018 (rho 0.09, CTR 0.11, lift 0.09). Guaranteed miss of any pageview-only multiplier on one of the two (twin_min_miss): 0.3404 half-widths (needs >= 0.33).

Shipped code's readout (environment/app/output/result.json):
```
{
  "experiment": "EXP-2291",
  "n_users": {
    "A": 20042,
    "B": 19518
  },
  "pageviews": {
    "A": 198876,
    "B": 186115
  },
  "clicks": {
    "A": 15079,
    "B": 14691
  },
  "ctr": {
    "A": 0.075821114664414,
    "B": 0.07893506702845016
  },
  "diff": 0.0031139523640361516,
  "rel_lift": 0.04106972546919913,
  "ci_95": [
    0.0014245322454811047,
    0.004803372482591198
  ],
  "p_value": 0.00030061701944224603,
  "decision": "ship"
}
```

File sizes (bytes):
- `environment/app/data/assignments.csv`: 1361276
- `environment/app/data/pageviews.csv`: 13758445
- `environment/app/data/users.csv`: 440015
- `tests/hidden/h_bots/assignments.csv.gz`: 326056
- `tests/hidden/h_bots/pageviews.csv.gz`: 3043854
- `tests/hidden/h_bots/users.csv.gz`: 143755
- `tests/hidden/h_null/assignments.csv.gz`: 340279
- `tests/hidden/h_null/pageviews.csv.gz`: 2636845
- `tests/hidden/h_null/users.csv.gz`: 158818
- `tests/hidden/h_pos/assignments.csv.gz`: 357474
- `tests/hidden/h_pos/pageviews.csv.gz`: 2773862
- `tests/hidden/h_pos/users.csv.gz`: 167172
- `tests/hidden/h_srm/assignments.csv.gz`: 357464
- `tests/hidden/h_srm/pageviews.csv.gz`: 2773763
- `tests/hidden/h_srm/users.csv.gz`: 166961
- `tests/hidden/h_twin/assignments.csv.gz`: 340279
- `tests/hidden/h_twin/pageviews.csv.gz`: 2638575
- `tests/hidden/h_twin/users.csv.gz`: 158818

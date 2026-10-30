# EXP-2291 analysis plan ("related items v2")

Written and agreed before launch (2026-08-25). The readout must follow this plan. The same plan applies to every
experiment exported in this layout.

## 1. Question
Does variant B (the redesigned related-items module) change click-through on product pages compared with A (the
current module)?

## 2. Randomization
- The unit of randomization is the **user**. Each user is assigned once, 50/50, to A or B, at their first eligible
  product pageview, and keeps that variant for the whole experiment.
- `assignments.csv` logs the assignment. The logger retries, so a row can appear more than once, exactly repeated; an
  exact repeat counts once. A user never has two different assignment rows.

## 3. Population
- Users flagged as bots (`users.csv`, `is_bot` = 1) are excluded from **both** arms, before anything is counted.
  Every assigned user has exactly one row in `users.csv`.
- `n_users` of an arm = the assigned users of that arm after this exclusion, whether or not they have any pageview.
- Only pageviews at or after the user's `assigned_at` count. A pageview with `ts` strictly earlier than `assigned_at` is
  dropped; one with `ts` equal to `assigned_at` counts.
- Timestamps are ISO 8601 with a `Z` or a `+hh:mm` / `-hh:mm` offset (both forms occur in the same file). Compare
  instants, not text.

## 4. Metric
- Every row of `pageviews.csv` is one pageview. Two rows with the same `user_id` and the same instant (written the
  same way or with different offsets) are two pageviews in the same second, so pageviews are never deduplicated.
- `clicks` of an arm = the number of counted pageviews with `clicked` = 1; `pageviews` = the number of counted pageviews.
- CTR of an arm = clicks / pageviews over the whole arm (a ratio of sums, not the average of per-user CTRs).
- `diff` = CTR_B - CTR_A (absolute, not relative).

## 5. Uncertainty
- The 95% confidence interval for `diff` must reflect that users, not pageviews, were randomized: the pageviews of one
  user are not independent of each other. Any one of these is acceptable:
  - (a) the delta method for each arm's ratio of sums, treating the arms as independent;
  - (b) a user-level bootstrap: resample users with replacement within each arm, at least 2,000 resamples, percentile
    interval;
  - (c) cluster-robust (CR1) standard errors clustered by user, from a pageview-level regression of `clicked` on an
    indicator of B.
- An interval that treats each pageview as an independent trial is not acceptable.

## 6. Sample ratio mismatch (SRM) check
- Pearson chi-square goodness-of-fit test of (`n_users` A, `n_users` B) against a 50/50 split: 1 degree of freedom,
  no continuity correction. `srm_p` is its p-value; `srm_flag` = `srm_p` < 0.001.

## 7. Decision rule (apply in this order)
1. `srm_flag` is true: `"invalid"` (the assignment is broken; do not read the result, investigate).
2. The lower bound of the 95% CI is above 0: `"ship"`.
3. Otherwise: `"no_ship"`.

## 8. Input files (one folder per experiment)
| File | Columns |
|---|---|
| `assignments.csv` | `user_id` (text), `variant` (`A` or `B`), `assigned_at` (ISO 8601 with offset) |
| `users.csv` | `user_id` (text), `is_bot` (0 or 1) |
| `pageviews.csv` | `user_id` (text), `ts` (ISO 8601 with offset), `clicked` (0 or 1) |

## 9. Output: `result.json`
A JSON object with at least these keys (more keys are fine):

| Key | Type | Meaning |
|---|---|---|
| `n_users` | object `{"A": int, "B": int}` | section 3 |
| `pageviews` | object `{"A": int, "B": int}` | section 4 |
| `clicks` | object `{"A": int, "B": int}` | section 4 |
| `ctr` | object `{"A": number, "B": number}` | section 4 |
| `diff` | number | CTR_B - CTR_A |
| `ci_95` | array `[lower, upper]` | section 5 |
| `srm_p` | number | section 6 |
| `srm_flag` | boolean | section 6 |
| `decision` | `"ship"`, `"no_ship"` or `"invalid"` | section 7 |

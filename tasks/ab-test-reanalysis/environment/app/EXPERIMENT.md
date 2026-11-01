# EXP-2291 analysis plan ("related items v2")

Written and agreed before launch (2026-08-25). The readout must follow this plan. The same plan applies to every
experiment exported in this layout.

## 1. Question
Does variant B (the redesigned related-items module) change click-through on product pages compared with A (the
current module)?

## 2. Randomization
- The unit of randomization is the **user**. The assignment service randomizes each user once, 50/50, by a hash of
  the experiment's salt and the user id, at the user's first eligible product pageview; the user keeps that variant
  for the whole experiment.
- `assignments` logs it. The logger retries, so a row can appear more than once, exactly repeated; an exact repeat of
  a row counts once. A user never has two different assignment rows.

## 3. Population
- The experiment is the users the assignment service randomized; a user whose variant was not set by the
  randomization is not in the experiment.
- Bot traffic is excluded from both arms, before anything is counted: a user is excluded if the platform's bot
  screening flagged the user by a rule that looks only at who the client is (its user agent, network or device),
  whenever that flag was raised. No user is excluded for anything the user did during the experiment.
- `n_users` of an arm = the users of the experiment in that arm after the bot exclusion, users with no pageview
  included.
- Only pageviews at or after the user's `assigned_at` count. A pageview with `ts` strictly earlier than `assigned_at`
  is dropped; one with `ts` equal to `assigned_at` counts.
- Timestamps are ISO 8601 with a `Z` or a `+hh:mm` / `-hh:mm` offset (both forms occur in the same file). Compare
  instants, not text.

## 4. Metric
- A counted pageview is a pageview of a user counted in `n_users`, at or after that user's `assigned_at` (section 3).
- A counted pageview is clicked when the user opened the page of at least one related product from the module on it;
  opening two product pages from one pageview is still one clicked pageview.
- `clicks` of an arm = the number of its clicked counted pageviews; `pageviews` = the number of its counted pageviews.
- CTR of an arm = clicks / pageviews over the whole arm (a ratio of sums, not the average of per-user CTRs).
- `diff` = CTR_B - CTR_A (absolute, not relative).

## 5. Uncertainty
- The 95% confidence interval for `diff` must reflect that users, not pageviews, were randomized: the pageviews of one
  user are not independent of each other. Any one of these is acceptable:
  - (a) the delta method for each arm's ratio of per-user sums (the sum of the users' clicks over the sum of the
    users' counted pageviews), treating the arms as independent;
  - (b) a user-level bootstrap: resample users with replacement within each arm, at least 2,000 resamples, percentile
    interval;
  - (c) cluster-robust (CR1) standard errors clustered by user, from a pageview-level regression of the clicked
    indicator (section 4) on an indicator of B.
- An interval that treats each pageview as an independent trial is not acceptable.

## 6. Sample ratio mismatch (SRM) check
- Pearson chi-square goodness-of-fit test of (`n_users` A, `n_users` B) of section 3 against a 50/50 split: 1 degree
  of freedom, no continuity correction. `srm_p` is its p-value; `srm_flag` = `srm_p` < 0.001.
- An SRM means the arms, as counted, are not the groups the randomization made. Find the cause before reading
  anything else: if the assignment itself is unbalanced, the experiment cannot be read; if a step of the analysis
  made the imbalance, that step is wrong: fix it and check again.

## 7. Decision rule (apply in this order)
1. `srm_flag` is true: `"invalid"` (the assignment is broken; do not read the result, investigate).
2. The lower bound of the 95% CI is above 0: `"ship"`.
3. Otherwise: `"no_ship"`.

## 8. Input files (one folder per experiment)
Four gzip-compressed CSV files with a header row: `assignments.csv.gz`, `bot_flags.csv.gz`, `pageviews.csv.gz` and
`module_clicks.csv.gz`. Their rows and columns are as the data platform documents them in `docs/DATA_DICTIONARY.md`.

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

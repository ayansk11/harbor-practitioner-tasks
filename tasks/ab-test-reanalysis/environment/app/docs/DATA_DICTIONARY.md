# Experiment export: data dictionary

Data platform documentation. It applies to every experiment export of this layout.

An export is one folder with four gzip-compressed CSV files (UTF-8, comma-separated, one header row). It holds:
- every assignment row the assignment service logged for the experiment;
- every flag the platform's bot screening raised on the experiment's assigned users, up to the time of the export;
- each assigned user's product pageviews, from about three days before the user's `assigned_at` to the end of the
  experiment (so pageviews before a user's assignment are included);
- every module event logged on those pageviews, whatever its time (an event can come after the end of the
  experiment when its pageview came just before it).

Timestamps are ISO 8601, to the second, with a `Z` or a `+hh:mm` / `-hh:mm` offset. The offset varies from row to
row, so the same instant can be written in different ways; compare instants, not text.

## assignments.csv.gz
One row per assignment, as the assignment service logged it. The logger retries, so a row can appear more than once,
exactly repeated. A user never has two different rows.

| Column | Meaning |
|---|---|
| `user_id` | the user (text) |
| `variant` | `A` or `B` |
| `assigned_at` | when the user got the variant |
| `method` | how the variant was set: `hash` = the variant from the hash (the randomization); `override` = set by hand in the feature-flag console's allowlist (dogfood and QA accounts), without the hash |

## bot_flags.csv.gz
One row per flag raised by the platform's bot screening (`docs/BOT_SCREENING.md`). A user can have rows of both rules,
and more than one row of the same rule.

| Column | Meaning |
|---|---|
| `user_id` | the flagged user |
| `rule` | the screening rule that raised the flag: `ua_crawler` or `velocity` |
| `flagged_at` | when the flag was raised (for each rule: `docs/BOT_SCREENING.md`) |

## pageviews.csv.gz
One row per product pageview, logged when the page has loaded. The assignment service assigns a user when the page
is requested, so the pageview on which a user was assigned has no row if the user left before the page loaded: an
assigned user need not have a pageview at `assigned_at`, and can have no pageview row at all.

| Column | Meaning |
|---|---|
| `pageview_id` | the pageview (text); unique per row |
| `user_id` | the user |
| `ts` | when the page loaded |
| `clicked` | 1 if at least one module_click event was logged on this pageview, else 0 (precomputed for dashboards) |

## module_clicks.csv.gz
One row per module_click event of the related-items module (`docs/TRACKING.md`). Times are to the second, so two
clicks on the same element in the same second give two identical rows; each row is one event.

| Column | Meaning |
|---|---|
| `pageview_id` | the pageview the event was logged on (`pageviews.csv.gz`); the event belongs to that pageview's user |
| `user_id` | the user |
| `ts` | when the click happened; at or after the pageview's `ts` |
| `target` | the `data-target` value of the clicked element (`docs/TRACKING.md`) |

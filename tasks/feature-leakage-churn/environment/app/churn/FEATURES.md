# Churn model features: specification

Owner: retention data science. This is the contract between the feature pipeline (`python -m churn.build_features`)
and the churn model (`python -m churn.train`). The live scoring service computes the same features from the same
definitions, so offline and live values must agree.

## The one rule
Each output row is one prediction for one customer at one moment `t` (the row's `as_of`). **A feature for that row may
use only information that existed strictly before `t`.** The definitions below say exactly what that means for each
feature; where they are more specific, they win.

## Conventions
- All timestamps are UTC, written as ISO 8601 with a `Z` suffix and whole seconds (`2025-03-04T06:00:00Z`).
- "Day" means a UTC calendar date. `date(t)` is the UTC date of `t`.
- "In days" means elapsed seconds divided by 86,400 (a fractional number).
- `W days` means exactly `W × 86,400` seconds.
- Windows are half-open: `[t − W days, t)` contains an event at exactly `t − W days` and does **not** contain an event at
  exactly `t`. Events are stamped to the second, and an event stamped exactly at `t` (for example the box charge that
  the 06:00 billing run creates while the 06:00 scoring run is reading) is not visible to the prediction at `t`.

## Input tables (`--data <dir>`)
| File | Columns | Notes |
|---|---|---|
| `customers.csv` | `customer_id, signup_at, plan, postcode_district` | one row per customer |
| `scoring_points.csv` | `customer_id, as_of, trigger, app_minutes_7d` | one row per prediction; `(customer_id, as_of)` is unique; `trigger` is `batch` (the 06:00 run) or `ticket` (scored by the support desk when a ticket is opened, at the ticket's `opened_at`); `app_minutes_7d` is the product-analytics reading for that prediction and is often empty (export outages, devices offline) |
| `orders.csv` | `order_id, customer_id, ordered_at, kind, amount_cents` | `kind` is `box` or `addon`; amounts are integer cents |
| `tickets.csv` | `ticket_id, customer_id, opened_at, topic` | support tickets |
| `status_snapshots.csv` | `customer_id, snapshot_date, status` | `snapshot_date` is a date (`YYYY-MM-DD`); at most one row per `(customer_id, snapshot_date)`; a snapshot dated `D` records the account status at the **end** of day `D`; `status` is one of `active`, `paused`, `payment_failed`, `cancelled` |
| `labels.csv` | `customer_id, as_of, churned_30d, label_available_at` | one row per labelled prediction; `churned_30d` is 1 if the customer cancelled in `(as_of, as_of + 30 days]`, else 0; `label_available_at` is when that outcome landed in the warehouse. Predictions whose outcome had not landed when the extract was taken have no row. |

## Output (`--out <file.parquet>`)
One row per row of `scoring_points.csv`, exactly once each, with these columns (row and column order do not matter):

| Column | Type | Definition |
|---|---|---|
| `customer_id` | integer | key, from `scoring_points.csv` |
| `as_of` | timestamp (UTC) | key, `t` |
| `orders_7d` | integer | number of orders with `t − 7 days ≤ ordered_at < t` |
| `orders_30d` | integer | number of orders with `t − 30 days ≤ ordered_at < t` |
| `spend_30d_cents` | integer | sum of `amount_cents` over the same 30-day window; `0` when there are none |
| `tickets_30d` | integer | number of tickets with `t − 30 days ≤ opened_at < t` |
| `days_since_last_order` | float or null | `t` minus the latest `ordered_at` that is `< t`, in days; null when the customer has no earlier order |
| `tenure_days` | float | `t − signup_at`, in days |
| `status` | string or null | `status` of the customer's latest snapshot with `snapshot_date < date(t)`; null when there is none. (The snapshot dated `date(t)` describes the end of that day, so it does not exist yet at `t`.) |
| `app_minutes_7d` | float or null | the row's own `app_minutes_7d` when present; otherwise the value of the same customer's most recent row with a strictly earlier `as_of` that has one; otherwise null. Never a value from a row at or after `t`. |
| `te_district` | float | target encoding of the customer's `postcode_district`, defined below |

### `te_district`
A label row is **available at `t`** when its `label_available_at < t`. For a prediction at `t` for a customer in
district `k`:
- `p` = the mean of `churned_30d` over all label rows available at `t` (every district, every customer); if no label row
  is available at `t`, `p = 0.05`.
- `n` = the number of label rows available at `t` whose customer is in district `k` (this includes the same customer's
  own earlier predictions whose outcome has landed); `s` = the sum of their `churned_30d`.
- `te_district = (s + 20 × p) / (n + 20)`  (a smoothed mean with prior weight `m = 20`).

## Run time
A run on an extract of the size in `/app/data` (about 3,000 customers) must finish within the limit stated in the task
ticket.

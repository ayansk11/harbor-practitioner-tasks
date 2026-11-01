# Warehouse tables (churn scoring)

Written 2025-02-14 by the data platform for the warehouse and its nightly loaders as they were on that date, and not
updated since. The scheduler's own records of every job run and transaction, later changes included, are in each
extract's `_ops/` folder (below).

The seven tables below are the warehouse tables that the live scoring service (`live/features.py`) and the churn
pipeline (`churn/`) read. This page says what each table holds and which system writes it. Every brand of the company
runs the same warehouse and jobs; each brand's job runs, failures and changes are its own.

## Reading the warehouse
- A query that starts at a moment t sees exactly the rows and values committed before t: a row committed at or after
  t is not seen, and a value overwritten at or after t is seen as it was before the overwrite, whatever the date of
  the event the row records.
- A query reads each table by the name it has when the query starts.
- `_loaded_at` is the commit time of the load that wrote the row; in `orders`, `_load_job` names that load.
- An extract is a copy of every table as the warehouse held it at one moment: the rows and values committed before
  that moment, with the `_ops/` records written before it.
- Timestamps are UTC, written as ISO 8601 with a `Z` suffix and whole seconds (`2025-02-04T06:00:00Z`);
  `snapshot_date` is a UTC date (`YYYY-MM-DD`); amounts are integer cents. Columns whose names start with `_` are
  written by the loaders, not by the source systems.

## The scheduler's records (`_ops/`)
- `_ops/scheduler.log` has one UTC event per line, `<time> <job> run=<run> <event>`: each task's start
  (`state=running`) and end (`state=success` or `state=failed`), and between them the lines the task writes, such as
  the rows it selected or copied, the transaction it sent (`sent txn <n> to commit`), the statements it ran and the
  checks it made.
- `_ops/commits.jsonl` has one JSON object per transaction a scheduled job sent: `txn`, `at`, `outcome` (`commit` or
  `rollback`), `table` and `rows` (the table the transaction writes rows into and how many; null for schema
  statements).
- `_ops/commits.jsonl` is the commit log of the scheduled jobs: a transaction is committed if and only if its outcome
  is `commit`, and it is committed at its `at`; the scheduler's task states describe tasks, not commits.
- Change data capture (`tickets`), the sign-up service and the scoring service write without the scheduler and are not
  in `_ops/`.

## Tables

### `customers`
`customer_id, signup_at, plan, postcode_district, last_login_at, _updated_at`: one row per customer.
- The sign-up service writes the row at `signup_at`: the plan chosen at sign-up (`basic`, `plus` or `family`), the
  postcode district, an empty `last_login_at`, and `_updated_at` = `signup_at`. `signup_at` and `postcode_district`
  never change.
- `crm_sync` reads the CRM at its start. For each customer whose plan or last login in the CRM (the latest login to
  the app or website before the sync's start) differs from the row, it overwrites `plan` and `last_login_at` with the
  CRM's values and sets `_updated_at` to the sync's commit time.
- Only plan changes are logged (`plan_changes`); no history of `last_login_at` is kept.

### `plan_changes`
`customer_id, changed_at, old_plan, new_plan, _loaded_at`: one row per plan change that `crm_sync` has applied. Each
sync writes one row for every change made in the CRM before its start that no earlier sync applied; `changed_at` is
when the customer made the change in the CRM, `_loaded_at` the commit of the sync that applied it. A customer's rows
are every change applied since sign-up, so the earliest row's `old_plan` is the plan chosen at sign-up. When one sync
applies several changes of a customer, the plan after that sync is the `new_plan` of the latest of them (by
`changed_at`), the CRM's plan at the sync's start.

### `scoring_points`
`customer_id, as_of, trigger, app_minutes_7d`: one row per scoring request, written by the scoring service at the
moment of the request, `as_of`. `trigger` is `batch` (the 06:00 run, which scores a customer every 14 days, on the
customer's billing weekday) or `ticket` (a request the support desk sends when a ticket is opened, for some of the
tickets, at the ticket's `opened_at`). `app_minutes_7d` is the product-analytics reading that came with the request (the customer's minutes in
the app over the last 7 days), empty when the request came without one (analytics export outages, devices offline).
`(customer_id, as_of)` is unique.

### `orders`
`order_id, customer_id, ordered_at, kind, amount_cents, _load_job, _loaded_at`. `kind` is `box` (the weekly box,
charged by billing at 05:30 on the customer's billing weekday; `ordered_at` is the charge) or `addon` (an extra item,
ordered at any time). Each order exists in the order system, which the loaders read, from its `ordered_at` on.
The nightly `legacy_orders` job writes the table: each run selects orders from the order system and sends them to
`orders` in one transaction.

### `tickets`
`ticket_id, customer_id, opened_at, topic, _loaded_at`: support tickets, written by change data capture from the
support desk 1 to 30 seconds after `opened_at`.

### `status_snapshots`
`customer_id, snapshot_date, status, _loaded_at`: the billing system's account status (`active`, `paused`,
`payment_failed` or `cancelled`) at the end of day `snapshot_date`. Billing records a row for a customer on the
sign-up day, on every day the status changed, and on the first day of every month, up to the cancellation (a
`cancelled` row is the customer's last); there is at most one row per customer and date.
`billing_export` writes each day's partition (all the rows dated D) in one transaction.

### `labels`
`customer_id, as_of, churned_30d, _loaded_at`: the outcome of a prediction (`customer_id` and `as_of` as in
`scoring_points`): `churned_30d` is 1 if the customer cancelled in `(as_of, as_of + 30 days]`, else 0. The outcome
becomes known at the cancellation, or when the 30 days have passed without one.
`label_job` writes, in one transaction per run, a row for each prediction whose outcome became known before the run
started and that has no row yet.

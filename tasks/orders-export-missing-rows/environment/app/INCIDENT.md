# INC-2291 (P1): nightly order export is missing orders

**Reported** 2026-10-27 08:12 UTC by Finance Operations (month-end reconciliation)
**Service** orders API (`/app/orders_service`), owned by the commerce backend team
**Severity** P1: the accounting close is blocked

## What happened
The nightly export job (`/app/tools/export_orders.py`, cron 02:00 UTC) pages through `GET /orders` with
`limit=200` and writes one CSV row per order. Last night's file has **47,961 rows**. `GET /orders/count`,
called by the same job right before the first page, returned **48,213**. The reconciliation against the payment
processor flags the 252 missing orders. Finance spot-checked a few of them: they exist and look normal.

Nothing in the export job changed this month. The request log of last night's run is
`/app/logs/export-2026-10-27.log`. `/app/data/orders.db` is a copy of the production database taken when the
export started (no orders were written during that run).

## What we need
Find why the export loses orders and fix the orders API so that a client that follows `next_cursor` from the first
page to the last gets every order exactly once, as `/app/docs/API.md` promises. The same holds for every listing that
pages, not only `/orders`. Checkout, the POS sync and the import jobs keep writing orders into the same database
while exports run, so the fix must hold while new orders arrive.

## Notes from the on-call engineer
- Smaller page sizes seem to lose more orders. A re-run with `limit=500` lost fewer, but still some.
- The support tool (`GET /customers/<id>/orders`, which asks for pages of 20) showed wholesale account 5 with
  20 orders, while its invoice history has 61. Possibly related, not confirmed.

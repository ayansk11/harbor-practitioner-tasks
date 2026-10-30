Our nightly finance export lost orders: last night's file has 47,961 rows while `GET /orders/count` said 48,213. The
ticket is `/app/INCIDENT.md`. The export pages through our orders API, a Flask service in `/app/orders_service` whose
contract is `/app/docs/API.md`; `/app/README.md` says how to run the service, the export (`/app/tools/export_orders.py`)
and the tests. `/app/data/orders.db` is a copy of the production database taken when that export started, and
`/app/logs/export-2026-10-27.log` is the export's request log.

Find why orders go missing and fix the service so that every listing keeps the promises in `API.md`: a client that
follows `next_cursor` from the first page to the last gets every order exactly once, in the documented order, with the
documented page sizes, also while other systems insert new orders into the database.

How your fix will be checked:
- We copy `/app` to another folder and start the service from there, as an unprivileged user, with
  `python -m orders_service --db <path> --port <port>`, on a fresh copy of a different database with the same schema
  (other customers and orders, many orders sharing one second, backfilled orders with high ids and old dates). Do not
  depend on the ids, dates or counts of the development data, on absolute `/app` paths, or on running as root. The
  service must answer `GET /orders/count` within 30 seconds of starting and each request within 10 seconds (a request
  that gets no answer in time or loses its connection is sent once more; if that also fails, the check fails). We send
  about 5,300 requests (page walks of `/orders` and `/customers/<id>/orders` at page sizes from 1 to 500), and all of
  them together must finish within 900 seconds.
- We compare the order ids of every walk with the order `API.md` defines, and check page sizes, `next_cursor`, the
  error codes in `API.md`, that every order in listings and from `GET /orders/<id>` has at least the fields in
  `API.md`, with the same values as the service gives today, and that `GET /orders/count` gives the same count.
- During one walk of `/orders` and one walk of a customer's orders, between two of our requests, another process
  inserts orders into the database file (an `INSERT` into `orders` naming its existing columns, as checkout and the
  POS sync do): new orders, and orders synced late with high ids and old dates. Every order that existed when the walk
  started must come back exactly once and in order, and no inserted order more than once. Walks, customer listings and
  `GET /orders/count` made afterwards must include every inserted order.
- The service must not change stored data: after our requests we read the `orders` and `customers` tables from the
  database file directly, and every stored order and customer must be unchanged (plus the inserted orders). You may
  add indexes, but `orders` and `customers` must stay tables, and their columns must keep their names and meaning.

Only /app is kept when we grade: folders named `data`, `__pycache__` or `.venv` anywhere under /app are dropped, and the packages already installed are available.

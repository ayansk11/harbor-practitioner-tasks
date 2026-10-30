# orders-api

Read-only HTTP API over the merchant's orders database (Flask, served by waitress). Contract: `docs/API.md`.
Open incident: `INCIDENT.md`.

| Path | What |
|---|---|
| `orders_service/app.py` | routes |
| `orders_service/pagination.py` | `limit` and cursor parsing, the shared keyset pagination helper |
| `orders_service/queries.py` | customer views (account page, support tool) |
| `orders_service/db.py` | one SQLite connection per request, the order fields |
| `orders_service/__main__.py` | `python -m orders_service --db ... --port ...` |
| `tools/export_orders.py` | the nightly finance export (a client of `GET /orders`) |
| `tests/test_api.py` | API tests (pytest, Flask test client, small temporary databases) |
| `data/orders.db` | development copy of the production database, taken when the 2026-10-27 export started |
| `logs/export-2026-10-27.log` | request log of that export |

Run the service and the export against the development copy:

```
cd /app
python -m orders_service --db data/orders.db --port 8080 &
python tools/export_orders.py --base http://127.0.0.1:8080 --limit 200 --out /tmp/orders.csv
```

Run the tests: `cd /app && python -m pytest -q tests`. Inspect the data: `python -c "import sqlite3; ..."` (there is
no `sqlite3` command-line tool in the image).

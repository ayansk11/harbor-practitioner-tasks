# Orders API (v1)

Read-only HTTP API over the merchant's orders database. Clients: the nightly finance export
(`tools/export_orders.py`), the support tool and the customer account page. The API never writes orders; checkout, the
POS sync and the import jobs insert them into the same database, also while clients are paging.

Start: `python -m orders_service --db <path to orders.db> --port <port>` from `/app`. It listens on 127.0.0.1.
All responses are JSON. An error answers `{"error": "<message>"}` with the status code given below.

## The order object
| Field | Type | Meaning |
|---|---|---|
| `id` | integer | order id. Ids grow in the order rows are written, not in the order orders were placed: an order synced late (for example an offline POS sale) has a high id and an old `created_at`. |
| `customer_id` | integer | the customer who placed the order |
| `created_at` | string | when the order was placed, UTC, `YYYY-MM-DDTHH:MM:SSZ`, whole seconds. Many orders can share one second (bulk imports write hundreds at once). |
| `status` | string | `paid`, `shipped`, `refunded` or `cancelled` |
| `total_cents` | integer | order total in the currency's minor unit |
| `currency` | string | ISO 4217 code |

## Listings and paging
`GET /orders` and `GET /customers/<id>/orders` return pages of orders.

- **Order.** Newest first: by `created_at` descending; orders with the same `created_at` by `id` descending.
- **`limit`** (query parameter): page size, an integer from 1 to 500. Default 100 when the parameter is absent.
- **`cursor`** (query parameter): leave it out for the first page; for the next page, pass the `next_cursor` value
  of the previous page exactly as received. Cursors are opaque strings: clients do not build or read them.
- **Response 200:** `{"orders": [<order>, ...], "next_cursor": "<string>" or null}`.
- Every page holds exactly `limit` orders, except the last page, which holds at most `limit`.
- `next_cursor` is null on the last page and only there. When the number of orders is a multiple of `limit`, the
  last page may be empty.
- Following `next_cursor` from the first page to the last returns every order of the listing exactly once, in the
  order above.
- **Orders written while a client pages:** every order that existed when the client asked for the first page is
  returned exactly once. An order written after that may or may not appear in that pass, and never more than once.
  A listing started later includes it.
- **Errors:** `400` if `limit` is not an integer from 1 to 500; `400` if `cursor` is malformed.

## Endpoints
### `GET /orders`
All orders, paged as above.

### `GET /orders/count`
`{"count": <number of orders>}`.

### `GET /orders/<id>`
The order object. `404` if there is no order with that id.

### `GET /customers/<id>/orders`
The customer's orders, paged and ordered as above. `404` if there is no customer with that id. A customer without
orders gets `{"orders": [], "next_cursor": null}`.

## Database (for maintainers)
SQLite, tables `customers` and `orders` (schema: `SELECT sql FROM sqlite_master` on `data/orders.db`). Indexes: `orders_created_at`
on `orders(created_at)`, `orders_customer` on `orders(customer_id, created_at)`. Other systems insert into `orders`
naming its columns; they rely on the tables and columns keeping their names and meaning.

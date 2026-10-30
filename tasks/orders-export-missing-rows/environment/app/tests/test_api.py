"""API tests for the orders service (run from /app: python -m pytest -q tests).

Each test builds a small database in a temporary folder and talks to the app through Flask's test client."""
import sqlite3

import pytest

from orders_service import create_app

SCHEMA = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, segment TEXT NOT NULL,
                        created_at TEXT NOT NULL);
CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL REFERENCES customers(id),
                     created_at TEXT NOT NULL, status TEXT NOT NULL, total_cents INTEGER NOT NULL,
                     currency TEXT NOT NULL, channel TEXT NOT NULL);
CREATE INDEX orders_created_at ON orders(created_at);
CREATE INDEX orders_customer ON orders(customer_id, created_at);
"""


def make_db(path, n_orders=57):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
                    [(c, f"Customer {c}", f"c{c}@example.org", "retail", "2025-01-01T00:00:00Z") for c in (1, 2, 3)])
    rows = []
    for i in range(1, n_orders + 1):
        minute, second = divmod(i * 7, 60)
        rows.append((i, 1 + i % 2, f"2026-03-01T10:{minute:02d}:{second:02d}Z", "paid", 1000 + i, "USD", "web"))
    con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    con.commit()
    con.close()
    return rows


@pytest.fixture()
def client(tmp_path):
    db = tmp_path / "orders.db"
    make_db(db)
    return create_app(str(db)).test_client()


def walk(client, path, limit):
    out, cursor = [], None
    for _ in range(1000):
        q = {"limit": limit} if cursor is None else {"limit": limit, "cursor": cursor}
        body = client.get(path, query_string=q).get_json()
        out += body["orders"]
        cursor = body["next_cursor"]
        if cursor is None:
            return out
    raise AssertionError("too many pages")


def test_count(client):
    assert client.get("/orders/count").get_json() == {"count": 57}


def test_get_order(client):
    assert client.get("/orders/5").get_json() == {"id": 5, "customer_id": 2, "created_at": "2026-03-01T10:00:35Z",
                                                  "status": "paid", "total_cents": 1005, "currency": "USD"}
    assert client.get("/orders/999").status_code == 404


def test_first_page_newest_first(client):
    body = client.get("/orders").get_json()
    assert [o["id"] for o in body["orders"]] == list(range(57, 0, -1))
    assert body["next_cursor"] is None


@pytest.mark.parametrize("limit", [1, 5, 10, 57, 100])
def test_walk_returns_every_order_once(client, limit):
    ids = [o["id"] for o in walk(client, "/orders", limit)]
    assert ids == list(range(57, 0, -1))


def test_customer_orders(client):
    ids = [o["id"] for o in walk(client, "/customers/1/orders", 4)]
    assert ids == [i for i in range(57, 0, -1) if i % 2 == 0]
    assert client.get("/customers/3/orders").get_json() == {"orders": [], "next_cursor": None}
    assert client.get("/customers/42/orders").status_code == 404


@pytest.mark.parametrize("query", ["limit=0", "limit=501", "limit=-1", "limit=ten", "cursor=not-a-cursor"])
def test_bad_parameters(client, query):
    assert client.get(f"/orders?{query}").status_code == 400

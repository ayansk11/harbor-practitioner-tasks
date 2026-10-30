"""Regression tests for INC-2291: pages that end inside a group of orders sharing one created_at second."""
import sqlite3

import pytest

from orders_service import create_app
from test_api import SCHEMA


def make_db(path):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
                    [(c, f"Customer {c}", f"c{c}@example.org", "retail", "2025-01-01T00:00:00Z") for c in (1, 2)])
    rows, oid = [], 0
    for second, size in enumerate([1, 7, 1, 13, 2, 30, 1]):         # same-second groups of several sizes
        for _ in range(size):
            oid += 1
            rows.append((oid, 1 + oid % 2, f"2026-03-01T10:00:{second:02d}Z", "paid", 1000 + oid, "USD", "import"))
    rows.append((oid + 1, 1, "2026-03-01T10:00:03Z", "paid", 5, "USD", "pos_backfill"))   # late id, old second
    con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    con.commit()
    con.close()
    return sorted(rows, key=lambda r: (r[2], r[0]), reverse=True)


def walk(client, path, limit):
    out, cursor = [], None
    for _ in range(1000):
        q = {"limit": limit} if cursor is None else {"limit": limit, "cursor": cursor}
        body = client.get(path, query_string=q).get_json()
        out += [o["id"] for o in body["orders"]]
        cursor = body["next_cursor"]
        if cursor is None:
            return out
    raise AssertionError("too many pages")


@pytest.mark.parametrize("limit", [1, 2, 3, 5, 8, 13, 100])
def test_pages_inside_same_second_groups(tmp_path, limit):
    rows = make_db(tmp_path / "orders.db")
    client = create_app(str(tmp_path / "orders.db")).test_client()
    assert walk(client, "/orders", limit) == [r[0] for r in rows]
    assert walk(client, "/customers/1/orders", limit) == [r[0] for r in rows if r[1] == 1]

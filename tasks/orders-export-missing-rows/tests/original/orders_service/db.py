"""One SQLite connection per request. Other systems (checkout, the POS sync, back-office imports) write to the same
database file, so the API never caches rows: every request reads what is committed at that moment."""
import sqlite3

from flask import current_app, g

ORDER_FIELDS = ("id", "customer_id", "created_at", "status", "total_cents", "currency")
ORDER_COLUMNS = ", ".join(ORDER_FIELDS)


def get_db():
    if "db" not in g:
        con = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        con.row_factory = sqlite3.Row
        g.db = con
    return g.db


def close_db(_exc=None):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def order_json(row):
    return {name: row[name] for name in ORDER_FIELDS}

"""Flask application for the orders API. Endpoints and response formats: docs/API.md."""
from flask import Flask, abort, jsonify, request
from werkzeug.exceptions import HTTPException

from . import db, pagination, queries


def create_app(database):
    app = Flask(__name__)
    app.config["DATABASE"] = database
    app.json.sort_keys = False
    app.teardown_appcontext(db.close_db)

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error=exc.description), exc.code

    @app.get("/orders")
    def list_orders():
        con = db.get_db()
        limit = pagination.parse_limit(request.args.get("limit"))
        after = pagination.parse_cursor(request.args.get("cursor"), con)
        if after is None:
            rows = con.execute(f"SELECT {db.ORDER_COLUMNS} FROM orders ORDER BY created_at DESC, id DESC LIMIT ?",
                               (limit + 1,)).fetchall()
        else:
            # strictly after order `after` in (created_at DESC, id DESC): an older second, or the same second and a
            # lower id. The `<=` bound lets SQLite range-scan orders_created_at.
            rows = con.execute(
                f"SELECT {db.ORDER_COLUMNS} FROM orders "
                "WHERE created_at <= (SELECT created_at FROM orders WHERE id = :after) "
                "AND (created_at < (SELECT created_at FROM orders WHERE id = :after) OR id < :after) "
                "ORDER BY created_at DESC, id DESC LIMIT :n", {"after": after, "n": limit + 1}).fetchall()
        rows, next_cursor = pagination.page_and_cursor(rows, limit)
        return jsonify(orders=[db.order_json(r) for r in rows], next_cursor=next_cursor)

    @app.get("/orders/count")
    def count_orders():
        (n,) = db.get_db().execute("SELECT COUNT(*) FROM orders").fetchone()
        return jsonify(count=n)

    @app.get("/orders/<int:order_id>")
    def get_order(order_id):
        row = db.get_db().execute(f"SELECT {db.ORDER_COLUMNS} FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            abort(404, description="order not found")
        return jsonify(db.order_json(row))

    @app.get("/customers/<int:customer_id>/orders")
    def customer_orders(customer_id):
        con = db.get_db()
        if not queries.customer_exists(con, customer_id):
            abort(404, description="customer not found")
        limit = pagination.parse_limit(request.args.get("limit"))
        after = pagination.parse_cursor(request.args.get("cursor"), con)
        rows = queries.customer_orders_page(con, customer_id, limit, after)
        rows, next_cursor = pagination.page_and_cursor(rows, limit)
        return jsonify(orders=[db.order_json(r) for r in rows], next_cursor=next_cursor)

    return app

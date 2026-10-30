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
        limit = pagination.parse_limit(request.args.get("limit"))
        cursor = pagination.decode_cursor(request.args.get("cursor"))
        rows, next_cursor = pagination.paginate(db.get_db(), db.ORDER_COLUMNS, "orders", limit, cursor)
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
        cursor = pagination.decode_cursor(request.args.get("cursor"))
        rows, next_cursor = queries.customer_orders_page(con, customer_id, limit, cursor)
        return jsonify(orders=[db.order_json(r) for r in rows], next_cursor=next_cursor)

    return app

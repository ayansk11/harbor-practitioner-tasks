"""Flask application for the orders API (attempt G: everything served from a start-up snapshot)."""
from flask import Flask, abort, jsonify, request
from werkzeug.exceptions import HTTPException

from . import pagination
from .snapshot import Snapshot


def create_app(database):
    app = Flask(__name__)
    app.json.sort_keys = False
    snap = Snapshot(database)

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error=exc.description), exc.code

    @app.get("/orders")
    def list_orders():
        limit = pagination.parse_limit(request.args.get("limit"))
        rows, nxt = snap.page(snap.all, limit, request.args.get("cursor"))
        return jsonify(orders=rows, next_cursor=nxt)

    @app.get("/orders/count")
    def count_orders():
        return jsonify(count=len(snap.all))

    @app.get("/orders/<int:order_id>")
    def get_order(order_id):
        if order_id not in snap.by_id:
            abort(404, description="order not found")
        return jsonify(snap.by_id[order_id])

    @app.get("/customers/<int:customer_id>/orders")
    def customer_orders(customer_id):
        if customer_id not in snap.customers:
            abort(404, description="customer not found")
        limit = pagination.parse_limit(request.args.get("limit"))
        rows, nxt = snap.page(snap.by_customer.get(customer_id, []), limit, request.args.get("cursor"))
        return jsonify(orders=rows, next_cursor=nxt)

    return app

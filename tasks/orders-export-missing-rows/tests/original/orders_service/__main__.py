"""Start the orders API: python -m orders_service --db data/orders.db --port 8080"""
import argparse
import os

from waitress import serve

from .app import create_app


def main():
    parser = argparse.ArgumentParser(prog="python -m orders_service", description=__doc__)
    parser.add_argument("--db", required=True, help="path to the SQLite orders database")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if not os.path.isfile(args.db):
        parser.error(f"database not found: {args.db}")
    app = create_app(os.path.abspath(args.db))
    serve(app, host=args.host, port=args.port, threads=args.threads, ident="orders-api")


if __name__ == "__main__":
    main()

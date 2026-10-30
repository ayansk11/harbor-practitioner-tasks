"""Run the API: python -m docshare.serve --db <path> --port <port>."""
import argparse
import os
import sys

from waitress import serve

from . import db
from .app import create_app


def main(argv=None):
    p = argparse.ArgumentParser(description="docshare API server")
    p.add_argument("--db", required=True, help="path to an existing docshare SQLite database")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--threads", type=int, default=4)
    args = p.parse_args(argv)
    if not os.path.isfile(args.db):
        sys.exit(f"database not found: {args.db}")
    conn = db.connect(args.db)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.close()
    serve(create_app(os.path.abspath(args.db)), host=args.host, port=args.port, threads=args.threads,
          ident="docshare")


if __name__ == "__main__":
    main()

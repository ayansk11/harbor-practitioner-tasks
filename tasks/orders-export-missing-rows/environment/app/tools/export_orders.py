"""Nightly finance export: page through GET /orders and write one CSV row per order.

    python tools/export_orders.py --base http://127.0.0.1:8080 --limit 200 --out /tmp/orders.csv [--log export.log]

Runs from cron at 02:00 UTC against production. It only follows next_cursor; it never builds cursors itself.
"""
import argparse
import csv
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request

FIELDS = ["id", "customer_id", "created_at", "status", "total_cents", "currency"]


def now():
    t = dt.datetime.now(dt.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def get(base, path, params=None):
    url = base.rstrip("/") + path + ("?" + urllib.parse.urlencode(params) if params else "")
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.status, json.load(resp)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", help="append the request log here (default: stderr)")
    args = ap.parse_args()
    log = open(args.log, "a") if args.log else sys.stderr
    print(f"# export_orders.py started {now()} base={args.base} limit={args.limit} out={args.out}", file=log)
    status, body = get(args.base, "/orders/count")
    total = body["count"]
    print(f"{now()} GET /orders/count {status} count={total}", file=log)
    rows = pages = 0
    cursor = None
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        while True:
            params = {"limit": args.limit}
            if cursor is not None:
                params["cursor"] = cursor
            status, body = get(args.base, "/orders", params)
            pages += 1
            for o in body["orders"]:
                w.writerow([o[k] for k in FIELDS])
            rows += len(body["orders"])
            shown = "/orders?" + "&".join(f"{k}={v}" for k, v in params.items())
            print(f"{now()} GET {shown} {status} rows={len(body['orders'])} next_cursor={body['next_cursor'] or 'null'}",
                  file=log)
            cursor = body["next_cursor"]
            if cursor is None:
                break
    print(f"# done {now()}: {rows} rows written, {pages} pages, count at start was {total}", file=log)
    if log is not sys.stderr:
        log.close()


if __name__ == "__main__":
    main()

#!/bin/bash
# Reference solutions for tenant-isolation-docshare. Each variant is a set of replacement files copied over
# /app/docshare (nothing here reads /tests or any expected answer).
#   SOLUTION unset or "canonical": central access check (docshare/access.py) used by every file endpoint, and
#                                  X-Org-Id checked against the caller's memberships.
#   SOLUTION=alt:                  no central helper; every SQL query is scoped by the caller's org and role,
#                                  refusals are 403 instead of 404.
#   SOLUTION=<attempt>:            a wrong or shortcut attempt from attempts/<attempt>/ (each must score 0).
# APP_DIR (default /app) lets the local authoring harness apply a variant to a scratch copy.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP_DIR:-/app}"
VARIANT="${SOLUTION:-canonical}"
case "$VARIANT" in
  canonical) SRC="$HERE/canonical" ;;
  alt) SRC="$HERE/alt" ;;
  *) SRC="$HERE/attempts/$VARIANT" ;;
esac
if [ ! -d "$SRC/docshare" ]; then
  echo "unknown SOLUTION=$VARIANT" >&2
  exit 2
fi
cp -R "$SRC/docshare/." "$APP/docshare/"
find "$APP/docshare" -name __pycache__ -type d -prune -exec rm -rf {} +
echo "applied $VARIANT to $APP/docshare"

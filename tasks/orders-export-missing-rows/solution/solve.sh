#!/bin/bash
# Reference solutions for orders-export-missing-rows. Nothing here reads /tests or any expected answer.
#   SOLUTION unset or "canonical": the cursor carries the full sort key (created_at, id), and one shared
#                                  keyset_clause() (a row-value comparison) is used by both listings.
#   SOLUTION=alt:                  a different fix: the cursor is only the last order's id, each route writes its own
#                                  OR-expanded predicate with sub-selects, and pages are fetched with limit + 1.
#   SOLUTION=<attempt>:            a wrong or shortcut attempt from attempts/<attempt>/ (each must score 0; see its
#                                  ABOUT.md).
# A variant folder holds app/ (files copied over /app) and, if needed, apply.py (run as: python3 apply.py <app dir>).
# APP_DIR (default /app) lets the local authoring harness apply a variant to a scratch copy.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP_DIR:-/app}"
VARIANT="${SOLUTION:-canonical}"
case "$VARIANT" in
  canonical|alt) SRC="$HERE/$VARIANT" ;;
  *) SRC="$HERE/attempts/$VARIANT" ;;
esac
if [ ! -d "$SRC" ]; then
  echo "unknown SOLUTION=$VARIANT" >&2
  exit 2
fi
if [ -d "$SRC/app" ]; then
  cp -R "$SRC/app/." "$APP/"
fi
if [ -f "$SRC/apply.py" ]; then
  python3 "$SRC/apply.py" "$APP"
fi
find "$APP" -name __pycache__ -type d -prune -exec rm -rf {} +
echo "applied $VARIANT to $APP"

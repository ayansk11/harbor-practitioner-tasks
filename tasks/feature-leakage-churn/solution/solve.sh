#!/bin/bash
# Reference solutions for feature-leakage-churn.
#   SOLUTION unset or canonical : fix the four leaks in place (windows.py, encoding.py, status.py, impute.py)
#   SOLUTION=alt                : replace the CLI with a per-row implementation (bisect + sqlite3, no pandas)
#   SOLUTION=<attempt>          : one of the wrong or shortcut attempts in attempts/ (each must score 0)
# APP_DIR (default /app) lets the authoring harness apply a solution to a copy of /app.
set -euo pipefail
APP="${APP_DIR:-/app}"
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "${SOLUTION:-canonical}" in
  canonical) cp "$SOL"/canonical/churn/*.py "$APP/churn/" ;;
  alt) cp "$SOL"/alt/churn/*.py "$APP/churn/" ;;
  *)
    if [ ! -f "$SOL/attempts/${SOLUTION}.py" ]; then echo "unknown SOLUTION=${SOLUTION}" >&2; exit 2; fi
    python3 "$SOL/attempts/${SOLUTION}.py" "$APP"
    exit 0 ;;
esac
# Smoke test for the two valid solutions: rebuild the visible feature table (not graded; /app/output is kept in the
# artifact, about 1.3 MB).
cd "$APP" && python3 -m churn.build_features --data "$APP/data" --out "$APP/output/features.parquet"

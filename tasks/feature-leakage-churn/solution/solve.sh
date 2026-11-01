#!/bin/bash
# Reference solutions for feature-leakage-churn (the oracle runs the default, canonical).
#   SOLUTION unset or canonical : copy solution/canonical/churn/*.py over /app/churn (pandas and numpy, on top of the
#                                 v3 pipeline): every feature from the rows the warehouse held at as_of (_loaded_at,
#                                 for orders not before the cutover's commit; for orders below the last legacy
#                                 watermark, the commit of the legacy_orders transaction whose range holds them, from
#                                 _ops/), the plan rebuilt from plan_changes, days_since_last_login left out
#   SOLUTION=alt                : copy solution/alt/churn/*.py over /app/churn (an event replay in pure Python, no
#                                 pandas)
#   SOLUTION=<attempt>          : run solution/attempts/<attempt>.py on /app (a realistic wrong or shortcut answer;
#                                 each must score 0)
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
# artifact, about 1.5 MB for the canonical).
cd "$APP" && python3 -m churn.build_features --data "$APP/data" --out "$APP/output/features.parquet"

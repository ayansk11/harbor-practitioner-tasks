#!/bin/bash
# Reference solution for ab-test-reanalysis.
#   default / SOLUTION=canonical : bots out of both arms; user-level delta-method CI; SRM chi-square; the plan's
#                                  decision rule (canonical/filters.py, stats.py, report.py)
#   SOLUTION=alt                 : user-level bootstrap (5,000 resamples, fixed seed), numpy per-user sums (alt/)
#   SOLUTION=alt_cr1             : CR1 cluster-robust errors from a pageview-level regression (alt_cr1/stats.py)
#   SOLUTION=nop                 : change nothing (the original state)
#   SOLUTION=<attempt>           : a wrong or shortcut attempt (attempts/; each must score 0):
#       hardcode_no_ship, fix_visible_result_only, fix_bots_only, mean_of_ratios, no_srm_gate,
#       constant_inflation, fix_ci_only (CI, SRM and decision fixed; the B-only bot filter left in place),
#       icc_tuned (pageview CI x sqrt(1 + rho (m_w - 1)) per arm with one rho tuned on every graded set),
#       kish_tuned (pageview CI with each arm's variance x K^g, K = mean(v^2)/mean(v)^2, one g tuned on every set)
# APP_DIR (default /app) lets the authoring harness run this on a local copy. Nothing here reads /tests.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP_DIR:-/app}"
PY="${PYTHON:-python3}"
PKG="$APP/abtest"

regen() {
  (cd "$APP" && "$PY" -m abtest.report --data data --out output/result.json)
}
canonical() {
  cp "$HERE/canonical/filters.py" "$HERE/canonical/stats.py" "$HERE/canonical/report.py" "$PKG/"
}

case "${SOLUTION:-canonical}" in
  canonical)
    canonical; regen ;;
  alt)
    cp "$HERE/alt/filters.py" "$HERE/alt/stats.py" "$HERE/alt/report.py" "$PKG/"; regen ;;
  alt_cr1)
    canonical; cp "$HERE/alt_cr1/stats.py" "$PKG/"; regen ;;
  nop)
    : ;;
  hardcode_no_ship|no_srm_gate|mean_of_ratios)
    canonical; "$PY" "$HERE/attempts/${SOLUTION}/patch.py" "$APP"; regen ;;
  fix_bots_only|constant_inflation|icc_tuned|kish_tuned)
    canonical; cp "$HERE/attempts/${SOLUTION}/stats.py" "$PKG/"; regen ;;
  fix_ci_only)
    cp "$HERE/canonical/stats.py" "$HERE/canonical/report.py" "$PKG/"; regen ;;
  fix_visible_result_only)
    "$PY" "$HERE/attempts/fix_visible_result_only/oneoff.py" "$APP" ;;
  *)
    echo "unknown SOLUTION=${SOLUTION}" >&2
    exit 2 ;;
esac

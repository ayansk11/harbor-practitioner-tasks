#!/bin/bash
# Solutions for ab-test-reanalysis. SOLUTION picks one (default canonical):
#   canonical      the plan's readout: users randomized by the hash only (override accounts out), users with a
#                  ua_crawler flag out of both arms (velocity flags read in-experiment clicks and exclude no one), a
#                  counted pageview is clicked when it has an item: event, user-level delta-method CI, SRM chi-square,
#                  the plan's decision (canonical/: load.py, filters.py, stats.py, report.py)
#   alt_time       population by time (no flag of any rule at or before assigned_at), pandas joins and groupby sums,
#                  user-level bootstrap, 5,000 resamples, fixed seed, percentile (alt_time/)
#   alt_recount    csv and gzip readers, numpy bincount sums, ua_crawler plus the velocity rule recounted on item:
#                  events, CR1 cluster-robust CI by user (alt_recount/)
#   nop            change nothing (the shipped state)
#   <attempt>      a wrong or shortcut attempt that must score 0: attempts/<attempt>/ or attempts/<attempt>.py
# canonical and every alt* folder are complete sets of abtest modules, copied over the shipped ones.
# An attempt folder attempts/<attempt>/ is applied in this order:
#   1. base: canonical, unless the folder has a file BASE whose first word is "shipped" (the shipped code stays);
#   2. every *.py file of the folder except patch.py and oneoff.py is copied into abtest/;
#   3. patch.py, if present, runs as: python patch.py <APP>  (it edits files under <APP> in place);
#   4. oneoff.py, if present, runs as: python oneoff.py <APP>  instead of step 5 (it writes output/result.json);
#   5. output/result.json is regenerated with the package's own command.
# An attempt file attempts/<attempt>.py runs as patch.py on the canonical base, then step 5. Names starting with "_"
# are helpers, never a SOLUTION. APP_DIR (default /app) lets the authoring harness run this on a local copy, PYTHON
# (default python3) names the interpreter. Nothing here reads /tests.
set -euo pipefail
shopt -s nullglob
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP_DIR:-/app}"
PY="${PYTHON:-python3}"
PKG="$APP/abtest"
SOL="${SOLUTION:-canonical}"

die() {
  echo "solve.sh: $*" >&2
  exit 2
}

regen() {
  (cd "$APP" && "$PY" -m abtest.report --data data --out output/result.json)
}

modules() {   # copy the abtest modules of one solution folder over the package
  local f
  for f in "$1"/*.py; do
    case "${f##*/}" in
      patch.py|oneoff.py) ;;
      *) cp "$f" "$PKG/" ;;
    esac
  done
}

[[ "$SOL" =~ ^[A-Za-z0-9][A-Za-z0-9_]*$ ]] || die "invalid SOLUTION=$SOL"
echo "solve.sh: SOLUTION=$SOL"
case "$SOL" in
  canonical)
    modules "$HERE/canonical"; regen ;;
  nop)
    : ;;
  alt*)
    [ -d "$HERE/$SOL" ] || die "unknown SOLUTION=$SOL"
    modules "$HERE/$SOL"; regen ;;
  *)
    d="$HERE/attempts/$SOL"
    if [ -d "$d" ]; then
      base=canonical
      if [ -f "$d/BASE" ]; then
        { read -r base _ || true; } < "$d/BASE"
      fi
      case "$base" in
        canonical) modules "$HERE/canonical" ;;
        shipped) ;;
        *) die "attempts/$SOL/BASE: unknown base '$base'" ;;
      esac
      modules "$d"
      if [ -f "$d/patch.py" ]; then
        "$PY" "$d/patch.py" "$APP"
      fi
      if [ -f "$d/oneoff.py" ]; then
        "$PY" "$d/oneoff.py" "$APP"
      else
        regen
      fi
    elif [ -f "$d.py" ]; then
      modules "$HERE/canonical"; "$PY" "$d.py" "$APP"; regen
    else
      die "unknown SOLUTION=$SOL"
    fi ;;
esac

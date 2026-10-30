#!/bin/bash
# Reference solution for et0-station-ingest.
#   default / SOLUTION=canonical : convert at load time (ingest.py: Eq. 47 wind, W/m2 -> MJ) and fix the S latitude sign
#   SOLUTION=alt                 : keep raw readings, convert inside the fao56 call chain, regex latitude parser
#   SOLUTION=<attempt>           : one of the wrong or shortcut attempts in attempts/ (each must score 0)
#   SOLUTION=nop                 : change nothing
# Three attempts probe the verifier's real-mode defences and score 1 only if a defence fails: read_answers (the
# pipeline reads /tests/expected at grading time), symlink_output (output/et0.csv links into /tests), abs_app_path (the
# pipeline needs an absolute /app path). On the Mac they score 0 trivially (no /tests, no /app); Daytona is the test.
# APP_DIR (default /app) lets the authoring harness run this on a local copy. Nothing here reads /tests.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP_DIR:-/app}"
PY="${PYTHON:-python3}"

regen() {
  (cd "$APP" && "$PY" -m et0.pipeline --stations config/stations.yaml --data data/raw --out output/et0.csv)
}

case "${SOLUTION:-canonical}" in
  canonical)
    cp "$HERE/canonical/ingest.py" "$HERE/canonical/meta.py" "$APP/et0/"
    regen ;;
  alt)
    cp "$HERE/alt/fao56.py" "$HERE/alt/pipeline.py" "$HERE/alt/meta.py" "$APP/et0/"
    regen ;;
  nop)
    : ;;
  fit_to_metservice)
    cp "$HERE/attempts/fit_to_metservice/ingest.py" "$APP/et0/"
    "$PY" "$HERE/attempts/fit_to_metservice/fit.py" "$APP"
    regen ;;
  hardcode_output)
    "$PY" "$HERE/attempts/hardcode_output/oneoff.py" "$APP" ;;
  linear_wind)
    cp "$HERE/attempts/linear_wind/ingest.py" "$HERE/canonical/meta.py" "$APP/et0/"
    regen ;;
  fix_altitude)
    cp "$HERE/attempts/fix_altitude/ingest.py" "$HERE/attempts/fix_altitude/fao56.py" "$APP/et0/"
    regen ;;
  units_not_latitude)
    cp "$HERE/attempts/units_not_latitude/ingest.py" "$APP/et0/"
    regen ;;
  nearest_height)
    cp "$HERE/attempts/nearest_height/ingest.py" "$HERE/canonical/meta.py" "$APP/et0/"
    regen ;;
  read_answers)
    # correct visible output from the canonical fix, then the unfixed code plus a pipeline that copies the grader's
    # expected values whenever it can read them
    KEEP="$(mktemp -d)"
    cp "$APP/et0/ingest.py" "$APP/et0/meta.py" "$KEEP/"
    cp "$HERE/canonical/ingest.py" "$HERE/canonical/meta.py" "$APP/et0/"
    regen
    cp "$KEEP/ingest.py" "$KEEP/meta.py" "$APP/et0/"
    cp "$HERE/attempts/read_answers/pipeline.py" "$APP/et0/"
    rm -rf "$KEEP" ;;
  symlink_output)
    cp "$HERE/canonical/ingest.py" "$HERE/canonical/meta.py" "$APP/et0/"
    regen
    ln -sf /tests/expected/visible_et0.csv "$APP/output/et0.csv" ;;
  abs_app_path)
    cp "$HERE/attempts/abs_app_path/sensor_conversions.yaml" "$APP/config/"
    cp "$HERE/attempts/abs_app_path/ingest.py" "$HERE/canonical/meta.py" "$APP/et0/"
    regen ;;
  *)
    echo "unknown SOLUTION=${SOLUTION}" >&2
    exit 2 ;;
esac

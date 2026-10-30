"""Station summary for DESIGN.md section 5 (authoring only).

Run (repository root): .venv/bin/python authoring/et0-station-ingest/summarize.py > station_summary.out.md
Per station: reference ET0 min/mean/max (tests/expected), and for visible stations the mean of the shipped wrong
output (environment/app/output/et0.csv).
"""
import os
import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "et0-station-ingest"))
now = pd.read_csv(os.path.join(TASK, "environment/app/output/et0.csv"))
print("| Set | Station | latitude | elev m | wind m | radiation | humidity | ET0 min | ET0 mean | ET0 max | shipped output mean |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for set_name, yml, exp in [("visible", "environment/app/config/stations.yaml", "tests/expected/visible_et0.csv"),
                           ("hidden", "tests/hidden/stations.yaml", "tests/expected/hidden_et0.csv")]:
    e = pd.read_csv(os.path.join(TASK, exp))
    for s in yaml.safe_load(open(os.path.join(TASK, yml)))["stations"]:
        v = e[e.station_id == s["id"]].et0_mm_day
        n = now[now.station_id == s["id"]].et0_mm_day
        print(f"| {set_name} | {s['id']} | {s['latitude']} | {s['elevation_m']} | {s['wind_height_m']} | "
              f"{s['radiation_units']} | {s['humidity']} | {v.min():.2f} | {v.mean():.2f} | {v.max():.2f} | "
              f"{n.mean():.2f} |" if len(n) else
              f"| {set_name} | {s['id']} | {s['latitude']} | {s['elevation_m']} | {s['wind_height_m']} | "
              f"{s['radiation_units']} | {s['humidity']} | {v.min():.2f} | {v.mean():.2f} | {v.max():.2f} | - |")
    print(f"| {set_name} | all | | | | | | {e.et0_mm_day.min():.2f} | {e.et0_mm_day.mean():.2f} | {e.et0_mm_day.max():.2f} | |")

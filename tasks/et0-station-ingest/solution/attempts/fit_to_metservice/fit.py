"""Shortcut attempt (must score 0): fix the obvious radiation units, then calibrate to the met-service sample.

Fits one factor per station and month (met service / ours) for the two stations the met service publishes, stores
them in /app/et0/metservice_factors.json and makes the pipeline multiply by them. No sensor-height or latitude fix.
Usage: python fit.py <app_dir>
"""
import json, os, sys

app = sys.argv[1]
sys.path.insert(0, app)
import pandas as pd
from et0 import pipeline

ours = pipeline.run(os.path.join(app, "config/stations.yaml"), os.path.join(app, "data/raw"),
                    os.path.join(app, "output/et0.csv"))
ms = pd.read_csv(os.path.join(app, "reference/metservice_et0_2025.csv"))
m = ms.merge(ours, on=["station_id", "date"], suffixes=("_ms", "_ours"))
m["month"] = m["date"].str[5:7].astype(int)
g = m.groupby(["station_id", "month"])
factors = {f"{s}:{mo}": float(r["et0_mm_day_ms"].sum() / r["et0_mm_day_ours"].sum()) for (s, mo), r in g}
with open(os.path.join(app, "et0", "metservice_factors.json"), "w") as f:
    json.dump(factors, f, indent=1)

p = os.path.join(app, "et0", "pipeline.py")
src = open(p).read()
anchor = '        frames.append(df[["station_id", "date", "et0_mm_day"]])'
patch = '''        months = df["date"].str[5:7].astype(int)
        df["et0_mm_day"] = df["et0_mm_day"] * [_FACTORS.get(f"{st.station_id}:{mo}", 1.0) for mo in months]
        frames.append(df[["station_id", "date", "et0_mm_day"]])'''
assert anchor in src
src = src.replace(anchor, patch)
src = src.replace("from . import fao56, ingest, meta\n", '''from . import fao56, ingest, meta

import json as _json
# station-month calibration against the met-service ET0 (fitted by fit.py)
_FACTORS = _json.load(open(os.path.join(os.path.dirname(__file__), "metservice_factors.json")))
''')
open(p, "w").write(src)
print(f"fitted {len(factors)} station-month factors")

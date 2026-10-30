"""Shortcut attempt (must score 0): produce a correct /app/output/et0.csv by a one-off script, leave the pipeline broken.

The conversions (Eq. 47 for wind, 0.0864 for W/m2, the S sign of latitude) are done here, for our eight stations
only, and written straight into the output file; et0.pipeline itself is not changed.
Usage: python oneoff.py <app_dir>
"""
import math, os, sys

app = sys.argv[1]
sys.path.insert(0, app)
import pandas as pd
import yaml
from et0 import fao56

reg = yaml.safe_load(open(os.path.join(app, "config/stations.yaml")))["stations"]
frames = []
for st in reg:
    lat = st["latitude"]
    lat = -float(lat[:-1]) if isinstance(lat, str) and lat.endswith("S") else float(str(lat).rstrip("N"))
    raw = pd.read_csv(os.path.join(app, "data/raw", f"{st['id']}.csv"))
    d = pd.to_datetime(raw["date"])
    u2 = raw["wind_ms"] * 4.87 / math.log(67.8 * st["wind_height_m"] - 5.42)
    rs = raw["solar_rad"] * (0.0864 if st["radiation_units"] == "W/m2" else 1.0)
    if st["humidity"] == "dewpoint":
        ea = fao56.actual_vapour_pressure_dewpoint(raw["tdew_c"])
    else:
        ea = fao56.actual_vapour_pressure_rh(raw["tmax_c"], raw["tmin_c"], raw["rh_max_pct"], raw["rh_min_pct"])
    et0 = fao56.et0_daily(raw["tmax_c"], raw["tmin_c"], u2, rs, ea, d.dt.dayofyear, lat, st["elevation_m"])
    frames.append(pd.DataFrame({"station_id": st["id"], "date": raw["date"], "et0_mm_day": et0}))
pd.concat(frames).to_csv(os.path.join(app, "output/et0.csv"), index=False, float_format="%.3f")
print("wrote output/et0.csv")

"""Daily ET0 for every station in a register.

    python -m et0.pipeline --stations config/stations.yaml --data data/raw --out output/et0.csv
"""
import argparse
import os
import sys

import pandas as pd

from . import fao56, ingest, meta


def run(stations_path, data_dir, out_path):
    frames = []
    for st in meta.load_stations(stations_path):
        df = ingest.load_station(st, data_dir)
        df["et0_mm_day"] = fao56.et0_daily(df["tmax"], df["tmin"], df["u2"], df["rs"], df["ea"], df["doy"],
                                           st.latitude, st.elevation_m)
        frames.append(df[["station_id", "date", "et0_mm_day"]])
        print(f"{st.station_id}: {len(df)} days, mean ET0 {df['et0_mm_day'].mean():.2f} mm/day")
    out = pd.concat(frames, ignore_index=True)
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    out.to_csv(out_path, index=False, float_format="%.3f")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stations", required=True, help="station register (YAML)")
    ap.add_argument("--data", required=True, help="folder with one <station_id>.csv per station")
    ap.add_argument("--out", required=True, help="output CSV")
    args = ap.parse_args(argv)
    run(args.stations, args.data, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

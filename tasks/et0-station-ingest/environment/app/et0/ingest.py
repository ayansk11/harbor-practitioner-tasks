"""Read one station's raw daily file and turn it into the standard daily inputs used by fao56.et0_daily."""
import os

import pandas as pd

from . import fao56

BASE_COLUMNS = ["date", "tmax_c", "tmin_c", "wind_ms", "solar_rad"]
HUMIDITY_COLUMNS = {"rh_minmax": ["rh_max_pct", "rh_min_pct"], "dewpoint": ["tdew_c"]}


def load_station(station, data_dir):
    """Return a DataFrame with columns station_id, date, doy, tmax, tmin, ea, u2, rs (standard units)."""
    path = os.path.join(data_dir, f"{station.station_id}.csv")
    raw = pd.read_csv(path)
    if station.humidity not in HUMIDITY_COLUMNS:
        raise ValueError(f"{station.station_id}: unknown humidity type {station.humidity!r}")
    missing = [c for c in BASE_COLUMNS + HUMIDITY_COLUMNS[station.humidity] if c not in raw.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")

    dates = pd.to_datetime(raw["date"], format="%Y-%m-%d")
    df = pd.DataFrame({
        "station_id": station.station_id,
        "date": dates.dt.strftime("%Y-%m-%d"),
        "doy": dates.dt.dayofyear.astype(int),
        "tmax": raw["tmax_c"].astype(float),
        "tmin": raw["tmin_c"].astype(float),
    })
    if station.humidity == "dewpoint":
        df["ea"] = fao56.actual_vapour_pressure_dewpoint(raw["tdew_c"].astype(float))
    else:
        df["ea"] = fao56.actual_vapour_pressure_rh(df["tmax"], df["tmin"], raw["rh_max_pct"].astype(float),
                                                   raw["rh_min_pct"].astype(float))
    df["u2"] = raw["wind_ms"].astype(float)          # m/s at 2 m
    df["rs"] = raw["solar_rad"].astype(float)        # MJ m-2 day-1
    return df

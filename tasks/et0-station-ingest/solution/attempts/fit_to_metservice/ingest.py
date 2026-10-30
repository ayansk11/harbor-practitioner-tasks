"""Read one station's raw daily file and turn it into the standard daily inputs used by fao56.et0_daily."""
import math
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
    df["u2"] = raw["wind_ms"].astype(float)                                          # m/s at 2 m
    df["rs"] = radiation_mj(raw["solar_rad"].astype(float), station.radiation_units)   # MJ m-2 day-1
    return df


def wind_at_2m(uz, height_m):
    """FAO-56 Eq. 47: wind speed measured at height_m above ground -> wind speed at 2 m (logarithmic profile)."""
    if height_m <= 0:
        raise ValueError(f"wind sensor height must be positive, got {height_m}")
    return uz * 4.87 / math.log(67.8 * height_m - 5.42)


def radiation_mj(values, units):
    """Daily solar radiation in MJ m-2 day-1 from either unit used in the register."""
    if units == "MJ/m2/day":
        return values
    if units == "W/m2":                     # daily mean irradiance: 1 W m-2 = 0.0864 MJ m-2 day-1
        return values * 0.0864
    raise ValueError(f"unknown radiation_units {units!r}")

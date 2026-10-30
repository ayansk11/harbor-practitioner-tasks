"""Reference B: FAO-56 Penman-Monteith daily ET0, vectorised with numpy (authoring only, never shipped to /app).

Written separately from ref_a.py so that the two can check each other. Same standard and constants (FAO-56 chapter 3
and 4; the task's METHOD.md), but a different code path: whole arrays at once, the arctan form of the sunset hour angle
(Eq. 26 and 27 instead of Eq. 25), Eq. 6 as one fraction, its own wind, unit and latitude handling.
"""
import re
import numpy as np


def parse_latitude(value):
    """Signed decimal degrees from a number, a signed decimal string, or '<decimal>N' / '<decimal>S'."""
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)\s*([NnSs]?)", s)
    if not m:
        raise ValueError(f"bad latitude {value!r}")
    deg = float(m.group(1))
    if m.group(2).upper() == "S":
        deg = -abs(deg)
    elif m.group(2).upper() == "N":
        deg = abs(deg)
    return deg


def u2_from(uz, z):
    z = np.asarray(z, dtype=float)
    return np.asarray(uz, dtype=float) * (4.87 / np.log(67.8 * z - 5.42))


def rs_to_mj(rs, units):
    return np.asarray(rs, dtype=float) * (0.0864 if units == "W/m2" else 1.0)


def _sat(t):
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def et0_daily(tmax, tmin, lat_deg, elev_m, doy, u2, rs_mj=None, sunshine_h=None, rh_max=None, rh_min=None, tdew=None):
    tmax, tmin = np.asarray(tmax, float), np.asarray(tmin, float)
    tm = 0.5 * (tmax + tmin)
    p = 101.3 * np.power((293.0 - 0.0065 * np.asarray(elev_m, float)) / 293.0, 5.26)
    gam = 0.000665 * p
    e_hi, e_lo = _sat(tmax), _sat(tmin)
    es = 0.5 * (e_hi + e_lo)
    if tdew is not None:
        ea = _sat(np.asarray(tdew, float))
    else:
        ea = 0.5 * (e_lo * np.asarray(rh_max, float) + e_hi * np.asarray(rh_min, float)) / 100.0
    dlt = 4098.0 * _sat(tm) / np.square(tm + 237.3)
    phi = np.deg2rad(np.asarray(lat_deg, float))
    x = 2.0 * np.pi * np.asarray(doy, float) / 365.0
    dr = 1.0 + 0.033 * np.cos(x)
    dec = 0.409 * np.sin(x - 1.39)
    big_x = 1.0 - np.square(np.tan(phi)) * np.square(np.tan(dec))
    big_x = np.where(big_x <= 0.0, 0.00001, big_x)
    ws = np.pi / 2.0 - np.arctan(-np.tan(phi) * np.tan(dec) / np.sqrt(big_x))
    ra = (1440.0 / np.pi) * 0.0820 * dr * (ws * np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.sin(ws))
    if rs_mj is None:
        n_max = 24.0 * ws / np.pi
        rs_mj = (0.25 + 0.5 * np.asarray(sunshine_h, float) / n_max) * ra
    rs_mj = np.asarray(rs_mj, float)
    rso = (0.75 + 0.00002 * np.asarray(elev_m, float)) * ra
    rel = np.minimum(rs_mj / rso, 1.0)
    tk4 = 0.5 * (np.power(tmax + 273.16, 4) + np.power(tmin + 273.16, 4))
    rnl = 4.903e-9 * tk4 * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * rel - 0.35)
    rn = 0.77 * rs_mj - rnl
    u2 = np.asarray(u2, float)
    num = 0.408 * dlt * rn + gam * (900.0 / (tm + 273.0)) * u2 * (es - ea)
    return num / (dlt + gam * (1.0 + 0.34 * u2))

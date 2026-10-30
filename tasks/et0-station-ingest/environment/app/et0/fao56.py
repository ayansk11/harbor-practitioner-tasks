"""FAO-56 Penman-Monteith reference evapotranspiration, daily time step.

Implements the daily procedure of FAO Irrigation and Drainage Paper 56 (Allen et al., 1998), chapters 3 and 4, as
written up in /app/docs/METHOD.md. Every function works on numpy arrays (one element per day).

Inputs expected by et0_daily (already in standard form):
    tmax, tmin   daily maximum and minimum air temperature [deg C]
    u2           mean daily wind speed at 2 m above ground [m/s]
    rs           incoming solar radiation [MJ m-2 day-1]
    ea           actual vapour pressure [kPa] (see actual_vapour_pressure_*)
    doy          day of the year, 1 = 1 January
    latitude     decimal degrees, north positive, south negative
    elevation    metres above sea level
"""
import numpy as np

SOLAR_CONSTANT = 0.0820        # MJ m-2 min-1
STEFAN_BOLTZMANN = 4.903e-9    # MJ K-4 m-2 day-1
ALBEDO = 0.23                  # hypothetical grass reference


def atmospheric_pressure(elevation):
    """Eq. 7, kPa."""
    return 101.3 * ((293.0 - 0.0065 * np.asarray(elevation, float)) / 293.0) ** 5.26


def psychrometric_constant(pressure):
    """Eq. 8, kPa/degC."""
    return 0.665e-3 * pressure


def saturation_vapour_pressure(t):
    """Eq. 11, kPa."""
    t = np.asarray(t, float)
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def vapour_pressure_slope(t):
    """Eq. 13, kPa/degC."""
    t = np.asarray(t, float)
    return 4098.0 * saturation_vapour_pressure(t) / (t + 237.3) ** 2


def actual_vapour_pressure_rh(tmax, tmin, rh_max, rh_min):
    """Eq. 17, kPa, from daily maximum and minimum relative humidity [%]."""
    return (saturation_vapour_pressure(tmin) * np.asarray(rh_max, float) / 100.0
            + saturation_vapour_pressure(tmax) * np.asarray(rh_min, float) / 100.0) / 2.0


def actual_vapour_pressure_dewpoint(tdew):
    """Eq. 14, kPa, from the daily mean dewpoint temperature [degC]."""
    return saturation_vapour_pressure(tdew)


def extraterrestrial_radiation(latitude, doy):
    """Eqs. 21-25: Ra [MJ m-2 day-1] and the sunset hour angle ws [rad]."""
    phi = np.deg2rad(np.asarray(latitude, float))
    doy = np.asarray(doy, float)
    dr = 1.0 + 0.033 * np.cos(2.0 * np.pi * doy / 365.0)
    decl = 0.409 * np.sin(2.0 * np.pi * doy / 365.0 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(decl), -1.0, 1.0))
    ra = (24.0 * 60.0 / np.pi) * SOLAR_CONSTANT * dr * (
        ws * np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.sin(ws))
    return ra, ws


def daylight_hours(ws):
    """Eq. 34, hours."""
    return 24.0 / np.pi * ws


def clear_sky_radiation(ra, elevation):
    """Eq. 37, MJ m-2 day-1."""
    return (0.75 + 2e-5 * np.asarray(elevation, float)) * ra


def net_longwave_radiation(tmax, tmin, ea, rs, rso):
    """Eq. 39, MJ m-2 day-1. Rs/Rso is limited to 1.0."""
    rel = np.minimum(np.asarray(rs, float) / rso, 1.0)
    tk4 = ((np.asarray(tmax, float) + 273.16) ** 4 + (np.asarray(tmin, float) + 273.16) ** 4) / 2.0
    return STEFAN_BOLTZMANN * tk4 * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * rel - 0.35)


def et0_daily(tmax, tmin, u2, rs, ea, doy, latitude, elevation):
    """Eq. 6, FAO-56 Penman-Monteith reference evapotranspiration [mm/day]; soil heat flux G = 0 (Eq. 42)."""
    tmax = np.asarray(tmax, float)
    tmin = np.asarray(tmin, float)
    u2 = np.asarray(u2, float)
    rs = np.asarray(rs, float)
    ea = np.asarray(ea, float)
    tmean = (tmax + tmin) / 2.0
    delta = vapour_pressure_slope(tmean)
    gamma = psychrometric_constant(atmospheric_pressure(elevation))
    es = (saturation_vapour_pressure(tmax) + saturation_vapour_pressure(tmin)) / 2.0
    ra, _ = extraterrestrial_radiation(latitude, doy)
    rso = clear_sky_radiation(ra, elevation)
    rns = (1.0 - ALBEDO) * rs
    rnl = net_longwave_radiation(tmax, tmin, ea, rs, rso)
    rn = rns - rnl
    g = 0.0
    num = 0.408 * delta * (rn - g) + gamma * (900.0 / (tmean + 273.0)) * u2 * (es - ea)
    den = delta + gamma * (1.0 + 0.34 * u2)
    return num / den

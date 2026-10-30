"""Tolerance derivation for et0-station-ingest (authoring only).

Compares, over every visible and hidden station-day, reference A (tests/expected/*.csv, 6 decimals) with:
  - reference B (ref_b.py, independent vectorised code path);
  - the shipped et0/fao56.py fed by the canonical ingest (what a correct agent submits), unrounded;
  - honest variants a careful practitioner could produce while following METHOD.md (rounded Eq. 47 factors, 273.15 K,
    the exact psychrometric constant, the arctan sunset angle, output rounded to 2 decimals) and all of them at once.
Run (repository root): .venv/bin/python authoring/et0-station-ingest/tolerance_study.py
Prints a markdown table (max |difference| in mm/day) used in DESIGN.md "Tolerance".
"""
import csv, datetime as dt, os, sys
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ref_b

TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "et0-station-ingest"))
SETS = {"visible": (os.path.join(TASK, "environment/app/config/stations.yaml"), os.path.join(TASK, "environment/app/data/raw"),
                    os.path.join(TASK, "tests/expected/visible_et0.csv")),
        "hidden": (os.path.join(TASK, "tests/hidden/stations.yaml"), os.path.join(TASK, "tests/hidden/raw"),
                   os.path.join(TASK, "tests/expected/hidden_et0.csv"))}


def load(yml, raw_dir):
    out = []
    for st in yaml.safe_load(open(yml))["stations"]:
        rows = list(csv.DictReader(open(os.path.join(raw_dir, st["id"] + ".csv"))))
        out.append((st, rows))
    return out


def variant(st, rows, wind_round=None, kelvin=273.16, aero_k=273.0, exact_gamma=False, arctan=False, out_round=None,
            rso_no_alt=False, p_sea=False, es_tmean=False, ea_rhmean=False, no_cap=False, w_factor=0.0864,
            wind_fixed=None, leap_div=False, doy_clip=False, height_clamp=None):
    lat = ref_b.parse_latitude(st["latitude"])
    z = float(st["elevation_m"])
    tmax = np.array([float(r["tmax_c"]) for r in rows]); tmin = np.array([float(r["tmin_c"]) for r in rows])
    doy = np.array([dt.date.fromisoformat(r["date"]).timetuple().tm_yday for r in rows], float)
    year = dt.date.fromisoformat(rows[0]["date"]).year
    ndays = 366.0 if (leap_div and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))) else 365.0
    if doy_clip:
        doy = np.minimum(doy, 365.0)
    zw = float(st["wind_height_m"])
    if height_clamp is not None:
        zw = min(max(zw, height_clamp[0]), height_clamp[1])
    f = 4.87 / np.log(67.8 * zw - 5.42)
    if wind_round is not None:
        f = round(float(f), wind_round)
    if wind_fixed is not None:
        f = wind_fixed(float(st["wind_height_m"]))
    u2 = np.array([float(r["wind_ms"]) for r in rows]) * f
    rs = np.array([float(r["solar_rad"]) for r in rows]) * (w_factor if st["radiation_units"] == "W/m2" else 1.0)
    sat = lambda t: 0.6108 * np.exp(17.27 * t / (t + 237.3))
    if st["humidity"] == "dewpoint":
        ea = sat(np.array([float(r["tdew_c"]) for r in rows]))
    else:
        rmax = np.array([float(r["rh_max_pct"]) for r in rows]); rmin = np.array([float(r["rh_min_pct"]) for r in rows])
        if ea_rhmean:
            ea = (sat(tmax) + sat(tmin)) / 2 * (rmax + rmin) / 200.0
        else:
            ea = (sat(tmin) * rmax + sat(tmax) * rmin) / 200.0
    tm = (tmax + tmin) / 2
    p = 101.3 if p_sea else 101.3 * ((293 - 0.0065 * z) / 293) ** 5.26
    gam = (1.013e-3 * p / (0.622 * 2.45)) if exact_gamma else 0.665e-3 * p
    es = sat(tm) if es_tmean else (sat(tmax) + sat(tmin)) / 2
    dl = 4098 * sat(tm) / (tm + 237.3) ** 2
    phi = np.deg2rad(lat)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / ndays); dec = 0.409 * np.sin(2 * np.pi * doy / ndays - 1.39)
    if arctan:
        x = np.maximum(1 - np.tan(phi) ** 2 * np.tan(dec) ** 2, 1e-5)
        ws = np.pi / 2 - np.arctan(-np.tan(phi) * np.tan(dec) / np.sqrt(x))
    else:
        ws = np.arccos(np.clip(-np.tan(phi) * np.tan(dec), -1, 1))
    ra = 1440 / np.pi * 0.082 * dr * (ws * np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.sin(ws))
    rso = 0.75 * ra if rso_no_alt else (0.75 + 2e-5 * z) * ra
    rnl = 4.903e-9 * ((tmax + kelvin) ** 4 + (tmin + kelvin) ** 4) / 2 * (0.34 - 0.14 * np.sqrt(ea)) * \
        (1.35 * (rs / rso if no_cap else np.minimum(rs / rso, 1)) - 0.35)
    rn = 0.77 * rs - rnl
    et0 = (0.408 * dl * rn + gam * 900 / (tm + aero_k) * u2 * (es - ea)) / (dl + gam * (1 + 0.34 * u2))
    if out_round is not None:
        et0 = np.round(et0, out_round)
    return et0


def shipped_canonical(st, rows):
    """The package's own fao56.et0_daily with the canonical ingest and meta (imported from the solution folder)."""
    sys.path.insert(0, os.path.join(TASK, "environment", "app"))
    import importlib
    import et0.fao56 as fao56
    lat = ref_b.parse_latitude(st["latitude"])
    tmax = np.array([float(r["tmax_c"]) for r in rows]); tmin = np.array([float(r["tmin_c"]) for r in rows])
    doy = np.array([dt.date.fromisoformat(r["date"]).timetuple().tm_yday for r in rows], float)
    u2 = ref_b.u2_from([float(r["wind_ms"]) for r in rows], float(st["wind_height_m"]))
    rs = ref_b.rs_to_mj([float(r["solar_rad"]) for r in rows], st["radiation_units"])
    if st["humidity"] == "dewpoint":
        ea = fao56.actual_vapour_pressure_dewpoint([float(r["tdew_c"]) for r in rows])
    else:
        ea = fao56.actual_vapour_pressure_rh(tmax, tmin, [float(r["rh_max_pct"]) for r in rows],
                                             [float(r["rh_min_pct"]) for r in rows])
    return fao56.et0_daily(tmax, tmin, u2, rs, ea, doy, lat, float(st["elevation_m"]))


def main():
    variants = {
        "reference B (independent code)": None,
        "shipped fao56.py + canonical fix, unrounded": "shipped",
        "Eq. 47 factor rounded to 3 decimals": dict(wind_round=3),
        "Eq. 47 factor rounded to 2 decimals": dict(wind_round=2),
        "273.15 instead of 273.16 in Eq. 39": dict(kelvin=273.15),
        "T + 273.16 instead of T + 273 in Eq. 6": dict(aero_k=273.16),
        "exact gamma = cp P / (eps lambda)": dict(exact_gamma=True),
        "arctan sunset angle (Eq. 26)": dict(arctan=True),
        "output rounded to 3 decimals": dict(out_round=3),
        "output rounded to 2 decimals": dict(out_round=2),
        "all honest variants at once (2-decimal factor, 2-decimal output)":
            dict(wind_round=2, kelvin=273.15, aero_k=273.16, exact_gamma=True, arctan=True, out_round=2),
        "MISTAKE: Rso by Eq. 36 (no altitude term)": dict(rso_no_alt=True),
        "MISTAKE: sea-level pressure everywhere": dict(p_sea=True),
        "MISTAKE: es from Tmean (not Eq. 12)": dict(es_tmean=True),
        "MISTAKE: ea from RHmean (Eq. 19, not Eq. 17)": dict(ea_rhmean=True),
        "MISTAKE: Rs/Rso not capped at 1": dict(no_cap=True),
        "MISTAKE: W/m2 x 1/11.6 instead of x 0.0864": dict(w_factor=1 / 11.6),
        "MISTAKE: nearest of the 2, 3, 10 m factors": dict(wind_fixed=lambda h: {2.0: 1.0, 3.0: 0.921, 10.0: 0.748}[
            min((2.0, 3.0, 10.0), key=lambda k: abs(k - h))]),
        "MISTAKE: 0.75 for every height other than 2 m": dict(wind_fixed=lambda h: 1.0 if h == 2 else 0.75),
        "MISTAKE: wind height clamped to 2-12 m before Eq. 47": dict(height_clamp=(2.0, 12.0)),
        "MISTAKE: divisor 366 in a leap year (Eqs. 23, 24)": dict(leap_div=True),
        "MISTAKE: day of year clipped at 365": dict(doy_clip=True),
    }
    print("| Variant | max abs diff, visible (mm/day) | max abs diff, hidden (mm/day) | rows > 0.01 | rows > 0.02 | rows > 0.03 | rows > 0.05 |")
    print("|---|---|---|---|---|---|---|")
    for label, kw in variants.items():
        res, over1, over2, over3, over5 = {}, 0, 0, 0, 0
        for set_name, (yml, raw, exp_path) in SETS.items():
            exp = {(r["station_id"], r["date"]): float(r["et0_mm_day"]) for r in csv.DictReader(open(exp_path))}
            worst = 0.0
            for st, rows in load(yml, raw):
                if kw is None:
                    v = ref_b.et0_daily(*_b_args(st, rows))
                elif kw == "shipped":
                    v = shipped_canonical(st, rows)
                else:
                    v = variant(st, rows, **kw)
                d = np.abs(v - np.array([exp[(st["id"], r["date"])] for r in rows]))
                worst = max(worst, float(d.max()))
                over1 += int((d > 0.01).sum()); over2 += int((d > 0.02).sum())
                over3 += int((d > 0.03).sum()); over5 += int((d > 0.05).sum())
            res[set_name] = worst
        print(f"| {label} | {res['visible']:.6f} | {res['hidden']:.6f} | {over1} | {over2} | {over3} | {over5} |")


def _b_args(st, rows):
    lat = ref_b.parse_latitude(st["latitude"])
    tmax = np.array([float(r["tmax_c"]) for r in rows]); tmin = np.array([float(r["tmin_c"]) for r in rows])
    doy = np.array([dt.date.fromisoformat(r["date"]).timetuple().tm_yday for r in rows], float)
    u2 = ref_b.u2_from([float(r["wind_ms"]) for r in rows], float(st["wind_height_m"]))
    rs = ref_b.rs_to_mj([float(r["solar_rad"]) for r in rows], st["radiation_units"])
    z = np.full(len(rows), float(st["elevation_m"]))
    kw = {}
    if st["humidity"] == "dewpoint":
        kw["tdew"] = [float(r["tdew_c"]) for r in rows]
    else:
        kw["rh_max"] = [float(r["rh_max_pct"]) for r in rows]; kw["rh_min"] = [float(r["rh_min_pct"]) for r in rows]
    return (tmax, tmin, np.full(len(rows), lat), z, doy, u2, rs, None, kw.get("rh_max"), kw.get("rh_min"), kw.get("tdew"))


if __name__ == "__main__":
    main()

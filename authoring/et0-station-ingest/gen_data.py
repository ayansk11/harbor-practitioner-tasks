"""Generate the synthetic station records for task et0-station-ingest (fixed seeds; rerun gives identical bytes).

Run (repository root): .venv/bin/python authoring/et0-station-ingest/gen_data.py
Writes (inside tasks/et0-station-ingest/):
  environment/app/config/stations.yaml, environment/app/data/raw/<id>.csv          (8 visible stations, 2025)
  environment/app/reference/metservice_et0_2025.csv                                 (2 sites, rounded to 0.1)
  tests/hidden/stations.yaml, tests/hidden/raw/<id>.csv                             (10 hidden stations; H10 is 2024)
  tests/expected/visible_et0.csv, tests/expected/hidden_et0.csv                     (reference A, 6 decimals)
The weather is synthetic (a seasonal cycle plus autocorrelated noise), made to look like station data: realistic
ranges, RHmin <= RHmax <= 100, Tdew <= Tmin, Rs mostly below the clear-sky value with a few small excesses (so the
Rs/Rso cap is exercised). Expected ET0 is computed from the rounded values written to the files, never from the
unrounded draws.
"""
import csv, datetime as dt, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ref_a

TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "et0-station-ingest"))
YEAR = 2025
# Station-years other than YEAR. H10 is a leap year (366 rows, J up to 366, divisor still 365; METHOD.md 2 step 8), so
# the hidden run exercises the stated leap-year rule (added after the independent review of 2026-10-28; DESIGN.md
# section 12).
STATION_YEAR = {"H10": 2024}

# id, name, latitude as written in the YAML, true latitude, longitude, elevation, wind height, radiation units,
# humidity type, network, climate (t_base sea-level annual mean C, t_amp C, dtr C, dewpoint depression C,
# clearness mean, u2 mean m/s), seed
VISIBLE = [
    ("VNT", "Valle Norte", 38.42, 38.42, -3.71, 85, 2.0, "MJ/m2/day", "rh_minmax", "valley-agromet",
     (16.5, 9.0, 13.0, 4.0, 0.72, 2.0), 101),
    ("PAL", "Paso Alto", "36.95N", 36.95, -3.02, 1840, 10.0, "MJ/m2/day", "rh_minmax", "highland-synop",
     (17.0, 8.5, 12.0, 6.0, 0.76, 2.4), 102),
    ("CDB", "Costa del Bajo", "34.92S", -34.92, 138.60, 48, 2.0, "MJ/m2/day", "dewpoint", "southern-coast",
     (17.5, 6.0, 10.0, 3.5, 0.68, 2.6), 103),
    ("LGN", "Laguna Grande", -31.85, -31.85, 116.02, 420, 3.0, "W/m2", "rh_minmax", "southern-coast",
     (18.5, 7.0, 13.5, 6.5, 0.74, 2.2), 104),
    ("RSD", "Ribera Seca", "41.73N", 41.73, -1.02, 230, 2.0, "W/m2", "dewpoint", "highland-synop",
     (15.5, 9.5, 12.5, 5.5, 0.70, 2.8), 105),
    ("MRS", "Marisma", 35.10, 35.10, -6.15, 12, 3.0, "MJ/m2/day", "rh_minmax", "valley-agromet",
     (18.0, 7.0, 10.5, 3.0, 0.71, 3.0), 106),
    ("HLT", "Altiplano Sur", "33.40S", -33.40, -70.55, 610, 10.0, "W/m2", "dewpoint", "highland-synop",
     (15.0, 7.0, 14.0, 7.0, 0.77, 2.1), 107),
    ("ARN", "Arenales", 40.05, 40.05, -4.40, 690, 2.0, "MJ/m2/day", "dewpoint", "valley-agromet",
     (15.0, 9.5, 14.5, 6.0, 0.73, 1.8), 108),
]
METSERVICE_SITES = ["PAL", "CDB"]

# Ten hidden stations: both hemispheres, wind heights 1, 2, 2.5, 3, 4.5, 6, 7.5, 10, 12, 20 m (both ends of the stated
# 1-20 m range: added after the review), both units, both humidity types, every latitude form in METHOD.md,
# elevations 5 m to 1960 m, one leap year (H10, 2024). Only the variants METHOD.md lists are used.
HIDDEN = [
    ("H01", "Delta Verde", "12.35N", 12.35, -16.20, 5, 2.0, "W/m2", "dewpoint", "coastal-aws",
     (27.0, 2.5, 9.0, 3.0, 0.66, 2.4), 201),
    ("H02", "Planalto", -23.55, -23.55, -46.63, 760, 3.0, "MJ/m2/day", "rh_minmax", "plateau-aws",
     (22.5, 4.0, 10.5, 4.5, 0.62, 1.9), 202),
    ("H03", "Col Haut", "45.80N", 45.80, 6.95, 1960, 6.0, "MJ/m2/day", "rh_minmax", "mountain-synop",
     (16.0, 9.0, 10.0, 5.0, 0.64, 3.1), 203),
    ("H04", "Bahia Fria", "38.10S", -38.10, 144.35, 30, 10.0, "W/m2", "rh_minmax", "southern-coast",
     (15.5, 5.0, 9.5, 3.5, 0.63, 3.4), 204),
    ("H05", "Polder Oost", 52.20, 52.20, 5.10, 15, 2.5, "MJ/m2/day", "dewpoint", "lowland-aws",
     (11.5, 7.5, 8.5, 2.5, 0.55, 3.0), 205),
    ("H06", "Karoo Rand", "29.95S", -29.95, 24.50, 1250, 4.5, "W/m2", "dewpoint", "plateau-aws",
     (22.0, 7.5, 16.0, 9.0, 0.80, 2.6), 206),
    ("H07", "Wadi Sahl", 31.60, 31.60, 35.40, 410, 7.5, "MJ/m2/day", "rh_minmax", "desert-synop",
     (23.5, 8.5, 15.0, 10.0, 0.82, 2.7), 207),
    ("H08", "Ilha Baixa", "6.75S", -6.75, 39.25, 140, 12.0, "MJ/m2/day", "dewpoint", "coastal-aws",
     (26.5, 1.5, 8.5, 2.5, 0.60, 3.3), 208),
    ("H09", "Hochfeld", "47.30N", 47.30, 11.40, 880, 20.0, "MJ/m2/day", "rh_minmax", "mountain-synop",
     (13.0, 9.5, 10.5, 4.0, 0.58, 2.9), 209),
    ("H10", "Llanura Sur", -41.20, -41.20, -71.30, 260, 1.0, "W/m2", "rh_minmax", "southern-coast",
     (13.5, 6.5, 13.0, 5.5, 0.68, 3.6), 210),
]


def esat(t):
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def ar1(rng, n, phi, sd):
    e = rng.normal(0.0, sd * math.sqrt(1 - phi * phi), n)
    x = np.empty(n)
    x[0] = rng.normal(0.0, sd)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def make_station(spec):
    sid, name, lat_txt, lat, lon, elev, zw, units, hum, net, clim, seed = spec
    t_base, t_amp, dtr, dep_mean, k_mean, u_mean = clim
    rng = np.random.default_rng(seed)
    year = STATION_YEAR.get(sid, YEAR)
    days = [dt.date(year, 1, 1) + dt.timedelta(days=i) for i in range((dt.date(year + 1, 1, 1) - dt.date(year, 1, 1)).days)]
    n = len(days)
    doy = np.array([d.timetuple().tm_yday for d in days], dtype=float)
    peak = 200.0 if lat >= 0 else 17.0
    tm = t_base - 0.0065 * elev + t_amp * np.cos(2 * np.pi * (doy - peak) / 365.0) + ar1(rng, n, 0.7, 2.0)
    # clearness index Rs/Rso: beta around k_mean, a few days slightly above 1 (measured Rs can exceed the Eq. 37 estimate)
    a = 6.0
    m_b = (k_mean - 0.25) / 0.80
    b = a * (1 - m_b) / m_b
    k = 0.25 + 0.80 * rng.beta(a, b, n)
    k = np.clip(k, 0.28, 1.03)
    dtr_d = np.clip(dtr * (0.55 + 0.6 * k) + rng.normal(0, 1.0, n), 2.5, None)
    tmax = tm + dtr_d / 2
    tmin = tm - dtr_d / 2
    dep = np.clip(rng.gamma(2.0, dep_mean / 2.0, n) * (0.6 + 0.6 * k), 0.0, 18.0)
    tdew = tmin - dep
    u2 = np.exp(np.log(u_mean) - 0.06 + ar1(rng, n, 0.55, 0.35))
    u2 = np.clip(u2, 0.3, 9.0)
    factor = 4.87 / np.log(67.8 * zw - 5.42)
    uz = u2 / factor
    # radiation from the true latitude
    ra = np.array([ref_a.daily(20, 10, lat, elev, int(j), 2.0, rs=10.0, rh_max=80, rh_min=40)["Ra"] for j in doy])
    rso = (0.75 + 2e-5 * elev) * ra
    rs_mj = k * rso
    # round to what a station logger would write
    tmax_r = np.round(tmax, 1)
    tmin_r = np.round(tmin, 1)
    bad = tmax_r <= tmin_r
    tmax_r[bad] = tmin_r[bad] + 0.5
    rows = []
    for i, d in enumerate(days):
        r = {"date": d.isoformat(), "tmax_c": f"{tmax_r[i]:.1f}", "tmin_c": f"{tmin_r[i]:.1f}"}
        if hum == "dewpoint":
            td = min(round(float(tdew[i]), 1), float(tmin_r[i]))
            r["tdew_c"] = f"{td:.1f}"
        else:
            ea = float(esat(tdew[i]))
            rhmax = min(100, int(round(100 * ea / float(esat(tmin_r[i])) + rng.normal(0, 2.0))))
            rhmin = int(round(100 * ea / float(esat(tmax_r[i])) + rng.normal(0, 2.0)))
            rhmin = max(5, min(rhmin, rhmax))
            r["rh_max_pct"] = str(rhmax)
            r["rh_min_pct"] = str(rhmin)
        r["wind_ms"] = f"{max(0.1, round(float(uz[i]), 1)):.1f}"
        if units == "W/m2":
            r["solar_rad"] = f"{rs_mj[i] / 0.0864:.1f}"
        else:
            r["solar_rad"] = f"{rs_mj[i]:.2f}"
        rows.append(r)
    meta = {"id": sid, "name": name, "latitude": lat_txt, "longitude": lon, "elevation_m": elev,
            "wind_height_m": zw, "radiation_units": units, "humidity": hum, "network": net}
    return meta, rows, lat


def expected_rows(meta, rows, lat):
    out = []
    for r in rows:
        d = dt.date.fromisoformat(r["date"])
        u2 = ref_a.wind_to_2m(float(r["wind_ms"]), float(meta["wind_height_m"]))
        rs = float(r["solar_rad"]) * (ref_a.W_TO_MJ if meta["radiation_units"] == "W/m2" else 1.0)
        kw = {"tdew": float(r["tdew_c"])} if meta["humidity"] == "dewpoint" else \
             {"rh_max": float(r["rh_max_pct"]), "rh_min": float(r["rh_min_pct"])}
        v = ref_a.daily(float(r["tmax_c"]), float(r["tmin_c"]), lat, float(meta["elevation_m"]),
                        d.timetuple().tm_yday, u2, rs=rs, **kw)
        out.append((meta["id"], r["date"], v["et0"]))
    return out


def yaml_text(metas, header):
    lines = [header, "stations:"]
    for m in metas:
        lat = m["latitude"]
        lat_s = f'"{lat}"' if isinstance(lat, str) else f"{lat}"
        lines += [f"  - id: {m['id']}", f"    name: {m['name']}", f"    latitude: {lat_s}",
                  f"    longitude: {m['longitude']}", f"    elevation_m: {m['elevation_m']}",
                  f"    wind_height_m: {m['wind_height_m']}", f'    radiation_units: "{m["radiation_units"]}"',
                  f"    humidity: {m['humidity']}", f"    network: {m['network']}"]
    return "\n".join(lines) + "\n"


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def write_set(specs, yaml_path, raw_dir, expected_path, header):
    metas, all_exp = [], []
    for spec in specs:
        meta, rows, lat = make_station(spec)
        metas.append(meta)
        cols = list(rows[0].keys())
        write_csv(os.path.join(raw_dir, f"{meta['id']}.csv"), cols, [[r[c] for c in cols] for r in rows])
        all_exp += expected_rows(meta, rows, lat)
    os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
    with open(yaml_path, "w") as f:
        f.write(yaml_text(metas, header))
    write_csv(expected_path, ["station_id", "date", "et0_mm_day"], [(s, d, f"{v:.6f}") for s, d, v in all_exp])
    return all_exp


def main():
    env = os.path.join(TASK, "environment", "app")
    tests = os.path.join(TASK, "tests")
    vis = write_set(VISIBLE, os.path.join(env, "config", "stations.yaml"), os.path.join(env, "data", "raw"),
                    os.path.join(tests, "expected", "visible_et0.csv"),
                    "# Station register for the irrigation-advice ET0 run (see /app/docs/METHOD.md for every field).")
    write_set(HIDDEN, os.path.join(tests, "hidden", "stations.yaml"), os.path.join(tests, "hidden", "raw"),
              os.path.join(tests, "expected", "hidden_et0.csv"),
              "# Station register (same format as /app/config/stations.yaml).")
    ms = [(s, d, f"{round(v + 1e-9, 1):.1f}") for s, d, v in vis if s in METSERVICE_SITES]
    write_csv(os.path.join(env, "reference", "metservice_et0_2025.csv"), ["station_id", "date", "et0_mm_day"], ms)
    print(f"wrote {len(vis)} visible station-days, {len(ms)} met-service values, hidden set of {len(HIDDEN)} stations")
    # the currently published (wrong) output, made by the shipped pipeline itself
    import subprocess
    subprocess.run([sys.executable, "-m", "et0.pipeline", "--stations", "config/stations.yaml", "--data", "data/raw",
                    "--out", "output/et0.csv"], cwd=env, check=True, capture_output=True,
                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    write_sums(tests)


def write_sums(tests):
    """tests/SHA256SUMS over the hidden inputs and the expected values (grade.py checks it before grading)."""
    import hashlib
    lines = []
    for sub in ("hidden", "expected"):
        for root, _, files in os.walk(os.path.join(tests, sub)):
            for n in files:
                full = os.path.join(root, n)
                rel = os.path.relpath(full, tests)
                lines.append(f"{hashlib.sha256(open(full, 'rb').read()).hexdigest()}  {rel}")
    with open(os.path.join(tests, "SHA256SUMS"), "w") as f:
        f.write("\n".join(sorted(lines, key=lambda l: l.split("  ")[1])) + "\n")


if __name__ == "__main__":
    main()

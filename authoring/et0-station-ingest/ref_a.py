"""Reference A: FAO-56 Penman-Monteith daily ET0, one day at a time, plain `math` (authoring only, never shipped to /app).

Written from FAO Irrigation and Drainage Paper 56, chapter 3 (https://www.fao.org/4/x0490e/x0490e07.htm) and chapter 4
(https://www.fao.org/4/x0490e/x0490e08.htm), read from our saved Markdown copy of each page (not in this repository;
"ch3 line n" below = line n of the chapter 3 copy). Equation numbers are the book's. Where the saved text shows an
equation only as an image (Eq. 6, 13, 21, 34, 39, 47), the form used here is the one the book's worked examples spell out
(ch3 Examples 2, 3, 8, 9, 11, 14; ch4 Examples 17, 18); DESIGN.md lists the line of each.

This file is one of two independent references (see ref_b.py). It follows the order of the book's calculation sheet
(Box 11) and keeps every intermediate value so it can be printed next to the book's worked example.
"""
import math

GSC = 0.0820            # solar constant, MJ m-2 min-1 (ch3 line 495)
SIGMA = 4.903e-9        # Stefan-Boltzmann, MJ K-4 m-2 day-1 (ch3 line 751)
ALBEDO = 0.23           # grass reference (ch3 Eq. 38 text)
W_TO_MJ = 0.0864        # 1 W m-2 = 0.0864 MJ m-2 day-1 (ch3 line 470)


def pressure_kpa(z):                       # Eq. 7 (ch3 Example 2)
    return 101.3 * ((293.0 - 0.0065 * z) / 293.0) ** 5.26


def psychrometric(p):                      # Eq. 8 (ch3 Example 2: 0.665e-3 P)
    return 0.665e-3 * p


def esat(t):                               # Eq. 11 (ch3 Example 3)
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def slope(t):                              # Eq. 13 (image in the saved text; checked against ch4 Examples 17, 18)
    return 4098.0 * esat(t) / (t + 237.3) ** 2


def wind_to_2m(uz, z):                     # Eq. 47 (ch3 Example 14)
    return uz * 4.87 / math.log(67.8 * z - 5.42)


def daily(tmax, tmin, lat_deg, elev_m, doy, u2, rs=None, sunshine_h=None, rh_max=None, rh_min=None, tdew=None):
    """Return a dict of every intermediate value and 'et0' (mm/day). Give rs (MJ m-2 day-1) or sunshine_h."""
    v = {}
    v["P"] = pressure_kpa(elev_m)
    v["Tmean"] = (tmax + tmin) / 2.0                                     # Eq. 9
    v["Delta"] = slope(v["Tmean"])
    v["gamma"] = psychrometric(v["P"])
    v["1+0.34u2"] = 1.0 + 0.34 * u2
    den = v["Delta"] + v["gamma"] * v["1+0.34u2"]
    v["Delta/den"] = v["Delta"] / den
    v["gamma/den"] = v["gamma"] / den
    v["900/(T+273)u2"] = 900.0 / (v["Tmean"] + 273.0) * u2
    v["e(Tmax)"] = esat(tmax)
    v["e(Tmin)"] = esat(tmin)
    v["es"] = (v["e(Tmax)"] + v["e(Tmin)"]) / 2.0                       # Eq. 12
    if tdew is not None:
        v["ea"] = esat(tdew)                                             # Eq. 14
    else:
        v["ea"] = (v["e(Tmin)"] * rh_max / 100.0 + v["e(Tmax)"] * rh_min / 100.0) / 2.0   # Eq. 17
    v["es-ea"] = v["es"] - v["ea"]
    phi = math.pi / 180.0 * lat_deg                                      # Eq. 22
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)              # Eq. 23
    dec = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)            # Eq. 24
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(dec))))   # Eq. 25
    v["dr"], v["decl"], v["ws"] = dr, dec, ws
    v["Ra"] = 24.0 * 60.0 / math.pi * GSC * dr * (ws * math.sin(phi) * math.sin(dec)
                                                   + math.cos(phi) * math.cos(dec) * math.sin(ws))   # Eq. 21
    v["N"] = 24.0 / math.pi * ws                                         # Eq. 34
    if rs is None:
        v["n/N"] = sunshine_h / v["N"]
        rs = (0.25 + 0.50 * v["n/N"]) * v["Ra"]                          # Eq. 35
    v["Rs"] = rs
    v["Rso"] = (0.75 + 2e-5 * elev_m) * v["Ra"]                          # Eq. 37
    v["Rs/Rso"] = min(rs / v["Rso"], 1.0)                                # limited to <= 1.0 (Eq. 39 text)
    v["Rns"] = (1.0 - ALBEDO) * rs                                       # Eq. 38
    v["sTmax4"] = SIGMA * (tmax + 273.16) ** 4
    v["sTmin4"] = SIGMA * (tmin + 273.16) ** 4
    v["sT4mean"] = (v["sTmax4"] + v["sTmin4"]) / 2.0
    v["0.34-0.14sqrt(ea)"] = 0.34 - 0.14 * math.sqrt(v["ea"])
    v["1.35Rs/Rso-0.35"] = 1.35 * v["Rs/Rso"] - 0.35
    v["Rnl"] = v["sT4mean"] * v["0.34-0.14sqrt(ea)"] * v["1.35Rs/Rso-0.35"]   # Eq. 39
    v["Rn"] = v["Rns"] - v["Rnl"]                                        # Eq. 40
    v["G"] = 0.0                                                         # Eq. 42 (daily)
    v["0.408(Rn-G)"] = 0.408 * (v["Rn"] - v["G"])
    v["rad_term"] = v["0.408(Rn-G)"] * v["Delta/den"]
    v["aero_term"] = v["900/(T+273)u2"] * v["es-ea"] * v["gamma/den"]
    v["et0"] = v["rad_term"] + v["aero_term"]                            # Eq. 6
    return v


def monthly(tmax, tmin, lat_deg, elev_m, doy, u2, ea, sunshine_h, t_month, t_prev):
    """Example 17 check: same as daily() but ea given and G from Eq. 44."""
    v = daily(tmax, tmin, lat_deg, elev_m, doy, u2, sunshine_h=sunshine_h, tdew=None, rh_max=0.0, rh_min=0.0)
    # recompute the humidity and G dependent parts with the given ea and the monthly G
    v["ea"] = ea
    v["es-ea"] = v["es"] - ea
    v["0.34-0.14sqrt(ea)"] = 0.34 - 0.14 * math.sqrt(ea)
    v["Rnl"] = v["sT4mean"] * v["0.34-0.14sqrt(ea)"] * v["1.35Rs/Rso-0.35"]
    v["Rn"] = v["Rns"] - v["Rnl"]
    v["G"] = 0.14 * (t_month - t_prev)                                   # Eq. 44
    v["0.408(Rn-G)"] = 0.408 * (v["Rn"] - v["G"])
    v["rad_term"] = v["0.408(Rn-G)"] * v["Delta/den"]
    v["aero_term"] = v["900/(T+273)u2"] * v["es-ea"] * v["gamma/den"]
    v["et0"] = v["rad_term"] + v["aero_term"]
    return v

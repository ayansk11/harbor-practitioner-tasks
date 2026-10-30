"""Build step one: reproduce FAO-56 chapter 4 Example 18 (daily) and Example 17 (monthly) with both references.

Run (repository root): .venv/bin/python authoring/et0-station-ingest/reproduce_fao_examples.py
Prints a markdown table (ours vs the book's printed value) and exits non-zero if any value is outside the book's
rounding (half a unit of the last printed digit) or if ET0 differs from 3.88 (Example 18) by more than 0.01 mm/day.
Book values: FAO-56 chapter 4 (https://www.fao.org/4/x0490e/x0490e08.htm), from our saved Markdown copy of the page
(not in this repository): lines 256-324 (Ex. 18) and 182-242 (Ex. 17); the printed line column refers to that copy.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_a, ref_b

ok = True


def row(name, ours, book, decimals, line, note="", explained=None):
    """explained = (value the book's own table path gives, why): the row then passes only if that value rounds to the book."""
    global ok
    half = 0.5 * 10 ** (-decimals)
    good = abs(ours - book) <= half + 1e-9
    verdict = "yes" if good else "NO"
    if not good and explained is not None:
        alt, why = explained
        if abs(alt - book) <= half + 1e-9:
            verdict = f"no; explained: {why} gives {alt:.{decimals + 3}f}"
            good = True
    ok = ok and good
    print(f"| {name} | {ours:.{decimals + 3}f} | {book:.{decimals}f} | {line} | {verdict} | {note} |")


# ---------- Example 18: Uccle (Brussels), 6 July, 50 deg 48 min N, 100 m ----------
uz = 10.0 / 3.6                     # 10 km/h at 10 m
u2 = ref_a.wind_to_2m(uz, 10.0)
lat = 50.0 + 48.0 / 60.0
J = 187                              # 6 July (book: Table 2.5)
v = ref_a.daily(21.5, 12.3, lat, 100.0, J, u2, sunshine_h=9.25, rh_max=84.0, rh_min=63.0)
print("Example 18 (daily), reference A")
print("| Quantity | Ours | Book | Book line | Within book rounding | Note |")
print("|---|---|---|---|---|---|")
row("uz (m/s)", uz, 2.78, 2, 268)
row("u2 (m/s)", u2, 2.078, 3, 269, "book prints '2,078'; factor 4.87/ln(67.8*10-5.42)")
row("P (kPa)", v["P"], 100.1, 1, 272)
row("Tmean (C)", v["Tmean"], 16.9, 1, 273)
row("Delta (kPa/C)", v["Delta"], 0.122, 3, 275)
row("gamma (kPa/C)", v["gamma"], 0.0666, 4, 277)
row("1+0.34u2", v["1+0.34u2"], 1.71, 2, 278)
row("Delta/[Delta+gamma(1+0.34u2)]", v["Delta/den"], 0.518, 3, 279)
row("gamma/[Delta+gamma(1+0.34u2)]", v["gamma/den"], 0.282, 3, 280)
row("900/(T+273) u2", v["900/(T+273)u2"], 6.450, 3, 281)
row("e(Tmax) (kPa)", v["e(Tmax)"], 2.564, 3, 284)
row("e(Tmin) (kPa)", v["e(Tmin)"], 1.431, 3, 286)
row("es (kPa)", v["es"], 1.997, 3, 287, "book line omits the /2 but prints the mean")
row("ea (kPa)", v["ea"], 1.409, 3, 290)
row("es-ea (kPa)", v["es-ea"], 0.589, 3, 291, "book: 1.997-1.409 printed as 0.589 (unrounded inputs)")
row("Ra (MJ/m2/d)", v["Ra"], 41.09, 2, 297)
row("N (h)", v["N"], 16.1, 1, 300)
row("n/N", v["n/N"], 0.57, 2, 301, "book writes 9.25/16.3 (typo; N is 16.1 one line above); 0.57 either way")
row("Rs (MJ/m2/d)", v["Rs"], 22.07, 2, 302)
row("Rso (MJ/m2/d)", v["Rso"], 30.90, 2, 303)
row("Rs/Rso", v["Rs/Rso"], 0.71, 2, 304)
row("Rns (MJ/m2/d)", v["Rns"], 17.00, 2, 305)
row("sigma Tmax,K^4", v["sTmax4"], 36.96, 2, 308)
row("sigma Tmin,K^4", v["sTmin4"], 32.56, 2, 311)
row("mean sigma T^4", v["sT4mean"], 34.76, 2, 312)
row("0.34-0.14 sqrt(ea)", v["0.34-0.14sqrt(ea)"], 0.17, 2, 313)
row("1.35 Rs/Rso - 0.35", v["1.35Rs/Rso-0.35"], 0.61, 2, 314)
row("Rnl (MJ/m2/d)", v["Rnl"], 3.71, 2, 315)
row("Rn (MJ/m2/d)", v["Rn"], 13.28, 2, 316)
row("0.408(Rn-G) (mm/d)", v["0.408(Rn-G)"], 5.42, 2, 319)
row("radiation term (mm/d)", v["rad_term"], 2.81, 2, 321)
row("aerodynamic term (mm/d)", v["aero_term"], 1.07, 2, 322)
row("ET0 (mm/d)", v["et0"], 3.88, 2, 323)
et0_a = v["et0"]

# Reference B on the same day (its own code path: vectorised, arctan sunset angle, single-fraction Eq. 6)
import numpy as np
b = ref_b.et0_daily(np.array([21.5]), np.array([12.3]), np.array([lat]), np.array([100.0]), np.array([J]),
                    np.array([u2]), rs_mj=None, sunshine_h=np.array([9.25]),
                    rh_max=np.array([84.0]), rh_min=np.array([63.0]), tdew=None)
et0_b = float(b[0])
print()
print(f"Example 18 ET0: reference A {et0_a:.6f}, reference B {et0_b:.6f}, book 3.88; "
      f"|A-3.88| = {abs(et0_a - 3.88):.6f}, |A-B| = {abs(et0_a - et0_b):.2e}")
if abs(et0_a - 3.88) > 0.01 or abs(et0_b - 3.88) > 0.01:
    ok = False

# ---------- Example 17: Bangkok, April (monthly means), 13 deg 44 min N, 2 m ----------
lat17 = 13.0 + 44.0 / 60.0
v = ref_a.monthly(34.8, 25.6, lat17, 2.0, 105, 2.0, ea=2.85, sunshine_h=8.5, t_month=30.2, t_prev=29.2)
print()
print("Example 17 (monthly), reference A")
print("| Quantity | Ours | Book | Book line | Within book rounding | Note |")
print("|---|---|---|---|---|---|")
row("Delta (kPa/C)", v["Delta"], 0.246, 3, 197)
row("P (kPa)", v["P"], 101.3, 1, 199)
row("gamma (kPa/C)", v["gamma"], 0.0674, 4, 200, "book uses Table 2.1/2.2 (line 198), i.e. P rounded to 101.3",
    explained=(ref_a.psychrometric(101.3), "Eq. 8 with the book's rounded P = 101.3 kPa"))
row("1+0.34u2", v["1+0.34u2"], 1.68, 2, 201)
row("Delta/[...]", v["Delta/den"], 0.685, 3, 202)
row("gamma/[...]", v["gamma/den"], 0.188, 3, 203, "book writes 0.0667 in the formula, 0.0674 one line above")
row("900/(T+273) u2", v["900/(T+273)u2"], 5.94, 2, 204)
row("e(Tmax) (kPa)", v["e(Tmax)"], 5.56, 2, 207)
row("e(Tmin) (kPa)", v["e(Tmin)"], 3.28, 2, 209)
row("es (kPa)", v["es"], 4.42, 2, 210)
row("es-ea (kPa)", v["es-ea"], 1.57, 2, 212)
row("Ra (MJ/m2/d)", v["Ra"], 38.06, 2, 216)
row("N (h)", v["N"], 12.31, 2, 217)
row("n/N", v["n/N"], 0.69, 2, 218)
row("Rs (MJ/m2/d)", v["Rs"], 22.65, 2, 219)
row("Rso (MJ/m2/d)", v["Rso"], 28.54, 2, 220)
row("Rs/Rso", v["Rs/Rso"], 0.79, 2, 221)
row("Rns (MJ/m2/d)", v["Rns"], 17.44, 2, 222)
row("sigma Tmax,K^4", v["sTmax4"], 44.10, 2, 224)
row("sigma Tmin,K^4", v["sTmin4"], 39.06, 2, 226)
row("mean sigma T^4", v["sT4mean"], 41.58, 2, 227)
row("0.34-0.14 sqrt(ea)", v["0.34-0.14sqrt(ea)"], 0.10, 2, 229)
row("1.35 Rs/Rso - 0.35", v["1.35Rs/Rso-0.35"], 0.72, 2, 231)
row("Rnl (MJ/m2/d)", v["Rnl"], 3.11, 2, 232)
row("Rn (MJ/m2/d)", v["Rn"], 14.33, 2, 233)
row("G (MJ/m2/d)", v["G"], 0.14, 2, 234)
row("0.408(Rn-G) (mm/d)", v["0.408(Rn-G)"], 5.79, 2, 236)
row("radiation term (mm/d)", v["rad_term"], 3.97, 2, 239)
row("aerodynamic term (mm/d)", v["aero_term"], 1.75, 2, 240)
row("ET0 (mm/d)", v["et0"], 5.72, 2, 241)

print()
print("RESULT:", "REPRODUCED" if ok else "NOT REPRODUCED")
sys.exit(0 if ok else 1)

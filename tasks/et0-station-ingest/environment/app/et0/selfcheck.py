"""Check fao56.et0_daily against the daily worked example of FAO-56 (chapter 4, Example 18).

    python -m et0.selfcheck

Uccle (Brussels), 6 July, 50 deg 48 min N, 100 m: Tmax 21.5, Tmin 12.3 degC, RHmax 84 %, RHmin 63 %, sunshine 9.25 h,
wind 2.078 m/s at 2 m (the book first converts its 10 m reading). The book's answer is ETo = 3.88 mm/day (3.9 rounded).
"""
import sys

from . import fao56

BOOK_ET0 = 3.88


def main():
    lat, elev, doy = 50.0 + 48.0 / 60.0, 100.0, 187
    tmax, tmin, rh_max, rh_min, sunshine, u2 = 21.5, 12.3, 84.0, 63.0, 9.25, 2.078
    ra, ws = fao56.extraterrestrial_radiation(lat, doy)
    rs = (0.25 + 0.50 * sunshine / fao56.daylight_hours(ws)) * ra      # Angstrom formula (Eq. 35), as in the book
    ea = fao56.actual_vapour_pressure_rh(tmax, tmin, rh_max, rh_min)
    et0 = float(fao56.et0_daily(tmax, tmin, u2, rs, ea, doy, lat, elev))
    ok = abs(et0 - BOOK_ET0) <= 0.01
    print(f"FAO-56 Example 18: Ra={float(ra):.2f} Rs={float(rs):.2f} ea={float(ea):.3f} ET0={et0:.3f} "
          f"(book {BOOK_ET0}) -> {'OK' if ok else 'MISMATCH'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

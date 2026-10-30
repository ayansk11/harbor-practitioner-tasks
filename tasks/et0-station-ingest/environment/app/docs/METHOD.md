# How we compute daily ET0

This is the method the `et0` package must follow. It is the daily FAO-56 Penman-Monteith procedure: FAO Irrigation
and Drainage Paper No. 56, *Crop evapotranspiration* (Allen, Pereira, Raes and Smith, 1998), chapters 3 and 4.
Equation numbers below are the book's, so you can look any step up there. You do not need the book: everything the
pipeline needs is on this page.

ET0 is the water a well-watered reference grass surface would lose in one day, in mm/day. We publish one value per
station per day.

## 1. Inputs, after conversion to standard form

| Symbol | Meaning | Unit |
|---|---|---|
| Tmax, Tmin | daily maximum and minimum air temperature | deg C |
| u2 | mean daily wind speed **at 2 m above ground** | m/s |
| Rs | incoming solar radiation, daily total | MJ m-2 day-1 |
| ea | actual vapour pressure | kPa |
| J | day of the year: 1 on 1 January, up to 365 (366 in a leap year) | - |
| latitude | decimal degrees, **north positive, south negative** | deg |
| z | station elevation above sea level | m |

Station records do not always arrive in this form. Section 3 lists every form our station register and raw files use
and how each one is converted. The FAO-56 equations themselves (section 2) only ever see the standard form.

## 2. The daily procedure

Constants: solar constant Gsc = 0.0820 MJ m-2 min-1; Stefan-Boltzmann constant sigma = 4.903e-9 MJ K-4 m-2 day-1;
albedo of the reference grass 0.23; absolute temperature in Eq. 39 is T + 273.16.

1. Mean temperature (Eq. 9): Tmean = (Tmax + Tmin) / 2.
2. Air pressure from elevation (Eq. 7): P = 101.3 * ((293 - 0.0065 z) / 293) ^ 5.26, in kPa.
3. Psychrometric constant (Eq. 8): gamma = 0.665e-3 * P, in kPa/degC.
4. Saturation vapour pressure at temperature T (Eq. 11): e0(T) = 0.6108 * exp(17.27 T / (T + 237.3)), in kPa.
5. Mean saturation vapour pressure (Eq. 12): es = (e0(Tmax) + e0(Tmin)) / 2. Do not use e0(Tmean) here.
6. Slope of the saturation curve at Tmean (Eq. 13): Delta = 4098 * e0(Tmean) / (Tmean + 237.3)^2, in kPa/degC.
7. Actual vapour pressure ea, from whichever humidity the station reports (section 3.5):
   - from daily maximum and minimum relative humidity (Eq. 17): ea = [e0(Tmin) RHmax/100 + e0(Tmax) RHmin/100] / 2;
   - from the daily mean dewpoint temperature (Eq. 14): ea = e0(Tdew).
8. Extraterrestrial radiation Ra (Eqs. 21 to 25), with phi = latitude in radians (Eq. 22, negative in the south):
   - inverse relative Earth-Sun distance (Eq. 23): dr = 1 + 0.033 cos(2 pi J / 365);
   - solar declination (Eq. 24): delta = 0.409 sin(2 pi J / 365 - 1.39), in radians;
   - sunset hour angle (Eq. 25): ws = arccos(-tan(phi) tan(delta)), in radians;
   - Ra = (24 * 60 / pi) * Gsc * dr * [ws sin(phi) sin(delta) + cos(phi) cos(delta) sin(ws)] (Eq. 21), MJ m-2 day-1.
   The divisor is 365 in every year, leap years included; J itself runs to 366 in a leap year.
9. Clear-sky radiation (Eq. 37): Rso = (0.75 + 2e-5 z) * Ra.
10. Net shortwave radiation (Eq. 38): Rns = (1 - 0.23) * Rs.
11. Net longwave radiation (Eq. 39):
    Rnl = sigma * [(Tmax + 273.16)^4 + (Tmin + 273.16)^4] / 2 * (0.34 - 0.14 sqrt(ea)) * (1.35 Rs/Rso - 0.35),
    where the ratio Rs/Rso is limited to at most 1.0 before it is used.
12. Net radiation (Eq. 40): Rn = Rns - Rnl.
13. Soil heat flux for a daily step (Eq. 42): G = 0.
14. Reference evapotranspiration (Eq. 6):
    ET0 = [0.408 Delta (Rn - G) + gamma * 900 / (Tmean + 273) * u2 * (es - ea)] / [Delta + gamma (1 + 0.34 u2)],
    in mm/day. The factor 0.408 turns MJ m-2 day-1 into mm/day of evaporated water (Eq. 20).

`et0/fao56.py` implements steps 1 to 14, and `python -m et0.selfcheck` checks it against the daily worked example in
chapter 4 of the book (Example 18, ET0 = 3.88 mm/day).

## 3. Station register and raw files

### 3.1 The register (`config/stations.yaml`)
A YAML file with a list `stations`. Every station has every key below; there are no other forms than the ones listed.

| Key | What it holds |
|---|---|
| `id` | station code; the raw file is `<data folder>/<id>.csv` |
| `name`, `network` | free text, not used in the calculation |
| `latitude` | see 3.2 |
| `longitude` | decimal degrees, east positive; not used by the daily method |
| `elevation_m` | elevation above sea level in metres (z in Eqs. 7 and 37) |
| `wind_height_m` | height of the anemometer above ground in metres; see 3.3 |
| `radiation_units` | unit of the `solar_rad` column; see 3.4 |
| `humidity` | which humidity columns the raw file has; see 3.5 |

### 3.2 Latitude
Two forms are used:
- a number: signed decimal degrees, north positive, south negative (`38.42`, `-31.85`);
- text: unsigned decimal degrees followed directly by the hemisphere letter `N` or `S` (`"36.95N"`, `"34.92S"`).
  `"34.92S"` is the same place as `-34.92`.

### 3.3 Wind sensor height
`wind_ms` is the mean daily wind speed at the anemometer, which may be at any height (any positive value of
`wind_height_m` between 1 m and 20 m; 2, 3 and 10 m are the most common). The equations need u2, the speed at 2 m.
Convert with the logarithmic wind profile (Eq. 47), for every station:

    u2 = uz * 4.87 / ln(67.8 z_w - 5.42)

where uz is the measured speed and z_w the anemometer height in metres. At 10 m the factor is about 0.748; at 2 m it is
1.000 (to three decimals).

### 3.4 Radiation units
- `MJ/m2/day`: daily total incoming solar radiation, already Rs.
- `W/m2`: daily mean solar irradiance. Multiply by 0.0864 to get Rs in MJ m-2 day-1 (1 W m-2 sustained for a day is
  86 400 J m-2 = 0.0864 MJ m-2).

### 3.5 Humidity
- `rh_minmax`: columns `rh_max_pct` and `rh_min_pct` (daily maximum and minimum relative humidity, %); use Eq. 17.
- `dewpoint`: column `tdew_c` (daily mean dewpoint temperature, deg C); use Eq. 14.

### 3.6 Raw daily files (`<data folder>/<id>.csv`)
One row per day, no gaps and no missing values. Columns: `date` (YYYY-MM-DD), `tmax_c`, `tmin_c`, the humidity
column(s) of 3.5, `wind_ms` (m/s at the anemometer height), `solar_rad` (in the station's `radiation_units`).

## 4. Output
CSV with a header row and the columns `station_id`, `date` (YYYY-MM-DD) and `et0_mm_day`: one row for every station
and every day in the input. The pipeline writes three decimals.

Our irrigation advice uses daily reference evapotranspiration (ET0, FAO-56 Penman-Monteith) computed by the `et0`
package in `/app` (overview in `/app/README.md`, method in `/app/docs/METHOD.md`). Growers near some of our stations
say the advice is off, and the national met service's published ET0 for two of our stations
(`/app/reference/metservice_et0_2025.csv`, rounded to 0.1 mm/day) does not match ours. I suspect the high-altitude
station breaks the formula, but please check properly before changing anything.

What I need:

1. Find out why our numbers are wrong and fix the pipeline so that it computes FAO-56 daily ET0 as described in
   `/app/docs/METHOD.md`, for any station register and raw files that use the forms listed there, not only our eight
   stations. It is run like this, from the folder that holds the `et0` package:

   `python -m et0.pipeline --stations <register.yaml> --data <folder with <id>.csv files> --out <output.csv>`

2. Regenerate our published output with it:

   `cd /app && python -m et0.pipeline --stations config/stations.yaml --data data/raw --out output/et0.csv`

How the result is checked:

- We run the command in step 1 on station registers and raw files you have not seen (same formats, other stations),
  from a copy of your `/app` in another folder, as an unprivileged user; it must not need network access. It must
  exit with status 0 within 60 seconds. Apart from the files named on the command line, it must not rely on anything outside
  the folder that holds the `et0` package, nor on absolute `/app` paths.
- We also read `/app/output/et0.csv`.
- Both outputs are compared with an independent FAO-56 calculation. Each must be a CSV with a header row and the columns
  `station_id`, `date` (YYYY-MM-DD) and `et0_mm_day`, with exactly one row for every station and day in the input
  and no other rows. Extra columns and any row order are fine. Every value must be within 0.03 mm/day of the reference.

Only /app is kept when we grade: folders named `data`, `__pycache__` or `.venv` anywhere under /app are dropped, and the packages already installed are available.

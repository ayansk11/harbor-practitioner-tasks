# ET0 pipeline (irrigation advice)

Daily reference evapotranspiration (ET0, FAO-56 Penman-Monteith) for the stations our irrigation advice uses. The
advice service reads `output/et0.csv` every morning and turns ET0 into watering recommendations for growers near each
station.

Run it for our stations:

    cd /app
    python -m et0.pipeline --stations config/stations.yaml --data data/raw --out output/et0.csv

Check the formula against FAO-56's worked example: `python -m et0.selfcheck`.

| Path | What it is |
|---|---|
| `et0/pipeline.py` | command line: register + raw files -> one ET0 value per station and day |
| `et0/meta.py` | reads the station register |
| `et0/ingest.py` | reads one station's raw daily file into the standard inputs |
| `et0/fao56.py` | the FAO-56 daily equations |
| `et0/selfcheck.py` | FAO-56 chapter 4, Example 18 |
| `config/stations.yaml` | station register (8 stations from three networks) |
| `data/raw/<id>.csv` | raw daily records for 2025 |
| `docs/METHOD.md` | the method, every constant, and every input form we accept |
| `reference/metservice_et0_2025.csv` | ET0 published by the national met service for two of our stations (rounded to 0.1 mm/day) |
| `output/et0.csv` | the current published output |

The register now holds stations from three networks: the original `valley-agromet` stations and, since this year,
stations imported from the `highland-synop` and `southern-coast` networks.

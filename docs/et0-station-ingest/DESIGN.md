# et0-station-ingest: design and build record

**What this file is.** The authoring notes for the task `tasks/et0-station-ingest/`: its design, where the build departs
from the plan and why, the local checks, the quality-gate record against `docs/QUALITY_GATE.md` (checks G1-G30), the
Daytona proof results and the known limitations. Paths are relative to the repository root; short names such as
`tests/grade.py` are inside the task folder `tasks/et0-station-ingest/`.

Last updated: 2026-10-30 (Mac clock, MST): limitation 2 (section 11) now records the agent pilot. Before that, 2026-10-29 (Mac clock, MST): wording edited for outside readers and pointers fixed (no number, verdict
or limitation changed; a byte count added to section 2). Before that, also 2026-10-29: section 13 adds the Daytona proof results of 2026-10-28 and the gate record
(section 10) is re-scored from them; the Daytona UNVERIFIED notes of sections 8, 9, 10 and 11 predate that run. Before
that: 2026-10-28, after the second review (section 12). The plan was a design note written before the build; it is not
in this repository, and section 4 lists where the build departs from it. Labels: FACT (sourced, or measured by
us), INFERENCE (reasoned; basis named), UNVERIFIED (not checked). "ch3:n" / "ch4:n" = line n of our saved Markdown
copy of FAO-56 chapter 3 (https://www.fao.org/4/x0490e/x0490e07.htm) and chapter 4
(https://www.fao.org/4/x0490e/x0490e08.htm). The copies are not in this repository and the line numbers follow the order
of the page; where the text also names the book's example, box or table, that is the anchor to look for on the page.

## 1. What the task is
An irrigation-advice service computes daily FAO-56 Penman-Monteith ET0 for eight weather stations. The formula code
(`et0/fao56.py`) is correct. Three input-handling defects make some stations wrong:
1. `et0/ingest.py` ignores `wind_height_m`: wind measured at 3 m or 10 m is used as if measured at 2 m (FAO-56 Eq. 47
   is never applied).
2. `et0/ingest.py` ignores `radiation_units`: stations that log daily mean irradiance in W/m2 are used as if the value
   were MJ m-2 day-1 (the 0.0864 factor is never applied).
3. `et0/meta.py` reads `"34.92S"` as +34.92 (`rstrip("NS")` drops the hemisphere).

In the instruction, the user suspects the high-altitude station (PAL, 1,840 m). That is a misleading lead: PAL is
wrong because its anemometer is at 10 m, not because of its altitude. The agent must fix the pipeline for any register
that uses the forms listed in `/app/docs/METHOD.md` and regenerate `/app/output/et0.csv`. The grader runs the agent's
command on ten hidden stations (other heights, both hemispheres, both units, both humidity types) and checks the
visible output.

## 2. File map
Package `tasks/et0-station-ingest/` (58 files, 586,251 bytes; FACT, `find -type f | wc -l` and the sum of `stat`
sizes on 2026-10-29; `du -sh` gave 828 KB after the review fixes):

| Path | What it is |
|---|---|
| `task.toml` | schema 1.4, the shared `/app` artifact, `[verifier] environment_mode = "separate"`, timeouts, 1 vCPU, 1 GiB |
| `instruction.md` | the request; states the command, output schema, row rule, 0.03 mm/day tolerance, 60 s cap, unprivileged user, no network need, copy of /app, the shared closing sentence |
| `environment/Dockerfile` | pinned base digest; numpy 2.5.4, pandas 3.1.0, python-dateutil 3.0.0, six 1.17.0, tzdata 2026.6, PyYAML 6.0.3; `WORKDIR /app`; `COPY app/ /app/` |
| `environment/app/et0/` | `pipeline.py` (CLI), `meta.py` (defect 3), `ingest.py` (defects 1, 2), `fao56.py` (correct), `selfcheck.py` (FAO Example 18) |
| `environment/app/config/stations.yaml` | 8 visible stations (table in section 5) |
| `environment/app/data/raw/<id>.csv` | 365 days of 2025 per station (dropped at grading, by design) |
| `environment/app/docs/METHOD.md` | the method in our own words with equation numbers, every constant, every metadata form, file formats, output |
| `environment/app/reference/metservice_et0_2025.csv` | met-service ET0 for PAL and CDB, rounded to 0.1 mm/day (730 rows) |
| `environment/app/output/et0.csv` | the current wrong output, made by the shipped pipeline |
| `environment/app/README.md` | overview, command, layout, the three networks |
| `tests/Dockerfile` | same base and pins; `COPY . /tests/`, uid 1001 `runner`, `/tests` 0700 |
| `tests/test.sh`, `tests/kit.py` | shared kit, copied by `tools/sync_kit.py` |
| `tests/grade.py` | the grader (section 6); in real mode it also makes `/app` unavailable after copying it |
| `tests/hidden/` | `stations.yaml` + `raw/H01..H10.csv` (10 hidden stations; H01-H09 in 2025, H10 in 2024, a leap year) |
| `tests/expected/` | `visible_et0.csv`, `hidden_et0.csv`: reference A, 6 decimals |
| `tests/SHA256SUMS` | 13 files (hidden inputs and expected values); `grade.py` verifies them before grading |
| `solution/solve.sh` | `SOLUTION` = canonical (default), `alt`, `nop`, or one of nine attempts |
| `solution/canonical/` | `ingest.py` (Eq. 47 + unit conversion at load), `meta.py` (N/S letter) |
| `solution/alt/` | `fao56.py` (+ `et0_from_readings`), `pipeline.py` (passes height and unit into the call chain), `meta.py` (regex) |
| `solution/attempts/` | six wrong or shortcut attempts: `fit_to_metservice`, `hardcode_output`, `linear_wind`, `fix_altitude`, `units_not_latitude`, `nearest_height`; three real-mode defence probes: `read_answers`, `symlink_output` (README only; solve.sh makes the link), `abs_app_path` |

Authoring scripts `authoring/et0-station-ingest/` (shipped in the repository, outside the package):

| Script | What it does | Output |
|---|---|---|
| `ref_a.py` | reference A: scalar `math`, book order (Box 11), keeps every intermediate | used by the next three |
| `ref_b.py` | reference B: vectorised numpy, arctan sunset angle (Eq. 26), one-fraction Eq. 6, own parsers | |
| `reproduce_fao_examples.py` | build step one: Examples 18 and 17, ours vs the book | `reproduce_fao_examples.out.md` |
| `gen_data.py` | all visible and hidden data, expected values (reference A), met-service file, current output, SHA256SUMS | fixed seeds 101-108, 201-210; H10 in 2024 |
| `tolerance_study.py` | reference B, the shipped code, honest variants and material mistakes vs reference A | `tolerance_study.out.md` |
| `local_check.py` | the local proof matrix (section 9) | `local_results.json` |
| `summarize.py` | per-station reference ET0 and shipped-output means (section 5) | `station_summary.out.md` |
| `grader_probes.py` | format and tamper probes on the output file; per-station attempt errors | `grader_probes.out.md` |
| `defence_probes.py` | the three defence probes with their target path made reachable (defence absent) must score 1 | `defence_probes.out.md` |

## 3. Build step one: the reference reproduces FAO-56 (G6, G15)
FACT (`reproduce_fao_examples.py`, exit 0, output `reproduce_fao_examples.out.md`): reference A reproduces Example 18
(Uccle, Brussels, 6 July, 50 deg 48 min N, 100 m; ch4:256-324): ET0 = 3.880259 mm/day against the book's 3.88
(|difference| 0.000259, limit 0.01), and all 33 intermediate values are within the book's printed rounding (half a
unit of the last printed digit). Reference B gives 3.880259 on the same day (|A - B| = 0).

**Example 18 (daily), reference A vs the book**

| Quantity | Ours | Book | ch4 line | Within book rounding | Note |
|---|---|---|---|---|---|
| uz (m/s) | 2.77778 | 2.78 | 268 | yes | 10 km/h / 3.6 |
| u2 (m/s) | 2.077642 | 2.078 | 269 | yes | book prints "2,078"; factor 4.87/ln(67.8*10-5.42) |
| P (kPa) | 100.1235 | 100.1 | 272 | yes | |
| Tmean (C) | 16.9000 | 16.9 | 273 | yes | |
| Delta (kPa/C) | 0.122113 | 0.122 | 275 | yes | |
| gamma (kPa/C) | 0.0665821 | 0.0666 | 277 | yes | |
| 1+0.34u2 | 1.70640 | 1.71 | 278 | yes | |
| Delta/[Delta+gamma(1+0.34u2)] | 0.518023 | 0.518 | 279 | yes | |
| gamma/[Delta+gamma(1+0.34u2)] | 0.282453 | 0.282 | 280 | yes | |
| 900/(T+273) u2 | 6.450078 | 6.450 | 281 | yes | |
| e(Tmax) (kPa) | 2.564420 | 2.564 | 284 | yes | |
| e(Tmin) (kPa) | 1.430551 | 1.431 | 286 | yes | |
| es (kPa) | 1.997486 | 1.997 | 287 | yes | the book's line omits the /2 but prints the mean |
| ea (kPa) | 1.408624 | 1.409 | 290 | yes | Eq. 17 |
| es-ea (kPa) | 0.588862 | 0.589 | 291 | yes | |
| Ra (MJ/m2/d) | 41.08838 | 41.09 | 297 | yes | J = 187 |
| N (h) | 16.1046 | 16.1 | 300 | yes | |
| n/N | 0.57437 | 0.57 | 301 | yes | the book writes 9.25/16.3, a typo (N = 16.1 one line above); 0.57 either way |
| Rs (MJ/m2/d) | 22.07205 | 22.07 | 302 | yes | Eq. 35 |
| Rso (MJ/m2/d) | 30.89846 | 30.90 | 303 | yes | |
| Rs/Rso | 0.71434 | 0.71 | 304 | yes | |
| Rns (MJ/m2/d) | 16.99548 | 17.00 | 305 | yes | |
| sigma Tmax,K^4 | 36.96125 | 36.96 | 308 | yes | |
| sigma Tmin,K^4 | 32.55689 | 32.56 | 311 | yes | |
| mean sigma T^4 | 34.75907 | 34.76 | 312 | yes | |
| 0.34-0.14 sqrt(ea) | 0.17384 | 0.17 | 313 | yes | |
| 1.35 Rs/Rso - 0.35 | 0.61436 | 0.61 | 314 | yes | |
| Rnl (MJ/m2/d) | 3.71229 | 3.71 | 315 | yes | |
| Rn (MJ/m2/d) | 13.28319 | 13.28 | 316 | yes | |
| 0.408(Rn-G) (mm/d) | 5.41954 | 5.42 | 319 | yes | G = 0 |
| radiation term (mm/d) | 2.80745 | 2.81 | 321 | yes | |
| aerodynamic term (mm/d) | 1.07281 | 1.07 | 322 | yes | |
| ET0 (mm/d) | 3.88026 | 3.88 | 323 | yes | |

**Example 17 (monthly, the second check; ch4:182-242).** FACT (same output file): ET0 5.71612 against 5.72; 29 of 30
values within the book's rounding. The one miss is gamma: ours 0.0673488 against the book's 0.0674 (ch4:200). The book
took gamma from its tables (ch4:198, "From Table 2.1 and Table 2.2"), i.e. from P rounded to 101.3 kPa; Eq. 8 with
P = 101.3 gives 0.0673645, which rounds to 0.0674. INFERENCE: the difference is the book's table rounding, not ours.
The full Example 17 table is in `reproduce_fao_examples.out.md`.

**Where each equation's form comes from.** The saved pages show several equations only as images, so the form used is
the one the book's worked examples spell out. FACT, by line: Eq. 7 and Eq. 8 = ch3:129-130 (Example 2); Eq. 11 =
ch3:228; Eq. 12 = ch3:230; Eq. 14 = ch3:252; Eq. 17 with the /2 = ch4:110 (Box 11, "(average)") and ch4:290; Eq. 22
sign = ch3:505; Eq. 23, 24 = ch3:552-553; Eq. 25 = ch3:531; Eq. 21 = ch3:557; J from 1 to 365 or 366 = ch3:527; Eq. 34
= ch3:635; Eq. 37 = ch3:717; albedo 0.23 = ch3:735; Eq. 39 = ch3:788, sigma = ch3:751, T + 273.16 = ch3:753, Rs/Rso
<= 1.0 = ch3:759; Eq. 42 = ch3:861; Eq. 47 = ch3:945 (Example 14); 0.0864 = ch3:470; 0.408 = ch3:452; Gsc = ch3:495.
Eq. 13 (slope) appears only as an image: the form `4098 e0(T)/(T+237.3)^2` reproduces the book's 0.122 at 16.9 C and
0.246 at 30.2 C (the Delta row above, and the Delta row of the Example 17 table in
`authoring/et0-station-ingest/reproduce_fao_examples.out.md`), so it is FACT by reproduction. Eq. 6 = ch4:321-323 and ch4:238-241 (the two terms).

`/app/docs/METHOD.md` restates all of this in our own words with the equation numbers (no FAO text copied).

## 4. Deviations from the planned design (and why)
"Plan" is the pre-build design note (not in this repository).

| # | Plan says | Built | Why |
|---|---|---|---|
| 1 | tolerance placeholder 0.02 mm/day, "set at build from the spread of two independent implementations" | **0.03 mm/day** | The two references agree exactly (spread 0), so the spread gives no floor. The floor comes from honest variants instead (section 7): the worst single one is 0.018, all of them at once 0.0277. 0.03 passes all of them and still catches the smallest material mistake (0.085) and the smallest designed attempt (0.434). |
| 2 | five attempts | nine: adds `nearest_height` and three real-mode defence probes (`read_answers`, `symlink_output`, `abs_app_path`) | The plan's "Shortcuts fail" already names a lookup of factors for the visible heights as hardening; it now has its own attempt. The three probes are the only evidence for this task that the kit's privilege steps and the /app lock hold on Daytona: each scores 1 only if its defence fails (`defence_probes.py`). |
| 3 | `fit_to_metservice`, `fix_altitude` | both also fix the radiation units | The units defect gives 27-35 mm/day at three stations, so any real attempt fixes it first; leaving it would make these attempts fail for a trivial reason and test nothing. |
| 4 | per-run cap "3 x the measured slowest valid solution" (the plan's shared verifier rules for all five tasks) | 60 s | 3 x 0.786 s = 2.4 s, measured on an Apple M4, not on a 1-vCPU Daytona sandbox (UNVERIFIED there). A correct run must not fail on sandbox speed (G15, G16). This task has no slow-but-wrong failure mode, so a larger cap costs nothing. |
| 5 | verifier timeout "sum of caps + measured grading time + 50%" | 120 s | The formula gives (60 + 0.84) x 1.5 = 91.3 s; rounded up to 120 s because the grading steps outside the cap were timed only on the Mac. |
| 6 | "two humidity types" (not named) | RH max/min (Eq. 17) and dewpoint (Eq. 14) | The two forms the daily procedure uses most; both in METHOD.md 3.5. |
| 7 | "one year of daily data" | visible 2025; hidden H01-H09 2025 and H10 2024 (a leap year, 366 rows) | Visible stays 2025 (no J/366 question for the agent's own data). The hidden leap year exercises the rule METHOD.md states (J up to 366, divisor 365): a pipeline that assumes 365 rows or fails at J = 366 now fails. The 366 divisor itself moves values by at most 0.011, under the tolerance (section 7, limitation 9). |
| 8 | (not in the plan) | `grade.py` verifies `tests/SHA256SUMS` before grading; a mismatch scores 0 | Guards G16: the verifier grades against exactly the committed data. |
| 9 | "Pinned numpy, pandas, PyYAML" | the same plus their dependencies (python-dateutil, six, tzdata), identical in both images; no pytest | The self-check is a module (`python -m et0.selfcheck`), so no test runner is needed. |
| 10 | hidden heights 2, 3, 6, 10 m plus 2.5, 4.5, 7.5, 12 m | adds 1 m (H10, was 2 m) and 20 m (H09, was 10 m); 2 m and 10 m remain at H01 and H04 | METHOD.md 3.3 promises any height from 1 m to 20 m; the two ends were not exercised. A clamp of the height to 2-12 m now fails (0.433 mm/day, 687 station-days over 0.03; section 7). |
| 11 | (not in the plan) | real mode: `grade.py` renames `/app` to `/app.unavailable` right after copying it (fallback: root-owned, mode 0700); metric `app_locked` | The instruction says the pipeline must not rely on absolute `/app` paths. Without this step the artifact still sat at `/app` in the verifier, so such a pipeline would score 1 on Daytona and 0 on the Mac. The step never raises; a failure is logged and reported as `app_locked` = 0. Unproven on the Mac (no `/app` there). |
| 12 | (not in the plan) | hidden inputs staged with `kit.stage_for_runner` (`/work/hidden_in`, empty `/work/hidden_out`); `kit.TESTS_DIR`; `GRADE_PYTHON` honoured only in local mode | Follows rules 2, 5 and 7 of the kit README (`base/verifier_kit/README.md`). The earlier hand-made copy under `/work` was safe here (no agent code had run yet) but departed from the documented API. |

## 5. Stations
Visible (2025; FACT, `gen_data.py` and `summarize.py` -> `station_summary.out.md`; ET0 = reference A
min/mean/max in mm/day; "now" = mean of the shipped wrong output):

| id | latitude as written | elev m | wind m | radiation | humidity | network | defect(s) | ET0 min/mean/max | now |
|---|---|---|---|---|---|---|---|---|---|
| VNT | 38.42 | 85 | 2 | MJ/m2/day | RH | valley-agromet | none | 1.09/3.55/7.74 | 3.55 |
| PAL | "36.95N" | 1840 | 10 | MJ/m2/day | RH | highland-synop | wind (the misleading lead) | 0.85/2.88/6.47 | 3.10 |
| CDB | "34.92S" | 48 | 2 | MJ/m2/day | dewpoint | southern-coast | latitude | 1.25/3.59/7.41 | 3.60 |
| LGN | -31.85 | 420 | 3 | W/m2 | RH | southern-coast | wind, units | 1.36/4.23/9.76 | 34.48 |
| RSD | "41.73N" | 230 | 2 | W/m2 | dewpoint | highland-synop | units | 0.98/3.70/9.09 | 26.88 |
| MRS | 35.10 | 12 | 3 | MJ/m2/day | RH | valley-agromet | wind | 1.45/4.01/8.59 | 4.11 |
| HLT | "33.40S" | 610 | 10 | W/m2 | dewpoint | highland-synop | all three | 1.11/3.71/9.29 | 29.91 |
| ARN | 40.05 | 690 | 2 | MJ/m2/day | dewpoint | valley-agromet | none | 0.67/3.21/7.55 | 3.21 |

CDB's annual mean is almost unchanged (3.60 vs 3.59) but its seasons are wrong (INFERENCE: with measured Rs, latitude
enters through Rso, so winter days lose most of their net longwave loss). The met service publishes PAL and CDB.

Hidden (10 stations; H01-H09 in 2025, H10 in 2024): H01 "12.35N" 5 m elev, 2 m, W/m2, dewpoint; H02 -23.55, 760,
3 m, MJ, RH; H03 "45.80N", 1960, 6 m, MJ, RH; H04 "38.10S", 30, 10 m, W/m2, RH; H05 52.20, 15, 2.5 m, MJ, dewpoint; H06
"29.95S", 1250, 4.5 m, W/m2, dewpoint; H07 31.60, 410, 7.5 m, MJ, RH; H08 "6.75S", 140, 12 m, MJ, dewpoint; H09
"47.30N", 880, 20 m, MJ, RH; H10 -41.20, 260, 1 m, W/m2, RH, 366 days. Every latitude form, both units, both humidity
types, heights 1, 2, 2.5, 3, 4.5, 6, 7.5, 10, 12 and 20 m, elevations 5-1,960 m, one leap year; only forms listed in
METHOD.md. 3,651 hidden station-days. Reference ET0 ranges 0.35-11.77 mm/day hidden and 0.67-9.76 visible (FACT,
`station_summary.out.md`).

The weather is synthetic: a seasonal cycle by hemisphere and elevation plus autocorrelated noise, clearness index
mostly 0.28-1.0 with a few days up to 1.03 (so the Rs/Rso cap matters: removing it moves 17 station-days by more
than 0.02), RHmin <= RHmax <= 100, Tdew <= Tmin, values rounded as a logger writes them. Expected ET0 is computed from the
rounded file values. FACT: rerunning `gen_data.py` gives byte-identical files (32 of 32 compared, 2026-10-28; and
again after the H09/H10 change: sha256 of all 54 package files then present, identical after a second run). The change
left every visible file, the met-service file and the shipped output byte-identical; only `tests/hidden/stations.yaml`,
`H09.csv`, `H10.csv`, `tests/expected/hidden_et0.csv` and `tests/SHA256SUMS` changed (still 13 files listed).

## 6. The grader (`tests/grade.py`)
1. Verify `tests/SHA256SUMS` (13 files); any mismatch raises, and `kit.main` scores 0.
2. `kit.prepare_submission()` copies the `/app` artifact to `/work/sub` for uid 1001, removing auto-run files.
3. Real mode only: `/app` is made unavailable (deviation 11). First `rename("/app", "/app.unavailable")` (it moves the
   entry itself and never follows a symlink; `/` is root-owned, so uid 1001 cannot recreate `/app`); if that fails, for
   example on a mount point, the real directory is made root-owned 0700 through an `O_NOFOLLOW` descriptor. The step
   never raises: `app_locked` = 1 (locked), 0 (failed, logged) or -1 (local mode, nothing to lock). Nothing after this
   step reads `/app`.
4. Visible check: `/work/sub/output/et0.csv` read with `kit.read_as_runner` (a symlink into /tests then fails), compared
   with `tests/expected/visible_et0.csv`.
5. Hidden check: `kit.stage_for_runner(<tests>/hidden, "hidden_in")` copies the hidden inputs (never the answers) to
   `/work/hidden_in` for uid 1001, and `kit.stage_for_runner(None, "hidden_out")` makes an empty output folder. Then
   `python3 -m et0.pipeline --stations /work/hidden_in/stations.yaml --data /work/hidden_in/raw --out
   /work/hidden_out/et0.csv` runs as uid 1001 with cwd `/work/sub` and a 60 s cap, without `-I` (the stated interface
   needs the package folder on `sys.path`); the output is read as uid 1001 and compared with
   `tests/expected/hidden_et0.csv`.
6. Comparison: header must contain `station_id`, `date`, `et0_mm_day` once each; extra columns and any row order
   accepted; each (station_id, date) exactly once; no missing, extra, duplicate or unreadable rows; finite values;
   every |value - reference| <= 0.03. Reward 1 only if both checks pass and the run exits 0 in time.
7. Sub-metrics in `reward.json`: per check `*_max_abs_err`, `*_rows_over_tol`, `*_missing_rows`, `*_extra_rows`,
   `*_bad_rows`, `*_duplicate_rows`, plus `hidden_run_rc`, `hidden_run_timed_out`, `hidden_run_seconds`,
   `app_locked`, `tolerance_mm_day`.
The grader uses only the standard library; it never imports agent code. `GRADE_TESTS_DIR` (through `kit.TESTS_DIR`) and
`GRADE_PYTHON` are honoured only in local mode.

## 7. Tolerance
FACT (`tolerance_study.py`, `tolerance_study.out.md`, re-run after the H09/H10 change; max |difference from reference A|
in mm/day over the 2,920 visible and the 3,651 hidden station-days; the row counts are visible and hidden together):

| Variant | visible | hidden | rows > 0.02 | rows > 0.03 | rows > 0.05 |
|---|---|---|---|---|---|
| reference B (independent code) | 0.000000 | 0.000000 | 0 | 0 | 0 |
| shipped fao56.py + canonical fix, unrounded | 0.000000 | 0.000000 | 0 | 0 | 0 |
| Eq. 47 factor rounded to 3 decimals | 0.000858 | 0.001674 | 0 | 0 | 0 |
| Eq. 47 factor rounded to 2 decimals | 0.010060 | 0.018051 | 0 | 0 | 0 |
| 273.15 instead of 273.16 in Eq. 39 | 0.000286 | 0.000321 | 0 | 0 | 0 |
| T + 273.16 instead of T + 273 in Eq. 6 | 0.003952 | 0.005077 | 0 | 0 | 0 |
| exact gamma = cp P / (eps lambda) | 0.000858 | 0.001291 | 0 | 0 | 0 |
| arctan sunset angle (Eq. 26) | 0.000000 | 0.000000 | 0 | 0 | 0 |
| output rounded to 2 decimals | 0.005000 | 0.004999 | 0 | 0 | 0 |
| all honest variants at once | 0.012026 | 0.027656 | 22 | 0 | 0 |
| MISTAKE: Rso by Eq. 36 (no altitude term) | 0.113692 | 0.106290 | 2369 | 1254 | 569 |
| MISTAKE: sea-level pressure everywhere | 0.261314 | 0.247549 | 2241 | 1657 | 927 |
| MISTAKE: es from Tmean | 0.769708 | 1.163006 | 6571 | 6570 | 6527 |
| MISTAKE: ea from RHmean (Eq. 19) | 0.991739 | 1.097633 | 3646 | 3631 | 3585 |
| MISTAKE: Rs/Rso not capped at 1 | 0.044715 | 0.085077 | 17 | 13 | 8 |
| MISTAKE: W/m2 x 1/11.6 instead of x 0.0864 | 0.012727 | 0.011922 | 0 | 0 | 0 |
| MISTAKE: nearest of the 2, 3, 10 m factors | 0.000858 | 0.433895 | 2456 | 2171 | 1734 |
| MISTAKE: 0.75 for every height other than 2 m | 0.751104 | 1.139117 | 3596 | 3426 | 3027 |
| MISTAKE: wind height clamped to 2-12 m before Eq. 47 | 0.000000 | 0.433329 | 719 | 687 | 562 |
| MISTAKE: divisor 366 in a leap year (Eqs. 23, 24) | 0.000000 | 0.011403 | 0 | 0 | 0 |
| MISTAKE: day of year clipped at 365 | 0.000000 | 0.001480 | 0 | 0 | 0 |

Reading (INFERENCE from the table): a correct fix that keeps the shipped `fao56.py` lands within 0.0005 (its own
3-decimal output). Every honest variant passes 0.03, even all at once (0.0277; that combination includes choices
METHOD.md does not make, such as a 2-decimal wind factor). The 0.02 placeholder would fail that combination on 22
station-days. The smallest material mistake (no Rs/Rso cap) still fails at 0.03 on 13 station-days. Every wrong or
shortcut attempt has a worst hidden error of at least 0.434 (14 times the tolerance) and fails at two or more hidden
stations (table below). Using 1/11.6 instead of 0.0864 passes: it is within the precision of the book's own conversion
table and is accepted (G11). The H09/H10 change adds two checks: a height clamp to 2-12 m fails (0.433 mm/day), and a
pipeline that assumes 365 rows or cannot handle J = 366 fails on H10's row count. The leap-year arithmetic is not
caught: a 366 divisor moves values by at most 0.011 and clipping J at 365 by at most 0.0015, both under 0.03, so both
are accepted as within tolerance (limitation 9).

Worst hidden error per station and variant (FACT, `grader_probes.out.md`; bold = over 0.03):

| Variant | H01 2 m N W | H02 3 m - MJ | H03 6 m N MJ | H04 10 m S W | H05 2.5 m + MJ | H06 4.5 m S W | H07 7.5 m + MJ | H08 12 m S MJ | H09 20 m N MJ | H10 1 m - W 2024 |
|---|---|---|---|---|---|---|---|---|---|---|
| canonical | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 |
| alt | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 |
| nop | **57.634** | **0.220** | **0.377** | **48.864** | **0.086** | **67.411** | **1.290** | **1.083** | **0.905** | **50.649** |
| fit_to_metservice | 0.001 | **0.220** | **0.377** | **1.378** | **0.086** | **1.296** | **1.290** | **1.083** | **0.905** | **0.434** |
| hardcode_output | **57.634** | **0.220** | **0.377** | **48.864** | **0.086** | **67.411** | **1.290** | **1.083** | **0.905** | **50.649** |
| linear_wind | 0.001 | **0.509** | **0.141** | 0.006 | **0.434** | **0.422** | **0.210** | **0.087** | **0.224** | **1.139** |
| fix_altitude | 0.001 | **0.324** | **0.496** | **1.379** | **0.087** | **1.343** | **1.445** | **1.113** | **0.983** | **0.417** |
| units_not_latitude | 0.000 | 0.000 | 0.000 | **1.018** | 0.000 | **1.107** | 0.000 | **0.266** | 0.000 | 0.001 |
| nearest_height | 0.001 | 0.001 | **0.226** | 0.001 | **0.086** | **0.253** | **0.223** | **0.079** | **0.218** | **0.434** |

The canonical 0.001 at H10 is the 3-decimal display of 0.0005 (`local_results.json`: `hidden_max_abs_err` 0.0005).
`linear_wind` passes at 2 m and 10 m (0.75 is close to 0.748) and fails at every other height, as designed;
`nearest_height` passes at the heights in its table and fails at 1, 2.5, 4.5, 6, 7.5, 12 and 20 m.

## 8. Timings and caps
FACT (local, Apple M4, two full runs of `local_check.py`; the second is in `local_results.json`): the hidden pipeline
run took 0.761-0.819 s (first run) and 0.757-1.004 s (second run) across all variants; the slowest valid solution was
canonical at 0.786 s; a whole grading pass took 0.82-1.07 s; `solve.sh` took 0.77-0.94 s for canonical and alt (1.54 s
for `fit_to_metservice`, first run). Derived: per-run cap 60 s (deviation 4: 3 x 0.786 = 2.4 s); `verifier.timeout_sec` 120 s
(deviation 5: formula 91.3 s); `agent.timeout_sec` 1800 s (the plan). UNVERIFIED: the same steps on a 1-vCPU Daytona sandbox;
the proof run's `hidden_run_seconds` metric will show it. Image size about 250 MB: UNVERIFIED (not built; no Docker on
the Mac). Re-runs after the review fixes (FACT, all twelve variants; the second is in `local_results.json`): hidden
pipeline run 0.271-0.382 s and 0.312-0.375 s, slowest valid solution canonical at 0.382 s and 0.33 s, grading pass
0.34-0.48 s and 0.38-0.47 s, `solve.sh` 0.01-0.61 s and 0.01-0.59 s. The caps stay as derived from the slower first
runs.

## 9. LOCAL RESULTS
Command, from the repository root: `.venv/bin/python authoring/et0-station-ingest/local_check.py` (`.venv` is our
local authoring environment, not in the repository; its pins are `tools/dev-requirements.lock`). Each variant: copy
`environment/app`, `SOLUTION=<variant> APP_DIR=<copy> bash solution/solve.sh`, drop `data`, `__pycache__`, `.venv` at
any depth, then `KIT_LOCAL=1 KIT_SUBMISSION=<artifact> KIT_LOGS=<dir> KIT_WORK=<dir> GRADE_TESTS_DIR=<task>/tests
GRADE_PYTHON=<venv python> python tests/grade.py`. FACT, run 2026-10-28 18:59 MST after the review fixes and again at
19:06 MST after the last kit sync, same verdicts and errors (`local_results.json` holds the second; both printed
`ALL AS EXPECTED`; `app_locked` = -1 in every run, local mode):

| Variant | Expected | Got | visible max err | visible rows > tol | hidden max err | hidden rows > tol | Note |
|---|---|---|---|---|---|---|---|
| canonical | 1 | 1 | 0.0005 | 0 | 0.0005 | 0 | |
| alt | 1 | 1 | 0.0005 | 0 | 0.0005 | 0 | |
| nop (original state) | 0 | 0 | 66.684 | 2184 | 67.411 | 3461 | |
| fit_to_metservice | 0 | 0 | 1.455 | 1597 | 1.378 | 3073 | |
| hardcode_output | 0 | 0 | 0.0005 | 0 | 67.411 | 3461 | fails only on the hidden run |
| linear_wind | 0 | 0 | 0.752 | 730 | 1.139 | 2693 | |
| fix_altitude | 0 | 0 | 1.451 | 1898 | 1.445 | 2901 | |
| units_not_latitude | 0 | 0 | 1.405 | 715 | 1.107 | 1027 | |
| nearest_height | 0 | 0 | 0.0012 | 0 | 0.434 | 2174 | fails only on the hidden run |
| read_answers | 0 | 0 | 0.0005 | 0 | 67.411 | 3461 | trivial 0 here: no /tests on the Mac, so it falls back to the unfixed code |
| symlink_output | 0 | 0 | unreadable | 2920 missing | 0.0005 | 0 | trivial 0 here: the link target /tests does not exist on the Mac |
| abs_app_path | 0 | 0 | 0.0005 | 0 | no output | 3651 missing | trivial 0 here: no /app on the Mac; hidden run rc 1 (FileNotFoundError) |

Each of the last three fails exactly at the point it targets: the visible file is correct for `read_answers` and
`abs_app_path`, the hidden run is correct for `symlink_output`. Discrimination check (FACT, `defence_probes.py`,
`defence_probes.out.md`): with each attempt's hard-coded path pointed at a file that exists (the defence absent), all
three score 1 (`ALL DISCRIMINATE`). So a 0 for them on Daytona means the defence held, with one caveat for
`symlink_output`: the kit logs the same `visible output unreadable: ... missing or not visible to the runner` line
whether the link was refused or never reached the verifier; the trial's `artifacts/app/output/et0.csv` tells which
(`solution/attempts/symlink_output/README.md`).

UNPROVEN LOCALLY: the /app lock (deviation 11), uid 1001, `/tests` 0700, the symlink defence and the reward-folder lock
are kit or grader steps that KIT_LOCAL skips. The Daytona matrix is the only evidence for them. A 1 on `read_answers`,
`symlink_output` or `abs_app_path` there is a kit or lock failure, not a task failure, and blocks the task until fixed.

Grader probes (FACT, `grader_probes.py`, re-run after the review fixes; the canonical artifact with only
`output/et0.csv` rewritten): pass as expected for shuffled rows, extra columns in another order, 2-decimal values,
quoted fields with CRLF, a UTF-8 BOM with a blank trailing line; fail as expected for one duplicate row, one missing
row, one extra station-day, one NaN, a renamed header, one value off by 0.05 (`ALL PROBES AS EXPECTED`).

Static checks (FACT, after `python tools/sync_kit.py`): `harbor lint tasks/et0-station-ingest --json` printed `[]`;
`python tools/check_task.py tasks/et0-station-ingest` printed `OK et0-station-ingest`. `python -m et0.selfcheck` on the
shipped package prints Example 18 -> 3.880 (book 3.88); `reproduce_fao_examples.py` output unchanged.

## 10. Gate record (implementation)
Each check G1-G30 is defined in `docs/QUALITY_GATE.md`. "(run)" = shown by a recorded run; "(plan)" = PASS by design,
not shown by a run.

```
Gate record: et0-station-ingest, implementation (2026-10-28, after the second review; the (run) items re-scored 2026-10-29 from the recorded Daytona runs, section 13; paths relative to the repository root)
Applies to: task et0-station-ingest
G1  PASS - code, data, method notes, pins, hidden data and answers are in the package; FAO-56 is not needed at run time (images install pinned wheels from PyPI at build time, like every task)
G2  PASS - irrigation advice depends on correct daily ET0 per station
G3  PASS - a small real-looking pipeline: CLI, register from three networks, raw logger files, method notes, met-service comparison, self-check
G4  PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - per station-day numeric comparison by script; proven locally in KIT_LOCAL mode; Daytona gave the same verdicts (13 of 13 rows as expected) and the same error values as section 9
G5  PASS - the only task about unit and metadata handling under a published standard
G6  PASS - build step one done: Example 18 reproduced (3.8803 vs 3.88, 33/33 intermediates within the book's rounding), Example 17 reproduced (one explained table-rounding difference); two independent references agree on all 6,571 station-days
G7  PASS - agro-met and irrigation services compute FAO-56 ET0 daily from mixed station networks
G8  PASS - METHOD.md lists every equation, constant, metadata form, file format and the output; the instruction states every task-specific rule the verifier enforces: the command, columns, row rule, 0.03 tolerance, 60 s cap, exit 0, unprivileged user, no network need, the /app copy and no absolute /app paths (now enforced, deviation 11). The shared kit's removal of auto-run files and its size and output caps are not stated (fixed closing line; limitation 8)
G9  PASS - 1 to 20 m masts, W/m2 vs MJ/m2/day and hemisphere letters are real metadata variants; ranges plausible (section 5); see limitation 1
G10 PASS - a fixed pipeline plus the regenerated output file
G11 PASS - only output numbers are checked; conversion at load (canonical) and in the call chain (alt) both pass; a magnitude-based unit guess would pass too and is accepted; every stated input form is exercised, including the 1 m and 20 m ends and a leap year (deviations 7, 10)
G12 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - the six wrong or shortcut attempts and the three defence probes score 0 locally and on Daytona; the probes score 1 with their defence absent (defence_probes.py); answers only in root-only /tests (read_answers scored 0 on Daytona, which fits that: INFERENCE, NOTES.md); agent code runs as uid 1001; /app locked in real mode (app_locked 1 in 22 of 22 trials; abs_app_path rc 1); symlink_output scored 0 through Harbor's artifact sanitising, so the grader's own symlink defence was not exercised (validation/et0-station-ingest/NOTES.md)
G13 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - alt scores 1 locally and 1.0 on Daytona; format probes pass locally (order, extra columns, 2 decimals, CRLF, BOM, quotes)
G14 PASS - the crux is diagnosis of three input defects against a misleading altitude hint, and a general fix for any height; probably at the easy end for a strong agent (limitation 2), but the difficulty that exists comes from the diagnosis, not from volume or formatting
G15 PASS - tolerance from the honest-variant study (all pass, worst 0.0277); every task-specific rule stated and enforced; cap 60 s vs under 1 s measured
G16 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - pinned digest and exact pins in both images; generator byte-identical on rerun (re-checked after the H09/H10 change); SHA256SUMS checked by the grader (13 files verified in 22 of 22 trials); no randomness at grade time; on Daytona oracle 10 of 10 and --force-build 1.0, hidden max error 0.0005 in each
G17 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - separate verifier (24 of 24 trials); tests/ only in the verifier image (read_answers scored 0, which fits a root-only /tests: INFERENCE, NOTES.md); environment/Dockerfile copies only app/; /app made unavailable to the runs in real mode (renamed to /app.unavailable in 22 of 22); the met-service sample is a deliberate visible input for two visible stations
G18 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - harbor lint [] and check_task OK; Daytona ran both images in all 22 trials, and the --force-build trial scored 1.0
G19 PASS - kit copied into tests/; nothing depends on another task's folder
G20 PASS (plan) - README row text in section 11; the repository README is written once for all five tasks
G21 PASS (plan) - limitations in section 11, including the likely-easy difficulty, the unstated kit behaviours and the leap-year arithmetic blind spot
G22 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - canonical 1 locally; Daytona oracle 10 of 10 = 1.0 and --force-build 1.0
G23 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - nop 0 locally and 0.0 on Daytona
G24 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - nine attempts 0 locally (three of them trivially, see section 9) and 0.0 on Daytona, where the three probes met the real defences (symlink caveat in G12)
G25 PASS (run, recorded: validation/et0-station-ingest/PROOF_RESULTS_full1.md) - alt 1 locally and 1.0 on Daytona (--ae SOLUTION=alt)
G26 PASS (plan) - proof-run traces shipped (one trial per variant is in validation/et0-station-ingest/traces/)
G27 PASS (plan) - no keys or our machines needed; no network_mode set; images build from public PyPI
G28 PASS - valuable work, per-day scoring of the requested numbers, failure = misdiagnosis or a wrong conversion
G29 PASS - the three defects are real metadata fields; off-grid hidden heights, the 1 m and 20 m ends and the leap year test stated rules, nothing more
G30 PASS (plan) - delivery of the repository is a separate, repository-level step
Result: PASS (implementation); no FAIL; the (run) items are proven by the recorded Daytona runs of 2026-10-28 (section 13); the grader's own symlink defence (read_as_runner) is still unexercised on Daytona, a second layer behind Harbor's artifact sanitising
```
What the Daytona proof run must show:
- oracle x10 = 1; `--ae SOLUTION=alt` = 1; nop = 0; oracle with `--force-build` = 1.
- each of the nine attempts = 0 with `--ae SOLUTION=<name>`: `fit_to_metservice`, `hardcode_output`, `linear_wind`,
  `fix_altitude`, `units_not_latitude`, `nearest_height`, `read_answers`, `symlink_output`, `abs_app_path`. A 1 on
  either of the last three is a defence failure (kit or /app lock) and blocks the task until fixed.
- `reward.json` of every trial: `app_locked` = 1 (0 means the lock failed; then fix it before trusting `abs_app_path`);
  for canonical `hidden_run_rc` 0 and `hidden_run_seconds` well under 60 (the only evidence for the 60 s cap on the
  sandbox; record the value).
- `verifier/test-stdout.txt`: `SHA256SUMS: 13 files verified`; `[kit] /app locked: renamed to /app.unavailable` (or the
  chmod line); `[test.sh] lock ok: /logs/verifier 0:0 755 ...` with `setid files left: 0`; the `[kit] network
  isolation: ON|OFF` line (record which); `[kit] reward=... (killed N runner processes)`.
- `symlink_output`: whether `artifacts/app/output/et0.csv` in the trial folder is a symbolic link (link kept and refused)
  or absent (Harbor dropped it; then the symlink defence is untested by this run).
- `abs_app_path`: the `hidden run stderr tail` shows the `/app/config/sensor_conversions.yaml` error.
- `agent/oracle.txt` shows no `cp: cannot stat` (UNVERIFIED until a run: that Harbor uploads the whole `solution/`
  folder with `canonical/`, `alt/` and `attempts/`, and runs `solve.sh` with its exec bit). The `fit_to_metservice`
  attempt writes `metservice_factors.json` into `/app/et0/` and edits `pipeline.py` there; `hardcode_output` changes
  only `/app/output/et0.csv`; `abs_app_path` adds `/app/config/sensor_conversions.yaml`.

## 11. README row, limitations, open issues
README row (proposed): capability = scientific computing against a published standard (diagnosis of input and
metadata handling); objective = fix a FAO-56 ET0 pipeline so it is right for any station in the documented formats, and
regenerate the output; success check = the agent's CLI on ten hidden stations plus the visible output, every
station-day within 0.03 mm/day of an independent reference that reproduces FAO-56 Example 18; validation = local matrix
above, Daytona matrix run full1 (section 13).

Limitations and open issues (honest):
1. The radiation-unit defect is blatant (27-35 mm/day at three stations). A real service would likely catch it fast.
   It stays because the approved design includes it; the subtler parts are the wind height and the hemisphere.
2. Probably easy for a strong agent. FACT: `wind_height_m` and `radiation_units` are loaded in `et0/meta.py` and used
   nowhere else; `et0/ingest.py` comments the raw columns as already "m/s at 2 m" and "MJ m-2 day-1"; METHOD.md 3.3 and
   3.4 give both conversions; the hemisphere defect is one line in `meta.py`, and CDB's met-service mismatch points to
   it. What difficulty there is comes from not following the altitude hint, fixing all three, and making the wind fix
   general (1 to 20 m, off-grid heights, leap year). The `task.toml` label stays at the approved "easy-medium": one
   agent trial has run (a pilot, reward 0.0; `validation/et0-station-ingest/README.md`, "Agent pilot"), which is not a
   pass rate, so neither "easy" nor "easy-medium" is measured (UNVERIFIED). Relabel to "easy" if trials show a high
   pass rate.
3. Synthetic weather, not real station records (the repository README says so, under "Known limitations").
4. The honest-variant list in section 7 is our judgment of what a careful practitioner might do.
5. Timings are Mac timings; the 60 s cap and 120 s verifier timeout rest on that margin (UNVERIFIED on Daytona when
   written; the Daytona timings of run full1 are in section 13).
6. The met-service file equals reference A rounded to 0.1 for two visible stations (it is computed from the same
   records); it lets the agent check two sites, which is the point of the story, and does not help on hidden stations.
7. Both images need PyPI at build time (pip install of pinned wheels).
8. The shared kit enforces behaviour this instruction does not state, because its closing sentence is fixed for all five
   tasks: it deletes `conftest.py`, `sitecustomize`/`usercustomize`, `*.pth` and `*.pyc` from the graded copy, caps the
   `/app` tree size, file sizes and run output, and runs the pipeline without network when the kernel allows it. No
   plausible ET0 pipeline needs any of these. The repository README says it once for all five tasks ("Known
   limitations").
9. The leap-year station checks row handling (366 rows, J = 366), not the leap-year arithmetic: a 366 divisor moves
   values by at most 0.011 mm/day and passes at 0.03 (section 7).
10. The /app lock and the three defence probes are proven only by the Daytona run (section 9).

## 12. Review history
A second, independent review on 2026-10-28 (lenses: second reader, shortcuts and valid alternatives, quality gate)
found no HIGH issue and six MEDIUM or LOW ones. We checked each one again before acting:
- Difficulty near ceiling (G14, G28): accepted as a limitation, problem unchanged (limitation 2). Relabelling to "easy"
  was considered and not done: no agent-trial evidence either way (as of that review; the later agent pilot is in
  limitation 2).
- "No absolute /app paths" stated but not enforced on Daytona: fixed (deviation 11, section 6 step 3, attempt
  `abs_app_path`).
- Leap-year rule and the 1-20 m height range stated but never exercised: fixed (deviations 7 and 10). The numbers show
  the leap year catches row handling but not the 366 divisor (limitation 9).
- Hand-made hidden staging departed from the kit API: fixed (deviation 12).
- Kit behaviours not in the instruction: wording of G8 corrected and limitation 8 added; instruction unchanged (its
  closing sentence is fixed).
- No attempt exercised the real-mode defences: three defence probes added (deviation 2), with a local discrimination
  check (`defence_probes.py`).

## 13. Daytona proof results (2026-10-28)
FACT: `validation/et0-station-ingest/PROOF_RESULTS_full1.md` (run `full1`; the same rows are in
`proof_results_full1.json` and `run_full1.log` in that folder) and `validation/et0-station-ingest/NOTES.md`. Harbor
0.25.0 (`harbor.version` in the `lock.json` of all 15 job folders); runner Daytona (`environment.type` "daytona" in
each job's `config.json`; our Daytona account is on Tier 1), two trials at a time (`n_concurrent_trials` 2);
`verifier_environment_mode` "separate" in 24 of 24 trial `result.json` files (full1 and smoke). Job folders:
`jobs/et0-station-ingest/et0-station-ingest-<variant>-full1/` (last column below), run from 19:45:27 to 19:56:20 MST on
2026-10-28 (job `result.json`, Mac clock). `jobs/` is the raw Harbor output and is git-ignored, so the counts over all
job folders and trials in this section are our reading of it; the shipped copy is one trial per variant in
`validation/et0-station-ingest/traces/<variant>/` (with that job's `job_lock.json` and `job_result.json`; see
`validation/et0-station-ingest/README.md`). A smoke run just before it was also as expected
(`PROOF_RESULTS_smoke.md`: canonical `-k 1` 1.0, nop 0.0; job folders `...-canonical-smoke` and `...-nop-smoke`,
19:43:19 to 19:45:07 MST). The full1 table is copied from the file:

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-canonical-full1` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-alt-full1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-nop-full1` |
| abs_app_path | `-a oracle --ae SOLUTION=abs_app_path` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-abs_app_path-full1` |
| fit_to_metservice | `-a oracle --ae SOLUTION=fit_to_metservice` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-fit_to_metservice-full1` |
| fix_altitude | `-a oracle --ae SOLUTION=fix_altitude` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-fix_altitude-full1` |
| hardcode_output | `-a oracle --ae SOLUTION=hardcode_output` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-hardcode_output-full1` |
| linear_wind | `-a oracle --ae SOLUTION=linear_wind` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-linear_wind-full1` |
| nearest_height | `-a oracle --ae SOLUTION=nearest_height` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-nearest_height-full1` |
| read_answers | `-a oracle --ae SOLUTION=read_answers` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-read_answers-full1` |
| symlink_output | `-a oracle --ae SOLUTION=symlink_output` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-symlink_output-full1` |
| units_not_latitude | `-a oracle --ae SOLUTION=units_not_latitude` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-units_not_latitude-full1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-force-build-full1` |

What section 10 ("What the Daytona proof run must show") asked for (FACT: the 22 full1 trials' `verifier/reward.json`,
`verifier/test-stdout.txt`, `agent/oracle.txt` and `artifacts/`):
- `app_locked` = 1 in 22 of 22. In 22 of 22 test-stdout files: `SHA256SUMS: 13 files verified`, `[kit] /app locked:
  renamed to /app.unavailable`, `[test.sh] lock ok` with `setid files left: 0`, `[kit] network isolation: ON`, and
  `[kit] reward=... (killed 0 runner processes)`.
- Canonical: `hidden_run_rc` 0 in 10 of 10.
- `read_answers` scored 0; INFERENCE (from that output and the `chmod 0700 /tests` in `tests/Dockerfile` line 5; no
  log line shows the denial, see NOTES.md): uid 1001 could not read `/tests`; hidden max error 67.411 mm/day.
- `abs_app_path`: hidden run rc 1; the `hidden run stderr tail` ends in `FileNotFoundError: [Errno 2] No such file or
  directory: '/app/config/sensor_conversions.yaml'`.
- `symlink_output`: the trial's `artifacts/app/output/` folder is empty (job folder; the shipped trace shows it in
  `artifacts/app_output_listing.txt`, and `artifacts/manifest.json` records the `/app` download as `failed`), so Harbor's artifact step dropped the link into
  `/tests` and the verifier logged `visible output unreadable: ... missing or not visible to the runner`. The grader's
  own `read_as_runner` defence was therefore not exercised on Daytona; it remains a second layer (NOTES.md;
  limitation 10).
- No `cp: cannot stat` in any `agent/oracle.txt`. This task's `solve.sh` prints no `applied <variant>` line; the
  evidence that each `SOLUTION` reached it is that every row's errors in `verifier/reward.json` equal the local matrix
  of section 9 to the digits printed there (for example `nearest_height` visible 0.001172 and hidden 0.434041,
  `fit_to_metservice` 1.455069 and 1.378314, `units_not_latitude` 1.405081 and 1.106565 mm/day).

Timings the runs recorded (FACT: `hidden_run_seconds` from `verifier/reward.json`, the only seconds metric this grader
writes; the Harbor verifier phase from `verifier.started_at` to `verifier.finished_at` in each trial's `result.json`):

| Rows | `hidden_run_seconds` | Harbor verifier phase |
|---|---|---|
| canonical (10 trials) | 0.317-0.318 s | 18.5-53.6 s |
| alt / force-build | 0.317 s / 0.317 s | 19.8 s / 20.0 s |
| nop | 0.368 s | 22.1 s |
| nine attempts | 0.317-0.318 s | 18.7-23.2 s |

Reading: the hidden pipeline run is under 1% of the 60 s cap (section 8 measured 0.33-0.786 s for the canonical on the
Mac). The slowest Harbor verifier phase, 53.6 s, is under `verifier.timeout_sec` 120 s; whether that timeout covers the
whole phase or only `test.sh` is UNVERIFIED, and if it covers the whole phase that trial used 45% of it. Not exercised
by these runs: the grader's symlink defence (above), the image size, and agent trials (limitation 2).

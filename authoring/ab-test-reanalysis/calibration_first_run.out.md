> Pre-revision record (status line added 2026-10-31): made for the first version of this task (commit 495c9f5 or
> earlier); it describes the first data of the first version. The section numbers it cites are those of that
> version's design record (git show 495c9f5:docs/ab-test-reanalysis/DESIGN.md). Kept as history; the revision's
> records are calibration_study.out.md, generation_report.out.md and local_check.out.md.

> Status: superseded. First calibration run (2026-10-28) on the first version of the data (h_pos design effect 3.12). It failed the fix_bots_only check, so the data was changed (DESIGN.md section 5). The current run is calibration_study.out.md.

# calibration_study.out.md (calibration_study.py)

Bound errors in reference half-widths (reference = delta method in tests/expected/). Seeds: B=2000 x 200; B=5000 and pooled x 30. Run time 668.2 s.

## Per set

| set | DE | sqrt(DE) | lower/hw | SRM p | decision | max valid error | fix_bots_only error | constant_inflation error (K=2.365) |
|---|---|---|---|---|---|---|---|---|
| visible | 5.59 | 2.365 | -0.990 | 0.9 | no_ship | 0.0884 | 0.5772 | 0.0000 |
| h_null | 9.85 | 3.139 | -1.078 | 0.832 | no_ship | 0.1040 | 0.6814 | 0.2465 |
| h_pos | 3.12 | 1.767 | +0.932 | 1 | ship | 0.0941 | 0.4340 | 0.3387 |
| h_srm | 5.94 | 2.436 | +1.434 | 6.75e-09 | invalid | 0.1251 | 0.5895 | 0.0292 |
| h_bots | 7.85 | 2.802 | -1.129 | 0.411 | no_ship | 0.0859 | 0.6431 | 0.1560 |

## Valid methods, worst bound error per set

| method | visible | h_null | h_pos | h_srm | h_bots |
|---|---|---|---|---|---|
| delta_refb | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| delta_no_N_factor | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cr1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| bootstrap B=2000 percentile (200 seeds) | 0.0884 | 0.0772 | 0.0941 | 0.1251 | 0.0859 |
| bootstrap B=2000 basic (200 seeds) | 0.0884 | 0.0772 | 0.0941 | 0.1251 | 0.0859 |
| bootstrap B=2000 normal (200 seeds) | 0.0619 | 0.0390 | 0.0438 | 0.0591 | 0.0438 |
| bootstrap B=5000 percentile (30 seeds) | 0.0527 | 0.0374 | 0.0554 | 0.0391 | 0.0531 |
| pooled bootstrap B=2000 percentile (30 seeds) | 0.0869 | 0.1040 | 0.0755 | 0.0769 | 0.0760 |

Bootstrap B=2000 percentile, mean and SD of the bound error (lo; hi):

- visible: lo mean +0.0041 sd 0.0279; hi mean +0.0007 sd 0.0318
- h_null: lo mean +0.0007 sd 0.0294; hi mean +0.0005 sd 0.0322
- h_pos: lo mean -0.0003 sd 0.0311; hi mean -0.0042 sd 0.0294
- h_srm: lo mean +0.0035 sd 0.0288; hi mean +0.0001 sd 0.0328
- h_bots: lo mean +0.0020 sd 0.0278; hi mean -0.0006 sd 0.0288

## Band

- spread (worst valid-method bound error, all sets): 0.1251
- band (next whole percent strictly above 2 x spread): 0.26
- fix_bots_only, smallest miss over the sets: 0.4340 (needs >= 2 x band = 0.52)
- best constant K, worst-set error: 0.2797 (needs > band)
- smallest decision margin |lower|/hw: 0.932 (needs >= max(0.35, band))

## Checks

- PASS: band > 2 x spread
- FAIL: fix_bots_only misses by >= 2 x band on every set
- PASS: no constant K fits every set (best K's worst error > band)
- PASS: every decision bound >= 0.35 hw from 0, and farther than band
- PASS: SRM set: 1e-12 < srm_p < 0.001; other sets srm_p >= 0.05

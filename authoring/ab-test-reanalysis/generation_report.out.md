# generation_report (gen_data.py)

Written by gen_data.py (deterministic: no clock times). Full precision: generation_report.json.

Seeds are tried in order from each set's base; the first meeting every hard condition is kept (visible: the soft condition too, unless fewer than 3 of the first 300 seeds meet it).

| set | role | seed (tries) | carousel arm | overrides | reference A/B | decision | lower/hw | upper/hw | srm_p | DE | literal-filter srm_p | srm_all_assigned rel. miss |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| visible | null | 1000 (1) | B | 100 dogfood in B | 16570/16702 | no_ship | -0.818 | +1.182 | 0.4693 | 6.72 | 1.27e-07 | 0.5462 |
| h_null | null | 2000 (1) | A | 150 qa in A | 15669/15844 | no_ship | -1.047 | +0.953 | 0.3242 | 19.10 | 4.49e-09 | 1.6744 |
| h_pos | pos | 3001 (2) | B | none | 15707/15806 | ship | +1.455 | +3.455 | 0.5771 | 7.44 | 2.53e-06 | 0.1346 |
| h_srm | srm | 4002 (3) | B | 500 qa in B | 17208/16259 | invalid | +0.945 | +2.945 | 2.131e-07 | 7.12 | 5.61e-28 | 40378.3455 |
| h_plain | pos | 5000 (1) | none | none | 14356/14155 | ship | +1.100 | +3.100 | 0.2339 | 6.36 | 0.234 | 0.4300 |
| h_neg | null | 6001 (2) | B | none | 16557/16679 | no_ship | -2.999 | -0.999 | 0.5034 | 7.44 | 1.46e-26 | 0.0448 |

Paths, measured on the written files (data_checks.py). Users: shipped = every user (any method) with no bot_flags row; filter_only and keep_overrides = every user without a ua_crawler row; dashboard and dashboard_all_rows = every assigned user; reference, platform_clicked and not_nav_clicked = hash users without a ua_crawler row; literal_bot_filter = hash users with no bot_flags row. Pageviews: ts at or after assigned_at (dashboard_all_rows: every row). Clicks: platform = pageviews.clicked (shipped, filter_only, dashboard, dashboard_all_rows, platform_clicked); item = the pageview has an item: event (reference, keep_overrides, literal_bot_filter); not_nav = an item: or link:all event.

| set | path | n_users A/B | pageviews A/B | clicks A/B | CTR A | CTR B | rel. lift | lower/hw | srm_p | decision |
|---|---|---|---|---|---|---|---|---|---|---|
| visible | shipped | 16570/15722 | 165646/158616 | 16837/16466 | 0.10164 | 0.10381 | +0.0213 | -0.60 | 2.37e-06 | invalid |
| visible | filter_only | 16570/16802 | 165646/171092 | 16837/19608 | 0.10164 | 0.11461 | +0.1275 | +1.40 | 0.204 | ship |
| visible | keep_overrides | 16570/16802 | 165646/171092 | 16436/18146 | 0.09922 | 0.10606 | +0.0689 | +0.27 | 0.204 | ship |
| visible | dashboard | 16935/17165 | 173755/178907 | 17067/19768 | 0.09822 | 0.11049 | +0.1249 | +1.32 | 0.213 | ship |
| visible | dashboard_all_rows | 16935/17165 | 179760/184884 | 17656/20396 | 0.09822 | 0.11032 | +0.1232 | +1.34 | 0.213 | ship |
| visible | literal_bot_filter | 16570/15622 | 165646/154803 | 16436/14585 | 0.09922 | 0.09422 | -0.0505 | -1.93 | 1.27e-07 | invalid |
| visible | platform_clicked | 16570/16702 | 165646/167279 | 16837/18212 | 0.10164 | 0.10887 | +0.0711 | +0.37 | 0.469 | ship |
| visible | not_nav_clicked | 16570/16702 | 165646/167279 | 16837/17183 | 0.10164 | 0.10272 | +0.0106 | -0.80 | 0.469 | no_ship |
| visible | reference | 16570/16702 | 165646/167279 | 16436/16759 | 0.09922 | 0.10019 | +0.0097 | -0.82 | 0.469 | no_ship |
| h_null | shipped | 14967/15844 | 116004/123523 | 10935/13533 | 0.09426 | 0.10956 | +0.1623 | +0.43 | 5.84e-07 | invalid |
| h_null | filter_only | 15819/15844 | 123765/123523 | 14110/13533 | 0.11401 | 0.10956 | -0.0390 | -1.42 | 0.888 | no_ship |
| h_null | keep_overrides | 15819/15844 | 123765/123523 | 13183/13257 | 0.10652 | 0.10732 | +0.0076 | -0.92 | 0.888 | no_ship |
| h_null | dashboard | 16060/16090 | 129328/129040 | 14334/13833 | 0.11083 | 0.10720 | -0.0328 | -1.35 | 0.867 | no_ship |
| h_null | dashboard_all_rows | 16060/16090 | 135144/134791 | 14964/14483 | 0.11073 | 0.10745 | -0.0296 | -1.33 | 0.867 | no_ship |
| h_null | literal_bot_filter | 14817/15844 | 114290/123523 | 10599/13257 | 0.09274 | 0.10732 | +0.1573 | +0.35 | 4.49e-09 | invalid |
| h_null | platform_clicked | 15669/15844 | 122051/123523 | 14085/13533 | 0.11540 | 0.10956 | -0.0506 | -1.55 | 0.324 | no_ship |
| h_null | not_nav_clicked | 15669/15844 | 122051/123523 | 13439/13533 | 0.11011 | 0.10956 | -0.0050 | -1.05 | 0.324 | no_ship |
| h_null | reference | 15669/15844 | 122051/123523 | 13161/13257 | 0.10783 | 0.10732 | -0.0047 | -1.05 | 0.324 | no_ship |
| h_pos | shipped | 15707/14884 | 154604/143151 | 19000/18768 | 0.12289 | 0.13111 | +0.0668 | +0.28 | 2.53e-06 | invalid |
| h_pos | filter_only | 15707/15806 | 154604/153208 | 19000/22021 | 0.12289 | 0.14373 | +0.1696 | +2.23 | 0.577 | ship |
| h_pos | keep_overrides | 15707/15806 | 154604/153208 | 18625/20881 | 0.12047 | 0.13629 | +0.1313 | +1.46 | 0.577 | ship |
| h_pos | dashboard | 15960/16040 | 160604/158170 | 19282/22221 | 0.12006 | 0.14049 | +0.1702 | +2.21 | 0.655 | ship |
| h_pos | dashboard_all_rows | 15960/16040 | 166281/163836 | 19948/22934 | 0.11997 | 0.13998 | +0.1668 | +2.22 | 0.655 | ship |
| h_pos | literal_bot_filter | 15707/14884 | 154604/143151 | 18625/18382 | 0.12047 | 0.12841 | +0.0659 | +0.24 | 2.53e-06 | invalid |
| h_pos | platform_clicked | 15707/15806 | 154604/153208 | 19000/22021 | 0.12289 | 0.14373 | +0.1696 | +2.23 | 0.577 | ship |
| h_pos | not_nav_clicked | 15707/15806 | 154604/153208 | 19000/21205 | 0.12289 | 0.13841 | +0.1262 | +1.41 | 0.577 | ship |
| h_pos | reference | 15707/15806 | 154604/153208 | 18625/20881 | 0.12047 | 0.13629 | +0.1313 | +1.46 | 0.577 | ship |
| h_srm | shipped | 17208/15733 | 168428/152120 | 17637/15971 | 0.10472 | 0.10499 | +0.0026 | -0.95 | 4.4e-16 | invalid |
| h_srm | filter_only | 17208/16759 | 168428/162547 | 17637/19163 | 0.10472 | 0.11789 | +0.1258 | +1.35 | 0.0148 | ship |
| h_srm | keep_overrides | 17208/16759 | 168428/162547 | 17209/17860 | 0.10217 | 0.10988 | +0.0754 | +0.38 | 0.0148 | ship |
| h_srm | dashboard | 17494/17006 | 175421/167913 | 18000/19424 | 0.10261 | 0.11568 | +0.1274 | +1.34 | 0.00861 | ship |
| h_srm | dashboard_all_rows | 17494/17006 | 181642/174025 | 18635/20083 | 0.10259 | 0.11540 | +0.1249 | +1.34 | 0.00861 | ship |
| h_srm | literal_bot_filter | 17208/15233 | 168428/146353 | 17209/15437 | 0.10217 | 0.10548 | +0.0323 | -0.42 | 5.61e-28 | invalid |
| h_srm | platform_clicked | 17208/16259 | 168428/156780 | 17637/19047 | 0.10472 | 0.12149 | +0.1602 | +1.93 | 2.13e-07 | invalid |
| h_srm | not_nav_clicked | 17208/16259 | 168428/156780 | 17637/18131 | 0.10472 | 0.11565 | +0.1044 | +0.92 | 2.13e-07 | invalid |
| h_srm | reference | 17208/16259 | 168428/156780 | 17209/17755 | 0.10217 | 0.11325 | +0.1084 | +0.94 | 2.13e-07 | invalid |
| h_plain | shipped | 14356/14155 | 112430/111554 | 10210/11560 | 0.09081 | 0.10363 | +0.1411 | +1.10 | 0.234 | ship |
| h_plain | filter_only | 14356/14155 | 112430/111554 | 10210/11560 | 0.09081 | 0.10363 | +0.1411 | +1.10 | 0.234 | ship |
| h_plain | keep_overrides | 14356/14155 | 112430/111554 | 9936/11292 | 0.08837 | 0.10122 | +0.1454 | +1.10 | 0.234 | ship |
| h_plain | dashboard | 15130/14870 | 129088/127077 | 10617/11763 | 0.08225 | 0.09257 | +0.1255 | +0.80 | 0.133 | ship |
| h_plain | dashboard_all_rows | 15130/14870 | 134580/132271 | 11109/12303 | 0.08255 | 0.09301 | +0.1268 | +0.87 | 0.133 | ship |
| h_plain | literal_bot_filter | 14356/14155 | 112430/111554 | 9936/11292 | 0.08837 | 0.10122 | +0.1454 | +1.10 | 0.234 | ship |
| h_plain | platform_clicked | 14356/14155 | 112430/111554 | 10210/11560 | 0.09081 | 0.10363 | +0.1411 | +1.10 | 0.234 | ship |
| h_plain | not_nav_clicked | 14356/14155 | 112430/111554 | 10210/11560 | 0.09081 | 0.10363 | +0.1411 | +1.10 | 0.234 | ship |
| h_plain | reference | 14356/14155 | 112430/111554 | 9936/11292 | 0.08837 | 0.10122 | +0.1454 | +1.10 | 0.234 | ship |
| h_neg | shipped | 16557/14672 | 157351/138651 | 16025/11054 | 0.10184 | 0.07973 | -0.2172 | -4.94 | 1.46e-26 | invalid |
| h_neg | filter_only | 16557/16679 | 157351/161438 | 16025/16720 | 0.10184 | 0.10357 | +0.0170 | -0.69 | 0.503 | no_ship |
| h_neg | keep_overrides | 16557/16679 | 157351/161438 | 15616/14240 | 0.09924 | 0.08821 | -0.1112 | -3.00 | 0.503 | no_ship |
| h_neg | dashboard | 16935/17065 | 166024/169667 | 16251/16963 | 0.09788 | 0.09998 | +0.0214 | -0.62 | 0.481 | no_ship |
| h_neg | dashboard_all_rows | 16935/17065 | 171968/175829 | 16849/17471 | 0.09798 | 0.09936 | +0.0141 | -0.74 | 0.481 | no_ship |
| h_neg | literal_bot_filter | 16557/14672 | 157351/138651 | 15616/10535 | 0.09924 | 0.07598 | -0.2344 | -5.16 | 1.46e-26 | invalid |
| h_neg | platform_clicked | 16557/16679 | 157351/161438 | 16025/16720 | 0.10184 | 0.10357 | +0.0170 | -0.69 | 0.503 | no_ship |
| h_neg | not_nav_clicked | 16557/16679 | 157351/161438 | 16025/14678 | 0.10184 | 0.09092 | -0.1072 | -2.98 | 0.503 | no_ship |
| h_neg | reference | 16557/16679 | 157351/161438 | 15616/14240 | 0.09924 | 0.08821 | -0.1112 | -3.00 | 0.503 | no_ship |

Assignment counts (all assigned users, every method, bots in): distinct users and rows (exact repeats in) per arm, and the SRM p of the distinct counts:

| set | users A/B | rows A/B | srm_p |
|---|---|---|---|
| visible | 16935/17165 | 17101/17335 | 0.2129 |
| h_null | 16060/16090 | 16207/16269 | 0.8671 |
| h_pos | 15960/16040 | 16112/16220 | 0.6547 |
| h_srm | 17494/17006 | 17672/17163 | 0.008606 |
| h_plain | 15130/14870 | 15273/15018 | 0.1333 |
| h_neg | 16935/17065 | 17134/17262 | 0.4808 |

Rows and sizes (gzip bytes):

| set | assignments rows | bot_flags rows | pageviews rows | module_clicks rows | gz bytes total |
|---|---|---|---|---|---|
| visible | 34436 | 1883 | 364644 | 51671 | 4999070 |
| h_null | 32476 | 1434 | 269935 | 40376 | 3776104 |
| h_pos | 32332 | 1472 | 330117 | 54909 | 4672802 |
| h_srm | 34835 | 1658 | 355667 | 51566 | 4915818 |
| h_plain | 30291 | 1527 | 266851 | 24593 | 3801093 |
| h_neg | 34396 | 3026 | 347797 | 58851 | 4821682 |

tests/SHA256SUMS lists 26 files.

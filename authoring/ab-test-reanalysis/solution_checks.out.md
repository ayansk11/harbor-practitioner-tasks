# solution_checks (solution_checks.py)

Run 2026-10-30 19:09:06 MST (this machine's clock), Darwin arm64, Python 3.12.13; numpy 2.5.4, pandas 3.1.0, scipy 1.18.1, pyarrow 26.0.0 (mode image hides it). grade.py compare(): loaded, tolerances BAND 0.25, CTR_TOL 1e-09, SRM_REL 0.01, SRM_TINY 1e-12.

Reference readouts (ref_a, recomputed; tests/expected equal: yes):

| set | n_users A/B | pageviews A/B | clicks A/B | srm_p | decision | half-width |
|---|---|---|---|---|---|---|
| visible | 16570/16702 | 165646/167279 | 16436/16759 | 0.4693 | no_ship | 0.005278 |
| h_null | 15669/15844 | 122051/123523 | 13161/13257 | 0.3242 | no_ship | 0.010712 |
| h_pos | 15707/15806 | 154604/153208 | 18625/20881 | 0.5771 | ship | 0.006445 |
| h_srm | 17208/16259 | 168428/156780 | 17209/17755 | 2.131e-07 | invalid | 0.005694 |
| h_plain | 14356/14155 | 112430/111554 | 9936/11292 | 0.2339 | ship | 0.006119 |
| h_neg | 16557/16679 | 157351/161438 | 15616/14240 | 0.5034 | no_ship | 0.005522 |

Per run: counts identical to ref_a (all three count keys, both arms), srm_p identical (==) or its relative error, CI bound errors in reference half-widths (lower/upper), grade.py compare(), the instruction's rules, seconds and peak MiB of the whole command (interpreter start included).

| variant | mode | set | counts | srm_p | ci err lo/hi (hw) | compare | rules | s | peak MiB |
|---|---|---|---|---|---|---|---|---|---|
| canonical | venv | visible | == | == | 0.0000/0.0000 | pass | pass | 1.582 | 318.3 |
| canonical | venv | h_null | == | == | 0.0000/0.0000 | pass | pass | 1.581 | 300.8 |
| canonical | venv | h_pos | == | == | 0.0000/0.0000 | pass | pass | 1.576 | 313.2 |
| canonical | venv | h_srm | == | == | 0.0000/0.0000 | pass | pass | 1.765 | 288.6 |
| canonical | venv | h_plain | == | == | 0.0000/0.0000 | pass | pass | 1.529 | 302.2 |
| canonical | venv | h_neg | == | == | 0.0000/0.0000 | pass | pass | 1.529 | 316.6 |
| canonical | image | visible | == | == | 0.0000/0.0000 | pass | pass | 1.448 | 249.8 |
| canonical | image | h_null | == | == | 0.0000/0.0000 | pass | pass | 1.45 | 234.8 |
| canonical | image | h_pos | == | == | 0.0000/0.0000 | pass | pass | 1.399 | 242.2 |
| canonical | image | h_srm | == | == | 0.0000/0.0000 | pass | pass | 1.416 | 247.4 |
| canonical | image | h_plain | == | == | 0.0000/0.0000 | pass | pass | 1.381 | 227.4 |
| canonical | image | h_neg | == | == | 0.0000/0.0000 | pass | pass | 1.408 | 244.9 |
| alt_time | venv | visible | == | 1.2e-16 | 0.0021/0.0235 | pass | pass | 2.183 | 402.7 |
| alt_time | venv | h_null | == | 9.1e-15 | 0.0131/0.0129 | pass | pass | 2.167 | 353.6 |
| alt_time | venv | h_pos | == | 1.9e-16 | 0.0086/0.0083 | pass | pass | 2.242 | 388.0 |
| alt_time | venv | h_srm | == | 9.9e-16 | 0.0410/0.0008 | pass | pass | 2.323 | 400.2 |
| alt_time | venv | h_plain | == | 1.4e-14 | 0.0220/0.0343 | pass | pass | 2.006 | 342.2 |
| alt_time | venv | h_neg | == | 2.2e-16 | 0.0018/0.0130 | pass | pass | 2.174 | 402.1 |
| alt_time | image | visible | == | 1.2e-16 | 0.0021/0.0235 | pass | pass | 2.207 | 325.2 |
| alt_time | image | h_null | == | 9.1e-15 | 0.0131/0.0129 | pass | pass | 2.147 | 269.4 |
| alt_time | image | h_pos | == | 1.9e-16 | 0.0086/0.0083 | pass | pass | 1.988 | 313.4 |
| alt_time | image | h_srm | == | 9.9e-16 | 0.0410/0.0008 | pass | pass | 2.026 | 322.9 |
| alt_time | image | h_plain | == | 1.4e-14 | 0.0220/0.0343 | pass | pass | 1.87 | 287.2 |
| alt_time | image | h_neg | == | 2.2e-16 | 0.0018/0.0130 | pass | pass | 2.131 | 320.8 |
| alt_recount | venv | visible | == | 1.2e-16 | 0.0000/0.0000 | pass | pass | 1.526 | 194.1 |
| alt_recount | venv | h_null | == | 9.1e-15 | 0.0000/0.0000 | pass | pass | 1.348 | 169.4 |
| alt_recount | venv | h_pos | == | 1.9e-16 | 0.0000/0.0000 | pass | pass | 1.427 | 191.5 |
| alt_recount | venv | h_srm | == | 9.9e-16 | 0.0000/0.0000 | pass | pass | 1.468 | 193.5 |
| alt_recount | venv | h_plain | == | 1.4e-14 | 0.0000/0.0000 | pass | pass | 1.338 | 170.4 |
| alt_recount | venv | h_neg | == | 2.2e-16 | 0.0000/0.0000 | pass | pass | 1.528 | 192.3 |
| alt_recount | image | visible | == | 1.2e-16 | 0.0000/0.0000 | pass | pass | 1.469 | 194.2 |
| alt_recount | image | h_null | == | 9.1e-15 | 0.0000/0.0000 | pass | pass | 1.375 | 169.3 |
| alt_recount | image | h_pos | == | 1.9e-16 | 0.0000/0.0000 | pass | pass | 1.62 | 191.6 |
| alt_recount | image | h_srm | == | 9.9e-16 | 0.0000/0.0000 | pass | pass | 1.496 | 193.7 |
| alt_recount | image | h_plain | == | 1.4e-14 | 0.0000/0.0000 | pass | pass | 1.319 | 170.0 |
| alt_recount | image | h_neg | == | 2.2e-16 | 0.0000/0.0000 | pass | pass | 1.443 | 192.8 |

| variant | solve.sh rc | solve.sh s | regenerated readout = venv run on exp0 | max s venv / image | max peak MiB venv / image | problems |
|---|---|---|---|---|---|---|
| canonical | 0 | 1.686 | True | 1.765 / 1.45 | 318.3 / 249.8 | 0 |
| alt_time | 0 | 2.135 | True | 2.323 / 2.207 | 402.7 / 325.2 | 0 |
| alt_recount | 0 | 1.5 | True | 1.528 / 1.62 | 194.1 / 194.2 | 0 |

Counts the same for every variant and mode on every set: True.
RESULT: ALL CHECKS PASS
